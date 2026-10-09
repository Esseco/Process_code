# octadist 参数索引

源码静态索引；保留原有函数名。类构造和公开方法分别列出。默认值不代表适用于所有体系。

## `OctaDist`

源文件：[main.py](main.py)，第 38 行。

```python
OctaDist
```

OctaDist class initiates main program UI and create all widgets.

Program interface is structured as follows:

+-------------------+
|   Program Menu    |
+-------------------+
|     Frame 1       |
+---------+---------+
| Frame 2 | Frame 3 |
+---------+---------+
|     Frame 4       |
+-------------------+

- Frame 1 : Program name and short description
- Frame 2 : Program console
- Frame 3 : Textbox for showing summary output
- Frame 4 : textbox for showing detailed output

Examples
--------
>>> my_app = OctaDist()
>>> my_app.start_app()

## `OctaDist.__init__`

源文件：[main.py](main.py)，第 66 行。

```python
OctaDist.__init__(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `OctaDist.create_logo`

源文件：[main.py](main.py)，第 117 行。

```python
OctaDist.create_logo(self)
```

Create icon file from Base64 raw code.

This will be used only for Windows OS.

Other OS like Linux and macOS use default logo of Tkinter.

Examples
--------
>>> if self.octadist_icon is True:
>>>     self.create_logo()
>>> else:
>>>     pass

## `OctaDist.start_master`

源文件：[main.py](main.py)，第 143 行。

```python
OctaDist.start_master(self)
```

Start application with UI settings.

## `OctaDist.add_menu`

源文件：[main.py](main.py)，第 156 行。

```python
OctaDist.add_menu(self)
```

Add menu bar to master windows.

## `OctaDist.add_widgets`

源文件：[main.py](main.py)，第 289 行。

```python
OctaDist.add_widgets(self)
```

Add all widgets and components to master windows.

GUI style of widgets in master windows use ttk style.

## `OctaDist.show_text`

源文件：[main.py](main.py)，第 422 行。

```python
OctaDist.show_text(self, text)
```

Insert text to result box

Parameters
----------
text : str
    Text to show in result box.

Returns
-------
None : None

## `OctaDist.welcome_msg`

源文件：[main.py](main.py)，第 439 行。

```python
OctaDist.welcome_msg(self)
```

Show welcome message in result box:

1. Program name, version, and release.
2. Full author names.
3. Official website: https://octadist.github.io.

## `OctaDist.open_file`

源文件：[main.py](main.py)，第 458 行。

```python
OctaDist.open_file(self)
```

Open file dialog where the user will browse input files.

## `OctaDist.search_coord`

源文件：[main.py](main.py)，第 485 行。

```python
OctaDist.search_coord(self)
```

Search and extract atomic symbols and coordinates from input file.

See Also
--------
octadist.src.io.extract_coord :
    Extract atomic symbols and atomic coordinates from input file.
octadist.src.io.extract_octa :
    Extract octahedral structure from complex.

## `OctaDist.show_coord`

源文件：[main.py](main.py)，第 563 行。

```python
OctaDist.show_coord(self)
```

Show coordinates in box.

## `OctaDist.save_results`

源文件：[main.py](main.py)，第 589 行。

```python
OctaDist.save_results(self)
```

Save results as output file. Default file extension is .txt.

## `OctaDist.save_coord`

源文件：[main.py](main.py)，第 620 行。

```python
OctaDist.save_coord(self)
```

Save atomic coordinates (Cartesian coordinate) of octahedral structure.
Default file extension is .xyz.

## `OctaDist.calc_distortion`

源文件：[main.py](main.py)，第 670 行。

```python
OctaDist.calc_distortion(self)
```

Calculate all distortion parameters:

- D_mean
- Zeta
- Delta
- Sigma
- Theta
- Volume

See Also
--------
octadist.src.calc.CalcDistortion.calc_d_mean :
    Calculate mean metal-ligand bond length.
octadist.src.calc.CalcDistortion.calc_zeta :
    Calculate Zeta parameter.
octadist.src.calc.CalcDistortion.calc_delta :
    Calculate Delta parameter.
octadist.src.calc.CalcDistortion.calc_sigma :
    Calculate Sigma parameter.
octadist.src.calc.CalcDistortion.calc_theta :
    Calculate Theta parameter.
octadist.src.calc.CalcDistortion.calc_vol :
    Calculate octahedron volume.

## `OctaDist.settings`

源文件：[main.py](main.py)，第 774 行。

```python
OctaDist.settings(self)
```

Program settings allows the user to configure the values of variables
that used in molecular display function.

For example, cutoff distance for screening bond distance between atoms.

## `OctaDist.copy_name`

源文件：[main.py](main.py)，第 1056 行。

```python
OctaDist.copy_name(self)
```

Copy input file name to clipboard.

See Also
--------
copy_path :
    Copy absolute path of input file to clibboard.
copy_results :
    Copy results to clibboard.
copy_octa :
    Copy octahedral structure coordinates to clibboard.

## `OctaDist.copy_path`

源文件：[main.py](main.py)，第 1082 行。

```python
OctaDist.copy_path(self)
```

Copy absolute path of input file to clipboard.

See Also
--------
copy_name
    Copy input file name to clibboard.
copy_results :
    Copy results to clibboard.
copy_octa :
    Copy octahedral structure coordinates to clibboard.

## `OctaDist.copy_results`

源文件：[main.py](main.py)，第 1106 行。

```python
OctaDist.copy_results(self)
```

Copy the results and computed distortion parameters to clipboard.

See Also
--------
copy_name
    Copy input file name to clibboard.
copy_path :
    Copy absolute path of input file to clibboard.
copy_octa :
    Copy octahedral structure coordinates to clibboard.

## `OctaDist.copy_octa`

源文件：[main.py](main.py)，第 1145 行。

```python
OctaDist.copy_octa(self)
```

Copy atomic coordinates of octahedral structure to clipboard.

See Also
--------
copy_name
    Copy input file name to clibboard.
copy_path :
    Copy absolute path of input file to clibboard.
copy_results :
    Copy results to clibboard.

## `OctaDist.edit_file`

源文件：[main.py](main.py)，第 1169 行。

```python
OctaDist.edit_file(self)
```

Edit file by specified text editor on Windows.

See Also
--------
settings

## `OctaDist.scripting_console`

源文件：[main.py](main.py)，第 1199 行。

```python
OctaDist.scripting_console(self)
```

Start scripting interface for an interactive code.

User can access to class variable (dynamic variable).

+------------+
| Output box |
+------------+
| Input box  |
+------------+

See Also
--------
settings :
    Program settings.

## `OctaDist.draw_all_atom`

源文件：[main.py](main.py)，第 1224 行。

```python
OctaDist.draw_all_atom(self)
```

Display 3D complex.

See Also
--------
octadist.src.draw.DrawComplex :
    Show 3D molecule.

## `OctaDist.draw_all_atom_and_face`

源文件：[main.py](main.py)，第 1273 行。

```python
OctaDist.draw_all_atom_and_face(self)
```

Display 3D complex with the faces.

See Also
--------
octadist.src.draw.DrawComplex :
    Show 3D molecule.

## `OctaDist.draw_octa`

源文件：[main.py](main.py)，第 1313 行。

```python
OctaDist.draw_octa(self)
```

Display 3D octahedral structure.

See Also
--------
octadist.src.draw.DrawComplex :
    Show 3D molecule.

## `OctaDist.draw_octa_and_face`

源文件：[main.py](main.py)，第 1348 行。

```python
OctaDist.draw_octa_and_face(self)
```

Display 3D octahedral structure with the faces.

See Also
--------
octadist.src.draw.DrawComplex :
    Show 3D molecule.

## `OctaDist.draw_projection`

源文件：[main.py](main.py)，第 1388 行。

```python
OctaDist.draw_projection(self)
```

Draw projection planes.

See Also
--------
octadist.src.draw.DrawProjection :
    Show graphical projections.

## `OctaDist.draw_twisting_plane`

源文件：[main.py](main.py)，第 1413 行。

```python
OctaDist.draw_twisting_plane(self)
```

Draw twisting triangular planes.

See Also
--------
octadist.src.draw.DrawTwistingPlane :
    Show graphical triangular twisting planes.

## `OctaDist.show_data_complex`

源文件：[main.py](main.py)，第 1442 行。

```python
OctaDist.show_data_complex(self)
```

Show info of input complex.

See Also
--------
octadist.src.structure.DataComplex :
    Show data summary of complex.

## `OctaDist.show_param_octa`

源文件：[main.py](main.py)，第 1464 行。

```python
OctaDist.show_param_octa(self)
```

Show structural parameters of selected octahedral structure.

See Also
--------
octadist.src.structure.StructParam :
    Show structural parameter symmary of complex.

## `OctaDist.show_surface_area`

源文件：[main.py](main.py)，第 1486 行。

```python
OctaDist.show_surface_area(self)
```

Calculate the area of eight triangular faces of octahedral structure.

See Also
--------
octadist.src.structure.SurfaceArea :
    Show the area of the faces of octahedral structure.

## `OctaDist.plot_zeta_sigma`

源文件：[main.py](main.py)，第 1512 行。

```python
OctaDist.plot_zeta_sigma(self)
```

Plot relationship between zeta and sigma.

See Also
--------
octadist.src.plot.Plot :
    Show relationship plot.

## `OctaDist.plot_sigma_theta`

源文件：[main.py](main.py)，第 1532 行。

```python
OctaDist.plot_sigma_theta(self)
```

Plot relationship between sigma and theta.

See Also
--------
octadist.src.plot.Plot :
    Show relationship plot.

## `OctaDist.tool_jahn_teller`

源文件：[main.py](main.py)，第 1558 行。

```python
OctaDist.tool_jahn_teller(self)
```

Calculate Jahn-Teller distortion parameter.

See Also
--------
octadist.src.tools.CalcJahnTeller :
    Calculate Jahn-Teller distortion parameter.

## `OctaDist.tool_rmsd`

源文件：[main.py](main.py)，第 1589 行。

```python
OctaDist.tool_rmsd(self)
```

Calculate root mean squared displacement of atoms in complex, RMSD.

See Also
--------
octadist.src.tools.CalcRMSD :
    Calculate RMSD.

## `OctaDist.check_update`

源文件：[main.py](main.py)，第 1636 行。

```python
OctaDist.check_update()
```

Check program update by comparing version of program user is using with
that of the latest version released on github.

References
----------
File: https://www.github.com/OctaDist/OctaDist/version_update.txt.

## `OctaDist.callback`

源文件：[main.py](main.py)，第 1694 行。

```python
OctaDist.callback(event)
```

On-clink open web browser.

Parameters
----------
event : object
    Event object for callback.

## `OctaDist.show_about`

源文件：[main.py](main.py)，第 1707 行。

```python
OctaDist.show_about()
```

Show author details on a sub-window.

1. Name of authors
2. Official program website
3. Citation

## `OctaDist.show_license`

源文件：[main.py](main.py)，第 1729 行。

```python
OctaDist.show_license()
```

Show license details on a sub-window.

GNU General Public License version 3.0.

References
----------
Link: https://www.gnu.org/licenses/gpl-3.0.en.html.

## `OctaDist.clear_cache`

源文件：[main.py](main.py)，第 1763 行。

```python
OctaDist.clear_cache(self)
```

Clear program cache by nullifying all default variables
and clear both of parameter and result boxes.

## `OctaDist.clear_param_box`

源文件：[main.py](main.py)，第 1788 行。

```python
OctaDist.clear_param_box(self)
```

Clear parameter box.

## `OctaDist.clear_result_box`

源文件：[main.py](main.py)，第 1800 行。

```python
OctaDist.clear_result_box(self)
```

Clear result box.

## `OctaDist.start_app`

源文件：[main.py](main.py)，第 1808 行。

```python
OctaDist.start_app(self)
```

Start application.

## `main`

源文件：[main.py](main.py)，第 1816 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `check_file`

源文件：[octadist_cli.py](octadist_cli.py)，第 26 行。

```python
check_file(file)
```

Check if input file is exist or not.

Parameters
----------
file : str
    Input file name.

Returns
-------
file : str
    Input file name.

## `find_coord`

源文件：[octadist_cli.py](octadist_cli.py)，第 50 行。

```python
find_coord(file)
```

Find atomic symbols and atomic coordinates of structure.

Parameters
----------
file : str
    Input file name.

Returns
-------
atom : list
    Atomic symbols.
coord : list
    Atomic coordinates.

## `calc_param`

源文件：[octadist_cli.py](octadist_cli.py)，第 82 行。

```python
calc_param(coord)
```

Calculate octahedral distortion parameters.

Parameters
----------
coord : array_like
    Atomic coordinates of octahedral structure.

Returns
-------
computed : dict
    Computed parameters: zeta, delta, sigma, theta.

## `run_cli`

源文件：[octadist_cli.py](octadist_cli.py)，第 108 行。

```python
run_cli()
```

OctaDist command-line interface (CLI).
This function has been implemented by entry points function
in setuptools package.

## `run_gui`

源文件：[octadist_gui.py](octadist_gui.py)，第 27 行。

```python
run_gui()
```

OctaDist graphical user interface (GUI).

## `CalcDistortion`

源文件：[src/calc.py](src/calc.py)，第 24 行。

```python
CalcDistortion
```

Calculate octahedral histortion parameters:

- Bond distance : :meth:`calc_d_bond`
- Mean bond distance : :meth:`calc_d_mean`
- Bond angle around metal center atom : :meth:`calc_bond_angle`
- zeta parameter : :meth:`calc_zeta`
- Delta parameter : :meth:`calc_delta`
- Sigma parameter : :meth:`calc_sigma`
- Minimum Tehta parameter : :meth:`calc_theta_min`
- Maximum Theta parameter : :meth:`calc_theta_max`
- Mean Theta parametes : :meth:`calc_theta`
- Volume : :meth:`calc_vol`

Parameters
----------
coord : array_like
    Atomic coordinates of octahedral structure.

Examples
--------
>>> coord = [[2.298354000, 5.161785000, 7.971898000],  # <- Metal atom
             [1.885657000, 4.804777000, 6.183726000],
             [1.747515000, 6.960963000, 7.932784000],
             [4.094380000, 5.807257000, 7.588689000],
             [0.539005000, 4.482809000, 8.460004000],
             [2.812425000, 3.266553000, 8.131637000],
             [2.886404000, 5.392925000, 9.848966000]]
>>> test = CalcDistortion(coord)
>>> test.sigma
47.926528379270124

## `CalcDistortion.__init__`

源文件：[src/calc.py](src/calc.py)，第 59 行。

```python
CalcDistortion.__init__(self, coord)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `CalcDistortion.calc_d_bond`

