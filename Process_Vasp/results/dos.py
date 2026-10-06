"""DOS reader and CSV exporter."""

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from monty.os.path import zpath
from pymatgen.electronic_structure.core import Spin
from pymatgen.io.vasp.inputs import Incar
from pymatgen.io.vasp.outputs import Procar, Vasprun


def _spin_label(spin: Spin) -> str:
    """Return a stable CSV label for a spin channel."""
    return "up" if spin == Spin.up else "down"


def _ordered_spins(densities: dict[Spin, Any]) -> list[Spin]:
    """Return available spin channels in up/down column order."""
    return [spin for spin in (Spin.up, Spin.down) if spin in densities]


def read_dos(
    init_dir: str | Path,
    output_csv: str | Path | None = None,
    read_ipr: bool = False,
    include_orbital: bool = False,
    ipr_sigma: float | None = None,
    *,
    include_element: bool = True,
    include_total: bool = True,
    shift_fermi: bool = True,
    mirror_spin_down: bool = False,
) -> dict[str, Any]:
    """Read DOS and calculation metadata; optionally export the numeric table.

    Args:
        init_dir: Directory containing ``vasprun.xml`` or ``vasprun.xml.gz``.
            Compressed INCAR and PROCAR are also read directly.
        output_csv: Destination CSV path. None means no file is written.
        read_ipr: Whether to add Gaussian-broadened IPR columns from ``PROCAR``.
        include_orbital: Whether to include the s/p/d/f PDOS of every element.
        ipr_sigma: Gaussian broadening width in eV for the IPR. Defaults to the
            ``SIGMA`` value in ``vasprun.xml``.
        include_element: Include element-projected DOS (enabled by default).
        include_total: Include total DOS.
        shift_fermi: Use E - E_F instead of absolute energy (eV).
        mirror_spin_down: Negate down-spin DOS for mirrored plots; IPR is unchanged.

    Returns:
        Dict with ``NEDOS``, ``kpoint_density`` (KPPRA = full mesh size times
        atom count), ``kpoint_mesh``, ``nkpoints``, ``KSPACING``, ``efermi``,
        ``path``, ``composition``, and ``df``. Density is None when no regular
        mesh is available (e.g. explicit or line-mode k-points). ``NEDOS`` is
        read from INCAR when present, otherwise from the recorded XML input.
        ``df`` contains only numeric plotting columns; export with
        ``result['df'].to_csv('dos.csv', index=False)``.
    """
    init_dir = Path(init_dir)
    vasprun = Vasprun(
        zpath(init_dir / "vasprun.xml"),
        parse_dos=True,
        parse_eigen=False,
        parse_projected_eigen=False,
        parse_potcar_file=False,
        exception_on_bad_xml=False,
    )
    dos = vasprun.complete_dos
    if vasprun.dos_has_errors or dos is None:
        raise ValueError(f"Could not read complete DOS from {init_dir / 'vasprun.xml'}")
    if not any((include_total, include_element, include_orbital, read_ipr)):
        raise ValueError("Enable at least one DOS or IPR output option")
    data: dict[str, Any] = {
        "energy": dos.energies - dos.efermi if shift_fermi else dos.energies,
    }
    if include_total:
        for spin in _ordered_spins(dos.densities):
            data[f"dos_{_spin_label(spin)}"] = dos.densities[spin]

    if read_ipr:
        sigma = (
            float(vasprun.parameters.get("SIGMA", 0.05))
            if ipr_sigma is None
            else ipr_sigma
        )
        data.update(_read_broadened_ipr(init_dir, dos.energies - dos.efermi, dos.efermi, sigma))

    if include_element or include_orbital:
        if not dos.pdos:
            raise ValueError("Projected DOS is missing; use a VASP DOS run with LORBIT=11, or disable element/orbital output")
        elements = vasprun.final_structure.composition.elements
    if include_element:
        element_dos = dos.get_element_dos()

        # Write each element's total PDOS before its orbital-resolved PDOS.
        for element in elements:
            element_label = element.symbol
            projected_dos = element_dos[element]
            for spin in _ordered_spins(projected_dos.densities):
                data[f"{element_label}_{_spin_label(spin)}"] = (
                    projected_dos.densities[spin]
                )

    if include_orbital:
        for element in elements:
            element_label = element.symbol
            for orbital, orbital_dos in dos.get_element_spd_dos(element).items():
                orbital_label = orbital.name.lower()
                for spin in _ordered_spins(orbital_dos.densities):
                    column = f"{element_label}_{orbital_label}_{_spin_label(spin)}"
                    data[column] = orbital_dos.densities[spin]

    if mirror_spin_down:
        for column in data:
            if column.endswith("_down") and not column.startswith("ipr_"):
                data[column] = -np.asarray(data[column])
    dataframe = pd.DataFrame(data)
    incar_path = Path(zpath(init_dir / "INCAR"))
    incar = Incar.from_file(incar_path) if incar_path.is_file() else vasprun.incar
    mesh = None
    kpoints = vasprun.kpoints
    if kpoints.style.name in ("Gamma", "Monkhorst") and len(kpoints.kpts) == 1:
        divisions = np.asarray(kpoints.kpts[0], dtype=float)
        if np.all(divisions > 0) and np.all(divisions == np.floor(divisions)):
            mesh = tuple(int(value) for value in divisions)
    result = {
        "NEDOS": int(incar["NEDOS"]) if "NEDOS" in incar else None,
        "kpoint_density": int(np.prod(mesh)) * len(vasprun.final_structure) if mesh else None,
        "kpoint_mesh": mesh,
        "nkpoints": len(vasprun.actual_kpoints),
        "KSPACING": incar.get("KSPACING"),
        "efermi": float(dos.efermi),
        "path": str(init_dir.resolve()),
        "composition": str(vasprun.final_structure.composition),
        "df": dataframe,
    }
    if output_csv is not None:
        output_path = Path(output_csv)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        dataframe.to_csv(output_path, index=False)
    return result


