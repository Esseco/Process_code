# Process_Struct 参数索引

源码静态索引；保留原有函数名。类构造和公开方法分别列出。默认值不代表适用于所有体系。

## `theoretical_specific_capacity`

源文件：[Cal_capacity.py](Cal_capacity.py)，第 43 行。

```python
theoretical_specific_capacity(formula: str, migrating_ion=None)
```

Calculate theoretical specific capacity in mAh/g.

The number of transferable ions is taken from the stoichiometric coefficient
of ``migrating_ion`` in ``formula``. The molar mass includes the complete
input formula.

Args:
    formula: Electrode formula, for example ``"LiFePO4"``.

Returns:
    Theoretical specific capacity in mAh/g.

## `calc_formation_energy`

源文件：[Cal_eform.py](Cal_eform.py)，第 4 行。

```python
calc_formation_energy(df, comp_col, energy_col, fix_ion=None, ion=None, calc_voltage=False)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `read_channel_net`

源文件：[ccnb_net.py](ccnb_net.py)，第 5 行。

```python
read_channel_net(path: Path)
```

Read NET rows, retaining periodic images and reverse connections.

## `prepare_anion_groups`

源文件：[Chemical_Capacity_Constraints/anion_context.py](Chemical_Capacity_Constraints/anion_context.py)，第 13 行。

```python
prepare_anion_groups(formula: str, amounts: Mapping[str, float], rules: Mapping, anion_groups: Mapping[str, float] | None=None)
```

Remove recognized fixed-charge groups and return their net charge.

Groups in parentheses are treated as explicit. Without explicit grouping,
common groups are inferred from the composition and the result is marked as
heuristic. Pass ``anion_groups={"PO4": 2, "SO4": 1}`` to resolve ambiguous
or unparenthesized formulas. Context-dependent groups are never inferred.

## `estimate_mobile_ion_window`

源文件：[Chemical_Capacity_Constraints/framework_ion_window.py](Chemical_Capacity_Constraints/framework_ion_window.py)，第 37 行。

```python
estimate_mobile_ion_window(formula: str, *, mobile_ion: str='Na', environment: str='auto', anion_redox_scenario: str='none', anion_groups: Mapping[str, float] | None=None, rules_path: str=RULES_PATH)
```

Estimate the min/max Li or Na content charge-balanced by a framework.

``formula`` may be either a bare framework (for example ``FePO4``) or a
full composition containing the selected mobile ion (for example
``NaFePO4``). The selected Li/Na is removed before framework charges are
evaluated. If present, its input amount is returned as ``initial_x``.

For each framework element, the configured oxidation-state endpoints are
combined independently. The guest-ion range is therefore a permissive
envelope that allows mixed valence / partial occupancy between endpoints.

## `batch_estimate_mobile_ion_windows`

源文件：[Chemical_Capacity_Constraints/framework_ion_window.py](Chemical_Capacity_Constraints/framework_ion_window.py)，第 267 行。

```python
batch_estimate_mobile_ion_windows(formulas: Iterable[str], *, mobile_ion: str='Na', environment: str='auto', anion_redox_scenario: str='none', anion_groups: Mapping[str, float] | None=None, rules_path: str=RULES_PATH)
```

Estimate guest-ion windows for many formulas, retaining row-level errors.

## `load_rules`

源文件：[Chemical_Capacity_Constraints/redox_capacity.py](Chemical_Capacity_Constraints/redox_capacity.py)，第 25 行。

```python
load_rules(path: str | Path=RULES_PATH)
```

Load the editable oxidation-state rules.

## `infer_environment`

源文件：[Chemical_Capacity_Constraints/redox_capacity.py](Chemical_Capacity_Constraints/redox_capacity.py)，第 35 行。

```python
infer_environment(formula: str | Composition)
```

Infer a broad anion family; pass environment explicitly when ambiguous.

## `estimate_redox_capacity`

源文件：[Chemical_Capacity_Constraints/redox_capacity.py](Chemical_Capacity_Constraints/redox_capacity.py)，第 199 行。

```python
estimate_redox_capacity(formula: str, *, environment: str='auto', mobile_ions: Mapping[str, float] | None=None, active_elements: Iterable[str] | None=None, anion_redox_scenario: str='none', anion_groups: Mapping[str, float] | None=None, rules_path: str | Path=RULES_PATH, max_solutions: int=10000)
```

Estimate charge-neutral valences and a heuristic electron/capacity budget.

Pass the full composition at the intended initial SOC (normally the
alkali-containing, discharged composition). Alkali ions are assigned their
fixed formal charges for neutrality and their extractable charge inventory
caps the reported capacity. If no mobile ion from mobile_ions is present,
no mobile-ion cap is applied.

The default Q_redox includes transition-metal/cation oxidation only.
Optional anion scenarios are reported separately and added only when
explicitly selected.

## `batch_estimate_redox_capacity`

源文件：[Chemical_Capacity_Constraints/redox_capacity.py](Chemical_Capacity_Constraints/redox_capacity.py)，第 406 行。

```python
batch_estimate_redox_capacity(formulas: Iterable[str], *, environment: str='auto', capacity_cutoff_mAh_g: float=100.0, mobile_ions: Mapping[str, float] | None=None, anion_redox_scenario: str='none', anion_groups: Mapping[str, float] | None=None, rules_path: str | Path=RULES_PATH)
```

Apply the estimator to many formulas and return flat, CSV-friendly rows.

## `screen_substitutions`

源文件：[Chemical_Capacity_Constraints/redox_capacity.py](Chemical_Capacity_Constraints/redox_capacity.py)，第 476 行。

```python
screen_substitutions(formula: str, replaced_element: str, candidate_elements: Sequence[str] | None=None, *, environment: str='auto', capacity_cutoff_mAh_g: float=100.0, q_cutoff_e_per_formula: float | None=None, mobile_ions: Mapping[str, float] | None=None, anion_redox_scenario: str='none', anion_groups: Mapping[str, float] | None=None, rules_path: str | Path=RULES_PATH)
```

Screen same-stoichiometry elemental substitutions by charge/capacity only.

This does not create or relax structures and does not predict synthesis,
phase stability, percolation, ion transport, or electronic conductivity.

## `main`

源文件：[Chemical_Capacity_Constraints/redox_capacity.py](Chemical_Capacity_Constraints/redox_capacity.py)，第 593 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `deduplicate`

源文件：[deduplication.py](deduplication.py)，第 9 行。

```python
deduplicate(struc_lst: list)
```

deduplicate 的 Docstring

:param struc_lst: structs list
:type struc_lst: list
:return: deduplicated list
:rtype: list

## `deduplicate_dict`

源文件：[deduplication.py](deduplication.py)，第 33 行。

```python
deduplicate_dict(struc_dict: dict)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `deduplicate_df`

