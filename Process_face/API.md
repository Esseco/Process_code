# Process_face 参数索引

源码静态索引；保留原有函数名。类构造和公开方法分别列出。默认值不代表适用于所有体系。

## `main`

源文件：[examples/fix_bottom.py](examples/fix_bottom.py)，第 8 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/generate_slabs.py](examples/generate_slabs.py)，第 12 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/surface_configurations.py](examples/surface_configurations.py)，第 9 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/symmetry_partners.py](examples/symmetry_partners.py)，第 7 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `SurfaceFixer`

源文件：[Fix_atoms.py](Fix_atoms.py)，第 16 行。

```python
SurfaceFixer
```

Identify and fix atomic layers in slab structures.

Supports both ASE ``Atoms`` and pymatgen ``Structure`` / ``Slab``
backends.  Uses coordination-number (CN) heuristics to separate
surface atoms from bulk atoms, and provides several strategies for
choosing which atoms to fix (constrain) during a relaxation.

Attributes:
    structure: The input structure (ASE or pymatgen).
    backend: ``"ase"`` or ``"pymatgen"``.
    coords: Cartesian coordinates (N, 3).
    n_atoms: Total number of atoms.
    z: Cartesian z coordinates of all atoms.
    zmax: Maximum z value.
    zmin: Minimum z value.
    z_center: Midpoint between zmax and zmin.
    frac_z: Fractional c-direction coordinates of all atoms.

## `SurfaceFixer.__init__`

源文件：[Fix_atoms.py](Fix_atoms.py)，第 36 行。

```python
SurfaceFixer.__init__(self, structure: Any)
```

Initialize the fixer from an ASE or pymatgen structure.

Args:
    structure: An ``ase.Atoms`` or ``pymatgen.core.Structure`` (or
        subclass such as ``Slab``).

Raises:
    TypeError: If *structure* is neither an ASE nor a pymatgen type.

## `SurfaceFixer.get_symbol`

源文件：[Fix_atoms.py](Fix_atoms.py)，第 97 行。

```python
SurfaceFixer.get_symbol(self, i: int)
```

Return the element symbol of atom *i*.

Args:
    i: Atom index.

Returns:
    Element symbol string (e.g. ``"Ti"``).

## `SurfaceFixer.analyze_slab`

源文件：[Fix_atoms.py](Fix_atoms.py)，第 114 行。

```python
SurfaceFixer.analyze_slab(self, target_cn: int=6)
```

Separate atoms into top-surface, bulk, and bottom-surface layers.

Atoms whose coordination number is below *target_cn* are
considered surface atoms; the rest are bulk.

Args:
    target_cn: Minimum coordination number for a bulk atom.

Returns:
    A tuple of ``(thickness, n_layers, layers)`` where *layers*
    is ``[bottom_indices, bulk_indices, top_indices]``.

## `SurfaceFixer.get_surface_atoms`

源文件：[Fix_atoms.py](Fix_atoms.py)，第 139 行。

```python
SurfaceFixer.get_surface_atoms(self, target_cn: int=6, distance: float | None=None)
```

Return detailed surface-atom information.

Args:
    target_cn: Minimum coordination number for a bulk atom.
    distance: If given, group surface atoms by z proximity
        (used to resolve sub-layer structure).

Returns:
    Dictionary with keys ``top_info``, ``bottom_info``, ``top``,
    ``bottom``.  When *distance* is provided also includes
    ``top_groups``, ``bottom_groups``, ``n_top_groups``,
    ``n_bottom_groups``.

## `SurfaceFixer.fix_center_layers`

源文件：[Fix_atoms.py](Fix_atoms.py)，第 198 行。

```python
SurfaceFixer.fix_center_layers(self, target_cn: int=6)
```

Fix (constrain) the bulk layer identified by CN analysis.

Args:
    target_cn: Minimum coordination number for a bulk atom.

Returns:
    The structure with the bulk layer fixed.

## `SurfaceFixer.fix_center_distance`

源文件：[Fix_atoms.py](Fix_atoms.py)，第 210 行。

```python
SurfaceFixer.fix_center_distance(self, thickness: float=4.0)
```

Fix atoms within a slab of *thickness* centered on z_center.

Args:
    thickness: Total thickness (Å) of the fixed central region.

Returns:
    The structure with the central region fixed.

## `SurfaceFixer.fix_center_fraction`

源文件：[Fix_atoms.py](Fix_atoms.py)，第 222 行。

```python
SurfaceFixer.fix_center_fraction(self, fraction: float=1 / 3)
```

Fix a given fraction of atoms closest to z_center.

Atoms are sorted by distance from the slab centre; the
closest *fraction* are fixed.

Args:
    fraction: Fraction of total atoms to fix (default 1/3).

Returns:
    The structure with the closest atoms fixed.

## `SurfaceFixer.fix_bottom_fraction`

源文件：[Fix_atoms.py](Fix_atoms.py)，第 239 行。

```python
SurfaceFixer.fix_bottom_fraction(self, fraction: float=0.5)
```

Fix atoms in the bottom *fraction* of the c-axis range.

Unlike the atom-count-based ``fix_center_fraction``, this
method uses the fractional c-coordinate range, so that all
atoms on the same c-layer are either fully fixed or fully free.

Args:
    fraction: Fraction of the c-axis range to fix, measured from
        the bottom (default 0.5).  Must be in (0, 1].

Returns:
    The structure with the selected bottom region fixed.

Raises:
    ValueError: If *fraction* is not in (0, 1].

## `SurfaceFixer.fix_bottom_distance`

源文件：[Fix_atoms.py](Fix_atoms.py)，第 265 行。

```python
SurfaceFixer.fix_bottom_distance(self, distance: float=2.0)
```

