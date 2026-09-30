from collections.abc import Iterable
from fractions import Fraction
import random
import warnings

import pandas as pd
from pymatgen.analysis.structure_matcher import StructureMatcher
from pymatgen.core import Element, Species, Structure
from pymatgen.transformations.standard_transformations import (
    OrderDisorderedStructureTransformation,
)


def gen_ESGS_structure(disordered_structure: Structure, nstr: int) -> list:
    """
    gen_ESGS_structure 的 Docstring

    :param disordered_structure: disorderd struct
    :type disordered_structure: Structure
    :param nstr: generate nstr structs
    :type nstr: int
    :return: struct_lsit
    :rtype: list
    """
    # symmetrized_structure = SpacegroupAnalyzer(disordered_structure).get_symmetrized_structure()
    order = OrderDisorderedStructureTransformation(algo=2, no_oxi_states=False)
    ordered_structure_dict = order.apply_transformation(disordered_structure, nstr)
    structure_lst = [
        str_dict["structure"] for ind, str_dict in enumerate(ordered_structure_dict)
    ]
    print(
        f"{len(ordered_structure_dict)} electrostatic ground statete structures found."
    )
    return structure_lst


def deduplicate(struc_lst: list) -> list:
    """
    deduplicate 的 Docstring

    :param struc_lst: structs list
    :type struc_lst: list
    :return: deduplicated list
    :rtype: list
    """
    matcher = StructureMatcher()
    deduplicated_struc_lst = []

    for struc in struc_lst:
        flag = True
        for deduplicated_struc in deduplicated_struc_lst:
            if matcher.fit(struc, deduplicated_struc):
                flag = False
                break
        if flag:
            deduplicated_struc_lst.append(struc.copy())

    return deduplicated_struc_lst


def deduplicate_dict(struc_dict: dict) -> dict:
    matcher = StructureMatcher()
    deduplicated_dict = {}
    seen_structures = []

    for key, struc_lst in struc_dict.items():
        current_key_deduped = []

        for struc in struc_lst:
            is_duplicate = False
            for existing_struc in seen_structures:
                if matcher.fit(struc, existing_struc):
                    is_duplicate = True
                    break

            if not is_duplicate:
                copied_struc = struc.copy()
                current_key_deduped.append(copied_struc)
                seen_structures.append(struc)

        if current_key_deduped:
            deduplicated_dict[key] = current_key_deduped

    return deduplicated_dict


def deduplicate_df(
    df: pd.DataFrame,
    n_keep: int,
    struct_col: str = "struct",
    energy_col: str = "energy_mean_per_atom",
):

    matcher = StructureMatcher()

    df_sorted = df.sort_values(energy_col, ascending=True)
    keep_indices = []
    keep_structs = []

    for idx, row in df_sorted.iterrows():
        struct = row[struct_col]
        is_duplicate = False

        for saved_struct in keep_structs:
            if matcher.fit(struct, saved_struct):
                is_duplicate = True
                break

        if not is_duplicate:
            keep_indices.append(idx)
            keep_structs.append(struct)

        if len(keep_indices) >= n_keep:
            break
    print("keep_indices =", len(keep_indices))
    return df_sorted.loc[keep_indices]


