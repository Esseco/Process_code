"""Convenient single-structure entry; the existing workflow owns all MD."""
from dataclasses import replace
from datetime import datetime
import os
from pathlib import Path
from uuid import uuid4

import numpy as np
from process_md import prepare_structure

from .calculators import mace_model_path
from .config import ScreeningConfig
from .presets import screening_preset
from .workflow import run_screening


def run_md(structure, *, reference_sites, output_dir=None, config=None,
           calculator=None, **overrides):
    """Run relaxation, precheck and continuous MD with a caller's supercell.

    structure/reference_sites: ASE Atoms or file paths with matching input
    cell and origin; reference_sites contains the full mobile-site population.
    Default preset keeps atom count/cell, uses CUDA MACE-OMat + Symmetrix,
    cell LBFGS relaxation, 5 ps precheck and 10 ps checks up to 200 ps production.
    Mobile species is inferred as Li/Na when no explicit config/override is given.
    config is an optional ScreeningConfig; keyword overrides replace its fields.
    Model path: config -> PROCESS_MD_MACE_MODEL -> sibling MLIP_model/mace/.
    An injected calculator skips model loading/path discovery.

    output_dir must be new; None selects runs/<input>_<timestamp>. Returns
    WorkflowResult. Results/diagnostics are persisted and exceptions propagate.
    The default preset gzip archives the trajectory after analysis; disable with
    compress_trajectory=False. Decompress .traj.gz before separate ASE analysis.
    No installation, scheduling, automatic heating or strict restart occurs.
    """
    if reference_sites is None:
        raise ValueError("reference_sites is required: supply the full-site reference")
    if config is not None and not isinstance(config, ScreeningConfig):
        raise TypeError("config must be ScreeningConfig or None")
    atoms = prepare_structure(structure)
    sites = prepare_structure(reference_sites)
    if not atoms.pbc.all() or not sites.pbc.all():
        raise ValueError("structure and reference_sites require full 3D PBC")
    if not np.allclose(atoms.cell.array, sites.cell.array, rtol=1e-9, atol=1e-8):
        raise ValueError("reference_sites must use the input structure cell and origin")
    if config is None and "mobile_species" not in overrides:
        candidates = set(atoms.get_chemical_symbols()) & {"Li", "Na"}
        if len(candidates) != 1:
            raise ValueError("Set mobile_species explicitly when Li/Na cannot be inferred uniquely")
        overrides["mobile_species"] = candidates.pop()
    selected = screening_preset(**overrides) if config is None else replace(config, **overrides)
    if calculator is None:
        source = selected.model_path or os.environ.get("PROCESS_MD_MACE_MODEL")
        if not source:
            import Process_MLIP
            source = Path(Process_MLIP.__file__).resolve().parent.parent / "MLIP_model/mace/mace-omat-0-medium.model"
        selected = replace(selected, model_path=mace_model_path(replace(selected, model_path=source)))
    if output_dir is None:
        name = Path(structure).stem if isinstance(structure, (str, Path)) else atoms.get_chemical_formula()
        output_dir = Path.cwd() / "runs" / f"{name}_{datetime.now():%Y%m%d_%H%M%S_%f}_{uuid4().hex[:8]}"
    return run_screening(structure, reference_sites=reference_sites, config=selected,
                         output_dir=Path(output_dir).expanduser().resolve(), calculator=calculator)