Fix atoms within *distance* (Å) of the bottom of the slab.

Args:
    distance: Maximum distance from ``zmin`` to fix (Å).

Returns:
    The structure with the bottom region fixed.

## `LOSlabProcessor`

源文件：[Generate_StructFace_Class.py](Generate_StructFace_Class.py)，第 22 行。

```python
LOSlabProcessor
```

Generate and classify surface slabs for a bulk structure.

The processor iterates over symmetrically distinct Miller indices,
creates slab models, and applies an oxidation-state transformation
to analyse polarity and symmetry.  Results are written as VASP
POSCAR files into an output directory tree.

Attributes:
    struct: The bulk pymatgen ``Structure``.
    oxi: An oxidation-state transformer (e.g.
        ``OxidationStateDecorationTransformation``).
    base_dir: Root output directory as a ``Path``.

## `LOSlabProcessor.__init__`

源文件：[Generate_StructFace_Class.py](Generate_StructFace_Class.py)，第 37 行。

```python
LOSlabProcessor.__init__(self, structure: Structure, oxi_transformer: Any, output_dir: str='output')
```

Initialize the processor.

Args:
    structure: Bulk pymatgen structure.
    oxi_transformer: Callable / transformation that decorates a
        structure with oxidation states.
    output_dir: Root directory for POSCAR output.

## `LOSlabProcessor.get_miller_indices`

源文件：[Generate_StructFace_Class.py](Generate_StructFace_Class.py)，第 60 行。

```python
LOSlabProcessor.get_miller_indices(self, max_index: int)
```

Return symmetrically distinct Miller indices sorted by d-spacing.

Args:
    max_index: Maximum Miller index to consider.

Returns:
    List of ``((h, k, l), d_hkl)`` tuples, descending by
    d-spacing (largest interplanar distance first).

## `LOSlabProcessor.generate_slabs`

源文件：[Generate_StructFace_Class.py](Generate_StructFace_Class.py)，第 81 行。

```python
LOSlabProcessor.generate_slabs(self, miller_index: tuple[int, ...], min_slab_size: float=15.0, min_vacuum_size: float=12.0)
```

Generate all unique slabs for a given Miller index.

Args:
    miller_index: (h, k, l) tuple.
    min_slab_size: Minimum slab thickness (Å).
    min_vacuum_size: Minimum vacuum thickness (Å).

Returns:
    A tuple of ``(slabs, generator)``.

## `LOSlabProcessor.analyze_face`

源文件：[Generate_StructFace_Class.py](Generate_StructFace_Class.py)，第 112 行。

```python
LOSlabProcessor.analyze_face(self, slab_struct: Structure)
```

Analyze polarity and symmetry of a slab.

An oxidation-state transformation is applied to both the slab
and the bulk before constructing the ``Slab`` analysis object.

Args:
    slab_struct: A slab ``Structure`` with a ``miller_index``
        attribute.

Returns:
    Dictionary with keys ``is_polar``, ``is_symmetric``, and
    ``slab_obj`` (the pymatgen ``Slab`` used for analysis).

## `LOSlabProcessor.process_and_save`

源文件：[Generate_StructFace_Class.py](Generate_StructFace_Class.py)，第 149 行。

```python
LOSlabProcessor.process_and_save(self, max_miller: int=2)
```

Run the full slab-generation pipeline for all faces up to *max_miller*.

Slabs are saved as POSCAR files under
``<base_dir>/Polar<p>_Sym<s>/``, where *p* and *s* are 0/1
flags for polarity and symmetry.

Non-symmetric or polar slabs are symmetrized via
``nonstoichiometric_symmetrized_slab``; if the slab is too thin
for symmetrization a 2×2×1 supercell is tried first.

Args:
    max_miller: Maximum Miller index to explore (default 2).

## `get_symmetry_atom`

源文件：[Surface_atom_process.py](Surface_atom_process.py)，第 63 行。

```python
get_symmetry_atom(struct: Structure, index_list: list[int] | None=None)
```

Find symmetry-equivalent partners for each atom in *index_list*.

For each atom index, returns the index of a symmetry-equivalent
atom (different from itself) if one exists within the tolerance
``SYM_DIST_TOL``, otherwise ``None``.

Args:
    struct: A pymatgen ``Structure``.
    index_list: Atom indices to query.  If ``None``, an empty list
        is used.

Returns:
    Dictionary with keys ``init_list`` (original indices) and
    ``sym_list`` (partner index or ``None`` for each).

## `sym_surface_remove_atoms_single`

源文件：[Surface_atom_process.py](Surface_atom_process.py)，第 107 行。

```python
sym_surface_remove_atoms_single(struct: Structure, tar_dir: Path, inter_atom: int=INTER_ATOM_STEP, nstr: int=NSTRUCT, select_s: int=SELECT_S)
```

Generate disordered surface configurations for single-element surfaces.

Designed for slabs whose top and bottom surfaces each consist of a
single element type.  The workflow:

1. Identify surface atoms via ``SurfaceFixer``.
2. Replace surface atoms with hydrogen.
3. Apply a solid-solution (H / original element) disorder.
4. Generate candidate structures with ``gen_ESGS_structure``.
5. Keep only structures where the original element is balanced
   between top and bottom surfaces.

Results are written as POSCAR files under *tar_dir*.

Args:
    struct: Slab structure (must have ``selective_dynamics`` site
        property).
    tar_dir: Output directory for POSCAR files.
    inter_atom: Atom-removal step size for composition sweeping.
    nstr: Number of trial structures per composition.
    select_s: Maximum structures to keep per composition.

Returns:
    ``"not single Surface"`` if the surface is not single-element
    on both sides; otherwise ``None`` (results written to disk).

