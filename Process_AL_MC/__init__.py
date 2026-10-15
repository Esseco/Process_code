"""Process_AL_MC public API, imported lazily to keep standalone Relax light."""

__all__ = [
    "LayeredOxide_MCOrderingClass",
    "extract_data_from_mcjson",
    "relax_structure_mace",
    "plan_ordering_search",
    "prepare_ordering_search",
    "run_ordering_search",
    "reconcile_ordering_search",
    "inspect_ordering_search",
]


def __getattr__(name):
    if name in {
        "plan_ordering_search",
        "prepare_ordering_search",
        "run_ordering_search",
        "reconcile_ordering_search",
        "inspect_ordering_search",
    }:
        from .ordering import api

        return getattr(api, name)
    if name == "LayeredOxide_MCOrderingClass":
        from .MC_sample import LayeredOxide_MCOrderingClass

        return LayeredOxide_MCOrderingClass
    if name == "extract_data_from_mcjson":
        from .Auc_code import extract_data_from_mcjson

        return extract_data_from_mcjson
    if name == "relax_structure_mace":
        from .relax import relax_structure_mace

        return relax_structure_mace
    raise AttributeError(name)
