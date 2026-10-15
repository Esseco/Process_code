"""H enumeration and bounded cheap electrostatic initialization; no model loading."""

from fractions import Fraction
import itertools
import math
import random

import numpy as np
from pymatgen.core import Structure, Element

from .common import digest, options, occupation_key, freeze_model


def normalize_H(value):
    array = np.asarray(value, dtype=float)
    if array.shape == (2, 2):
        expanded = np.eye(3)
        expanded[:2, :2] = array
        array = expanded
    if (
        array.shape != (3, 3)
        or not np.isfinite(array).all()
        or not np.equal(array, np.rint(array)).all()
    ):
        raise ValueError("H must be an integer 2x2 or 3x3 matrix")
    determinant = int(round(np.linalg.det(array)))
    if determinant <= 0:
        raise ValueError("H must have a positive determinant")
    return array.astype(int).tolist()


def select_matrices(reference, *, max_det_H=None, h_matrices=None, min_distance=2):
    if (max_det_H is None) == (h_matrices is None):
        raise ValueError("Specify exactly one of max_det_H or h_matrices")
    if h_matrices is not None:
        values = h_matrices
        if np.asarray(values).shape in {(2, 2), (3, 3)}:
            values = [values]
        if not isinstance(values, (tuple, list)) or not values:
            raise ValueError("h_matrices must contain at least one H")
        matrices = [normalize_H(value) for value in values]
    else:
        if type(max_det_H) is not int or max_det_H <= 0:
            raise ValueError("max_det_H must be a positive integer")
        from icet.tools.structure_enumeration import enumerate_supercells
        from pymatgen.io.ase import AseAtomsAdaptor

        atoms = AseAtomsAdaptor.get_atoms(reference)
        atoms.pbc = [True, True, False]
        matrices = []
        for cell in enumerate_supercells(atoms, sizes=list(range(1, max_det_H + 1))):
            matrix = np.asarray(cell.cell) @ np.linalg.inv(np.asarray(atoms.cell))
            if not np.allclose(matrix, np.rint(matrix), atol=1e-7):
                raise ValueError("Enumerator returned a noninteger H")
            H = normalize_H(np.rint(matrix))
            if H[2] != [0, 0, 1] or H[0][2] or H[1][2]:
                raise ValueError("Enumerator returned non-in-plane H")
            matrices.append(H)
    unique = {tuple(itertools.chain.from_iterable(H)): H for H in matrices}
    result, skipped = [], []
    for H in sorted(unique.values(), key=lambda H: (round(np.linalg.det(H)), H)):
        supercell = reference.copy()
        supercell.make_supercell(H)
        # LLL reduction bounds skewed explicit matrices without a finite coefficient cutoff.
        reduced = supercell.lattice.get_lll_reduced_lattice()
        shortest = min(
            float(np.linalg.norm(np.asarray(v) @ reduced.matrix))
            for v in itertools.product((-1, 0, 1), repeat=3)
            if any(v)
        )
        if shortest / 2 < min_distance:
            skipped.append(
                {"H": H, "reason": "periodic_distance_below_minimum", "distance": shortest}
            )
        else:
            result.append(H)
    return result, skipped


def build_structure(matrix, occupation):
    reference = Structure.from_dict(matrix["reference"])
    tm_sites = matrix["tm_sites"]
    for index, symbol in zip(tm_sites, occupation["tm"], strict=True):
        reference.replace(index, symbol)
    removed = {
        site
        for site, present in zip(matrix["na_sites"], occupation["na"], strict=True)
        if not present
    }
    site_ids = [i for i in range(len(reference)) if i not in removed]
    reference.remove_sites(sorted(removed, reverse=True))
    reference.add_site_property("ordering_reference_id", site_ids)
    return reference


def random_occupation(matrix, rng):
    labels = [symbol for symbol, count in matrix["tm_counts"].items() for _ in range(count)]
    rng.shuffle(labels)
    if matrix["move_kind"] == "tm_only" and matrix.get("fixed_na") is not None:
        na = list(matrix["fixed_na"])
    else:
        na = [1] * matrix["na_count"] + [0] * (len(matrix["na_sites"]) - matrix["na_count"])
        rng.shuffle(na)
    return {"na": na, "tm": labels}


