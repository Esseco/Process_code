from pymatgen.core.structure import Structure
import numpy as np
from chgnet.utils import read_json

from Process_VaspOut import (
    correct_energy,
)


def load_chgnet_json(
    json_path,
    model=None,
    last_only:bool=True,
    tasks:str="e",
    return_struct:bool=False,
    energy_correction:bool=True,
    include_el:bool=False
):
    """
    model : object or None
        ML model with:
            model.predict_structure(struct)
        If None -> only load VASP results

    last_only : bool
    tasks : str efsm
    Returns
    -------
    dict or list[dict]
    """

    data = read_json(json_path)

    # -------------------------
    # trajectory or single
    # -------------------------
    is_traj = isinstance(data.get("structure"), list)

    if is_traj:
        structures = data["structure"]
        energies = data["uncorrected_total_energy"]

        vasp_forces = data.get("force")
        vasp_stress = data.get("stress")

        indices = [-1] if last_only else range(len(structures))

    else:
        structures = [data["structure"]]
        energies = [data["uncorrected_total_energy"]]

        vasp_forces = [data["force"]] if "force" in data else None
        vasp_stress = [data["stress"]] if "stress" in data else None
        vasp_magmom = [data["magmom"]] if "magmom" in data else None
        indices = [0]

    results = []

    # =========================
    # loop over frames
    # =========================
    for frame_id, i in enumerate(indices):

        struct = Structure.from_dict(structures[i])

        comp = struct.composition

        try:
            Na_con = int(comp["Na"]) * 2 / int(comp["O"])
        except Exception:
            Na_con = None

        result = {
            'path':str(json_path),
            "frame": frame_id,
            "Na": Na_con,
            'com':str(comp)
        }
        if include_el:
            result['Elements'] = [site.specie.symbol for site in struct]
        if return_struct:
            result["struct"] = struct

        # =====================================================
        # VASP DATA
        # =====================================================
        if "e" in tasks:

            energy = energies[i]

            if energy_correction:
                energy = correct_energy(struct, energy)

            result["v_e"] = round(float(energy), 4)

        if "f" in tasks and vasp_forces is not None:
            result["v_f"] = np.array(vasp_forces[i])

        if "s" in tasks and vasp_stress is not None:
            result["v_s"] = np.array(vasp_stress[i])
            
        if "m" in tasks and vasp_magmom is not None:
            result["v_m"] = np.array(vasp_magmom[i])

        if model is not None:

            pred = model.predict_structure(struct)
            if "e" in tasks:
                result["chg_e"] = round(float(pred["e"[0]]), 4)
            if "f" in tasks:
                result["chg_f"] = np.array(pred["f"[0]])
            if "s" in tasks:
                result["chg_s"] = np.array(pred["s"[0]])
            if "m" in tasks:
                result["chg_m"] = np.array(pred["m"[0]])

        results.append(result)

    return results[0] if last_only else results