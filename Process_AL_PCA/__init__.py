"""Load FAISS-dependent functionality only when requested."""

__all__ = ["sample_traj_xyz", "DiverseSelector_struct"]


def __getattr__(name):
    if name not in __all__:
        raise AttributeError(name)
    from . import process_pool
    value = getattr(process_pool, name)
    globals()[name] = value
    return value

__all__ = [
    'sample_traj_xyz',
    'DiverseSelector_struct'
]