def _charge_scheme(matrix, occupation, supplied):
    candidate = build_structure(matrix, occupation)
    if supplied is None:
        guesses = candidate.composition.oxi_state_guesses()
        if not guesses:
            raise ValueError(
                "pymatgen could not infer neutral oxidation states; supply oxidation_states"
            )
        scheme = {str(k): float(v) for k, v in guesses[0].items()}
        source = "pymatgen_oxi_state_guesses"
    else:
        scheme = {str(k): float(v) for k, v in supplied.items()}
        source = "provided_oxidation_states"
    missing = set(candidate.composition.get_el_amt_dict()) - set(scheme)
    if missing or any(not math.isfinite(v) for v in scheme.values()):
        raise ValueError("Missing/nonfinite oxidation states: " + str(sorted(missing)))
    charge = sum(
        scheme[symbol] * count for symbol, count in candidate.composition.get_el_amt_dict().items()
    )
    if abs(charge) > 1e-6:
        raise ValueError(f"Oxidation states are not neutral: charge={charge}")
    return scheme, source


def initialize(matrix, config, supplied_charges):
    from pymatgen.analysis.ewald import EwaldSummation

    rng = random.Random(config["seed"] + int(matrix["matrix_id"][:8], 16))
    occupations = {}
    limit = min(
        matrix["joint_space_size"], max(config["initial_pool_size"], config["chains_per_H"])
    )
    for _ in range(max(100, limit * 100)):
        occupation = random_occupation(matrix, rng)
        occupations.setdefault(occupation_key(occupation), occupation)
        if len(occupations) >= limit:
            break
    if not occupations:
        raise ValueError("No legal initial occupations")
    charges, source = _charge_scheme(matrix, next(iter(occupations.values())), supplied_charges)
    # One geometric Ewald matrix serves every neutral fixed-composition occupation.
    template = Structure.from_dict(matrix["reference"])
    template.unset_charge()
    template.add_oxidation_state_by_site([1.0] * len(template))
    interaction = EwaldSummation(template).total_energy_matrix
    reference = Structure.from_dict(matrix["reference"])

    def score_occupation(occupation):
        vector = np.array([charges.get(site.specie.symbol, 0.0) for site in reference])
        for site, symbol in zip(matrix["tm_sites"], occupation["tm"], strict=True):
            vector[site] = charges[symbol]
        for site, present in zip(matrix["na_sites"], occupation["na"], strict=True):
            vector[site] = charges.get("Na", 0.0) if present else 0.0
        return float(vector @ interaction @ vector)

    scored = [(score_occupation(o), occupation_key(o), o) for o in occupations.values()]
    scored.sort(key=lambda row: (row[0], row[1]))
    if matrix["move_kind"] == "tm_only":
        matrix["fixed_na"] = scored[0][2]["na"]
        matrix["space_size"] = matrix["tm_space_size"]
        # All TM-only chains must share the SAME frozen Na arrangement.
        for _, _, occupation in scored:
            occupation["na"] = list(matrix["fixed_na"])
        # Regenerate and re-score after freezing the lowest-scored Na pattern.
        occupations = {occupation_key(o): o for _, _, o in scored}
        scored = []
        for key, occupation in occupations.items():
            scored.append((score_occupation(occupation), key, occupation))
        scored.sort(key=lambda row: (row[0], row[1]))
    count = min(config["chains_per_H"], len(scored))
    explore = (
        min(count - 1, math.ceil(count * config["initial_exploration_fraction"]))
        if len(scored) > count
        else 0
    )
    selected = scored[: count - explore]
    remaining = scored[count - explore :]
    if explore:
        selected += rng.sample(remaining, explore)
    matrix.update(
        initial_occupations=[row[2] for row in selected],
        initial_ewald_energies=[row[0] for row in selected],
        charge_scheme=charges,
        charge_source=source,
        tm_charge_discriminating=len({charges[s] for s in matrix["tm_counts"]}) > 1,
        initial_pool_evaluated=len(scored),
    )