def generate_neb_endpoints(
    fully_intercalated_structure: Structure,
    deintercalated_structure: Structure,
    mobile_ion: str,
    mode: str = "random",
    num_paths_per_ion: int = 1,
    indices: int | Iterable[int] | None = None,
    random_num: int = 3,
    max_distance: float = 5.0,
    dedu: bool = False,
    match_tol: float = 0.6,
    overlap_tol: float = 0.5,
    seed: int | None = None,
) -> list[tuple[Structure, Structure]]:
    """Generate NEB endpoints for hops into vacancies of a deintercalated structure.

    In ``select`` mode, ``indices`` are mobile-ion indices in the
    deintercalated structure. In ``random`` mode, ``random_num`` unique
    ion-vacancy pairs are sampled without replacement.
    """
    if num_paths_per_ion < 1 or max_distance <= 0:
        raise ValueError("num_paths_per_ion and max_distance must be positive")
    if mode not in {"select", "random"}:
        raise ValueError("mode must be 'select' or 'random'")

    full_ion_indices = [
        i
        for i, site in enumerate(fully_intercalated_structure)
        if site.specie.symbol == mobile_ion
    ]
    remaining_ion_indices = [
        i
        for i, site in enumerate(deintercalated_structure)
        if site.specie.symbol == mobile_ion
    ]

    distances = sorted(
        (
            deintercalated_structure.lattice.get_distance_and_image(
                fully_intercalated_structure[i].frac_coords,
                deintercalated_structure[j].frac_coords,
            )[0],
            i,
            j,
        )
        for i in full_ion_indices
        for j in remaining_ion_indices
    )
    full_to_deintercalated: dict[int, int] = {}
    matched_deintercalated_indices: set[int] = set()
    for distance, full_index, deintercalated_index in distances:
        if distance > match_tol:
            break
        if (
            full_index not in full_to_deintercalated
            and deintercalated_index not in matched_deintercalated_indices
        ):
            full_to_deintercalated[full_index] = deintercalated_index
            matched_deintercalated_indices.add(deintercalated_index)

    vacancies = [i for i in full_ion_indices if i not in full_to_deintercalated]
    if not vacancies:
        raise ValueError(
            f"No {mobile_ion} vacancy in deintercalated_structure was found"
        )

    deintercalated_to_full = {
        deintercalated_index: full_index
        for full_index, deintercalated_index in full_to_deintercalated.items()
    }

    def valid_hop(moving_index: int, vacancy_index: int) -> bool:
        vacancy_frac = fully_intercalated_structure[vacancy_index].frac_coords
        hop_distance = deintercalated_structure.lattice.get_distance_and_image(
            deintercalated_structure[moving_index].frac_coords, vacancy_frac
        )[0]
        return hop_distance >= overlap_tol and not any(
            i != moving_index
            and deintercalated_structure.lattice.get_distance_and_image(
                vacancy_frac, site.frac_coords
            )[0]
            < overlap_tol
            for i, site in enumerate(deintercalated_structure)
        )

    if mode == "select":
        if indices is None:
            raise ValueError("indices is required in select mode")
        selected = [indices] if isinstance(indices, int) else list(indices)
        if invalid := set(selected) - set(remaining_ion_indices):
            raise ValueError(
                f"Not {mobile_ion} indices in deintercalated_structure: {invalid}"
            )
        selected_hops = []
        for moving_index in selected:
            full_moving_index = deintercalated_to_full[moving_index]
            nearby_hops = sorted(
                (
                    fully_intercalated_structure.get_distance(
                        full_moving_index, vacancy_index
                    ),
                    moving_index,
                    vacancy_index,
                )
                for vacancy_index in vacancies
                if 0
                < fully_intercalated_structure.get_distance(
                    full_moving_index, vacancy_index
                )
                < max_distance
                and valid_hop(moving_index, vacancy_index)
            )
            selected_hops.extend(nearby_hops[:num_paths_per_ion])
    else:
        if random_num < 1:
            raise ValueError("positive random_num is required in random mode")
        rng = random.Random(seed)
        ion_pairs = list(full_to_deintercalated.items())
        rng.shuffle(ion_pairs)
        selected_hops = []
        for full_index, moving_index in ion_pairs:
            shuffled_vacancies = vacancies.copy()
            rng.shuffle(shuffled_vacancies)
            for vacancy_index in shuffled_vacancies:
                distance = fully_intercalated_structure.get_distance(
                    full_index, vacancy_index
                )
                if 0 < distance < max_distance and valid_hop(
                    moving_index, vacancy_index
                ):
                    selected_hops.append((distance, moving_index, vacancy_index))
                    if len(selected_hops) == random_num:
                        break
            if len(selected_hops) == random_num:
                break
        if len(selected_hops) < random_num:
            warnings.warn(
                f"Requested {random_num} random paths, but only "
                f"{len(selected_hops)} valid paths were found; returning all.",
                stacklevel=2,
            )

    finals = []
    for _, moving_index, vacancy_index in selected_hops:
        final = deintercalated_structure.copy()
        moving_site = final[moving_index]
        final.replace(
            moving_index,
            moving_site.species,
            fully_intercalated_structure[vacancy_index].frac_coords,
            properties=moving_site.properties,
        )
        finals.append(final)

    if dedu:
        finals = deduplicate(finals)
    endpoint_pairs = [(deintercalated_structure.copy(), final) for final in finals]

    return endpoint_pairs


