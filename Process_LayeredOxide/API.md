# Process_LayeredOxide 参数索引

源码静态索引；保留原有函数名。类构造和公开方法分别列出。默认值不代表适用于所有体系。

## `get_voltage`

源文件：[Diagram_get_voltage.py](Diagram_get_voltage.py)，第 5 行。

```python
get_voltage(df, Na_col='Na_content', e_col='full_e', μ_Na=-1.3, keep_cols=None)
```

Calculate voltage from convex hull lower envelope.

Parameters
----------
df : pd.DataFrame
    Input data containing Na content, energy, and optionally other columns.
Na_col : str
    Column name for Na content.
e_col : str
    Column name for formation energy.
μ_Na : float
    Chemical potential of Na (reference energy).
keep_cols : list of str or None
    Additional columns from df to include in the output. If None,
    only voltage-related columns are returned.

Returns
-------
pd.DataFrame
    Columns: plot_Na, plot_V, Na_start, Na_end, voltage, capacity_step
    (plus any columns specified in keep_cols).

## `main`

源文件：[examples/convert_phase.py](examples/convert_phase.py)，第 9 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/layer_features.py](examples/layer_features.py)，第 7 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/phase_diagram.py](examples/phase_diagram.py)，第 10 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/voltage.py](examples/voltage.py)，第 10 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `get_layer_spacing`

源文件：[Get_features.py](Get_features.py)，第 8 行。

```python
get_layer_spacing(structure: Structure, tol: float=0.5)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `get_bond_lengths`

源文件：[Get_features.py](Get_features.py)，第 41 行。

```python
get_bond_lengths(structure: Structure)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `row_factor`

源文件：[Get_features.py](Get_features.py)，第 143 行。

```python
row_factor(prim_struct, struct, species=('Fe', 'Mn'), sigma_map=None, layer_tol=0.05, demean=True, normalize='n2', return_complex=False)
```

Calculate layer-resolved row-order structure factors at the three M points
of the primitive triangular TM lattice.

This is useful for detecting row-like / stripe-like Fe-Mn ordering
in layered oxides.

Parameters
----------
prim_struct : pymatgen Structure
    Primitive reference structure. Its reciprocal lattice defines b1, b2.
    The first two reciprocal lattice vectors are assumed to span the TM layer.

struct : pymatgen Structure
    Supercell or relaxed structure containing Fe and Mn.

species : tuple[str, str]
    The two TM species to analyze. Default is ("Fe", "Mn").

sigma_map : dict or None
    Mapping from element symbol to occupation variable.
    Default: {"Fe": +1.0, "Mn": -1.0}.

layer_tol : float
    Tolerance for grouping TM atoms into layers, in fractional z of `struct`.

demean : bool
    If True, subtract layer mean from sigma before calculating structure
    factors. This removes composition background when Fe:Mn is not exactly 1:1
    within each layer.

normalize : {"n2", "n", "none"}
    Normalization of intensity |A|^2.
    - "n2": |A|^2 / n^2, bounded roughly by 0 to 1.
    - "n" : |A|^2 / n, useful as scattering-like normalization.
    - "none": raw |A|^2.

return_complex : bool
    If True, return complex amplitudes as real/imag pairs.

Returns
-------
dict
    {
        "M_cart": list of M-point Cartesian vectors,
        "layers": [
            {
                "z": layer center,
                "n": number of Fe/Mn atoms in layer,
                "counts": {"Fe": ..., "Mn": ...},
                "composition": {"Fe": ..., "Mn": ...},
                "mean_sigma": ...,
                "M1": intensity,
                "M2": intensity,
                "M3": intensity,
                "sum": M1 + M2 + M3,
                optionally "amp_M1": [real, imag], ...
            },
            ...
        ],
        "row_factor": average of layer sums,
        "row_factor_std": std of layer sums
    }

Notes
-----
The phase is calculated as exp(i M · r), where M is from the primitive
reciprocal lattice and r is the Cartesian coordinate in the supercell.

## `get_na_o_cn`

源文件：[Get_features.py](Get_features.py)，第 363 行。

```python
get_na_o_cn(struct, cutoff=3.0, return_index=False)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `get_oxi_states`

源文件：[Get_features.py](Get_features.py)，第 400 行。

```python
get_oxi_states(struct, init_oxi, redox_order)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `LayerOxide_O3_Transformer`