源文件：[src/calc.py](src/calc.py)，第 94 行。

```python
CalcDistortion.calc_d_bond(self)
```

Calculate metal-ligand bond distance and return value in Angstrom.

See Also
--------
calc_d_mean :
    Calculate mean metal-ligand bond length.

## `CalcDistortion.calc_d_mean`

源文件：[src/calc.py](src/calc.py)，第 109 行。

```python
CalcDistortion.calc_d_mean(self)
```

Calculate mean distance parameter and return value in Angstrom.

See Also
--------
calc_d_bond :
    Calculate metal-ligand bonds length.

## `CalcDistortion.calc_bond_angle`

源文件：[src/calc.py](src/calc.py)，第 121 行。

```python
CalcDistortion.calc_bond_angle(self)
```

Calculate 12 cis and 3 trans unique angles in octahedral structure.

See Also
--------
calc_sigma :
    Calculate Sigma parameter.

## `CalcDistortion.calc_zeta`

源文件：[src/calc.py](src/calc.py)，第 144 行。

```python
CalcDistortion.calc_zeta(self)
```

Calculate zeta parameter [1]_ and return value in Angstrom.

See Also
--------
calc_d_bond :
    Calculate metal-ligand bonds length.
calc_d_mean :
    Calculate mean metal-ligand bond length.

References
----------
.. [1] M. Buron-Le Cointe, J. Hébert, C. Baldé, N. Moisan,
    L. Toupet, P. Guionneau, J. F. Létard, E. Freysz,
    H. Cailleau, and E. Collet. - Intermolecular control of
    thermoswitching and photoswitching phenomena in two
    spin-crossover polymorphs. Phys. Rev. B 85, 064114.

## `CalcDistortion.calc_delta`

源文件：[src/calc.py](src/calc.py)，第 169 行。

```python
CalcDistortion.calc_delta(self)
```

Calculate Delta parameter, also known as Tilting distortion parameter [2]_.

See Also
--------
calc_d_bond :
    Calculate metal-ligand bonds length.
calc_d_mean :
    Calculate mean metal-ligand bond length.

References
----------
.. [2] M. W. Lufaso and P. M. Woodward. - Jahn–Teller distortions,
    cation ordering and octahedral tilting in perovskites.
    Acta Cryst. (2004). B60, 10-20. DOI: 10.1107/S0108768103026661

## `CalcDistortion.calc_sigma`

源文件：[src/calc.py](src/calc.py)，第 192 行。

```python
CalcDistortion.calc_sigma(self)
```

Calculate Sigma parameter [3]_ and return value in degree.

See Also
--------
calc_bond_angle :
    Calculate bond angles between ligand-metal-ligand.

References
----------
.. [3] James K. McCusker, A. L. Rheingold, D. N. Hendrickson.
    Variable-Temperature Studies of Laser-Initiated 5T2 → 1A1
    Intersystem Crossing in Spin-Crossover Complexes:
    Empirical Correlations between Activation Parameters
    and Ligand Structure in a Series of Polypyridyl.
    Ferrous Complexes. Inorg. Chem. 1996, 35, 2100.

## `CalcDistortion.determine_faces`

源文件：[src/calc.py](src/calc.py)，第 213 行。

```python
CalcDistortion.determine_faces(self)
```

Refine the order of ligand atoms in order to find the plane for projection.

Returns
-------
coord_metal : array_like
    Coordinate of metal atom.
coord_lig : array_like
    Coordinate of ligand atoms.

See Also
--------
calc_theta :
    Calculate mean Theta parameter

Examples
--------
>>> bef = np.array([
            [4.0674, 7.2040, 13.6117]
            [4.3033, 7.3750, 11.7292]
            [3.8326, 6.9715, 15.4926]
            [5.8822, 6.4461, 13.4312]
            [3.3002, 5.3828, 13.6316]
            [4.8055, 8.9318, 14.2716]
            [2.3184, 8.0165, 13.1152]
            ])
>>> metal, coord = self.determine_faces(bef)
>>> metal
[ 4.0674  7.204  13.6117]
>>> coord_lig
[[ 4.3033  7.375  11.7292]      # Front face
 [ 4.8055  8.9318 14.2716]      # Front face
 [ 5.8822  6.4461 13.4312]      # Front face
 [ 2.3184  8.0165 13.1152]      # Back face
 [ 3.8326  6.9715 15.4926]      # Back face
 [ 3.3002  5.3828 13.6316]]     # Back face

## `CalcDistortion.calc_theta`

源文件：[src/calc.py](src/calc.py)，第 339 行。

```python
CalcDistortion.calc_theta(self)
```

Calculate Theta parameter [4]_ and value in degree.

See Also
--------
calc_theta_min :
    Calculate minimum Theta parameter.
calc_theta_max :
    Calculate maximum Theta parameter.
octadist.src.linear.angle_btw_vectors :
    Calculate cosine angle between two vectors.
octadist.src.linear.angle_sign :
    Calculate cosine angle between two vectors sensitive to CW/CCW direction.
octadist.src.plane.find_eq_of_plane :
    Find the equation of the plane.
octadist.src.projection.project_atom_onto_plane :
    Orthogonal projection of point onto the plane.

References
----------
.. [4] M. Marchivie, P. Guionneau, J.-F. Létard, D. Chasseau.
    Photo‐induced spin‐transition: the role of the iron(II)
    environment distortion. Acta Crystal-logr. Sect. B Struct.
    Sci. 2005, 61, 25.

## `CalcDistortion.calc_theta_min`

源文件：[src/calc.py](src/calc.py)，第 443 行。

```python
CalcDistortion.calc_theta_min(self)
```

Calculate minimum Theta parameter and return value in degree.

See Also
--------
calc_theta :
    Calculate mean Theta parameter

## `CalcDistortion.calc_theta_max`

源文件：[src/calc.py](src/calc.py)，第 456 行。

```python
CalcDistortion.calc_theta_max(self)
```

Calculate maximum Theta parameter and return value in degree.

See Also
--------
calc_theta :
    Calculate mean Theta parameter

## `CalcDistortion.calc_vol`

源文件：[src/calc.py](src/calc.py)，第 469 行。

```python
CalcDistortion.calc_vol(self)
```

Calculate the octahedron volume and return value in cubic Angstrom.

## `DrawComplex_Matplotlib`

源文件：[src/draw.py](src/draw.py)，第 26 行。

```python
DrawComplex_Matplotlib
```

Display 3D structure of octahedral complex with label for each atoms using Matplotlib.

Parameters
----------
atom : list
    Atomic symbols of octahedral structure.
    Default is None.
coord : list or array_like or tuple or bool
    Atomic coordinates of octahedral structure.
    Default is None.
cutoff_global : int or float
    Global cutoff for screening bonds.
    Default is 2.0.
cutoff_hydrogen : int or float
    Cutoff for screening hydrogen bonds.
    Default is 1.2.

See Also
--------
draw.DrawComplex_Plotly :
    Use Plotly engine to draw a complex.

Examples
--------
>>> atom = ['Fe', 'N', 'N', 'N', 'O', 'O', 'O']
>>> coord = [[2.298354000, 5.161785000, 7.971898000],
             [1.885657000, 4.804777000, 6.183726000],
             [1.747515000, 6.960963000, 7.932784000],
             [4.094380000, 5.807257000, 7.588689000],
             [0.539005000, 4.482809000, 8.460004000],
             [2.812425000, 3.266553000, 8.131637000],
             [2.886404000, 5.392925000, 9.848966000]]
>>> test = DrawComplex_Matplotlib(atom=atom, coord=coord)
>>> test.add_atom()
>>> test.add_bond()
>>> test.add_legend()
>>> test.show_plot()

## `DrawComplex_Matplotlib.__init__`

源文件：[src/draw.py](src/draw.py)，第 68 行。

