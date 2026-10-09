# Magmom_Function 参数索引

源码静态索引；保留原有函数名。类构造和公开方法分别列出。默认值不代表适用于所有体系。

## `main`

源文件：[examples/check_na_fe_mn.py](examples/check_na_fe_mn.py)，第 5 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/read_moments.py](examples/read_moments.py)，第 5 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `check_magnetic_moments`

源文件：[io/Check_Magmom.py](io/Check_Magmom.py)，第 7 行。

```python
check_magnetic_moments(init_dir: p)
```

check_magnetic_moments 的 Docstring

:param init_dir: vasp_dir contains output
:type init_dir: p
:return: flag, round(total_magnetic_moment,1):Spin GS(1) or ES(0), if GS return total_magmom else return correct_magmom
:rtype: tuple

## `get_INCAR_NUPDOWN`

源文件：[io/Check_VaspOut.py](io/Check_VaspOut.py)，第 8 行。

```python
get_INCAR_NUPDOWN(init_dir)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `detect_converge`

源文件：[io/Check_VaspOut.py](io/Check_VaspOut.py)，第 12 行。

```python
detect_converge(init_dir)
```

Legacy log heuristic: (finished, ionic_accuracy_seen, serious_error).

Does not replace XML convergence validation or scheduler status.

## `update_incar`

源文件：[io/incar_compat.py](io/incar_compat.py)，第 6 行。

```python
update_incar(init_dir, tar_dir, spin, NUPDOWN, NSW=3)
```

Legacy side effects retained: copy CONTCAR and set NSW/NUPDOWN.

spin=0 copies CONTCAR to source POSCAR; spin=1 copies to target POSCAR.
Prefer Process_Vasp.update_incar for new code without these implicit copies.

## `InitDft_to_TarDft`

源文件：[utils/Init_To_Tar.py](utils/Init_To_Tar.py)，第 11 行。

```python
InitDft_to_TarDft(init_dir: p, tar_dir: p, Update: bool=True, NSW: int=3)
```

InitDft_to_TarDft 的 Docstring

:param init_dir: vasp_initdir 
:type init_dir: p
:param tar_dir: vasp_tardir
:type tar_dir: p
:param Update: update file(Ture,False)
:type Update: bool
:param NSW: if ES set INCAR NSW
:type NSW: int