def make_plan(
    reference,
    *,
    phase,
    tm_ratios,
    na_content,
    max_det_H=None,
    h_matrices=None,
    oxidation_states=None,
    model=None,
    search_options=None,
):
    reference = (
        reference.copy() if isinstance(reference, Structure) else Structure.from_file(reference)
    )
    reference.remove_oxidation_states()
    reference.unset_charge()
    if not reference.is_ordered:
        raise ValueError(
            "Reference must have explicit ordered sites, including all candidate Na sites"
        )
    composition = reference.composition.get_el_amt_dict()
    tm_count = sum(count for symbol, count in composition.items() if symbol not in {"Na", "O"})
    if (
        composition.get("Na", 0) != tm_count
        or composition.get("O", 0) != 2 * tm_count
        or not tm_count
    ):
        raise ValueError("Reference must be a full-Na NaTMO2 site template")
    phase = str(phase).strip().upper()
    if not phase or not tm_ratios:
        raise ValueError("phase and tm_ratios are required")
    ratios = {str(symbol): Fraction(str(value)) for symbol, value in tm_ratios.items()}
    if any(value <= 0 for value in ratios.values()):
        raise ValueError("TM ratios must be positive")
    for symbol in ratios:
        if not Element(symbol).is_transition_metal:
            raise ValueError("Not a transition metal: " + symbol)
    x = Fraction(str(na_content))
    if not 0 <= x <= 1:
        raise ValueError("na_content must lie between 0 and 1 Na/O2")
    config = options(search_options)
    model = freeze_model(model)
    matrices, skipped = select_matrices(
        reference, max_det_H=max_det_H, h_matrices=h_matrices, min_distance=config["min_distance"]
    )
    items = []
    for H in matrices:
        full = reference.copy()
        full.make_supercell(H)
        tm_sites = [i for i, s in enumerate(full) if s.specie.symbol not in {"Na", "O"}]
        na_sites = [i for i, s in enumerate(full) if s.specie.symbol == "Na"]
        counts = {
            symbol: len(tm_sites) * ratio / sum(ratios.values()) for symbol, ratio in ratios.items()
        }
        na_count = x * sum(s.specie.symbol == "O" for s in full) / 2
        if (
            not tm_sites
            or any(v.denominator != 1 for v in counts.values())
            or na_count.denominator != 1
        ):
            skipped.append({"H": H, "reason": "composition_not_integral"})
            continue
        if not 0 <= na_count <= len(na_sites):
            skipped.append({"H": H, "reason": "reference_has_insufficient_Na_sites"})
            continue
        counts = {s: int(v) for s, v in sorted(counts.items())}
        tm_space = math.factorial(len(tm_sites)) // math.prod(
            math.factorial(c) for c in counts.values()
        )
        na_space = math.comb(len(na_sites), int(na_count))
        move = config["move_kind"]
        if move == "auto":
            move = "na_tm" if 0 < na_count < len(na_sites) else "tm_only"
        if na_space == 1:
            move = "tm_only"
        item = {
            "matrix_id": digest(H)[:16],
            "H": H,
            "det_H": int(round(np.linalg.det(H))),
            "reference": full.as_dict(),
            "tm_sites": tm_sites,
            "na_sites": na_sites,
            "tm_counts": counts,
            "na_count": int(na_count),
            "move_kind": move,
            "tm_space_size": tm_space,
            "joint_space_size": tm_space * na_space,
            "space_size": tm_space * na_space if move == "na_tm" else tm_space,
        }
        initialize(item, config, oxidation_states)
        items.append(item)
    if not items:
        raise ValueError("No legal H remain: " + str(skipped))
    payload = {
        "schema_version": 1,
        "phase": phase,
        "na_content": str(x),
        "tm_ratios": {s: str(v) for s, v in ratios.items()},
        "model": dict(model),
        "options": config,
        "matrices": items,
        "skipped": skipped,
        "scope_kind": "explicit_H" if h_matrices is not None else "max_det_H",
        "max_det_H": max_det_H,
    }
    payload["workload"] = {
        "matrix_count": len(items),
        "chain_count": sum(len(row["initial_occupations"]) for row in items),
        "maximum_mlip_evaluations": sum(
            min(row["space_size"], len(row["initial_occupations"]) * (config["max_steps"] + 1))
            for row in items
        ),
        "maximum_parallel_model_instances": config["workers"],
    }
    payload["plan_id"] = digest(payload)
    return payload