```python
DrawComplex_Matplotlib.__init__(self, atom=None, coord=None, cutoff_global=2.0, cutoff_hydrogen=1.2)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `DrawComplex_Matplotlib.start_plot`

源文件：[src/draw.py](src/draw.py)，第 92 行。

```python
DrawComplex_Matplotlib.start_plot(self)
```

Introduce figure to plot.

## `DrawComplex_Matplotlib.plot_title`

源文件：[src/draw.py](src/draw.py)，第 102 行。

```python
DrawComplex_Matplotlib.plot_title(self, title='Full complex', font_size='12')
```

Add plot title at top position.

Parameters
----------
title : str
    Top title of the plot.
    Default is "Full complex".
fontsize : int or float or str
    Font size of title.
    Default is "12".

## `DrawComplex_Matplotlib.add_atom`

源文件：[src/draw.py](src/draw.py)，第 118 行。

```python
DrawComplex_Matplotlib.add_atom(self)
```

Add all atoms to show in figure.

## `DrawComplex_Matplotlib.add_symbol`

源文件：[src/draw.py](src/draw.py)，第 138 行。

```python
DrawComplex_Matplotlib.add_symbol(self)
```

Add symbol of atoms to show in figure.

## `DrawComplex_Matplotlib.add_bond`

源文件：[src/draw.py](src/draw.py)，第 152 行。

```python
DrawComplex_Matplotlib.add_bond(self)
```

Calculate bond distance, screen bond, and add them to show in figure.

See Also
--------
octadist.src.util.find_bonds :
    Find atomic bonds.

## `DrawComplex_Matplotlib.add_face`

源文件：[src/draw.py](src/draw.py)，第 177 行。

```python
DrawComplex_Matplotlib.add_face(self, coord)
```

Find the faces of octahedral structure and add those faces to show in figure.

See Also
--------
octadist.src.util.find_faces_octa :
    Find all faces of octahedron.

## `DrawComplex_Matplotlib.add_legend`

源文件：[src/draw.py](src/draw.py)，第 210 行。

```python
DrawComplex_Matplotlib.add_legend(self)
```

Add atoms legend to show in figure.

References
----------
1. Remove duplicate labels in legend.
    Ref: https://stackoverflow.com/a/26550501/6596684.

2. Fix size of point in legend.
    Ref: https://stackoverflow.com/a/24707567/6596684.

## `DrawComplex_Matplotlib.config_plot`

源文件：[src/draw.py](src/draw.py)，第 239 行。

```python
DrawComplex_Matplotlib.config_plot(self, show_title=True, show_axis=True, show_grid=True, **kwargs)
```

Setting configuration for figure.

Parameters
----------
show_title : bool
    If True, show title of figure.
    If False, not show title of figure.
show_axis : bool
    If True, show axis of figure.
    If False, not show axis of figure.
show_grid : bool
    If True, show grid of figure.
    If False, not show grid of figure.
kwargs : dict, optional
    title_name : title name of figure.
    title_size : text size of title.
    label_size : text size of axis labels.

## `DrawComplex_Matplotlib.save_img`

源文件：[src/draw.py](src/draw.py)，第 288 行。

```python
DrawComplex_Matplotlib.save_img(save='Complex_saved_by_OctaDist', file='png')
```

Save figure as an image.

Parameters
----------
save : str
    Name of image file.
    Default is "Complex_saved_by_OctaDist".
file : str
    Image type.
    Default is "png".

## `DrawComplex_Matplotlib.show_plot`

源文件：[src/draw.py](src/draw.py)，第 305 行。

```python
DrawComplex_Matplotlib.show_plot()
```

Show plot.

## `DrawComplex_Plotly`

源文件：[src/draw.py](src/draw.py)，第 313 行。

```python
DrawComplex_Plotly
```

Display 3D structure of octahedral complex in web browser using Plotly.

Parameters
----------
atom : list
    Atomic symbols of octahedral structure.
    Default is None.
coord : list or array_like or tuple or bool
    Atomic coordinates of octahedral structure.
    Default is None.
cutoff_global : int or float
    Global cutoff for screening bonds.
    Default is 2.0.
cutoff_hydrogen : int or float
    Cutoff for screening hydrogen bonds.
    Default is 1.2.

See Also
--------
draw.DrawComplex_Matplotlib :
    Use Matplotlib engine to draw a complex.

Examples
--------
>>> atom = ['Fe', 'N', 'N', 'N', 'O', 'O', 'O']
>>> coord = [[2.298354000, 5.161785000, 7.971898000],
             [1.885657000, 4.804777000, 6.183726000],
             [1.747515000, 6.960963000, 7.932784000],
             [4.094380000, 5.807257000, 7.588689000],
             [0.539005000, 4.482809000, 8.460004000],
             [2.812425000, 3.266553000, 8.131637000],
             [2.886404000, 5.392925000, 9.848966000]]
>>> test = DrawComplex_Plotly(atom=atom, coord=coord)
>>> test.add_atom()
>>> test.add_bond()
>>> test.show_plot()

## `DrawComplex_Plotly.__init__`

源文件：[src/draw.py](src/draw.py)，第 354 行。

```python
DrawComplex_Plotly.__init__(self, atom=None, coord=None, cutoff_global=2.0, cutoff_hydrogen=1.2)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `DrawComplex_Plotly.start_plot`

源文件：[src/draw.py](src/draw.py)，第 381 行。

```python
DrawComplex_Plotly.start_plot(self)
```

Introduce figure to plot.

## `DrawComplex_Plotly.plot_title`

源文件：[src/draw.py](src/draw.py)，第 391 行。

```python
DrawComplex_Plotly.plot_title(self, title='Full complex', font_size='12')
```

Add plot title at top position.

Parameters
----------
title : str
    Top title of the plot.
    Default is "Full complex".
fontsize : int or float or str
    Font size of title.
    Default is "12".

## `DrawComplex_Plotly.add_atom`

源文件：[src/draw.py](src/draw.py)，第 407 行。

```python
DrawComplex_Plotly.add_atom(self)
```

Add all atoms to show in figure.

## `DrawComplex_Plotly.add_bond`

源文件：[src/draw.py](src/draw.py)，第 461 行。

```python
DrawComplex_Plotly.add_bond(self)
```

Calculate bond distance, screen bond, and add them to show in figure.

See Also
--------
octadist.src.util.find_bonds :
    Find atomic bonds.

## `DrawComplex_Plotly.save_img`

源文件：[src/draw.py](src/draw.py)，第 527 行。

```python
DrawComplex_Plotly.save_img(self, save='Complex_saved_by_OctaDist', file='png')
```

Save figure as an image. Note that psutil and plotly-orca are needed for saving Plotly plot as image.

Parameters
----------
save : str
    Name of image file.
    Default is "Complex_saved_by_OctaDist".
file : str
    Image type.
    Default is "png".

## `DrawComplex_Plotly.show_plot`

源文件：[src/draw.py](src/draw.py)，第 543 行。

```python
DrawComplex_Plotly.show_plot(self)
```

Show plot.

## `DrawProjection`

源文件：[src/draw.py](src/draw.py)，第 551 行。

```python
DrawProjection
```

Display the selected 4 faces of octahedral complex.

Parameters
----------
atom : list
    Atomic symbols of octahedral structure.
    Default is None.
coord : list or array_like or tuple
    Atomic coordinates of octahedral structure.
    Default is None.

Examples
--------
>>> atom = ['Fe', 'N', 'N', 'N', 'O', 'O', 'O']
>>> coord = [[2.298354000, 5.161785000, 7.971898000],
             [1.885657000, 4.804777000, 6.183726000],
             [1.747515000, 6.960963000, 7.932784000],
             [4.094380000, 5.807257000, 7.588689000],
             [0.539005000, 4.482809000, 8.460004000],
             [2.812425000, 3.266553000, 8.131637000],
             [2.886404000, 5.392925000, 9.848966000]]
>>> test = DrawProjection(atom=atom, coord=coord)
>>> test.add_atom()
>>> test.add_symbol()
>>> test.add_plane()
>>> test.show_plot()

## `DrawProjection.__init__`

源文件：[src/draw.py](src/draw.py)，第 582 行。

```python
DrawProjection.__init__(self, atom=None, coord=None)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `DrawProjection.start_plot`

源文件：[src/draw.py](src/draw.py)，第 597 行。

```python
DrawProjection.start_plot(self)
```

Introduce figure to plot.

## `DrawProjection.plot_title`

源文件：[src/draw.py](src/draw.py)，第 609 行。

```python
DrawProjection.plot_title(self, title='4 pairs of opposite planes', font_size='x-large')
```

Add plot title at top position.

Parameters
----------
title : str
    Top title of the plot.
    Default is "Full complex".
fontsize : int or float or str
    Font size of title.
    Default is "x-large".

## `DrawProjection.shift_plot`

源文件：[src/draw.py](src/draw.py)，第 626 行。

```python
DrawProjection.shift_plot(self)
```

Shift subplots down.
Default is 0.25.

## `DrawProjection.add_atom`

源文件：[src/draw.py](src/draw.py)，第 635 行。

```python
DrawProjection.add_atom(self)
```

Add all atoms to show in figure.

## `DrawProjection.add_symbol`

源文件：[src/draw.py](src/draw.py)，第 669 行。

```python
DrawProjection.add_symbol(self)
```

Add all atoms to show in figure.

## `DrawProjection.add_plane`

源文件：[src/draw.py](src/draw.py)，第 695 行。

```python
DrawProjection.add_plane(self)
```

Add the projection planes to show in figure.

See Also
--------
octadist.src.util.find_faces_octa :
    Find all faces of octahedron.

## `DrawProjection.save_img`

源文件：[src/draw.py](src/draw.py)，第 730 行。

```python
DrawProjection.save_img(save='Complex_saved_by_OctaDist', file='png')
```

Save figure as an image.

Parameters
----------
save : str
    Name of image file.
    Default is "Complex_saved_by_OctaDist".
file : file
    Image type.
    Default is "png".

## `DrawProjection.show_plot`

源文件：[src/draw.py](src/draw.py)，第 747 行。

```python
DrawProjection.show_plot()
```

Show plot.

## `DrawTwistingPlane`

源文件：[src/draw.py](src/draw.py)，第 756 行。

```python
DrawTwistingPlane
```

Display twisting triangular faces and vector projection.

Parameters
----------
atom : list
    Atomic symbols of octahedral structure.
    Default is None.
coord : list or array or tuple
    Atomic coordinates of octahedral structure.
    Default is None.

Examples
--------
>>> atom = ['Fe', 'N', 'N', 'N', 'O', 'O', 'O']
>>> coord = [[2.298354000, 5.161785000, 7.971898000],
             [1.885657000, 4.804777000, 6.183726000],
             [1.747515000, 6.960963000, 7.932784000],
             [4.094380000, 5.807257000, 7.588689000],
             [0.539005000, 4.482809000, 8.460004000],
             [2.812425000, 3.266553000, 8.131637000],
             [2.886404000, 5.392925000, 9.848966000]]
>>> test = DrawTwistingPlane(atom=atom, coord=coord)
>>> test.add_plane()
>>> test.add_symbol()
>>> test.add_bond()
>>> test.show_plot()

## `DrawTwistingPlane.__init__`

源文件：[src/draw.py](src/draw.py)，第 787 行。

```python
DrawTwistingPlane.__init__(self, atom=None, coord=None, symbol_fontsize=15)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `DrawTwistingPlane.start_plot`

源文件：[src/draw.py](src/draw.py)，第 808 行。

```python
DrawTwistingPlane.start_plot(self)
```

Introduce figure to plot.

## `DrawTwistingPlane.plot_title`

源文件：[src/draw.py](src/draw.py)，第 815 行。

```python
DrawTwistingPlane.plot_title(self, title='Projected twisting triangular faces', font_size='x-large')
```

Add plot title at top position.

Parameters
----------
title : str
    Top title of the plot.
    Default is "Projected twisting triangular faces".
fontsize : int or float or str
    Font size of title.
    Default is "x-large".

