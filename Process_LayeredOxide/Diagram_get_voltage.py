import pandas as pd
import numpy as np
from scipy.spatial import ConvexHull

def get_voltage(df, Na_col='Na_content', e_col='full_e', μ_Na=-1.3, keep_cols=None):
    """Calculate voltage from convex hull lower envelope.

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
    """
    df_min = df.loc[df.groupby(Na_col)[e_col].idxmin()].copy()
    df_sorted = df_min.sort_values(Na_col, ascending=True).reset_index(drop=True)
    points = df_sorted[[Na_col, e_col]].values

    if len(points) < 2:
        return pd.DataFrame()

    hull = ConvexHull(points)
    # Sort hull vertices by Na content so we can walk left-to-right
    hull_indices = np.array(hull.vertices)
    hull_indices = hull_indices[np.argsort(points[hull_indices, 0])]

    # Extract lower hull using Andrew monotone chain (keep indices)
    lower_idx = []
    for idx in hull_indices:
        p = points[idx]
        while len(lower_idx) >= 2:
            p1 = points[lower_idx[-2]]
            p2 = points[lower_idx[-1]]
            # Cross product <= 0  →  non-counter-clockwise → pop
            if (p2[0] - p1[0]) * (p[1] - p1[1]) <= (p2[1] - p1[1]) * (p[0] - p1[0]):
                lower_idx.pop()
            else:
                break
        lower_idx.append(idx)

    keep_cols = keep_cols or []
    base_cols = ['plot_Na', 'plot_V', 'Na_start', 'Na_end', 'voltage', 'capacity_step']
    out_cols = base_cols + keep_cols

    full_records = []
    for i in range(len(lower_idx) - 1):
        idx1, idx2 = lower_idx[i], lower_idx[i + 1]
        x1, e1 = points[idx1]
        x2, e2 = points[idx2]
        dx = x2 - x1

        if abs(dx) <= 1e-10:
            continue

        v = μ_Na - (e2 - e1) / dx  # voltage = μ_Na - dE/dx

        extra1 = [df_sorted[c].iloc[idx1] for c in keep_cols]
        extra2 = [df_sorted[c].iloc[idx2] for c in keep_cols]
        full_records.append([x1, v, x1, x2, v, dx] + extra1)
        full_records.append([x2, v, x1, x2, v, dx] + extra2)

    return pd.DataFrame(full_records, columns=out_cols)