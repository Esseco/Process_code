"""Process_MD foundation: ASE structures, data contracts and result utilities.

MD/MSD/fitting functions delegate lazily to Process_MLIP. Structure,
composition and trajectory diagnostics are independent data-producing tools.
Strict cross-process restart and workflow decisions are not implemented.
Importing loads neither Process_MLIP nor model/analysis dependencies.
"""
from .analysis import calculate_msd, diffusion_from_slope, export_msd, fit_diffusion, fit_msd, validate_framework
from .md import (MDRunner, create_chgnet_calculator, create_grace_calculator,
                 create_mace_calculator, create_nep_calculator,
                 create_nequip_calculator, create_orb_calculator,
                 create_sevennet_calculator)
from .models import DiffusionResult, MDConfig, MDResult, MSDResult, StructureInfo, ValidationResult
from .io import save_csv, save_json, save_results
from .structure import estimate_hop_distance, get_structure_info, prepare_structure
from .state import AlkaliState, describe_alkali_state
from .analysis.trajectory import read_positions
from .analysis.diagnostics import compare_transport, describe_cell, summarize_md_log, ThermodynamicSummary
from .analysis.uncertainty import UncertaintyResult, analyze_diffusion_uncertainty, check_uncertainty_backend
from .analysis.jumps import JumpResult, analyze_jumps, check_jump_backend

__version__ = "0.1.0"
__all__ = [
    "MDConfig", "MDResult", "MSDResult", "DiffusionResult", "ValidationResult", "StructureInfo",
    "prepare_structure", "get_structure_info", "create_chgnet_calculator", "create_mace_calculator",
    "create_nep_calculator", "create_grace_calculator", "create_nequip_calculator",
    "create_orb_calculator", "create_sevennet_calculator", "MDRunner",
    "export_msd", "fit_msd", "calculate_msd", "fit_diffusion", "diffusion_from_slope", "validate_framework",
    "save_json", "save_csv", "save_results",
    "AlkaliState", "describe_alkali_state", "read_positions",
    "describe_cell", "summarize_md_log", "compare_transport", "ThermodynamicSummary",
    "UncertaintyResult", "analyze_diffusion_uncertainty", "check_uncertainty_backend",
    "JumpResult", "analyze_jumps", "check_jump_backend",
    "estimate_hop_distance",
]