## `DrawTwistingPlane.shift_plot`

源文件：[src/draw.py](src/draw.py)，第 833 行。

```python
DrawTwistingPlane.shift_plot(self)
```

Shift subplots down.
Default is 0.25.

## `DrawTwistingPlane.create_subplots`

源文件：[src/draw.py](src/draw.py)，第 842 行。

```python
DrawTwistingPlane.create_subplots(self)
```

Create subplots.

## `DrawTwistingPlane.add_plane`

源文件：[src/draw.py](src/draw.py)，第 853 行。

```python
DrawTwistingPlane.add_plane(self)
```

Add the projection planes to show in figure.

See Also
--------
octadist.src.plane.find_eq_of_plane :
    Find the equation of the plane.
octadist.src.projection.project_atom_onto_plane :
    Orthogonal projection of point onto the plane.

## `DrawTwistingPlane.add_symbol`

源文件：[src/draw.py](src/draw.py)，第 940 行。

```python
DrawTwistingPlane.add_symbol(self)
```

Add all atoms to show in figure.

## `DrawTwistingPlane.add_bond`

源文件：[src/draw.py](src/draw.py)，第 972 行。

```python
DrawTwistingPlane.add_bond(self)
```

Calculate bond distance, screen bond, and add them to show in figure.

## `DrawTwistingPlane.save_img`

源文件：[src/draw.py](src/draw.py)，第 990 行。

```python
DrawTwistingPlane.save_img(save='Complex_saved_by_OctaDist', file='png')
```

Save figure as an image.

Parameters
----------
save : str
    Name of image file.
    Default is "Complex_saved_by_OctaDist".
file : str
    Image type.
    Default is "png".

## `DrawTwistingPlane.show_plot`

源文件：[src/draw.py](src/draw.py)，第 1007 行。

```python
DrawTwistingPlane.show_plot()
```

Show plot.

## `number_to_symbol`

源文件：[src/elements.py](src/elements.py)，第 20 行。

```python
number_to_symbol(x)
```

Convert atomic number to symbol and vice versa for atom 1-109.

Parameters
----------
x : str or int
    symbol or atomic number.

Returns
-------
atom[x] : str
    If x is atomic number, return symbol.

atom.index(i) : int
    If x is symbol, return atomic number.

Examples
--------
>>> check_atom('He')
2
>>> check_atom(2)
'He'

## `number_to_radii`

源文件：[src/elements.py](src/elements.py)，第 166 行。

```python
number_to_radii(x)
```

Convert atomic number (index) to atom radii in Angstroms: 1-119.

Parameters
----------
x : int
    Atomic number.

Returns
-------
atom_radii[x] : int
    Atomic radius.

Examples
--------
>>> check_radii(2) # He
0.93

## `number_to_color`

源文件：[src/elements.py](src/elements.py)，第 318 行。

```python
number_to_color(x)
```

Convert atomic number to color: 1-109.

Parameters
----------
x : int
    Atomic number.

Returns
-------
atomic color[x] : str
    Atomic color.

References
----------
http://jmol.sourceforge.net/jscolors/

Examples
--------
>>> check_color(2) # He
'#D9FFFF'

## `is_cif`

源文件：[src/io.py](src/io.py)，第 26 行。

```python
is_cif(f)
```

Check if the input file is .cif file format.

Parameters
----------
f : str
    User input filename.

Returns
-------
bool : bool
    If file is CIF file, return True.

See Also
--------
get_coord_cif :
    Find atomic coordinates of molecule from CIF file.

Notes
-----
More details about CIF file format are provided at https://en.wikipedia.org/wiki/Crystallographic_Information_File.

Examples
--------
>>> # example.cif
>>> # example
>>> # _audit_creation_date              2012-10-26T21:09:50-0400
>>> # _audit_creation_method            fapswitch 2.2
>>> # _symmetry_space_group_name_H-M    P1
>>> # _symmetry_Int_Tables_number       1
>>> # _space_group_crystal_system       triclinic
>>> # _cell_length_a                    16.012374
>>> # _cell_length_b                    14.740457
>>> # _cell_length_c                    19.436146
>>> # _cell_angle_alpha                 89.939227
>>> # _cell_angle_beta                  90.110039
>>> # _cell_angle_gamma                 90.015104
>>> # _cell_volume                      4587.49671393
>>> #
>>> # loop_
>>> # _atom_site_label
>>> # _atom_site_type_symbol
>>> # _atom_type_description
>>> # _atom_site_fract_x
>>> # _atom_site_fract_y
>>> # _atom_site_fract_z
>>> # _atom_type_partial_charge
>>> # C1    C     C_R   0.340882 0.499989 0.500098 0.541130
>>> # C2    C     C_R   0.528123 0.048033 0.558069 0.232589
>>> # C3    C     C_R   0.499931 0.902862 0.500001 -0.063750
>>> # C4    C     C_R   0.500061 0.097137 0.500001 -0.063745
>>> # C5    C     C_1   0.499958 0.802655 0.499991 0.266033
>>> # ...
>>> is_cif("example.cif")
True

## `get_coord_cif`

源文件：[src/io.py](src/io.py)，第 94 行。

```python
get_coord_cif(f)
```

Get coordinate from .cif file.

Parameters
----------
f : str
    User input filename.

Returns
-------
atom : list
    Full atomic labels of complex.
coord : array_like
    Full atomic coordinates of complex.

Examples
--------
>>> file = "example.cif"
>>> atom, coord = get_coord_cif(file)
>>> atom
['Fe', 'O', 'O', 'N', 'N', 'N', 'N']
>>> coord
array([[18.268051, 11.28912 ,  2.565804],
       [19.823874, 10.436314,  1.381569],
       [19.074466,  9.706294,  3.743576],
       [17.364238, 10.733354,  0.657318],
       [16.149538, 11.306661,  2.913619],
       [18.599941, 12.116308,  4.528988],
       [18.364987, 13.407634,  2.249608]])

## `is_xyz`

源文件：[src/io.py](src/io.py)，第 138 行。

```python
is_xyz(f)
```

Check if the input file is .xyz file format.

Parameters
----------
f : str
    User input filename.

Returns
-------
bool : bool
    If file is XYZ file, return True.

See Also
--------
get_coord_xyz :
    Find atomic coordinates of molecule from XYZ file.

Examples
--------
>>> # example.xyz
>>> # 20
>>> # Comment: From Excel file
>>> # Fe  6.251705    9.063211    5.914842
>>> # N   8.15961     9.066456    5.463087
>>> # N   6.749414    10.457551   7.179682
>>> # N   5.709997    10.492955   4.658257
>>> # N   4.350474    9.106286    6.356091
>>> # O   5.789096    7.796326    4.611355
>>> # O   6.686381    7.763872    7.209699
>>> # ...
>>> is_xyz("example.xyz")
True

## `get_coord_xyz`

源文件：[src/io.py](src/io.py)，第 190 行。

```python
get_coord_xyz(f)
```

Get coordinate from .xyz file.

Parameters
----------
f : str
    User input filename.

Returns
-------
atom : list
    Full atomic labels of complex.
coord : array_like
    Full atomic coordinates of complex.

Examples
--------
>>> file = "Fe-distorted-complex.xyz"
>>> atom, coord = get_coord_xyz(file)
>>> atom
['Fe', 'O', 'O', 'N', 'N', 'N', 'N']
>>> coord
array([[18.268051, 11.28912 ,  2.565804],
       [19.823874, 10.436314,  1.381569],
       [19.074466,  9.706294,  3.743576],
       [17.364238, 10.733354,  0.657318],
       [16.149538, 11.306661,  2.913619],
       [18.599941, 12.116308,  4.528988],
       [18.364987, 13.407634,  2.249608]])

## `is_gaussian`

源文件：[src/io.py](src/io.py)，第 243 行。

```python
is_gaussian(f)
```

Check if the input file is Gaussian file format.

Parameters
----------
f : str
    User input filename.

Returns
-------
bool : bool
    If file is Gaussian output file, return True.

See Also
--------
get_coord_gaussian :
    Find atomic coordinates of molecule from Gaussian file.

Examples
--------
>>> # gaussian.log
>>> #                             Standard orientation:
>>> # ---------------------------------------------------------------------
>>> # Center     Atomic      Atomic             Coordinates (Angstroms)
>>> # Number     Number       Type             X           Y           Z
>>> # ---------------------------------------------------------------------
>>> #      1         26           0        0.000163    1.364285   -0.000039
>>> #      2          8           0        0.684192    0.084335   -1.192008
>>> #      3          8           0       -0.683180    0.083251    1.191173
>>> #      4          7           0        1.639959    1.353157    1.006941
>>> #      5          7           0       -0.563377    2.891083    1.435925
>>> # ...
>>> is_gaussian("gaussian.log")
True

## `get_coord_gaussian`

源文件：[src/io.py](src/io.py)，第 290 行。

```python
get_coord_gaussian(f)
```

Extract XYZ coordinate from Gaussian output file.

Parameters
----------
f : str
    User input filename.

Returns
-------
atom : list
    Full atomic labels of complex.
coord : array_like
    Full atomic coordinates of complex.

Examples
--------
>>> file = "Gaussian-Fe-distorted-complex.out"
>>> atom, coord = get_coord_gaussian(file)
>>> atom
['Fe', 'O', 'O', 'N', 'N', 'N', 'N']
>>> coord
array([[18.268051, 11.28912 ,  2.565804],
       [19.823874, 10.436314,  1.381569],
       [19.074466,  9.706294,  3.743576],
       [17.364238, 10.733354,  0.657318],
       [16.149538, 11.306661,  2.913619],
       [18.599941, 12.116308,  4.528988],
       [18.364987, 13.407634,  2.249608]])

## `is_nwchem`

源文件：[src/io.py](src/io.py)，第 354 行。

```python
is_nwchem(f)
```

Check if the input file is NWChem file format.

Parameters
----------
f : str
    User input filename.

Returns
-------
bool : bool
    If file is NWChem output file, return True.

See Also
--------
get_coord_nwchem :
    Find atomic coordinates of molecule from NWChem file.

Examples
--------
>>> # nwchem.out
>>> #   ----------------------
>>> #   Optimization converged
>>> #   ----------------------
>>> # ...
>>> # ...
>>> #  No.       Tag          Charge          X              Y              Z
>>> # ---- ---------------- ---------- -------------- -------------- --------------
>>> #    1 Ru(Fragment=1)      44.0000    -3.04059115    -0.08558108    -0.07699482
>>> #    2 C(Fragment=1)        6.0000    -1.62704660     2.40971357     0.63980357
>>> #    3 C(Fragment=1)        6.0000    -0.61467778     0.59634595     1.68841986
>>> #    4 C(Fragment=1)        6.0000     0.31519183     1.41684566     2.30745116
>>> #    5 C(Fragment=1)        6.0000     0.28773462     2.80126911     2.08006241
>>> # ...
>>> is_nwchem("nwchem.out")
True

## `get_coord_nwchem`

源文件：[src/io.py](src/io.py)，第 408 行。

```python
get_coord_nwchem(f)
```

Extract XYZ coordinate from NWChem output file.

Parameters
----------
f : str
    User input filename.

Returns
-------
atom : list
    Full atomic labels of complex.
coord : array_like
    Full atomic coordinates of complex.

