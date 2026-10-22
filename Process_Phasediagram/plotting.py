"""Composition–formation-energy plots; Matplotlib is imported only when plotting."""

import numpy as np


DEFAULT_PHASE_STYLES = {
    "O3": {"color": "#397CA5", "marker": "s"},
    "P3": {"color": "#F24B5B", "marker": "^"},
    "P2": {"color": "#E7A33E", "marker": "v"},
    "O2": {"color": "#8172B2", "marker": "o"},
    "OP2": {"color": "#1B9E77", "marker": "D"},
    "OP4": {"color": "#C77AA2", "marker": "p"},
    "O1": {"color": "#7B8585", "marker": "h"},
    "X": {"color": "#AD8C63", "marker": "X"},
}


def _phase_hull(x, energy, atol):
    # One minimum per composition; monotone chain also handles 1/2/collinear points.
    order = np.lexsort((energy, x))
    order = order[np.r_[True, np.diff(x[order]) != 0]]
    lower = []
    for i in order:
        while len(lower) >= 2:
            a, b = lower[-2:]
            cross = (x[b] - x[a]) * (energy[i] - energy[a]) - (
                energy[b] - energy[a]
            ) * (x[i] - x[a])
            if cross > 0:
                break
            lower.pop()
        lower.append(i)
    lower = np.asarray(lower, dtype=int)
    on_hull = np.isclose(energy, np.interp(x, x[lower], energy[lower]), rtol=0, atol=atol)
    return lower, on_hull


def plot_phase_diagram(
    x, eform, phase, is_stable, *, phase_hulls=False, phase_styles=None,
    point_size=28, stable_size=85, phase_hull_size=50,
    unstable_alpha=0.22, phase_hull_alpha=0.9, stable_alpha=0.95,
    hull_atol=1e-10, linewidth=1.6, edgewidth=1.2,
    xlabel=r"$\mathregular{x}$ in $\mathregular{Na_xTMO_2}$", ylabel="Formation energy (meV / formula unit)",
    figsize=(6.5, 4.8), ax=None, legend=True, font_family="Arial", font_size=13,
    xlim=None, ylim=None,
):
    """Plot supplied formation energies and global stability flags.

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
    """
    from matplotlib import pyplot as plt
    from matplotlib.lines import Line2D

    raw_x, raw_energy = np.asarray(x), np.asarray(eform)
    if np.iscomplexobj(raw_x) or np.iscomplexobj(raw_energy):
        raise ValueError("x and eform must be real")
    x, energy = np.asarray(x, dtype=float), np.asarray(eform, dtype=float)
    phases, stable = np.asarray(phase, dtype=object), np.asarray(is_stable)
    arrays = (x, energy, phases, stable)
    if any(a.ndim != 1 for a in arrays) or not len(x) or any(a.shape != x.shape for a in arrays):
        raise ValueError("inputs must be equal-length nonempty 1D arrays")
    if not np.isfinite(x).all() or not np.isfinite(energy).all():
        raise ValueError("x and eform must be finite")
    if any(not isinstance(p, str) or not p.strip() for p in phases):
        raise ValueError("phase must contain nonempty strings")
    if stable.dtype.kind not in "biuf" or not np.isin(stable, [0, 1]).all():
        raise ValueError("is_stable must contain booleans or numeric 0/1")
    stable = stable.astype(bool)
    for name, value in (("point_size", point_size), ("stable_size", stable_size),
                        ("phase_hull_size", phase_hull_size),
                        ("linewidth", linewidth), ("edgewidth", edgewidth),
                        ("font_size", font_size)):
        if not np.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be finite and positive")
    for value in (unstable_alpha, phase_hull_alpha, stable_alpha):
        if not np.isfinite(value) or not 0 <= value <= 1:
            raise ValueError("alpha must be between 0 and 1")
    if not np.isfinite(hull_atol) or hull_atol < 0:
        raise ValueError("hull_atol must be finite and nonnegative")

    # Prepare styles and phase hulls before creating any artists.
    labels = [p for p in DEFAULT_PHASE_STYLES if p in phases]
    labels += sorted(set(phases) - set(labels))
    groups = []
    for label in labels:
        style = {**DEFAULT_PHASE_STYLES.get(label, DEFAULT_PHASE_STYLES["X"]),
                 **(phase_styles or {}).get(label, {})}
        indices = np.flatnonzero(phases == label)
        vertices, on_hull = _phase_hull(x[indices], energy[indices], hull_atol) if phase_hulls else (
            np.array([], dtype=int), np.zeros(len(indices), dtype=bool)
        )
        groups.append((label, style, indices, vertices, on_hull))

    if ax is None:
        _, ax = plt.subplots(figsize=figsize, layout="constrained")
    handles = []
    for label, style, indices, vertices, on_hull in groups:
        color, marker = style["color"], style["marker"]
        for mask, alpha, size, edge, width, zorder in (
            (~stable[indices] & ~on_hull, unstable_alpha, point_size, "none", 0, 1),
            (~stable[indices] & on_hull, phase_hull_alpha, phase_hull_size, "none", 0, 3),
            (stable[indices], stable_alpha, stable_size, "black", edgewidth, 5),
        ):
            selected = indices[mask]
            if len(selected):
                ax.scatter(x[selected], energy[selected], s=size, c=color, marker=marker,
                           alpha=alpha, edgecolors=edge, linewidths=width, zorder=zorder)
        if phase_hulls and len(vertices) > 1:
            selected = indices[vertices]
            ax.plot(x[selected], energy[selected], color=color, linestyle="--",
                    linewidth=linewidth, zorder=2)
        handles.append(Line2D([], [], color=color, marker=marker, linestyle="none", label=label))
    selected = np.flatnonzero(stable)
    selected = selected[np.lexsort((energy[selected], x[selected]))]
    selected = selected[np.r_[True, np.diff(x[selected]) != 0]] if len(selected) else selected
    if len(selected) > 1:
        ax.plot(x[selected], energy[selected], color="black", linewidth=linewidth, zorder=4)
        handles.append(Line2D([], [], color="black", linewidth=linewidth, label="Global hull"))
    if phase_hulls:
        handles.append(Line2D([], [], color="0.4", linestyle="--", label="Phase hulls"))
    ax.set(xlabel=xlabel, ylabel=ylabel)
    if xlim is not None:
        ax.set_xlim(xlim)
    if ylim is not None:
        ax.set_ylim(ylim)
    ax.minorticks_off()
    ax.tick_params(which="major", direction="in", bottom=True, left=True,
                   top=False, right=False, labelbottom=True, labelleft=True,
                   labeltop=False, labelright=False, labelsize=font_size)
    for text in [ax.xaxis.label, ax.yaxis.label, ax.xaxis.get_offset_text(),
                 ax.yaxis.get_offset_text(), *ax.get_xticklabels(), *ax.get_yticklabels()]:
        text.set_fontfamily(font_family)
        text.set_fontsize(font_size)
    for spine in ax.spines.values():
        spine.set_linewidth(1.1)
    if legend:
        ax.legend(handles=handles, frameon=False, loc="upper left", bbox_to_anchor=(1.02, 1),
                  prop={"family": font_family, "size": font_size})
    return ax.figure, ax
