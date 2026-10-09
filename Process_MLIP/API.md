# Process_MLIP 参数索引

源码静态索引；保留原有函数名。类构造和公开方法分别列出。默认值不代表适用于所有体系。

## `make_calculator`

源文件：[examples/ase_relax.py](examples/ase_relax.py)，第 13 行。

```python
make_calculator()
```

Replace with a calculator compatible with the material and environment.

## `main`

源文件：[examples/ase_relax.py](examples/ase_relax.py)，第 18 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/mace_relax.py](examples/mace_relax.py)，第 11 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `relax_structure_mace`

源文件：[mace_relax.py](mace_relax.py)，第 8 行。

```python
relax_structure_mace(structure, model_path, *, output_path=None, device='cuda', head=None, default_dtype='float64', fmax=0.05, steps=150, relax_cell=True)
```

Relax one structure and return final energy, forces, and optimizer facts.

``structure`` may be a path, ASE ``Atoms``, or pymatgen ``Structure``.
No trajectory or per-step files are written. If ``output_path`` is given,
only the final structure is written there.

## `MLIPRelaxer`

源文件：[MLIP_Relax.py](MLIP_Relax.py)，第 7 行。

```python
MLIPRelaxer
```

Relax ASE Atoms with an explicitly supplied calculator.

Modifies the supplied Atoms and retains its constraints. Energies are eV,
fmax is eV/Å. Cell relaxation also tests filter stress degrees of freedom.

## `MLIPRelaxer.__init__`

源文件：[MLIP_Relax.py](MLIP_Relax.py)，第 14 行。

```python
MLIPRelaxer.__init__(self, atoms, calculator, fmax=0.05, steps=200, optimizer='BFGS', relax_cell=False)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MLIPRelaxer.relax`

源文件：[MLIP_Relax.py](MLIP_Relax.py)，第 52 行。

```python
MLIPRelaxer.relax(self, traj_file='relax.traj', log_file='relax.log', final_structure=None)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MaceCompatibilityTests`

源文件：[test_mace_compatibility.py](test_mace_compatibility.py)，第 12 行。

```python
MaceCompatibilityTests
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MaceCompatibilityTests.test_old_and_new_entry_points`

源文件：[test_mace_compatibility.py](test_mace_compatibility.py)，第 13 行。

```python
MaceCompatibilityTests.test_old_and_new_entry_points(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `RelaxTests`

源文件：[test_relax.py](test_relax.py)，第 9 行。

```python
RelaxTests
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `RelaxTests.test_convergence_and_constraints`

源文件：[test_relax.py](test_relax.py)，第 10 行。

```python
RelaxTests.test_convergence_and_constraints(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `RelaxTests.test_invalid_input`

源文件：[test_relax.py](test_relax.py)，第 21 行。

```python
RelaxTests.test_invalid_input(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