Examples
--------
>>> file = "NWChem-Fe-distorted-complex.out"
>>> atom, coord = get_coord_nwchem(file)
>>> atom
['Fe', 'O', 'O', 'N', 'N', 'N', 'N']
>>> coord
array([[18.268051, 11.28912 ,  2.565804],
       [19.823874, 10.436314,  1.381569],
       [19.074466,  9.706294,  3.743576],
       [17.364238, 10.733354,  0.657318],
       [16.149538, 11.306661,  2.913619],
       [18.599941, 12.116308,  4.528988],
       [18.364987, 13.407634,  2.249608]])

## `is_orca`

源文件：[src/io.py](src/io.py)，第 474 行。

```python
is_orca(f)
```

Check if the input file is ORCA file format.

Parameters
----------
f : str
    User input filename.

Returns
-------
bool : bool
    If file is ORCA output file, return True.

See Also
--------
get_coord_orca :
    Find atomic coordinates of molecule from ORCA file.

Examples
--------
>>> # orca.out
>>> # ---------------------------------
>>> # CARTESIAN COORDINATES (ANGSTROEM)
>>> # ---------------------------------
>>> #   C      0.009657    0.000000    0.005576
>>> #   C      0.009657   -0.000000    1.394424
>>> #   C      1.212436   -0.000000    2.088849
>>> #   C      2.415214    0.000000    1.394425
>>> #   C      2.415214   -0.000000    0.005575
>>> # ...
>>> is_orca("orca.out")
True

## `get_coord_orca`

源文件：[src/io.py](src/io.py)，第 518 行。

```python
get_coord_orca(f)
```

Extract XYZ coordinate from ORCA output file.

Parameters
----------
f : str
    User input filename.

Returns
-------
atom : list
    Full atomic labels of complex.
coord : array_like
    Full atomic coordinates of complex.

Examples
--------
>>> file = "ORCA-Fe-distorted-complex.out"
>>> atom, coord = get_coord_orca(file)
>>> atom
['Fe', 'O', 'O', 'N', 'N', 'N', 'N']
>>> coord
array([[18.268051, 11.28912 ,  2.565804],
       [19.823874, 10.436314,  1.381569],
       [19.074466,  9.706294,  3.743576],
       [17.364238, 10.733354,  0.657318],
       [16.149538, 11.306661,  2.913619],
       [18.599941, 12.116308,  4.528988],
       [18.364987, 13.407634,  2.249608]])

## `is_qchem`

源文件：[src/io.py](src/io.py)，第 581 行。

```python
is_qchem(f)
```

Check if the input file is Q-Chem file format.

Parameters
----------
f : str
    User input filename.

Returns
-------
bool : bool
    If file is Q-Chem output file, return True.

See Also
--------
get_coord_qchem :
    Find atomic coordinates of molecule from Q-Chem file.

Examples
--------
>>> # qchem.out
>>> # ******************************
>>> # **  OPTIMIZATION CONVERGED  **
>>> # ******************************
>>> #                            Coordinates (Angstroms)
>>> #     ATOM                X               Y               Z
>>> #      1  C         0.2681746845   -0.8206222796   -0.3704019386
>>> #      2  C        -1.1809302341   -0.5901746612   -0.6772716414
>>> #      3  H        -1.6636318262   -1.5373167851   -0.9496501352
>>> #      4  H        -1.2829834971    0.0829227646   -1.5389938241
>>> #      5  C        -1.9678565203    0.0191922768    0.5346693165
>>> # ...
>>> is_qchem("qchem.out")
True

## `get_coord_qchem`

源文件：[src/io.py](src/io.py)，第 628 行。

```python
get_coord_qchem(f)
```

Extract XYZ coordinate from Q-Chem output file.

Parameters
----------
f : str
    User input filename.

Returns
-------
atom : list
    Full atomic labels of complex.
coord : array_like
    Full atomic coordinates of complex.

Examples
--------
>>> file = "Qchem-Fe-distorted-complex.out"
>>> atom, coord = get_coord_qchem(file)
>>> atom
['Fe', 'O', 'O', 'N', 'N', 'N', 'N']
>>> coord
array([[18.268051, 11.28912 ,  2.565804],
       [19.823874, 10.436314,  1.381569],
       [19.074466,  9.706294,  3.743576],
       [17.364238, 10.733354,  0.657318],
       [16.149538, 11.306661,  2.913619],
       [18.599941, 12.116308,  4.528988],
       [18.364987, 13.407634,  2.249608]])

## `count_line`

源文件：[src/io.py](src/io.py)，第 691 行。

```python
count_line(file=None)
```

Count lines in an input file.

Parameters
----------
file : str
    Absolute or full path of input file.

Returns
-------
i + 1 : int
    Number of line in file.

Examples
--------
>>> file = "[Fe(1-bpp)2][BF4]2-HS.xyz"
>>> count_line(file)
27

## `extract_coord`

源文件：[src/io.py](src/io.py)，第 722 行。

```python
extract_coord(file=None)
```

Check file type, read data, extract atomic symbols and cartesian coordinate from
a structure input file provided by the user. This function can efficiently manupulate I/O process.
File types currently supported are listed in notes below. Other file formats can also be implemented
easily within this module.

Parameters
----------
file : str
    User input filename.

Returns
-------
atom : list
    Full atomic labels of complex.
coord : array_like
    Full atomic coordinates of complex.

See Also
--------
octadist.main.OctaDist.open_file :
    Open file dialog and to browse input file.
octadist.main.OctaDist.search_coord :
    Search octahedral structure in complex.

Notes
-----
The following are file types supported by the current virsion of OctaDist:

- ``CIF``
- ``XYZ``
- ``Gaussian``
- ``NWChem``
- ``ORCA``
- ``Q-Chem``

Examples
--------
>>> file = "[Fe(1-bpp)2][BF4]2-HS.xyz"
>>> atom, coord = extract_coord(file)
>>> atom
['Fe', 'N', 'N', 'N', 'N', 'N', 'N', 'C', 'C']
>>> coord
array([[-1.95348286e+00,  4.51770478e+00,  1.47855811e+01],
       [-1.87618286e+00,  4.48070478e+00,  1.26484811e+01],
       [-2.18698286e+00,  4.34540478e+00,  1.69060811e+01],
       [-4.88286000e-03,  3.69060478e+00,  1.42392811e+01],
       [-1.17538286e+00,  6.38340478e+00,  1.56457811e+01],
       [-2.75078286e+00,  2.50260478e+00,  1.51806811e+01],
       [-3.90128286e+00,  5.27750478e+00,  1.40814811e+01],
       [-6.14953418e+00,  8.30666180e+00,  2.91361978e+01],
       [-8.59995241e+00,  7.11630815e+00,  4.52898814e+01]])

## `find_metal`

源文件：[src/io.py](src/io.py)，第 836 行。

```python
find_metal(atom=None, coord=None)
```

Count the number of metal center atom in complex.

Parameters
----------
atom : list or None
    Full atomic labels of complex.
    Default is None.
coord : array_like or None
    Full atomic coordinates of complex.
    Default is None.

Returns
-------
atom_metal : list
    Atomic labels of metal center atom.
coord_metal : array_like
    Atomic coordinates of metal center atom.
index_metal : list
    Indices of metal atoms found.

See Also
--------
octadist.src.elements.check_atom :
    Convert atomic number to atomic symbol and vice versa.

Examples
--------
>>> atom = ['Fe', 'N', 'N', 'N', 'N', 'N', 'N']
>>> coord = [[-1.95348286e+00,  4.51770478e+00,  1.47855811e+01],
             [-1.87618286e+00,  4.48070478e+00,  1.26484811e+01],
             [-3.90128286e+00,  5.27750478e+00,  1.40814811e+01],
             [-4.88286000e-03,  3.69060478e+00,  1.42392811e+01],
             [-2.18698286e+00,  4.34540478e+00,  1.69060811e+01],
             [-1.17538286e+00,  6.38340478e+00,  1.56457811e+01],
             [-2.75078286e+00,  2.50260478e+00,  1.51806811e+01]]
>>> atom_metal, coord_metal = find_metal(atom, coord)
>>> atom_metal
['Fe']
>>> coord_metal
array([[-1.95348286,  4.51770478, 14.7855811 ]])

## `extract_octa`

源文件：[src/io.py](src/io.py)，第 904 行。

```python
extract_octa(atom, coord, ref_index=0, cutoff_ref_ligand=2.8)
```

Search the octahedral structure in complex and return atoms and coordinates.

Parameters
----------
atom : list
    Full atomic labels of complex.
coord : array_like
    Full atomic coordinates of complex.
ref_index : int
    Index of the reference to be used as the center atom for neighbor atoms
    in octahedral structure of the complex. Python-based index.
    Default is 0.
cutoff_ref_ligand : float, optional
    Cutoff distance for screening bond distance between reference and ligand atoms.
    Default is 2.8.

Returns
-------
atom_octa : list
    Atomic labels of octahedral structure.
coord_octa : array_like
    Atomic coordinates of octahedral structure.

See Also
--------
find_metal :
    Find metals in complex.
octadist.main.OctaDist.search_coord :
    Search octahedral structure in complex.

Examples
--------
>>> atom = ['Fe', 'N', 'N', 'N', 'N', 'N', 'N', 'C', 'C']
>>> coord = [[-1.95348286e+00,  4.51770478e+00,  1.47855811e+01],
             [-1.87618286e+00,  4.48070478e+00,  1.26484811e+01],
             [-3.90128286e+00,  5.27750478e+00,  1.40814811e+01],
             [-4.88286000e-03,  3.69060478e+00,  1.42392811e+01],
             [-2.18698286e+00,  4.34540478e+00,  1.69060811e+01],
             [-1.17538286e+00,  6.38340478e+00,  1.56457811e+01],
             [-2.75078286e+00,  2.50260478e+00,  1.51806811e+01],
             [-6.14953418e+00,  8.30666180e+00,  2.91361978e+01],
             [-8.59995241e+00,  7.11630815e+00,  4.52898814e+01]]
>>> atom_octa, coord_octa = extract_octa(atom, coord)
>>> atom_octa
['Fe', 'N', 'N', 'N', 'N', 'N', 'N']
>>> coord_octa
array([[-1.95348286e+00,  4.51770478e+00,  1.47855811e+01],
       [-1.87618286e+00,  4.48070478e+00,  1.26484811e+01],
       [-2.18698286e+00,  4.34540478e+00,  1.69060811e+01],
       [-4.88286000e-03,  3.69060478e+00,  1.42392811e+01],
       [-1.17538286e+00,  6.38340478e+00,  1.56457811e+01],
       [-2.75078286e+00,  2.50260478e+00,  1.51806811e+01],
       [-3.90128286e+00,  5.27750478e+00,  1.40814811e+01]])

## `angle_sign`

源文件：[src/linear.py](src/linear.py)，第 21 行。

```python
angle_sign(v1, v2, direct)
```

Compute angle between two vectors with sign and return value in degree.

Parameters
----------
v1 : array_like
    Vector in 3D space.
v2 : array_like
    Vector in 3D space.
direct : array
    Vector that refers to orientation of the plane.

Returns
-------
angle : float64
    Angle between two vectors in degree unit with sign.

See Also
--------
calc.calc_theta :
    Calculate theta parameter.

Examples
--------
>>> vector1 = [1.21859514, -0.92569245, -0.51717955]
>>> vector2 = [1.02186387,  0.57480095, -0.95220433]
>>> direction = [1.29280503, 0.69301873, 1.80572438]
>>> angle_sign(vector1, vector2, direction)
60.38697927455357

## `angle_btw_vectors`

源文件：[src/linear.py](src/linear.py)，第 70 行。

```python
angle_btw_vectors(v1, v2)
```