def _read_broadened_ipr(
    init_dir: Path,
    energy_grid: np.ndarray,
    efermi: float,
    sigma: float,
) -> dict[str, np.ndarray]:
    """Calculate Gaussian-broadened IPR on a DOS energy grid."""
    if sigma <= 0:
        raise ValueError("ipr_sigma must be greater than zero")

    procar = Procar(zpath(init_dir / "PROCAR"))
    broadened: dict[str, np.ndarray] = {}
    kpoint_weights = np.asarray(procar.weights, dtype=float)
    if not np.any(kpoint_weights > 0):
        # Line-mode band calculations commonly record every k-point weight as
        # zero. Equal weights still give a well-defined energy-resolved IPR.
        kpoint_weights = np.ones_like(kpoint_weights)

    for spin, energies in procar.eigenvalues.items():
        projections = procar.data[spin]
        atom_weights = projections.sum(axis=3)
        totals = atom_weights.sum(axis=2)
        state_ipr = np.divide(
            np.square(atom_weights).sum(axis=2),
            np.square(totals),
            out=np.full_like(totals, np.nan),
            where=~np.isclose(totals, 0),
        )

        state_energies = (energies - efermi).reshape(-1)
        state_ipr = state_ipr.reshape(-1)
        state_weights = np.repeat(kpoint_weights, energies.shape[1])
        valid = (
            np.isfinite(state_energies)
            & np.isfinite(state_ipr)
            & (state_weights > 0)
        )
        if not np.any(valid):
            raise ValueError(
                f"PROCAR contains no valid {_spin_label(spin)}-spin projections"
            )

        valid_energies = state_energies[valid]
        valid_ipr = state_ipr[valid]
        valid_weights = state_weights[valid]
        spin_ipr = np.full(energy_grid.shape, np.nan, dtype=float)

        # Process the DOS grid in blocks to avoid allocating one very large
        # energy-by-state matrix for dense k-point meshes.
        for start in range(0, len(energy_grid), 256):
            stop = start + 256
            grid_block = energy_grid[start:stop]
            exponent = -0.5 * (
                (grid_block[:, np.newaxis] - valid_energies[np.newaxis, :]) / sigma
            ) ** 2
            # Subtracting the largest exponent preserves the normalized result
            # while preventing all Gaussian weights from underflowing to zero.
            gaussian = np.exp(
                exponent - exponent.max(axis=1, keepdims=True)
            )
            weights = gaussian * valid_weights[np.newaxis, :]
            denominator = weights.sum(axis=1)
            spin_ipr[start:stop] = np.divide(
                weights @ valid_ipr,
                denominator,
                out=np.full(grid_block.shape, np.nan, dtype=float),
                where=denominator > 0,
            )

        broadened[f"ipr_{_spin_label(spin)}"] = spin_ipr

    return broadened


def read_ipr_data(
    init_dir: str | Path,
    output_csv: str | Path | None = None,
    efermi: float | None = None,
) -> pd.DataFrame:
    """Read atom-projected inverse participation ratios from ``PROCAR``.

    Args:
        init_dir: Directory containing ``PROCAR`` and, when ``efermi`` is omitted,
            ``vasprun.xml``.
        output_csv: Destination CSV path. Defaults to ``ipr.csv`` in the input directory.
        efermi: Fermi energy used as the energy zero. When omitted, it is read from
            ``vasprun.xml``.

    Returns:
        A DataFrame containing energy, spin, k-point, band, and IPR columns.
    """
    init_dir = Path(init_dir)
    if efermi is None:
        vasprun = Vasprun(
            zpath(init_dir / "vasprun.xml"),
            parse_dos=False,
            parse_eigen=False,
            parse_projected_eigen=False,
            parse_potcar_file=False,
            exception_on_bad_xml=False,
        )
        efermi = vasprun.efermi

    procar = Procar(zpath(init_dir / "PROCAR"))
    rows: list[dict[str, Any]] = []

    for spin, energies in procar.eigenvalues.items():
        projections = procar.data[spin]
        atom_weights = projections.sum(axis=3)
        totals = atom_weights.sum(axis=2)
        ipr = np.divide(
            np.square(atom_weights).sum(axis=2),
            np.square(totals),
            out=np.full_like(totals, np.nan),
            where=~np.isclose(totals, 0),
        )

        for kpoint, band in np.ndindex(energies.shape):
            rows.append(
                {
                    "energy": energies[kpoint, band] - efermi,
                    "spin": _spin_label(spin),
                    "kpoint": kpoint + 1,
                    "band": band + 1,
                    "ipr": ipr[kpoint, band],
                }
            )

    dataframe = pd.DataFrame(rows)
    output_path = init_dir / "ipr.csv" if output_csv is None else Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(output_path, index=False)
    return dataframe


def read_ipr(
    init_dir: str | Path,
    output_csv: str | Path | None = None,
    efermi: float | None = None,
) -> pd.DataFrame:
    """Read IPR data from ``PROCAR``, export it to CSV, and return it."""
    return read_ipr_data(init_dir, output_csv=output_csv, efermi=efermi)
