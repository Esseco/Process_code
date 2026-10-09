"""Process_AL_MC public API, imported lazily to keep standalone Relax light."""

__all__ = ["LayeredOxide_MCOrderingClass", "extract_data_from_mcjson", "relax_structure_mace"]


def __getattr__(name):
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