Compute angle between two vectors and return value in degree.

Parameters
----------
v1 : array_like
    Vector in 3D space.
v2 : array_like
    Vector in 3D space.

Returns
-------
angle : float64
    Angle between two vectors in degree unit.

Examples
--------
>>> vector1 = [-0.412697, -0.357008, -1.788172]
>>> vector2 = [-0.550839,  1.799178, -0.039114]
>>> angle_btw_vectors(vector1, vector2)
95.62773246517462

## `angle_btw_planes`

源文件：[src/linear.py](src/linear.py)，第 105 行。

```python
angle_btw_planes(a1, b1, c1, a2, b2, c2)
```

Find the angle between 2 planes in 3D and return value in degree.

::

    General equation of plane:

    a*X + b*Y + c*Z + d = 0

Parameters
----------
a1, b1, c1 : float
    Coefficient of the equation of plane 1.
a2, b2, c2 : float
    Coefficient of the equation of plane 2.

Returns
-------
angle : float64
    Angle between 2 planes in degree unit.

Examples
--------
>>> # Plane 1
>>> a1 = -3.231203733528
>>> b1 = -0.9688526458499996
>>> c1 = 0.9391692927779998
>>> # Plane 2
>>> a2 = 1.3904813057000005
>>> b2 = 3.928502357473003
>>> c2 = -4.924114034864001
>>> angle_btw_planes(a1, b1, c1, a2, b2, c2)
124.89920902358416

## `triangle_area`

源文件：[src/linear.py](src/linear.py)，第 151 行。

```python
triangle_area(a, b, c)
```

Calculate the area of the triangle using the cross product:

::

    Area = abs(ab X ac)/2

    where vector ab = b - a and vector ac = c - a.

Parameters
----------
a : array_like
    3D Coordinate of point.
b : array_like
    3D Coordinate of point.
c : array_like
    3D Coordinate of point.

Returns
-------
area : float64
    The triangle area.

Examples
--------
>>> # Three vertices
>>> a = [2.298354000, 5.161785000, 7.971898000]
>>> b = [1.885657000, 4.804777000, 6.183726000]
>>> c = [1.747515000, 6.960963000, 7.932784000]
>>> triangle_area(a, b, c)
1.7508135235821773

## `find_eq_of_plane`

源文件：[src/plane.py](src/plane.py)，第 23 行。

```python
find_eq_of_plane(x, y, z)
```

Find the equation of plane of given three points using cross product:

::

    The general form of plane equation:

    Ax + By + Cz = D

    where A, B, C, and D are coefficient.

    XZ  X  XY = (a, b, c)

    d = (a, b, c).Z

Parameters
----------
x : array_like
    3D Coordinate of point.
y : array_like
    3D Coordinate of point.
z : array_like
    3D Coordinate of point.

Returns
-------
a : float64
    Coefficient of the equation of the plane.
b : float64
    Coefficient of the equation of the plane.
c : float64
    Coefficient of the equation of the plane.
d : float64
    Coefficient of the equation of the plane.

Examples
--------
>>> N1 = [2.298354000, 5.161785000, 7.971898000]
>>> N2 = [1.885657000, 4.804777000, 6.183726000]
>>> N3 = [1.747515000, 6.960963000, 7.932784000]
>>> a, b, c, d = find_eq_of_plane(N1, N2, N3)
>>> a
-3.231203733528
>>> b
-0.9688526458499996
>>> c
0.9391692927779998
>>> d
-4.940497273569501

## `find_fit_plane`

源文件：[src/plane.py](src/plane.py)，第 90 行。

```python
find_fit_plane(coord)
```

Find best fit plane to the given data points (atoms).

Parameters
----------
coord : array_like
    Coordinates of selected atom chunk.

Returns
-------
xx : float
    Coefficient of the surface.
yy : float
    Coefficient of the surface.
z : float
    Coefficient of the surface.
abcd : tuple
    Coefficient of the equation of the plane.

See Also
--------
scipy.optimize.minimize :
    Used to find the least-square plane.

Examples
--------
>>> points = [(1.1, 2.1, 8.1),
              (3.2, 4.2, 8.0),
              (5.3, 1.3, 8.2),
              (3.4, 2.4, 8.3),
              (1.5, 4.5, 8.0),
              (5.5, 6.7, 4.5)
              ]
>>> # To plot the plane, run following commands:
>>> import matplotlib.pyplot as plt
>>> # map coordinates for scattering plot
>>> xs, ys, zs = zip(*points)
>>> plt.scatter(xs, ys, zs)
>>> plt.show()

## `Plot`

源文件：[src/plot.py](src/plot.py)，第 20 行。

```python
Plot
```

Relationship plot between Zeta and Sigma parameters.

Parameters
----------
args[0] : list
    List of data set 1 (data1).
args[0] = list
    List of data set 2 (data2).
name1 = str, optional
    Name of data set 1.
name2 = str, optional
    Name of data set 2.

Examples
--------
>>> data1 = [1, 2, 3, 4, 5]
>>> data2 = [1, 2, 3, 4, 5]
>>> test = Plot(data1, data2, name1="Data 1", name2="Data 2")
>>> test.add_point()
>>> test.add_text()
>>> test.add_legend()
>>> test.show_plot()

## `Plot.__init__`

源文件：[src/plot.py](src/plot.py)，第 47 行。

```python
Plot.__init__(self, *args, name1='Var1', name2='Var2')
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `Plot.start_plot`

源文件：[src/plot.py](src/plot.py)，第 65 行。

```python
Plot.start_plot(self)
```

Start plot.

## `Plot.add_point`

源文件：[src/plot.py](src/plot.py)，第 72 行。

```python
Plot.add_point(self)
```

Add all atoms to show in figure.

## `Plot.add_text`

源文件：[src/plot.py](src/plot.py)，第 80 行。

```python
Plot.add_text(self)
```

Added text to show in figure.

## `Plot.add_legend`

源文件：[src/plot.py](src/plot.py)，第 88 行。

```python
Plot.add_legend(self)
```

Add legend to show in figure.

## `Plot.config_plot`

源文件：[src/plot.py](src/plot.py)，第 102 行。

```python
Plot.config_plot(self)
```

Config structure of figure.

## `Plot.set_label`

源文件：[src/plot.py](src/plot.py)，第 113 行。

```python
Plot.set_label(self)
```

Set title of figure and axis labels.

## `Plot.save_img`

源文件：[src/plot.py](src/plot.py)，第 123 行。

```python
Plot.save_img(save='Image_saved_by_OctaDist', file='png')
```

Save figure as an image.

Parameters
----------
save : str
    Name of image file.
    Default is "Complex_saved_by_OctaDist".
file : file
    Image type.
    Default is "png".

## `Plot.show_plot`

源文件：[src/plot.py](src/plot.py)，第 140 行。

```python
Plot.show_plot()
```

Show plot.

## `err_no_file`

源文件：[src/popup.py](src/popup.py)，第 20 行。

```python
err_no_file()
```

Show this error when no input files uploaded/opened.

## `err_invalid_ftype`

源文件：[src/popup.py](src/popup.py)，第 25 行。

```python
err_invalid_ftype()
```

Show this error popup when file type is not supported by the program.

## `err_no_coord`

源文件：[src/popup.py](src/popup.py)，第 35 行。

```python
err_no_coord(i)
```

Show this error popup when the program cannot read the atomic coordinates of complex
inside the file or cannot extract the coordinates from the complex.

This will happen only if the input has no the proper format of atomic coordinates.

Parameters
----------
i : int
    Number of file.

## `err_less_ligands`

源文件：[src/popup.py](src/popup.py)，第 53 行。

```python
err_less_ligands(i)
```

Show this error popup when the complex has ligand atoms less that six atoms.

Parameters
----------
i : int
    Number of file.

## `err_no_metal`

源文件：[src/popup.py](src/popup.py)，第 70 行。

```python
err_no_metal()
```

Show this error popup when the complex has no transition metal atom.

## `err_no_calc`

源文件：[src/popup.py](src/popup.py)，第 79 行。

```python
err_no_calc()
```

Show this error popup when the user requests function that the results are required,
but the results have not been computed yet.

## `err_only_2_files`

源文件：[src/popup.py](src/popup.py)，第 89 行。

```python
err_only_2_files()
```

Show this error popup when having not uploaded two complexes
for using the RMSD function.

## `err_not_equal_atom`

源文件：[src/popup.py](src/popup.py)，第 96 行。

```python
err_not_equal_atom()
```

Show this error popup when the total number of atoms of two complexes are not equal.

## `err_atom_not_match`

源文件：[src/popup.py](src/popup.py)，第 103 行。

```python
err_atom_not_match(line)
```

show this error popup when atomic symbol of two similar complexes does not match.

Parameters
----------
line : int
    The line number that atomic symbol does not match.

## `err_many_files`

源文件：[src/popup.py](src/popup.py)，第 114 行。

```python
err_many_files()
```

Show this error popup when user has loaded too many files.

## `err_wrong_format`

源文件：[src/popup.py](src/popup.py)，第 119 行。

```python
err_wrong_format()
```

Show this error popup when user has loaded the file that is not supported by OctaDist.

## `err_no_editor`

源文件：[src/popup.py](src/popup.py)，第 128 行。

```python
err_no_editor()
```

Show this error popup if text editor path is empty.

## `err_visualizer_not_found`

源文件：[src/popup.py](src/popup.py)，第 136 行。

```python
err_visualizer_not_found()
```

Show this error popup if user-defined visualizer is not available.

## `err_cannot_update`

源文件：[src/popup.py](src/popup.py)，第 145 行。

```python
err_cannot_update()
```

Show this error popup when the program cannot detect the operating system that the user is using.

## `info_save_results`

源文件：[src/popup.py](src/popup.py)，第 154 行。

```python
info_save_results(file)
```

show this info popup when an output file has been saved successfully.

Parameters
----------
file : str
    Absolute or full path of saved output file.

## `info_new_update`

源文件：[src/popup.py](src/popup.py)，第 165 行。

```python
info_new_update()
```

Show this info popup when new version is available for update.

## `info_using_dev`

源文件：[src/popup.py](src/popup.py)，第 170 行。

```python
info_using_dev()
```

Show this info popup if user is using a development build version.

## `info_no_update`

源文件：[src/popup.py](src/popup.py)，第 175 行。

```python
info_no_update()
```

Show this info popup if program is the latest version.

## `warn_no_metal`

源文件：[src/popup.py](src/popup.py)，第 180 行。

```python
warn_no_metal(i)
```

Show this warning popup if no transition metal was found.

Parameters
----------
i : int
    Number of file.

## `warn_not_octa`

源文件：[src/popup.py](src/popup.py)，第 191 行。

```python
warn_not_octa()
```

Show this warning popup if the complex is non-octahedral structure.

## `project_atom_onto_line`

源文件：[src/projection.py](src/projection.py)，第 20 行。

```python
project_atom_onto_line(p, a, b)
```

Find the point projection on the line, which defined by two distinct end points.

::

    a <----> b

    P(x) = x1 + (p - x1).(x2 - x1)/(x2-x1).(x2-x1) * (x2-x1)

Parameters
----------
p : array_like
    Coordinate of point to project.
a : array_like
    Coordinate of head atom of the line.
b : array_like
    Coordinate of tail atom of the line.

Returns
-------
projected_point : array_like
    The projected point on the orthogonal line.

Examples
--------
>>> # point to project
>>> p = [10.1873, 5.7463, 5.615]
>>> # head and end points of line
>>> a = [8.494, 5.9735, 4.8091]
>>> b = [9.6526, 6.4229, 7.3079]
>>> project_atom_onto_line(p, a, b)
[9.07023235 6.19701012 6.05188388]

## `project_atom_onto_plane`

源文件：[src/projection.py](src/projection.py)，第 67 行。

```python
project_atom_onto_plane(p, a, b, c, d)
```

Find the orthogonal vector of point onto the given plane.
The equation of plane is ``Ax + By + Cz = D`` and point is ``(L, M, N)``,
then the location on the plane that is closest to the point ``(P, Q, R)`` is

::

    (P, Q, R) = (L, M, N) + λ * (A, B, C)

    where λ = (D - ( A*L + B*M + C*N)) / (A^2 + B^2 + C^2).

Parameters
----------
p : array_like
    Point to project.
a : int or float
    Coefficient of the equation of the plane.
b : int or float
    Coefficient of the equation of the plane.
c : int or float
    Coefficient of the equation of the plane.
d : int or float
    Coefficient of the equation of the plane.

Returns
-------
projected_point: array_like
    The projected point on the orthogonal plane.

Examples
--------
>>> # point to project
>>> p = [10.1873, 5.7463, 5.615]
>>> # coefficient of the equation of the plane
>>> a = -3.231203733528
>>> b = -0.9688526458499996
>>> c = 0.9391692927779998
>>> d = -4.940497273569501
>>> project_atom_onto_plane(p, a, b, c, d)
[2.73723598 3.51245316 7.78040705]

## `ScriptingConsole`

源文件：[src/scripting.py](src/scripting.py)，第 22 行。

```python
ScriptingConsole
```

Start scripting interface for an interactive code.

User can access to class variable (dynamic variable).

+------------+
| Output box |
+------------+
| Input box  |
+------------+

Parameters
----------
root : object
    Passing self object from another class to this class as root argument.

See Also
--------
settings :
    Program settings.

Examples
--------
>>> import tkinter as tk
>>> master = tk.Tk()
>>> console = ScriptingConsole(master)
>>> console.scripting_start()

## `ScriptingConsole.__init__`

源文件：[src/scripting.py](src/scripting.py)，第 53 行。

```python
ScriptingConsole.__init__(self, root)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `ScriptingConsole.scripting_start`

