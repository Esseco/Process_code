"""Dedicated model adapter; construction and scientific execution are explicit."""

import math
import re

import numpy as np


def identify_phase(structure, target_phase, H=None):
    """Conservative oxygen-triangle check; ambiguous classifications remain X."""
    indices = [i for i, s in enumerate(structure) if s.specie.symbol == "Na"]
    if not indices:
        return "X"
    a, b = np.asarray(structure.lattice.matrix[:2])
    normal = np.cross(a, b)
    normal /= np.linalg.norm(normal)
    axis = a / np.linalg.norm(a)
    other = np.cross(normal, axis)
    types = []
    for index in indices:
        site = structure[index]
        neighbors = sorted(
            (n for n in structure.get_neighbors(site, 4) if n.specie.symbol == "O"),
            key=lambda n: n.nn_distance,
        )[:6]
        top, bottom = [], []
        for neighbor in neighbors:
            vector = np.asarray(neighbor.coords - site.coords)
            (top if vector @ normal > 0 else bottom).append(vector)
        if len(top) != 3 or len(bottom) != 3:
            return "X"

        def order(vectors):
            return np.mean([np.exp(3j * np.arctan2(v @ other, v @ axis)) for v in vectors])

        t, b = order(top), order(bottom)
        magnitude = abs(t) * abs(b)
        correlation = float((t * np.conj(b)).real / magnitude) if magnitude > 0.1 else 0.0
        types.append("P" if correlation > 0.25 else "O" if correlation < -0.25 else "X")
    # Preserve the established coordination-layer identification, including c repeats.
    values = sorted(float(structure[i].frac_coords[2]) % 1 for i in indices)
    gaps = [values[i + 1] - values[i] for i in range(len(values) - 1)] + [
        values[0] + 1 - values[-1]
    ]
    repetitions = H[2][2] if H and H[0][2] == H[1][2] == 0 else 1 if H is None else None
    tolerance = 0.08 / max(1, repetitions or 1)
    layers = sum(gap > tolerance for gap in gaps)
    match = re.fullmatch(r"(O|P|OP)(\d+)", target_phase)
    if (
        match
        and repetitions
        and set(types) == set(match[1])
        and layers == int(match[2]) * repetitions
    ):
        return target_phase
    return "X"


class MACEOrderingEvaluator:
    """One existing main model per worker; optional committee metrics do not rank."""

    def __init__(self, model, config):
        from ..MC_sample import LayeredOxide_MCOrderingClass

        self.config = config
        paths = [
            model["model_path"],
            *[path for path in model.get("model_paths") or [] if path != model["model_path"]],
        ]
        self.backend = LayeredOxide_MCOrderingClass(
            model_paths=paths,
            model_type=model.get("model_type", "mace"),
            device=model.get("device", "cuda"),
            main_model_index=0,
            mace_head=model.get("mace_head"),
            mace_default_dtype=model.get("mace_default_dtype", "float64"),
            fmax=config["fmax"],
            relax_steps=config["relax_steps"],
            relax_cell=config["relax_cell"],
        )

    def __call__(self, structure, context):
        from ase.filters import FrechetCellFilter
        from ase.optimize import LBFGS
        from pymatgen.io.ase import AseAtomsAdaptor
        from pymatgen.core import Structure

        if self.backend.model_type == "mace":
            atoms = AseAtomsAdaptor.get_atoms(structure)
            atoms.calc = self.backend.model
            target = FrechetCellFilter(atoms) if self.config["relax_cell"] else atoms
            optimizer = LBFGS(target, logfile=None)
            converged = bool(
                optimizer.run(fmax=self.config["fmax"], steps=self.config["relax_steps"])
            )
            final = AseAtomsAdaptor.get_structure(atoms)
        else:
            relaxed = self.backend._relax_with_main_model(structure)
            final = relaxed["final_structure"]
            # Unsupported backend convergence reports are not promoted to success.
            converged = relaxed.get("converged") is True
        data = self.backend._evaluate_committee(final)
        energy = data["energy_per_model_per_atom"][self.backend.main_model_index]
        _, forces = self.backend._predict_energy_force(self.backend.model, final)
        max_force = float(np.linalg.norm(forces, axis=1).max())
        converged = converged and math.isfinite(max_force) and max_force <= self.config["fmax"]
        probe = final.copy()
        reference = Structure.from_dict(context["reference"])
        retained = set(context["reference_site_ids"])
        for i, site in enumerate(reference):
            if site.specie.symbol == "Na" and i not in retained:
                probe.append("Na", site.frac_coords, coords_are_cartesian=False)
        return {
            "structure": final.as_dict(),
            "energy_per_atom": float(energy),
            "energy_std_per_atom": data["energy_std_per_atom"],
            "max_force": max_force,
            "converged": converged,
            "phase": identify_phase(probe, context["phase"], context["H"]),
            "phase_method": "oxygen_triangle_coordination_with_vacancy_reference_probes",
        }