def check_layer_equal(
    structure: Structure,
    element: str = "Na",
    target_layers: int = 3,
    EL_Equal: bool = True,
) -> bool:
    """
    check_layer_equal 的 Docstring

    :param structure: Struct
    :type structure: Structure
    :param element: consider Element
    :type element: str
    :param target_layers:element layer >= target_layers
    :type target_layers: int
    :param EL_Equal: if Each Layer element Equal(0,1)
    :type EL_Equal: bool
    :return: if equal and len (0,1)
    :rtype: bool
    """
    tol = 0.05
    z = sorted([s.frac_coords[2] for s in structure if element in s.species_string])
    if not z:
        return False

    gaps = [z[i + 1] - z[i] for i in range(len(z) - 1)]
    gaps.append(z[0] + 1.0 - z[-1])

    max_gap_val = max(gaps)
    max_gap_idx = gaps.index(max_gap_val)

    shift = 1.0 - (z[max_gap_idx] + max_gap_val / 2)
    z_shifted = sorted([(val + shift) % 1.0 for val in z])

    layers = []
    current_layer = [z_shifted[0]]
    for val in z_shifted[1:]:
        if val - current_layer[-1] < tol:
            current_layer.append(val)
        else:
            layers.append(current_layer)
            current_layer = [val]
    layers.append(current_layer)

    layer_num_ok = len(layers) >= target_layers

    if EL_Equal:
        counts = [len(layer) for layer in layers]
        counts_equal = len(set(counts)) == 1
    else:
        counts_equal = True

    return layer_num_ok and counts_equal


def build_redox_disordered_structure(struct, na_num_now):

    s = struct.copy()

    na_num_full = int(struct.composition["Na"])
    n_removed = na_num_full - na_num_now

    n_mn = int(struct.composition.get("Mn", 0))
    n_fe = int(struct.composition.get("Fe", 0))

    n_mn4 = min(n_removed, n_mn)
    n_fe4 = max(0, n_removed - n_mn)

    if n_fe4 > n_fe:
        raise ValueError("Redox capacity exceeded")

    replace_dict = {Element("Na"): {Species("Na", 1): na_num_now / na_num_full}}

    if n_mn:
        replace_dict[Element("Mn")] = {
            Species("Mn", 3): 1 - n_mn4 / n_mn,
            Species("Mn", 4): n_mn4 / n_mn,
        }

    if n_fe:
        replace_dict[Element("Fe")] = {
            Species("Fe", 3): 1 - n_fe4 / n_fe,
            Species("Fe", 4): n_fe4 / n_fe,
        }

    s.replace_species(replace_dict)

    for i, site in enumerate(s):
        if site.species_string == "O":
            s[i] = Species("O", -2)

    return s


def remove_oxi(struct):

    s = struct.copy()

    for i, site in enumerate(s):
        sp = site.specie
        if hasattr(sp, "element"):
            s[i] = sp.element

    return s


def Na1_to_Nax(
    struct,
    tar_dir,
    interval=3,
    nstr=3,
    tar_layer=None,
    equal_num=None,
    select_num=None,
    dedu=False,
    is_Na0=False,
    phase=None,
):

    Na_num = int(struct.composition["Na"])
    end = 0 if is_Na0 else 1

    for Na in range(Na_num, end - 1, -interval):
        frac = Fraction(Na, Na_num)
        tar = tar_dir / f"{frac.numerator}_{frac.denominator}"
        tar.mkdir(exist_ok=True, parents=True)

        if Na == Na_num:
            # if phase == 'O3':
            struct.to(filename=tar / "0.vasp", fmt="poscar")
            continue

        if Na == 0:
            s = struct.copy()
            s.remove_species(["Na"])
            s.to(tar / "0.vasp", fmt="poscar")
            continue

        structs = gen_ESGS_structure(build_redox_disordered_structure(struct, Na), nstr)

        if tar_layer:
            structs = [
                s for s in structs if check_layer_equal(s, target_layers=tar_layer)
            ]

        print(f"Na={Na}, N={len(structs)}")

        if not structs:
            continue

        if equal_num:
            structs = random.sample(structs, min(equal_num, len(structs)))

        if dedu:
            structs = deduplicate(structs)

        if select_num:
            structs = structs[:select_num]

        for i, s in enumerate(structs):
            s = remove_oxi(s)
            s.sort()
            s.to(tar / f"{i}.vasp", fmt="poscar")