源文件：[src/scripting.py](src/scripting.py)，第 58 行。

```python
ScriptingConsole.scripting_start(self)
```

Start scripting console.

## `ScriptingConsole.script_run_help`

源文件：[src/scripting.py](src/scripting.py)，第 94 行。

```python
ScriptingConsole.script_run_help(self)
```

Show help messages.

## `ScriptingConsole.script_run_list`

源文件：[src/scripting.py](src/scripting.py)，第 127 行。

```python
ScriptingConsole.script_run_list(self)
```

Show list of commands in scripting run.

## `ScriptingConsole.script_run_info`

源文件：[src/scripting.py](src/scripting.py)，第 138 行。

```python
ScriptingConsole.script_run_info(self)
```

Show info of program.

## `ScriptingConsole.script_run_doc`

源文件：[src/scripting.py](src/scripting.py)，第 145 行。

```python
ScriptingConsole.script_run_doc(self)
```

Show document of program.

## `ScriptingConsole.script_run_show`

源文件：[src/scripting.py](src/scripting.py)，第 152 行。

```python
ScriptingConsole.script_run_show(self, args)
```

Show value of variable that user requests.

Parameters
----------
args : str
    Arbitrary argument.

## `ScriptingConsole.script_run_type`

源文件：[src/scripting.py](src/scripting.py)，第 185 行。

```python
ScriptingConsole.script_run_type(self, args)
```

Show data type of variable.

Parameters
----------
args : str
    Arbitrary argument.

## `ScriptingConsole.script_run_set`

源文件：[src/scripting.py](src/scripting.py)，第 211 行。

```python
ScriptingConsole.script_run_set(self, args)
```

Set new value to variable.

Parameters
----------
args : str
    Arbitrary argument.

## `ScriptingConsole.script_run_clear`

源文件：[src/scripting.py](src/scripting.py)，第 238 行。

```python
ScriptingConsole.script_run_clear(self)
```

Clear output box.

## `ScriptingConsole.script_run_clean`

源文件：[src/scripting.py](src/scripting.py)，第 245 行。

```python
ScriptingConsole.script_run_clean(self, args)
```

Clear output box and clean variable.

## `ScriptingConsole.script_run_restore`

源文件：[src/scripting.py](src/scripting.py)，第 259 行。

```python
ScriptingConsole.script_run_restore(self)
```

Restore all default settings.

## `ScriptingConsole.script_run_history`

源文件：[src/scripting.py](src/scripting.py)，第 288 行。

```python
ScriptingConsole.script_run_history(self)
```

Show history of command.

## `ScriptingConsole.script_no_command`

源文件：[src/scripting.py](src/scripting.py)，第 298 行。

```python
ScriptingConsole.script_no_command(self, command)
```

Show statement if command not found.

Parameters
----------
command : str
    Command that user submits.

## `ScriptingConsole.script_execute`

源文件：[src/scripting.py](src/scripting.py)，第 310 行。

```python
ScriptingConsole.script_execute(self, event)
```

Execute input command scripting.

Parameters
----------
event : object
    Object for button interaction

## `DataComplex`

源文件：[src/structure.py](src/structure.py)，第 25 行。

```python
DataComplex
```

Show info of input complex.

Parameters
----------
master : object, optional
    If None, use tk.Tk().
    If not None, use tk.Toplevel(master).

icon : str, optional
    If None, use tkinter default icon.
    If not None, use user-defined icon.

Examples
--------
>>> file = "File_1"
>>> atom = ['Fe', 'N', 'N', 'N', 'O', 'O', 'O']
>>> coord = [[2.298354000, 5.161785000, 7.971898000],
             [1.885657000, 4.804777000, 6.183726000],
             [1.747515000, 6.960963000, 7.932784000],
             [4.094380000, 5.807257000, 7.588689000],
             [0.539005000, 4.482809000, 8.460004000],
             [2.812425000, 3.266553000, 8.131637000],
             [2.886404000, 5.392925000, 9.848966000]]
>>> my_app = DataComplex()
>>> my_app.add_name(file)
>>> my_app.add_coord(atom, coord)

## `DataComplex.__init__`

源文件：[src/structure.py](src/structure.py)，第 56 行。

```python
DataComplex.__init__(self, master=None, icon=None)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `DataComplex.start_app`

源文件：[src/structure.py](src/structure.py)，第 66 行。

```python
DataComplex.start_app(self)
```

Start application.

## `DataComplex.add_name`

源文件：[src/structure.py](src/structure.py)，第 85 行。

```python
DataComplex.add_name(self, file_name)
```

Add file name to box.

Parameters
----------
file_name : array_like
    List containing the names of all input files.

## `DataComplex.add_coord`

源文件：[src/structure.py](src/structure.py)，第 97 行。

```python
DataComplex.add_coord(self, atom, coord)
```

Add atomic symbols and coordinates to box.

Parameters
----------
atom : array_like
    Atomic labels of full complex.
coord : array_like
    Atomic coordinates of full complex.

## `StructParam`

源文件：[src/structure.py](src/structure.py)，第 126 行。

```python
StructParam
```

Show structural parameters of structure.

Parameters
----------
master : object, optional
    If None, use tk.Tk().
    If not None, use tk.Toplevel(master).

icon : str, optional
    If None, use tkinter default icon.
    If not None, use user-defined icon.

Examples
--------
>>> metal = 'Fe'
>>> atom = ['Fe', 'N', 'N', 'N', 'O', 'O', 'O']
>>> coord = [[2.298354000, 5.161785000, 7.971898000],
             [1.885657000, 4.804777000, 6.183726000],
             [1.747515000, 6.960963000, 7.932784000],
             [4.094380000, 5.807257000, 7.588689000],
             [0.539005000, 4.482809000, 8.460004000],
             [2.812425000, 3.266553000, 8.131637000],
             [2.886404000, 5.392925000, 9.848966000]]
>>> my_app = StructParam()
>>> my_app.add_metal(metal)
>>> my_app.add_coord(atom, coord)

## `StructParam.__init__`

源文件：[src/structure.py](src/structure.py)，第 157 行。

```python
StructParam.__init__(self, master=None, icon=None)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `StructParam.start_app`

源文件：[src/structure.py](src/structure.py)，第 167 行。

```python
StructParam.start_app(self)
```

Start application.

## `StructParam.add_number`

源文件：[src/structure.py](src/structure.py)，第 188 行。

```python
StructParam.add_number(self, number)
```

Add file number to box.

Parameters
----------
number : int
    File number.

## `StructParam.add_metal`

源文件：[src/structure.py](src/structure.py)，第 200 行。

```python
StructParam.add_metal(self, metal)
```

Add metal atom to box:

Parameters
----------
metal : str
    Metal atom.

## `StructParam.add_coord`

源文件：[src/structure.py](src/structure.py)，第 212 行。

```python
StructParam.add_coord(self, atom, coord)
```

Add atomic symbols and coordinates to box.

Parameters
----------
atom : array_like
    Atomic labels of full complex.
coord : array_like
    Atomic coordinates of full complex.

## `SurfaceArea`

源文件：[src/structure.py](src/structure.py)，第 260 行。

```python
SurfaceArea
```

Find the area of the faces of octahedral structure.

Three ligand atoms are vertices of triangular face

Parameters
----------
master : object, optional
    If None, use tk.Tk().
    If not None, use tk.Toplevel(master).

icon : str, optional
    If None, use tkinter default icon.
    If not None, use user-defined icon.

Examples
--------
>>> metal = 'Fe'
>>> coord = [[2.298354000, 5.161785000, 7.971898000],
             [1.885657000, 4.804777000, 6.183726000],
             [1.747515000, 6.960963000, 7.932784000],
             [4.094380000, 5.807257000, 7.588689000],
             [0.539005000, 4.482809000, 8.460004000],
             [2.812425000, 3.266553000, 8.131637000],
             [2.886404000, 5.392925000, 9.848966000]]
>>> my_app = SurfaceArea()
>>> my_app.add_metal(metal)
>>> my_app.add_octa(coord)

## `SurfaceArea.__init__`

源文件：[src/structure.py](src/structure.py)，第 292 行。

