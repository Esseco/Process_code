"""Structure processing tools, loaded on demand by their required environment."""

from __future__ import annotations

from importlib import import_module


_EXPORTS = {
    "Octahedron": "van_vleck_calculator",
    "StructureFeatureExtractor": "Get_structfeatures_all",
    "WyckoffSiteGroup": "wyckoff",
    "analyze_octahedra_distortion": "Get_Oct_distortion",
    "get_wyckoff_sites": "wyckoff",
    "sanitize_for_json": "Get_Oct_distortion",
    "save_traj_xyz": "Traj_Convert",
    "traj_to_info": "Traj_Convert",
    "theoretical_specific_capacity": "Cal_capacity",
    "calc_formation_energy": "Cal_eform",
    "batch_estimate_mobile_ion_windows": "Chemical_Capacity_Constraints",
    "batch_estimate_redox_capacity": "Chemical_Capacity_Constraints",
    "estimate_mobile_ion_window": "Chemical_Capacity_Constraints",
    "estimate_redox_capacity": "Chemical_Capacity_Constraints",
    "screen_substitutions": "Chemical_Capacity_Constraints",
    "analyze_percolation": "percolation",
}

__all__ = list(_EXPORTS)


def __getattr__(name: str):
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(f".{_EXPORTS[name]}", __name__), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
