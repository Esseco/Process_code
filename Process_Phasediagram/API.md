# Process_Phasediagram 参数索引

源码静态索引；保留原有函数名。类构造和公开方法分别列出。默认值不代表适用于所有体系。

## `main`

源文件：[examples/plot_phase_diagram.py](examples/plot_phase_diagram.py)，第 37 行。

```python
main()
```

Read the configured CSV or demo arrays, plot, and optionally save/show.

## `calculate_hull_error`

源文件：[metrics.py](metrics.py)，第 81 行。

```python
calculate_hull_error(pred_hull: HullInput, ref_hull: HullInput, x_range: ArrayLike | None=None, *, return_curves: bool=False)
```

Return the exact mean absolute difference between endpoint-relative hulls.

Parameters
----------
pred_hull, ref_hull
    (N, 2) arrays of (x, energy), or mappings with 1D ``x`` and ``energy``
    columns. Vertices are sorted by x; duplicate x, NaN/Inf, fewer than two
    points and nonconvex inputs raise ValueError. Collinear points are allowed.
    Slopes must be nondecreasing, within 64 machine eps relative roundoff.
    Both energies must use the same unit/normalization, e.g. meV/TM.
x_range
    (xmin, xmax), strictly increasing and covered by both hulls. Defaults to
    their common coverage. Extrapolation and zero-width ranges are rejected.
return_curves
    Also return ``x``, ``pred_relative_energy``, ``ref_relative_energy`` on
    the union of interior vertex positions and evaluation endpoints.

Returns
-------
dict
    ``hull_error`` in input energy units and ``integral_error`` in energy
    times x units. Each hull has its own endpoint chord subtracted over the
    evaluation range. Piecewise linear integration splits sign crossings
    analytically, without sampling error (subject to floating-point precision).

Notes
-----
Pure deterministic calculation: no mutation, files, models or random seed.
Only prepared computational reference hulls are appropriate for this metric.

Examples
--------
>>> calculate_hull_error([[0, 0], [0.5, -2], [1, 0]], [[0, 0], [1, 0]])
{'hull_error': 1.0, 'integral_error': 1.0}

## `calculate_phase_iou_error`

源文件：[metrics.py](metrics.py)，第 182 行。

```python
calculate_phase_iou_error(pred_phases: PhaseInput, ref_phases: PhaseInput, *, x_range: ArrayLike, delta: float=0.0)
```

Return macro-averaged phase IoU error after symmetric interval dilation.

Parameters
----------
pred_phases, ref_phases
    Mappings from phase names (strings) to (N, 2) arrays/lists of (start, end).
    Multiple disconnected intervals and coexistence across labels are allowed.
    Overlapping/touching intervals within a phase are merged. [] is allowed.
    All input intervals must be finite with start < end, even outside x_range.
x_range
    Required finite (xmin, xmax), xmin < xmax; same x units as intervals/delta.
delta
    Finite nonnegative scalar. Both predicted and reference intervals expand
    left/right by delta before clipping to x_range. This is dilation IoU,
    not a rule assigning perfect scores to boundary shifts smaller than delta.

Returns
-------
dict
    ``phase_error = 1 - mean_iou``, ``mean_iou`` and ``phase_iou`` (per-label
    IoU), all in [0, 1]. Each label in either mapping has equal weight. A label
    missing from either mapping scores 0. If a label exists in both mappings
    but both dilated/clipped sets are empty, its IoU is 1 (equal empty sets).
    Two empty mappings raise ValueError because the macro mean is undefined.

Notes
-----
No phase identification, mutation, file I/O or randomness. Invalid inputs
raise ValueError. Repeat calls on identical inputs return identical results.

Examples
--------
>>> calculate_phase_iou_error({'O3': [(0, 1)]}, {'O3': [(0, 1)]}, x_range=(0, 1))
{'phase_error': 0.0, 'mean_iou': 1.0, 'phase_iou': {'O3': 1.0}}

## `plot_phase_diagram`

源文件：[plotting.py](plotting.py)，第 38 行。

```python
plot_phase_diagram(x, eform, phase, is_stable, *, phase_hulls=False, phase_styles=None, point_size=28, stable_size=85, phase_hull_size=50, unstable_alpha=0.22, phase_hull_alpha=0.9, stable_alpha=0.95, hull_atol=1e-10, linewidth=1.6, edgewidth=1.2, xlabel='$\\mathregular{x}$ in $\\mathregular{Na_xTMO_2}$', ylabel='Formation energy (meV / formula unit)', figsize=(6.5, 4.8), ax=None, legend=True, font_family='Arial', font_size=13, xlim=None, ylim=None)
```

Plot supplied formation energies and global stability flags.

Parameters
----------
x, eform, phase, is_stable
    Equal-length nonempty 1D arrays (or pandas Series). x/eform must be
    finite real numbers, phase nonempty strings, is_stable booleans or 0/1.
    eform is used unchanged: supply a consistent energy normalization and
    set ylabel to its actual unit. Global stability is trusted, not inferred.
phase_hulls : bool
    Also compute each phase's lower hull, draw matching colored dashed
    lines, and make its hull points opaque without black edges. Globally
    stable points always take precedence (larger, black edges).
phase_styles : dict or None
    Per-phase overrides, e.g. {'O3': {'color': '#397CA5', 'marker': 's'}}.
    Missing properties use DEFAULT_PHASE_STYLES; unknown phases use X.
point_size, stable_size, phase_hull_size : float
    Scatter areas in points squared for ordinary, global stable, and
    non-global phase hull points. Non-hull points use unstable_alpha
    (0 transparent, 1 opaque).
font_family : str
    Font for axis labels, major tick labels, offset text and legend.
    Defaults to Arial; install the font on the rendering machine.
font_size : float
    Axis label, major tick label and legend size in points (default 13).
unstable_alpha, phase_hull_alpha, stable_alpha : float
    Opacity for ordinary, phase hull, and global stable points (0 to 1).
    Global stable points default to 0.95; the black hull line stays opaque.
xlim, ylim : tuple or None
    Optional (minimum, maximum) axis limits. None (default) leaves automatic
    scaling unchanged; on existing axes, any caller-set limits are retained.
hull_atol : float
    Absolute energy tolerance for highlighting points on a phase hull,
    including tied minima and collinear points. Same unit as eform.
    The hull line itself uses the exact minima, without tolerance pruning.
linewidth, edgewidth : float
    Hull line and global stable marker edge widths in points.
ax : matplotlib.axes.Axes or None
    Existing axes, or create a figure with figsize (inches).

Returns
-------
(figure, axes)
    Caller owns saving/showing/closing. Global stable points are connected
    in increasing x with a black solid line; at duplicate x the lowest
    marked energy is used for the line, while all marked points are shown.
    Zero marked points produces no global line; one produces only a marker.
    A one-composition phase has markers but no dashed segment.

Notes
-----
No energy conversion, phase identification, files, randomness or input
mutation. Global points/line render above phase hull points/lines, which
render above other structures. Only left/bottom major ticks are shown.
Calls add artists to ax. Metrics still need only NumPy;
Matplotlib is needed only when this function is called.