```python
SurfaceArea.__init__(self, master=None, icon=None)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `SurfaceArea.start_app`

源文件：[src/structure.py](src/structure.py)，第 302 行。

```python
SurfaceArea.start_app(self)
```

Start application.

## `SurfaceArea.add_number`

源文件：[src/structure.py](src/structure.py)，第 321 行。

```python
SurfaceArea.add_number(self, number)
```

Add file number to box.

Parameters
----------
number : int
    File number.

## `SurfaceArea.add_metal`

源文件：[src/structure.py](src/structure.py)，第 333 行。

```python
SurfaceArea.add_metal(self, metal)
```

Add metal atom to box:

Parameters
----------
metal : str
    Metal atom.

## `SurfaceArea.add_octa`

源文件：[src/structure.py](src/structure.py)，第 345 行。

```python
SurfaceArea.add_octa(self, coord)
```

Add atomic coordinates of octahedron and find triangle area of the faces.

Parameters
----------
coord : array_like
    Atomic coordinates of octahedral structure.

See Also
--------
octadist.src.util.find_faces_octa :
    Find all faces of octahedron.

## `CalcJahnTeller`

源文件：[src/tools.py](src/tools.py)，第 29 行。

```python
CalcJahnTeller
```

Calculate angular Jahn-Teller distortion parameter [1]_.

Parameters
----------
atom : array_like
    Atomic labels of full complex.
coord : array_like
    Atomic coordinates of full complex.
master : None, object
    If None, use tk.Tk().
    If not None, use tk.Toplevel(master).
cutoff_global : int or float
    Global cutoff for screening bonds.
    Default is 2.0.
cutoff_hydrogen : int or float
    Cutoff for screening hydrogen bonds.
    Default is 1.2.
icon : str, optional
    If None, use tkinter default icon.
    If not None, use user-defined icon.

Examples
--------
>>> atom = ['Fe', 'N', 'N', 'N', 'O', 'O', 'O']
>>> coord = [[2.298354000, 5.161785000, 7.971898000],
             [1.885657000, 4.804777000, 6.183726000],
             [1.747515000, 6.960963000, 7.932784000],
             [4.094380000, 5.807257000, 7.588689000],
             [0.539005000, 4.482809000, 8.460004000],
             [2.812425000, 3.266553000, 8.131637000],
             [2.886404000, 5.392925000, 9.848966000]]
>>> test = CalcJahnTeller(atom=atom, coord=coord)
>>> test.start_app()
>>> test.find_bond()
>>> test.show_app()

References
----------
.. [1] J. M. Holland, J. A. McAllister, C. A. Kilner,
    M. Thornton-Pett, A. J. Bridgeman, M. A. Halcrow.
    Stereochemical effects on the spin-state transition
    shown by salts of [FeL2]2+ [L = 2,6-di(pyrazol-1-yl)pyridine].
    J. Chem. Soc., Dalton Trans., 2002, 548-554.
    DOI: 10.1039/B108468M.

## `CalcJahnTeller.__init__`

源文件：[src/tools.py](src/tools.py)，第 78 行。

```python
CalcJahnTeller.__init__(self, atom, coord, cutoff_global=2.0, cutoff_hydrogen=1.2, master=None, icon=None)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `CalcJahnTeller.start_app`

源文件：[src/tools.py](src/tools.py)，第 103 行。

```python
CalcJahnTeller.start_app(self)
```

Start application.

## `CalcJahnTeller.find_bond`

源文件：[src/tools.py](src/tools.py)，第 188 行。

```python
CalcJahnTeller.find_bond(self)
```

Find bonds.

See Also
--------
octadist.src.util.find_bonds :
    Find atomic bonds.

## `CalcJahnTeller.pick_atom`

源文件：[src/tools.py](src/tools.py)，第 206 行。

```python
CalcJahnTeller.pick_atom(self, group)
```

On-mouse pick atom and get XYZ coordinate.

Parameters
----------
group : str
    Group A or B.

## `CalcJahnTeller.plot_fit_plane`

源文件：[src/tools.py](src/tools.py)，第 355 行。

```python
CalcJahnTeller.plot_fit_plane(self)
```

Display complex and two fit planes of two sets of ligand in molecule.

## `CalcJahnTeller.clear_text`

源文件：[src/tools.py](src/tools.py)，第 483 行。

```python
CalcJahnTeller.clear_text(self)
```

Clear text in box A & B.

## `CalcJahnTeller.show_app`

源文件：[src/tools.py](src/tools.py)，第 505 行。

```python
CalcJahnTeller.show_app(self)
```

Show application.

## `CalcRMSD`

源文件：[src/tools.py](src/tools.py)，第 513 行。

```python
CalcRMSD
```

Calculate root mean squared displacement of atoms in complex, RMSD [2]_.

Parameters
----------
coord_1 : array_like
    Atomic coordinates of structure 1.
coord_2 : array_like
    Atomic coordinates of structure 2.
atom_1 : list or tuple, optional
    Atomic symbols of structure 1.
atom_2 : list or tuple, optional
    Atomic symbols of structure 2.
    If no atom_2 specified, assign it with None.

Returns
-------
rmsd_normal : float
    Normal RMSD.
rmsd_translate : float
    Translate RMSD (re-centered).
rmsd_rotate : float
    Kabsch RMSD (rotated).

References
----------
.. [2] J. C. Kromann. https://github.com/charnley/rmsd.

Examples
--------
>>> # Example of structure 1
>>> comp1 = [[10.1873, 5.7463, 5.615],
             [8.494, 5.9735, 4.8091],
             [9.6526, 6.4229, 7.3079],
             [10.8038, 7.5319, 5.1762],
             [9.6229, 3.9221, 6.0083],
             [12.0065, 5.5562, 6.3497],
             [10.8046, 4.9471, 3.9219]]

>>> # Example of structure 1
>>> comp2 = [[12.0937, 2.4505, 3.4207],
             [12.9603, 2.2952, 1.7286],
             [13.4876, 1.6182, 4.4230],
             [12.8522, 4.3174, 3.9894],
             [10.9307, 0.7697, 2.9315],
             [10.7878, 2.2987, 5.1071],
             [10.6773, 3.7960, 2.5424]]

>>> test = CalcRMSD(coord_1=comp1, coord_2=comp2)
>>> test.calc_rmsd()
>>> test.rmsd_normal
6.758144
>>> test.rmsd_translate
0.305792
>>> test.rmsd_rotate
0.277988

## `CalcRMSD.__init__`

源文件：[src/tools.py](src/tools.py)，第 573 行。

```python
CalcRMSD.__init__(self, coord_1, coord_2, atom_1=None, atom_2=None, master=None, icon=None)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `CalcRMSD.start_app`

源文件：[src/tools.py](src/tools.py)，第 596 行。

```python
CalcRMSD.start_app(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `CalcRMSD.show_coord`

源文件：[src/tools.py](src/tools.py)，第 651 行。

```python
CalcRMSD.show_coord(self)
```

Show atomic coordinates in box.

## `CalcRMSD.calc_rmsd`

源文件：[src/tools.py](src/tools.py)，第 673 行。

```python
CalcRMSD.calc_rmsd(self)
```

Calculate normal, translated, and rotated RMSD.

## `CalcRMSD.calc_and_show`

源文件：[src/tools.py](src/tools.py)，第 696 行。

```python
CalcRMSD.calc_and_show(self)
```

Execute calc_rmsd function to calculate RMSD
and show results in box.

## `CalcRMSD.show_app`

源文件：[src/tools.py](src/tools.py)，第 712 行。

```python
CalcRMSD.show_app(self)
```

Show application.

## `find_bonds`

源文件：[src/util.py](src/util.py)，第 23 行。

```python
find_bonds(atom, coord, cutoff_global=2.0, cutoff_hydrogen=1.2)
```

Find all bond distance and filter the possible bonds.

- Compute distance of all bonds
- Screen bonds out based on global cutoff distance
- Screen H bonds out based on local cutoff distance

Parameters
----------
atom : list
    List of atomic labels of molecule.
coord : list
    List of atomic coordinates of molecule.
cutoff_global : int or float
    Global cutoff for screening bonds.
    Default is 2.0.
cutoff_hydrogen : int or float
    Cutoff for screening hydrogen bonds.
    Default is 1.2.

Returns
-------
filtered_pair_2 : list
    List of pair of atoms of selected bonds in molecule after screening
filtered_bond_2 : array_like
    Array of bond distances of selected bonds in molecule after screening.

Examples
--------
>>> atom = ['Fe', 'N', 'N', 'N', 'O', 'O', 'O']
>>> coord = [[2.298354000, 5.161785000, 7.971898000],
             [1.885657000, 4.804777000, 6.183726000],
             [1.747515000, 6.960963000, 7.932784000],
             [4.094380000, 5.807257000, 7.588689000],
             [0.539005000, 4.482809000, 8.460004000],
             [2.812425000, 3.266553000, 8.131637000],
             [2.886404000, 5.392925000, 9.848966000]]
>>> pair_bond, bond_dist = find_bonds(atom, coord)
>>> pair_bond
[['Fe', 'N'], ['Fe', 'N'], ['Fe', 'N'], ['Fe', 'O'], ['Fe', 'O'], ['Fe', 'O']]
>>> bond_dist
[[[2.298354 5.161785 7.971898]
  [1.885657 4.804777 6.183726]]
 [[2.298354 5.161785 7.971898]
  [1.747515 6.960963 7.932784]]
 [[2.298354 5.161785 7.971898]
  [4.09438  5.807257 7.588689]]
 [[2.298354 5.161785 7.971898]
  [0.539005 4.482809 8.460004]]
 [[2.298354 5.161785 7.971898]
  [2.812425 3.266553 8.131637]]
 [[2.298354 5.161785 7.971898]
  [2.886404 5.392925 9.848966]]]

## `find_faces_octa`

源文件：[src/util.py](src/util.py)，第 116 行。

```python
find_faces_octa(c_octa)
```

Find the eight faces of octahedral structure.

::

    1. Choose 3 atoms out of 6 ligand atoms. The total number of combination is 20.
    2. Orthogonally project metal center atom onto the face: m ----> m'
    3. Calculate the shortest distance between original metal center to its projected point.
    4. Sort the 20 faces in ascending order of the shortest distance.
    5. Delete 12 faces that closest to metal center atom (first 12 faces).
    6. The remaining 8 faces are the (reference) face of octahedral structure.
    7. Find 8 opposite faces.

    Reference plane              Opposite plane
       [[1 2 3],                    [[4 5 6],
        [1 2 4],        --->         [3 5 6],
          ...                          ...
        [2 3 5]]                     [1 4 6]]

Parameters
----------
c_octa : array_like
    Atomic coordinates of octahedral structure.

Returns
-------
a_ref_f : list
    Atomic labels of reference face.
c_ref_f : array_like
    Atomic coordinates of reference face.
a_oppo_f : list
    Atomic labels of opposite face.
c_oppo_f : array_like
    Atomic coordinates of opposite face.

See Also
--------
octadist.src.plane.find_eq_of_plane :
    Find the equation of the plane.
octadist.src.projection.project_atom_onto_plane :
    Orthogonal projection of point onto the plane.

Examples
--------
>>> coord = [[14.68572, 18.49228, 6.66716],
             [14.86476, 16.48821, 7.43379],
             [14.44181, 20.59400, 6.21555],
             [13.37473, 17.23453, 5.45099],
             [16.26114, 18.54903, 8.20527],
             [13.04897, 19.25464, 7.93122],
             [16.09157, 18.96170, 5.02956]]
>>> a_ref, c_ref, a_oppo, c_oppo = find_faces_octa(coord)
>>> a_ref
[[1, 3, 6], [1, 4, 6], [2, 3, 6], [2, 3, 5],
 [2, 4, 5], [1, 4, 5], [1, 3, 5], [2, 4, 6]]
>>> c_ref
[[[14.86476 16.48821  7.43379]
  [13.37473 17.23453  5.45099]
  [16.09157 18.9617   5.02956]],
 ...,
 ...,
 [[14.44181 20.594    6.21555]
  [16.26114 18.54903  8.20527]
  [16.09157 18.9617   5.02956]]]
>>> a_octa
[[2, 4, 5], [2, 3, 5], [1, 4, 5], [1, 4, 6],
 [1, 3, 6], [2, 3, 6], [2, 4, 6], [1, 3, 5]]
>>> c_octa
[[[14.44181 20.594    6.21555]
  [16.26114 18.54903  8.20527]
  [13.04897 19.25464  7.93122]],
 ...,
 ...,
 [[14.86476 16.48821  7.43379]
  [13.37473 17.23453  5.45099]
  [13.04897 19.25464  7.93122]]]