源文件：[deduplication.py](deduplication.py)，第 59 行。

```python
deduplicate_df(df: pd.DataFrame, n_keep: int, struct_col: str='struct', energy_col: str='energy_mean_per_atom')
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/capacity.py](examples/capacity.py)，第 5 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/deduplicate_structures.py](examples/deduplicate_structures.py)，第 10 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/octahedra.py](examples/octahedra.py)，第 8 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/percolation.py](examples/percolation.py)，第 8 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `export_sites`

源文件：[examples/percolation_sites.py](examples/percolation_sites.py)，第 28 行。

```python
export_sites(folder: Path, migrant: str | None)
```

Export channel NET sites and edges; retain every periodic connection.

## `main`

源文件：[examples/percolation_sites.py](examples/percolation_sites.py)，第 97 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/structure_features.py](examples/structure_features.py)，第 9 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/wyckoff_sites.py](examples/wyckoff_sites.py)，第 7 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `sanitize_for_json`

源文件：[Get_Oct_distortion.py](Get_Oct_distortion.py)，第 8 行。

```python
sanitize_for_json(df)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `analyze_octahedra_distortion`

源文件：[Get_Oct_distortion.py](Get_Oct_distortion.py)，第 25 行。

```python
analyze_octahedra_distortion(struct, TM_elements=['Fe', 'Mn'], cutoff_O=2.5, cutoff_TM1=3.5, cutoff_TM2=5.5, ligands_max_dist=3.0)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `StructureFeatureExtractor`

源文件：[Get_structfeatures_all.py](Get_structfeatures_all.py)，第 27 行。

```python
StructureFeatureExtractor
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `StructureFeatureExtractor.__init__`

源文件：[Get_structfeatures_all.py](Get_structfeatures_all.py)，第 104 行。

