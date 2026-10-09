"""Postprocess an existing DOS checkpoint using a single AMSET CRT calculation."""

from pathlib import Path

from .amset_crt import run_amset_crt
from .atomate_runner import _save
from ..results.completed import get_completed_result


def _dos_directory(workflow_root, source_dir=None, source_stage="dos"):
    return get_completed_result(workflow_root, source_stage, source_dir=source_dir, require_uniform=True)


def _derived_properties(result):
    # Same definition as AMSET tools/effmass.py: m*/m_e = n e² (sigma/tau)^-1 / m_e.
    # n is the absolute net doping, not a separately computed band population.
    import numpy as np

    elementary_charge = 1.602176634e-19  # C, exact
    electron_mass = 9.1093837139e-31  # kg, CODATA 2022
    mass, average, mobility, normalized_mobility, notes = [], [], [], [], []
    for index, doping in enumerate(result["doping_cm3"]):
        number_density = abs(doping) * 1e6  # cm^-3 -> m^-3
        mass_row, average_row, mobility_row, normalized_row, note_row = [], [], [], [], []
        for tensor in result["sigma_over_tau_S_m_s"][index]:
            conductivity_ratio = np.asarray(tensor, dtype=float)
            mu_ratio = conductivity_ratio / (number_density * elementary_charge) * 1e4
            normalized_row.append(mu_ratio.tolist())  # cm² V^-1 s^-2
            mobility_row.append((mu_ratio * result["relaxation_time_s"]).tolist())
            try:
                symmetric = (conductivity_ratio + conductivity_ratio.T) / 2
                if np.any(np.linalg.eigvalsh(symmetric) <= 0):
                    raise ValueError("Conductivity tensor is not positive definite")
                tensor_mass = np.linalg.inv(conductivity_ratio) * number_density * elementary_charge**2 / electron_mass
                if not np.isfinite(tensor_mass).all():
                    raise ValueError("Effective mass is nonfinite")
                mass_row.append(tensor_mass.tolist())
                average_row.append(float(3 / np.trace(np.linalg.inv(tensor_mass))))
                note_row.append("ok")
            except (ValueError, np.linalg.LinAlgError) as error:
                mass_row.append(None)
                average_row.append(None)
                note_row.append(str(error))
        mass.append(mass_row)
        average.append(average_row)
        mobility.append(mobility_row)
        normalized_mobility.append(normalized_row)
        notes.append(note_row)
    result.update(
        conductivity_effective_mass_m0=mass,
        conductivity_effective_mass_harmonic_mean_m0=average,
        effective_mass_status=notes,
        mobility_crt_cm2_V_s=mobility,
        mobility_over_tau_cm2_V_s2=normalized_mobility,
        effective_mass_definition="AMSET eff-mass: abs(net doping) * e^2 * inverse(sigma/tau) / m_e",
        mobility_definition="sigma / (abs(net doping) * e); constant user-supplied tau, not ab initio scattering mobility",
    )
    return result


def run_amset_postprocess(workflow_root, output_dir=None, *, source_dir=None,
                          source_stage="dos",
                          doping=(-1e18, 1e18), temperatures=(300,),
                          relaxation_time=1e-14, interpolation_factor=10,
                          nworkers=1, resume=True):
    """Read a completed DOS task and export transport masses and CRT mobility.

    workflow_root contains workflow_state.json; source_stage selects dos/static.
    source_dir optionally overrides
    the DOS path (relative to workflow_root). Default output is root/amset_results.
    Units: doping cm^-3 (electrons negative), temperature K, tau s; mass in m_e,
    mobility cm²/(V s), sigma/tau S/(m s). Tensor axes match run_amset_crt.
    Requires AMSET and numpy; no random seed. Copies XML and writes only to the
    independent output subtree; no VASP runs/submission or source modification.
    Reuses completed CRT calculations by content/parameter fingerprint; derived
    properties can be regenerated without recomputing AMSET. Invalid mass tensors
    are null with a diagnostic; CRT success does not imply numerical convergence.
    """
    root = Path(workflow_root).resolve()
    if source_stage not in {"dos", "static"}:
        raise ValueError("AMSET requires a completed uniform DOS or static calculation")
    source = _dos_directory(root, source_dir, source_stage)
    target = Path(output_dir).resolve() if output_dir is not None else root / "amset_results"
    result = run_amset_crt(source, target / "crt", doping=doping,
                           temperatures=temperatures, relaxation_time=relaxation_time,
                           interpolation_factor=interpolation_factor,
                           nworkers=nworkers, resume=resume)
    result = _derived_properties(result)
    result["source_dir"] = str(source)
    _save(target / "transport_properties.json", result)
    # Flat table for quick plotting; retain the complete tensors in JSON.
    import csv
    with (target / "transport_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["carrier", "doping_cm-3", "temperature_K", "mass_harmonic_m0",
                         "mass_xx_m0", "mass_yy_m0", "mass_zz_m0",
                         "sigma_over_tau_xx_S_m_s", "sigma_over_tau_yy_S_m_s", "sigma_over_tau_zz_S_m_s",
                         "mobility_crt_xx_cm2_V_s", "mobility_crt_yy_cm2_V_s", "mobility_crt_zz_cm2_V_s"])
        for n, concentration in enumerate(result["doping_cm3"]):
            for t, temperature in enumerate(result["temperatures_K"]):
                mass_tensor = result["conductivity_effective_mass_m0"][n][t]
                writer.writerow([result["carrier_type"][n], concentration, temperature,
                                 result["conductivity_effective_mass_harmonic_mean_m0"][n][t],
                                 *([mass_tensor[i][i] for i in range(3)] if mass_tensor else [None]*3),
                                 *[result["sigma_over_tau_S_m_s"][n][t][i][i] for i in range(3)],
                                 *[result["mobility_crt_cm2_V_s"][n][t][i][i] for i in range(3)]])
    return result