源文件：[LO_O3TransClass.py](LO_O3TransClass.py)，第 6 行。

```python
LayerOxide_O3_Transformer
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `LayerOxide_O3_Transformer.__init__`

源文件：[LO_O3TransClass.py](LO_O3TransClass.py)，第 29 行。

```python
LayerOxide_O3_Transformer.__init__(self, tm_elements=['Mn', 'Ni', 'Cu', 'Fe'], ion_elements=['Na'], o_element='O')
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `LayerOxide_O3_Transformer.o3_to_op2_6layer`

源文件：[LO_O3TransClass.py](LO_O3TransClass.py)，第 71 行。

```python
LayerOxide_O3_Transformer.o3_to_op2_6layer(self, s: Structure, SC_matrix=[1, 1, 1])
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `LayerOxide_O3_Transformer.o3_to_o1`

源文件：[LO_O3TransClass.py](LO_O3TransClass.py)，第 79 行。

```python
LayerOxide_O3_Transformer.o3_to_o1(self, s: Structure, SC_matrix=[1, 1, 1])
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `LayerOxide_O3_Transformer.o3_to_p3`

源文件：[LO_O3TransClass.py](LO_O3TransClass.py)，第 84 行。

```python
LayerOxide_O3_Transformer.o3_to_p3(self, s: Structure, SC_matrix=[1, 1, 1])
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `LayerOxide_O3_Transformer.op2_6layer_to_2layer`

源文件：[LO_O3TransClass.py](LO_O3TransClass.py)，第 89 行。

```python
LayerOxide_O3_Transformer.op2_6layer_to_2layer(self, structure: Structure, check_dict: dict=None)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `LayerOxide_O3_Transformer.group_by_z`

源文件：[LO_O3TransClass.py](LO_O3TransClass.py)，第 153 行。

```python
LayerOxide_O3_Transformer.group_by_z(self, structure: Structure, species_list: list, tolerance=0.1)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `LayerOxide_O3_Transformer.batch_transform_by_keys`

源文件：[LO_O3TransClass.py](LO_O3TransClass.py)，第 172 行。

```python
LayerOxide_O3_Transformer.batch_transform_by_keys(self, s: Structure, A_matrix, key_prefixes: list, get_type: list=['o1', 'p3', 'op2_6layer'])
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `LayerOxide_O3_Transformer.outstruct_from_batch`

源文件：[LO_O3TransClass.py](LO_O3TransClass.py)，第 210 行。

```python
LayerOxide_O3_Transformer.outstruct_from_batch(self, results: dict, tar: p)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `LayerOxide_O3_Transformer.get_TM_con`

源文件：[LO_O3TransClass.py](LO_O3TransClass.py)，第 251 行。

```python
LayerOxide_O3_Transformer.get_TM_con(struct, el)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `LayerOxidePhaseDiagram`

源文件：[Phase_diagramClass.py](Phase_diagramClass.py)，第 7 行。

```python
LayerOxidePhaseDiagram
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `LayerOxidePhaseDiagram.__init__`

源文件：[Phase_diagramClass.py](Phase_diagramClass.py)，第 9 行。

```python
LayerOxidePhaseDiagram.__init__(self, parse_composition=True, na_col='Na_content', com_col='Composition', energy_col='energy', formula_e_col='formula_e', formation_e_col='formation_e', need_phase=False, phase_col='phase', calc_ehull=False, start_na=0.0, end_na=1.0, atol=0.01)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `LayerOxidePhaseDiagram.composition_to_na`

源文件：[Phase_diagramClass.py](Phase_diagramClass.py)，第 38 行。

```python
LayerOxidePhaseDiagram.composition_to_na(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `LayerOxidePhaseDiagram.identify_phase`

源文件：[Phase_diagramClass.py](Phase_diagramClass.py)，第 45 行。

```python
LayerOxidePhaseDiagram.identify_phase(self, df)
```

识别相结构类型

## `LayerOxidePhaseDiagram.process`

源文件：[Phase_diagramClass.py](Phase_diagramClass.py)，第 56 行。

```python
LayerOxidePhaseDiagram.process(self, df)
```

主处理流程

## `group_by_z`

源文件：[Trans_function.py](Trans_function.py)，第 4 行。

```python
group_by_z(structure: Structure, species_list: list, tolerance=0.1)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