```python
StructureFeatureExtractor.__init__(self, global_features: str | list[str] | None='all', local_features: str | list[str] | None='all', ligand: str='O', tm_elements: list[str] | None=None, na_species: tuple=('Na',), tm_species: tuple=('Mn', 'Fe', 'Co', 'Ni', 'Cu'), layer_axis: int=2, layer_tol: float=0.08, ligands_max_dist: float=3.0)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `StructureFeatureExtractor.cnn`

源文件：[Get_structfeatures_all.py](Get_structfeatures_all.py)，第 156 行。

```python
StructureFeatureExtractor.cnn(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `StructureFeatureExtractor.extract`

源文件：[Get_structfeatures_all.py](Get_structfeatures_all.py)，第 163 行。

```python
StructureFeatureExtractor.extract(self, structure: Structure, supercell_matrix=None)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `StructureFeatureExtractor.extract_features`

源文件：[Get_structfeatures_all.py](Get_structfeatures_all.py)，第 290 行。

```python
StructureFeatureExtractor.extract_features(cls, structure: Structure, **kwargs)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `analyze_percolation`

源文件：[percolation.py](percolation.py)，第 167 行。

```python
analyze_percolation(structure: Structure | str | Path, migrant: str | None=None, *, cutoff_radius: float, output_dir: str | Path | None=None)
```

Return geometric channel connectivity at a probe radius in Å.

``structure`` accepts a pymatgen Structure or any file format it can read.
An empty ``migrant`` keeps all atoms and measures the original void network.
A specified element is removed by CCNB before channel analysis. The
returned dimension is 0, 1, 2, or 3; it is not a migration energy barrier.
Generated files are retained under ``output_dir`` when that is provided.
On Windows, transient locks on generated files are retried during cleanup;
a persistent cleanup failure is returned in ``cleanup_warning`` together
with the remaining temporary directory path.

## `estimate_spatial_capacity`

源文件：[spatial_capacity.py](spatial_capacity.py)，第 54 行。

```python
estimate_spatial_capacity(structure: Structure | str | Path, mobile_ion: str='Na', *, cutoff_radius: float=0.8, min_site_distance_A: float=2.0, output_dir: str | Path | None=None, verbose: bool=True)
```

Estimate feasible loading of CCNB percolating-channel sites in mAh/g.

Input: ordered Structure or readable structure file; Li/Na is removed by
CCNB. First find channels at cutoff_radius (angstrom), then use only nodes
in their 1D/2D/3D percolating components, with free radius >= cutoff_radius.
Isolated voids and 0D components are excluded; no percolating channel means
zero capacity. Repeated periodic positions are counted once. Bottleneck
points are not storage sites; equivalent labels do not collapse different
positions. Pair distances include periodic boundaries and must be >=
min_site_distance_A (default 2 angstrom).

One deterministic radius-priority greedy pass returns a feasible site count,
using distance rows instead of a full matrix. It is NOT a proven
maximum or an experimental reversible capacity. Each selected site holds
one monovalent Li/Na. Default mass basis is framework + selected ions:
Q = 26801.481145 * N / (M_framework + N * M_ion), using the input cell's
composition and site count. Input-mass and framework-mass bases are also
returned. Geometric percolation is required, but charge balance, site energy
and migration barriers are not evaluated.

Run in ccnb. No random seed is used. CCNB writes a unique temporary folder;
default cleanup preserves the returned data on lock failure. output_dir
retains a new unique folder each run; existing results are not overwritten.
verbose prints elapsed CCNB and packing stages; set False to silence them.

## `DeduplicationTests`

源文件：[test_deduplication.py](test_deduplication.py)，第 8 行。

```python
DeduplicationTests
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `DeduplicationTests.test_compatibility_and_order`

源文件：[test_deduplication.py](test_deduplication.py)，第 9 行。

```python
DeduplicationTests.test_compatibility_and_order(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `save_traj_xyz`

源文件：[Traj_Convert.py](Traj_Convert.py)，第 6 行。

```python
save_traj_xyz(traj, save_name, include_e=True, include_f=False, include_s=False)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `traj_to_info`

源文件：[Traj_Convert.py](Traj_Convert.py)，第 26 行。

```python
traj_to_info(traj_file, include_e=True, include_f=False, include_s=False)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `Octahedron`

源文件：[van_vleck_calculator.py](van_vleck_calculator.py)，第 21 行。

```python
Octahedron
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `Octahedron.__init__`

源文件：[van_vleck_calculator.py](van_vleck_calculator.py)，第 33 行。

```python
Octahedron.__init__(self, core_site, structure, ligands_min_distance=0.0, ligands_max_distance=2.7, forbidden_ligands=[], possible_ligands=None)
```

The initialisation of an instance of the Octahedron class.

Arguments:
-core_site: the atom in the centre (pymatgen PeriodicSite object)
-structure: a pymatgen Structure object corresponding to the unit  
  cell containing the core_site
-ligands_min_distance: an optional argument (defaults to 0.0 if not 
  includes) which gives the minimum distance from core_site (in 
  Angstroms) for atoms to be considered possible ligands.
-ligands_max_distance: an optional argument (defaults to 2.7 if not
  included) which gives the maximum distance from core_site (in 
  Angstroms) for atoms to be considered possible ligands.
-forbidden_ligands: an optional argument which lists the names of 
  species which specifically cannot be considered as ligands; for 
  instance, if the core_site is "Ni" you may which to exclude "Ni" 
  from being considered as a possible ligand. If not included, 
  defaults to an empty list.
-possible_ligands: an optional argument which lists atom types 
  which can be considered Ligands. Defaults to a None value in 
  which case all species which are not listed in forbidden_ligands
  are considered as possible ligands.

## `Octahedron.calculate_core_ligand_distance_for_perfect_octahedron`

源文件：[van_vleck_calculator.py](van_vleck_calculator.py)，第 263 行。

```python
Octahedron.calculate_core_ligand_distance_for_perfect_octahedron(self)
```

This method will calculate the core-ligand distance for a perfect
  octahedron of equal volume to the octahedron.

A perfect octahedron can be split into two square-based pyramids 
  with base area a.
  Hence the volume is V=sqrt(2)*a^3/3
  from Pythagoras's theorem, 2a^2 = (2l_0)^2 so a = sqrt(2)*l_0
  therefore l_0 = (6*V)^(1/3)

return:
  float: the core-ligand distance for a perfect octahedron of 
    equal volume to the octahedron, in Angstroms.

## `Octahedron.calculate_quadratic_elongation`

源文件：[van_vleck_calculator.py](van_vleck_calculator.py)，第 281 行。

```python
Octahedron.calculate_quadratic_elongation(self)
```

This method calculates the quadratic elongation of the octahedron, 
  as defined in:
    Robinson, Keith, G. V. Gibbs, and P. H. Ribbe.
    "Quadratic elongation: a quantitative measure of distortion 
    in coordination polyhedra."
    Science 172.3983 (1971): 567-570.

Return:
  float: the quadratic elongation of the octahedron.

## `Octahedron.get_intersite_distance`

源文件：[van_vleck_calculator.py](van_vleck_calculator.py)，第 301 行。

```python
Octahedron.get_intersite_distance(self, site1, site2, override_lattice_check=False)
```

This method will give the distance between two sites. Pymatgen 
  does include functionality to do this, but it does not work well 
  when it encounters periodicity, i.e. if a neighbour is in a 
  neighbouring unit cell. This custom method should therefore be 
  used.

Arguments:
  site1: a Pymatgen PeriodicSite object
  site2: a Pymatgen PeriodicSite object
  override_lattice_check: bool. optional, defaults to False. If 
    True, there will be no check to make sure site1 and site2 are 
    in the same cell.

Return: 
  float: the distance (in Angstroms) between the two sites.

## `Octahedron.get_neighbours`

源文件：[van_vleck_calculator.py](van_vleck_calculator.py)，第 338 行。

```python
Octahedron.get_neighbours(self, ligands_min_distance=0.0, ligands_max_distance=2.7, forbidden_ligands=[], possible_ligands=None)
```

This method will list all ligands, in ascending order of bond 
  length from the core_site, provided they meet the criteria 
  given in the __init__ method.

Arguments (all optional):
  ligands_min_distance (float): the minimum distance of a site to 
    be considered a neighbour (in Angstroms)
  ligands_max_distance (float) the maximum distance of a site to 
    be considered a neighbour (in Angstroms)
  forbidden_ligands (list): a list of strings or site species which 
    may not be considered neighbours
  possible_ligands (list or None): a list of strings or site 
    species which only may be considered neighbours. Defaults to 
    None, meaning no restriction
  
Return:
  Python list: containing PeriodicSite objects

## `Octahedron.calculate_average_ligand_bond_length`

源文件：[van_vleck_calculator.py](van_vleck_calculator.py)，第 421 行。

```python
Octahedron.calculate_average_ligand_bond_length(self, octahedral_centre='core_atom')
```

Calculates the average bond length between the centre of the 
  octahedron and its ligands.

Arguments:
  octahedral_centre (string or list): if "core_atom", the centre 
    of the octahedron is the position of the core atom. If 
    "average_ligand_position" then the octahedral centre
    is the average position of the ligands. If list, must be 
    a list of three floats which are the coordinates to be taken
    as the centre of the octahedron.

Returns:
  float: The average bond length.

## `Octahedron.calculate_bond_length_distortion_index`

源文件：[van_vleck_calculator.py](van_vleck_calculator.py)，第 495 行。

```python
Octahedron.calculate_bond_length_distortion_index(self, octahedral_centre='core_atom')
```

Calculates and returns the bond length distortion index of a 
  polyhedron as defined in Baur (1974).
The bond length distortion index is calculated as the average 
  absolute deviation of individual centre-ligand bond lengths 
  from the average bond length, normalized by the average
  bond length.

Reference:
  Baur, W. H. "The geometry of polyhedral distortions. Predictive 
  relationships for the phosphate group." Acta Crystallographica 
  Section B: Structural Crystallography and Crystal Chemistry,
  1974, 30(5), 1195-1215.

Arguments:
  octahedral_centre (string or list): if "core_atom", the centre 
    of the octahedron is the position of the core atom. If 
    "average_ligand_position" then the octahedral centre
    is the average position of the ligands. If list, must be 
    a list of three floats which are the coordinates to be taken
    as the centre of the octahedron.

Returns:
  float: the bond length distortion index.

## `Octahedron.get_bond_angle`

源文件：[van_vleck_calculator.py](van_vleck_calculator.py)，第 574 行。

```python
Octahedron.get_bond_angle(self, ligand1, ligand2, degrees=True)
```

Calculates the angle between the bonds of two ligand ions 
  to the core atom.

Arguments:
    ligand1 (PeriodicSite): the first ligand ion
    ligand2 (PeriodicSite): the second ligand ion
    degrees: if True, output is in degrees. Otherwise output 
      is radians. Defaults to True

Returns:
    float: the angle between the bonds in degrees

## `Octahedron.list_all_ligand_core_ligand_angles`

源文件：[van_vleck_calculator.py](van_vleck_calculator.py)，第 628 行。

```python
Octahedron.list_all_ligand_core_ligand_angles(self, degrees=True)
```

Returns an array containing all bond angles (including bond angles 
  between opposite ligands).

Arguments:
  degrees (bool): an optional argument, defaults to True. 
    Calculated values are degrees (True) or radians (False)

## `Octahedron.calculate_bond_angle_variance`

源文件：[van_vleck_calculator.py](van_vleck_calculator.py)，第 654 行。

```python
Octahedron.calculate_bond_angle_variance(self, degrees=True)
```

Calculates the bond angle variance, as defined in
    Baur, W. H. "The geometry of polyhedral distortions. 
    Predictive relationships for the phosphate group."
    Acta Crystallographica Section B: Structural Crystallography 
    and Crystal Chemistry 30.5 (1974): 1195-1215.

Arguments:
  degrees (bool): an optional argument, defaults to True. 
    Calculated value is degrees (True) or radians (False)

return:
  float: the bond angle variance, in units of either degrees or
    radians depending on user input

## `Octahedron.calculate_effective_coordination_number`

源文件：[van_vleck_calculator.py](van_vleck_calculator.py)，第 687 行。

```python
Octahedron.calculate_effective_coordination_number(self)
```

This method calculates the effective coordination number of the 
  octahedron as first defined in the following paper:
    Hoppe, Rudolf. "Effective coordination numbers (ECoN) and 
    mean fictive ionic radii (MEFIR)." Zeitschrift für 
    Kristallographie-Crystalline Materials 150.1-4 (1979): 23-52.

return:
  float: the effective coordination number

## `Octahedron.calculate_off_centering_distance`

源文件：[van_vleck_calculator.py](van_vleck_calculator.py)，第 715 行。

```python
Octahedron.calculate_off_centering_distance(self)
```

This method calculates the off-centering distance defined in Eq 7 
  of:
    Koçer, Can P., et al.
    "Cation disorder and lithium insertion mechanism of 
    Wadsley–Roth crystallographic shear phases from first 
    principles."
    Journal of the American Chemical Society 141.38 
    (2019): 15121-15134.

return:
  float: the off-centering distance (in Angstroms)

## `Octahedron.calculate_surface_area`

源文件：[van_vleck_calculator.py](van_vleck_calculator.py)，第 951 行。

```python
Octahedron.calculate_surface_area(self)
```

Octahedral surface area is defined by splitting up the surface area
  into a set of triangles and summing the area of these triangles, 
  following the method described in:
    Swanson, Donald K., and R. C. Peterson. "Polyhedral volume 
    calculations."
    The Canadian Mineralogist 18.2 (1980): 153-156.

return:
  float: surface area of the exterior triangles of the Octahedron 
    (in Angstroms squared)

## `Octahedron.calculate_volume`

源文件：[van_vleck_calculator.py](van_vleck_calculator.py)，第 986 行。

```python
Octahedron.calculate_volume(self)
```

This method returns the volume of the octahedron. It first attempts
  to split the octahedron into 8 tetrahedra. If this fails, it uses
  the more generalised approach given in:
    Swanson, Donald K., and R. C. Peterson. "Polyhedral volume 
    calculations."
    The Canadian Mineralogist 18.2 (1980): 153-156.

return:
  float: octahedral volume in units of Angstrom cubed

## `Octahedron.is_identical`

源文件：[van_vleck_calculator.py](van_vleck_calculator.py)，第 1055 行。

```python
Octahedron.is_identical(self, octahedron)
```

This method checks to see whether a given octahedron object is 
  identical to self.

argument:
  an instance of the Octahedron class, or a subclass

return: 
  boolean: True, if the Octahedron object is 
    identical

## `Octahedron.visualise_pairs`

源文件：[van_vleck_calculator.py](van_vleck_calculator.py)，第 1117 行。

```python
Octahedron.visualise_pairs(self, plotted_vectors=None)
```

This method plots a 3D, interactive figure which shows the 
  positions of the pairs relative to the origin.
It can also plot axes alongside the atomic sites if plotted_vectors
  is included.

argument:
  plotted_vectors: must be a python list or None. If list, must be 
    a list with shape (3,3), representing three vectors which may be
    supplied and will be plotted alongside the points. Defaults to 
    None.

## `Octahedron.calculate_off_centering_metric`

源文件：[van_vleck_calculator.py](van_vleck_calculator.py)，第 1197 行。

```python
Octahedron.calculate_off_centering_metric(self)
```

This method calculates the off-centering metric defined in 
  page 3588 of:
    Halasyamani, P. Shiv.
    "Asymmetric cation coordination in oxide materials:
    Influence of lone-pair cations on the intra-octahedral 
    distortion in d0 transition metals."
    Chemistry of Materials 16.19 (2004): 3586-3592.

return:
  float: the value of the off-centering metric 

## `Octahedron.find_ligand_opposites`

源文件：[van_vleck_calculator.py](van_vleck_calculator.py)，第 1427 行。

```python
Octahedron.find_ligand_opposites(self)
```

Returns 3 arrays each containing two pymatgen PeriodicSite objects. 
  These are the two opposite ligands in the octahedra (i.e. have a 
  bond length 180 degrees through the central atom). It does this 
  by assuming opposite bonds will have the largest angle via the 
  central atom.

return:
  a list of shape (3,2), where the 3 are the three pairs of 
    opposite ligands and the 2 is each ligand within a pair.

## `Octahedron.calculate_van_vleck_distortion_modes`

源文件：[van_vleck_calculator.py](van_vleck_calculator.py)，第 2373 行。

```python
Octahedron.calculate_van_vleck_distortion_modes(self, octahedral_centre='core_atom', specified_axes=[[1, 0, 0], [0, 1, 0], [0, 0, 1]], suppress_warnings=False, automatic_rotation=True, output_pairs=False, ignore_angular_distortion=False, rotation_tolerance=GLOBAL_PARAM__FAILED_ROTATION_THRESHOLD, omit_failed_rotations=False)
```

This method calculates the magnitude of the Q_1 to Q_6 distortion 
  modes, as defined by Van Vleck:
    Van Vleck, J. H. "The Jahn‐Teller Effect and Crystalline Stark
    Splitting for Clusters of the Form XY6." The Journal of 
    Chemical Physics 7.1 (1939): 72-84.

arguments:
  octahedral_centre (string or list): if "core_atom", the centre 
    of the octahedron is the position of the core atom. If 
    "average_ligand_position" then the octahedral centre
    is the average position of the ligands. If list, must be 
    a list of three floats which are the coordinates to be taken
    as the centre of the octahedron.
  specified_axes must be a list containing three lists, with each 
    sub-list containing three elements. These are three vectors 
    which will be set as the axes for the Van Vleck calculation.  
    They must be perpendicular to eachother.
    For example: [[1,0,0],[0,1,0],[0,0,1]] 
      or [[1,0,1],[1,0,-1],[0,1,0]]
  automatic_rotation: bool. Defaults to True. If True, the 
    automated rotation of the octahedron will occur. If False, it
    will not.
  ignore_angular_distortion: if True, no rotation operations will 
    be performed, and the van Vleck modes will be calculated along 
    bond lengths without regard to their angles. 
  suppress_warnings: bool. if True, will suppress warnings to 
    console. Defaults to False.
  rotation_tolerance: float, in units of Angstroms. If an atom is
    more than this distance from its assigned axis, the rotation
    is considered to have failed.
  omit_failed_rotations: bool. If True, when rotation fails, 
    returns only NoneType output. Defaults to False.
  output_pairs: bool. if True, the code gives as a return the pairs 
    list. Defaults to False.

return:
  -a list containing the 6 Van Vleck modes
  -[if output_pairs]: a 2D list containing the coordinates of all sites after axis transformation

## `Octahedron.calculate_degenerate_Q3_van_vleck_modes`

源文件：[van_vleck_calculator.py](van_vleck_calculator.py)，第 2499 行。

```python
Octahedron.calculate_degenerate_Q3_van_vleck_modes(self, octahedral_centre='core_atom', specified_axes=[[1, 0, 0], [0, 1, 0], [0, 0, 1]], suppress_warnings=False, automatic_rotation=True, output_pairs=False, ignore_angular_distortion=False, rotation_tolerance=GLOBAL_PARAM__FAILED_ROTATION_THRESHOLD, omit_failed_rotations=False)
```

This method outputs the magnitude of the Q_3 distortion mode 
  and its two symmetrically identical linear combinations of Q_2 
  and Q_3:
    -1/2 Q_3 ± √3/2 Q_2
  where Q_2 and Q_3 are as defined by Van Vleck:
    Van Vleck, J. H. "The Jahn‐Teller Effect and Crystalline Stark
      Splitting for Clusters of the Form XY6." The Journal of 
      Chemical Physics 7.1 (1939): 72-84.

arguments:
  octahedral_centre (string or list): if "core_atom", the centre 
    of the octahedron is the position of the core atom. If 
    "average_ligand_position" then the octahedral centre
    is the average position of the ligands. If list, must be 
    a list of three floats which are the coordinates to be taken
    as the centre of the octahedron.
  specified_axes must be a list containing three lists, with each 
    sub-list containing three elements. These are three vectors 
    which will be set as the axes for the Van Vleck calculation.  
    They must be perpendicular to eachother.
    For example: [[1,0,0],[0,1,0],[0,0,1]] 
      or [[1,0,1],[1,0,-1],[0,1,0]]
  automatic_rotation: bool. Defaults to True. If True, the 
    automated rotation of the octahedron will occur. If False, it
    will not.
  ignore_angular_distortion: if True, no rotation operations will 
    be performed, and the van Vleck modes will be calculated along 
    bond lengths without regard to their angles. 
  suppress_warnings: bool. if True, will suppress warnings to 
    console. Defaults to False.
  rotation_tolerance: float, in units of Angstroms. If an atom is
    more than this distance from its assigned axis, the rotation
    is considered to have failed.
  omit_failed_rotations: bool. If True, when rotation fails, 
    returns only NoneType output. 
  output_pairs: bool. if True, the code gives as a return the pairs 
    list. Defaults to False.

## `Octahedron.calculate_van_vleck_jahn_teller_params`

源文件：[van_vleck_calculator.py](van_vleck_calculator.py)，第 2591 行。

```python
Octahedron.calculate_van_vleck_jahn_teller_params(self, octahedral_centre='core_atom', specified_axes=[[1, 0, 0], [0, 1, 0], [0, 0, 1]], degrees=False, suppress_warnings=False, automatic_rotation=True, output_pairs=False, ignore_angular_distortion=False, rotation_tolerance=GLOBAL_PARAM__FAILED_ROTATION_THRESHOLD, omit_failed_rotations=False)
```

This method outputs sqrt(Q_3^2 + Q_2^2) and arctan(Q_2/Q_3), which 
  can be used to generate a polar plot as in, for example:
    Zhou, J-S., et al. "Jahn–Teller distortion in perovskite 
    KCuF3 under high pressure."
    Journal of Fluorine Chemistry 132.12 (2011): 1117-1121.
    Figure 4.

arguments:
  octahedral_centre (string or list): if "core_atom", the centre 
    of the octahedron is the position of the core atom. If 
    "average_ligand_position" then the octahedral centre
    is the average position of the ligands. If list, must be 
    a list of three floats which are the coordinates to be taken
    as the centre of the octahedron.
  specified_axes must be a list containing three lists, with each 
    sub-list containing three elements. These are three vectors 
    which will be set as the axes for the Van Vleck calculation.  
    They must be perpendicular to eachother.
    For example: [[1,0,0],[0,1,0],[0,0,1]] 
      or [[1,0,1],[1,0,-1],[0,1,0]]
  automatic_rotation: bool. Defaults to True. If True, the 
    automated rotation of the octahedron will occur. If False, it
    will not.
  ignore_angular_distortion: if True, no rotation operations will 
    be performed, and the van Vleck modes will be calculated along 
    bond lengths without regard to their angles. 
  suppress_warnings: bool. if True, will suppress warnings to 
    console. Defaults to False.
  rotation_tolerance: float, in units of Angstroms. If an atom is
    more than this distance from its assigned axis, the rotation
    is considered to have failed.
  omit_failed_rotations: bool. If True, when rotation fails, 
    returns only NoneType output. Defaults to False.
  output_pairs: bool. if True, the code gives as a return the pairs 
    list. Defaults to False.
  degrees: bool. Defaults to False. If True, phi is returned in 
    degrees, otherwise it is in radians.

Return:
  -a list containing the params: magnitude and angle
  - [if output_pairs]: a list containing the atomic positions 
    within a list with shape (3,2,3)

## `Octahedron.output_sites_for_van_vleck`

源文件：[van_vleck_calculator.py](van_vleck_calculator.py)，第 2710 行。

```python
Octahedron.output_sites_for_van_vleck(self, octahedral_centre='core_atom', specified_axes=[[1, 0, 0], [0, 1, 0], [0, 0, 1]], automatic_rotation=True, suppress_warnings=False, rotation_tolerance=GLOBAL_PARAM__FAILED_ROTATION_THRESHOLD, omit_failed_rotations=False)
```

This method performs rotation of the ligands around a central point 
  and returns their positions. The purpose of this is for checking 
  that the ligand rotation for van Vleck calculation is working
  correctly.

arguments:
  octahedral_centre (string or list): if "core_atom", the centre 
    of the octahedron is the position of the core atom. If 
    "average_ligand_position" then the octahedral centre
    is the average position of the ligands. If list, must be 
    a list of three floats which are the coordinates to be taken
    as the centre of the octahedron.
  specified_axes must be a list containing three lists, with each 
    sub-list containing three elements. These are three vectors 
    which will be set as the axes for the Van Vleck calculation.  
    They must be perpendicular to eachother.
    For example: [[1,0,0],[0,1,0],[0,0,1]] 
      or [[1,0,1],[1,0,-1],[0,1,0]]
  automatic_rotation: bool. Defaults to True. If True, the 
    automated rotation of the octahedron will occur. If False, it
    will not.
  suppress_warnings: bool. if True, will suppress warnings to 
    console. Defaults to False.
  rotation_tolerance: float, in units of Angstroms. If an atom is
    more than this distance from its assigned axis, the rotation
    is considered to have failed.
  omit_failed_rotations: bool. If True, when rotation fails, 
    returns only NoneType output. Defaults to False.

## `Octahedron.visualise_sites_for_van_vleck`

源文件：[van_vleck_calculator.py](van_vleck_calculator.py)，第 2774 行。

```python
Octahedron.visualise_sites_for_van_vleck(self, octahedral_centre='core_atom', specified_axes=[[1, 0, 0], [0, 1, 0], [0, 0, 1]], automatic_rotation=True, output_pairs=False, rotation_tolerance=GLOBAL_PARAM__FAILED_ROTATION_THRESHOLD)
```

This method performs rotation of the ligands around a central point
  and plots their positions. The purpose of this is for checking 
  that the ligand rotation for van Vleck calculation is working
  correctly.

arguments:
  octahedral_centre (string or list): if "core_atom", the centre 
    of the octahedron is the position of the core atom. If 
    "average_ligand_position" then the octahedral centre
    is the average position of the ligands. If list, must be 
    a list of three floats which are the coordinates to be taken
    as the centre of the octahedron.
  specified_axes must be a list containing three lists, with each 
    sub-list containing three elements. These are three vectors 
    which will be set as the axes for the Van Vleck calculation.  
    They must be perpendicular to eachother.
    For example: [[1,0,0],[0,1,0],[0,0,1]] 
      or [[1,0,1],[1,0,-1],[0,1,0]]
  automatic_rotation: bool. Defaults to True. If True, the 
    automated rotation of the octahedron will occur. If False, it
    will not.
  rotation_tolerance: float, in units of Angstroms. If an atom is
    more than this distance from its assigned axis, the rotation
    is considered to have failed.
  output_pairs: if True, the code gives as a return the pairs 
    list. Defaults to False.

Action:
  plots 3D interactive plot showing the positions of the sites, to 
    check whether they are lose

## `Octahedron.output_and_visualise_sites_for_van_vleck`

源文件：[van_vleck_calculator.py](van_vleck_calculator.py)，第 2831 行。

```python
Octahedron.output_and_visualise_sites_for_van_vleck(self, octahedral_centre='core_atom', specified_axes=[[1, 0, 0], [0, 1, 0], [0, 0, 1]], automatic_rotation=True, rotation_tolerance=GLOBAL_PARAM__FAILED_ROTATION_THRESHOLD)
```

This method performs rotation of the ligands around a central 
  point and plots their positions. The purpose of this is for 
  checking that the ligand rotation for van Vleck calculation 
  is working correctly. It also returns a Python list with 
  shape (3,2,3) containing the coordinates of each site after 
  the rotation.

arguments:
  octahedral_centre (string or list): if "core_atom", the centre 
    of the octahedron is the position of the core atom. If 
    "average_ligand_position" then the octahedral centre
    is the average position of the ligands. If list, must be 
    a list of three floats which are the coordinates to be taken
    as the centre of the octahedron.
  specified_axes must be a list containing three lists, with each 
    sub-list containing three elements. These are three vectors 
    which will be set as the axes for the Van Vleck calculation.  
    They must be perpendicular to eachother.
    For example: [[1,0,0],[0,1,0],[0,0,1]] 
      or [[1,0,1],[1,0,-1],[0,1,0]]
  automatic_rotation: bool. Defaults to True. If True, the 
    automated rotation of the octahedron will occur. If False, it
    will not.
  rotation_tolerance: float, in units of Angstroms. If an atom is
    more than this distance from its assigned axis, the rotation
    is considered to have failed.

Action:
  plots 3D interactive plot showing the positions of the sites, to 
    check whether they are lose

## `Octahedron.calculate_angular_shear_modes`

源文件：[van_vleck_calculator.py](van_vleck_calculator.py)，第 2958 行。

```python
Octahedron.calculate_angular_shear_modes(self, octahedral_centre='core_atom', specified_axes=[[1, 0, 0], [0, 1, 0], [0, 0, 1]], suppress_warnings=False, automatic_rotation=True, rotation_tolerance=GLOBAL_PARAM__FAILED_ROTATION_THRESHOLD, omit_failed_rotations=False, degrees=False)
```

This method calculates the angular shear modes, Delta ab, 
  Delta ac, and Delta bc.

arguments:
  octahedral_centre (string or list): if "core_atom", the centre 
    of the octahedron is the position of the core atom. If 
    "average_ligand_position" then the octahedral centre
    is the average position of the ligands. If list, must be 
    a list of three floats which are the coordinates to be taken
    as the centre of the octahedron.
  specified_axes must be a list containing three lists, with each 
    sub-list containing three elements. These are three vectors 
    which will be set as the axes for the Van Vleck calculation.  
    They must be perpendicular to eachother.
    For example: [[1,0,0],[0,1,0],[0,0,1]] 
      or [[1,0,1],[1,0,-1],[0,1,0]]
  automatic_rotation: bool. Defaults to True. If True, the 
    automated rotation of the octahedron will occur. If False, it
    will not.
  rotation_tolerance: float, in units of Angstroms. If an atom is
    more than this distance from its assigned axis, the rotation
    is considered to have failed.
  degrees: bool. If True, returns units of degrees, otherwise 
    radians. Defaults to False.
  omit_failed_rotations: bool. If True, when rotation fails, 
    returns only NoneType output. Defaults to False.
  suppress_warnings: bool. if True, will suppress warnings to 
    console. Defaults to False.

return:
  list: a list of the three angular shear values, in units of
    degrees or radians depending on user-supplied arguments.

## `Octahedron.calculate_angular_antishear_modes`

源文件：[van_vleck_calculator.py](van_vleck_calculator.py)，第 3052 行。

```python
Octahedron.calculate_angular_antishear_modes(self, octahedral_centre='core_atom', specified_axes=[[1, 0, 0], [0, 1, 0], [0, 0, 1]], suppress_warnings=False, automatic_rotation=True, rotation_tolerance=GLOBAL_PARAM__FAILED_ROTATION_THRESHOLD, omit_failed_rotations=False, degrees=False)
```

This method calculates the angular anti-shear modes, Delta' ab, 
  Delta' ac, and Delta' bc.

arguments:
  octahedral_centre (string or list): if "core_atom", the centre 
    of the octahedron is the position of the core atom. If 
    "average_ligand_position" then the octahedral centre
    is the average position of the ligands. If list, must be 
    a list of three floats which are the coordinates to be taken
    as the centre of the octahedron.
  specified_axes must be a list containing three lists, with each 
    sub-list containing three elements. These are three vectors 
    which will be set as the axes for the Van Vleck calculation.  
    They must be perpendicular to eachother.
    For example: [[1,0,0],[0,1,0],[0,0,1]] 
      or [[1,0,1],[1,0,-1],[0,1,0]]
  automatic_rotation: bool. Defaults to True. If True, the 
    automated rotation of the octahedron will occur. If False, it
    will not.
  rotation_tolerance: float, in units of Angstroms. If an atom is
    more than this distance from its assigned axis, the rotation
    is considered to have failed.
  degrees: bool. If True, returns units of degrees, otherwise 
    radians. Defaults to False.
  omit_failed_rotations: bool. If True, when rotation fails, 
    returns only NoneType output. Defaults to False.
  suppress_warnings: bool. if True, will suppress warnings to 
    console. Defaults to False.

return:
  list: a list of the three angular anti-shear values, in units of
    degrees or radians depending on user-supplied arguments.

## `Octahedron.calculate_angular_shear_magnitude`

源文件：[van_vleck_calculator.py](van_vleck_calculator.py)，第 3145 行。

```python
Octahedron.calculate_angular_shear_magnitude(self, octahedral_centre='core_atom', specified_axes=[[1, 0, 0], [0, 1, 0], [0, 0, 1]], suppress_warnings=False, automatic_rotation=True, rotation_tolerance=GLOBAL_PARAM__FAILED_ROTATION_THRESHOLD, omit_failed_rotations=False)
```

This method calculates the Delta_shear parameter.

arguments:
  octahedral_centre (string or list): if "core_atom", the centre 
    of the octahedron is the position of the core atom. If 
    "average_ligand_position" then the octahedral centre
    is the average position of the ligands. If list, must be 
    a list of three floats which are the coordinates to be taken
    as the centre of the octahedron.
  specified_axes must be a list containing three lists, with each 
    sub-list containing three elements. These are three vectors 
    which will be set as the axes for the Van Vleck calculation.  
    They must be perpendicular to eachother.
    For example: [[1,0,0],[0,1,0],[0,0,1]] 
      or [[1,0,1],[1,0,-1],[0,1,0]]
  automatic_rotation: bool. Defaults to True. If True, the 
    automated rotation of the octahedron will occur. If False, it
    will not.
  rotation_tolerance: float, in units of Angstroms. If an atom is
    more than this distance from its assigned axis, the rotation
    is considered to have failed.
  omit_failed_rotations: bool. If True, when rotation fails, 
    returns only NoneType output. Defaults to False.
  suppress_warnings: bool. if True, will suppress warnings to 
    console. Defaults to False.

return:
  float: the square root of the sum of the angular shear 
    parameters for the three planes. In units of
    degrees or radians depending on user-supplied arguments.

## `Octahedron.calculate_angular_antishear_magnitude`

源文件：[van_vleck_calculator.py](van_vleck_calculator.py)，第 3228 行。

```python
Octahedron.calculate_angular_antishear_magnitude(self, octahedral_centre='core_atom', specified_axes=[[1, 0, 0], [0, 1, 0], [0, 0, 1]], suppress_warnings=False, automatic_rotation=True, rotation_tolerance=GLOBAL_PARAM__FAILED_ROTATION_THRESHOLD, omit_failed_rotations=False)
```

This method calculates the Delta_antishear parameter.

arguments:
  octahedral_centre (string or list): if "core_atom", the centre 
    of the octahedron is the position of the core atom. If 
    "average_ligand_position" then the octahedral centre
    is the average position of the ligands. If list, must be 
    a list of three floats which are the coordinates to be taken
    as the centre of the octahedron.
  specified_axes must be a list containing three lists, with each 
    sub-list containing three elements. These are three vectors 
    which will be set as the axes for the Van Vleck calculation.  
    They must be perpendicular to eachother.
    For example: [[1,0,0],[0,1,0],[0,0,1]] 
      or [[1,0,1],[1,0,-1],[0,1,0]]
  automatic_rotation: bool. Defaults to True. If True, the 
    automated rotation of the octahedron will occur. If False, it
    will not.
  rotation_tolerance: float, in units of Angstroms. If an atom is
    more than this distance from its assigned axis, the rotation
    is considered to have failed.
  omit_failed_rotations: bool. If True, when rotation fails, 
    returns only NoneType output. Defaults to False.
  suppress_warnings: bool. if True, will suppress warnings to 
    console. Defaults to False.

return:
  float: the square root of the sum of the angular antishear 
    parameters for the three planes. In units of
    degrees or radians depending on user-supplied arguments.

## `Octahedron.calculate_shear_fraction_angular_distortion`

源文件：[van_vleck_calculator.py](van_vleck_calculator.py)，第 3311 行。

```python
Octahedron.calculate_shear_fraction_angular_distortion(self, octahedral_centre='core_atom', specified_axes=[[1, 0, 0], [0, 1, 0], [0, 0, 1]], suppress_warnings=False, automatic_rotation=True, rotation_tolerance=GLOBAL_PARAM__FAILED_ROTATION_THRESHOLD, omit_failed_rotations=False)
```

This method calculates a parameter which represents the fraction 
  of angular distortion which stems from octahedral shear

arguments:
  octahedral_centre (string or list): if "core_atom", the centre 
    of the octahedron is the position of the core atom. If 
    "average_ligand_position" then the octahedral centre
    is the average position of the ligands. If list, must be 
    a list of three floats which are the coordinates to be taken
    as the centre of the octahedron.
  specified_axes must be a list containing three lists, with each 
    sub-list containing three elements. These are three vectors 
    which will be set as the axes for the Van Vleck calculation.  
    They must be perpendicular to eachother.
    For example: [[1,0,0],[0,1,0],[0,0,1]] 
      or [[1,0,1],[1,0,-1],[0,1,0]]
  automatic_rotation: bool. Defaults to True. If True, the 
    automated rotation of the octahedron will occur. If False, it
    will not.
  rotation_tolerance: float, in units of Angstroms. If an atom is
    more than this distance from its assigned axis, the rotation
    is considered to have failed.
  omit_failed_rotations: bool. If True, when rotation fails, 
    returns only NoneType output. Defaults to False.
  suppress_warnings: bool. if True, will suppress warnings to 
    console. Defaults to False.

return:
  float: the shear fraction, eta

## `WyckoffSiteGroup`

源文件：[wyckoff.py](wyckoff.py)，第 9 行。

```python
WyckoffSiteGroup
```

One group of symmetry-equivalent sites.

## `get_wyckoff_sites`

源文件：[wyckoff.py](wyckoff.py)，第 18 行。

```python
get_wyckoff_sites(structure: Structure, symprec: float=0.01, angle_tolerance: float=5.0)
```

Return the element, Wyckoff label, and sites for each equivalent group.

Args:
    structure: Structure to analyze.
    symprec: Cartesian distance tolerance used to determine symmetry, in angstrom.
    angle_tolerance: Angle tolerance used to determine symmetry, in degrees.

Returns:
    A list of dictionaries. Each dictionary describes one symmetry-equivalent
    group and contains ``element``, ``wyckoff``, ``indices``, and ``sites``.
    ``sites`` contains the corresponding sites from the input structure.

Raises:
    ValueError: If the structure is empty or a tolerance is not positive.

