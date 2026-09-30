from pymatgen.core import Composition
import pandas as pd

def calc_formation_energy(df, comp_col, energy_col, fix_ion=None, ion=None, calc_voltage=False):
    df = df.copy()
    raw = df[comp_col].apply(Composition)

    if ion is None:
        ion = "Na" if any(c["Na"] > 0 for c in raw) else "Li"

    if ion not in ["Na", "Li"]:
        raise ValueError("目前只支持 Na 和 Li 脱嵌")

    ion_energy = {"Na": -1.288, "Li": -2.00}[ion]

    if fix_ion is None:
        fix_el = next(el for el in ["O", "S", "Cl", "F", "N", "C"] if any(c[el] > 0 for c in raw))
        vals = [c[fix_el] for c in raw if c[fix_el] > 0]
        fix_num = min(vals)
    else:
        fix = Composition(fix_ion)
        fix_el, fix_num = list(fix.items())[0]

    def norm_formula(c):
        if c[fix_el] == 0:
            raise ValueError(f"{c.formula} 中不存在 {fix_el}")
        return c * (fix_num / c[fix_el])

    comps = raw.apply(norm_formula)
    df["formula_norm"] = comps.apply(lambda c: c.formula.replace(" ", ""))
    df["x"] = comps.apply(lambda c: c[ion])
    df["energy_formula"] = [e*c.num_atoms for e, c in zip(df[energy_col], comps)]

    xmin, xmax = df["x"].min(), df["x"].max()
    if xmax == xmin:
        df["E_form"] = 0.0
    else:
        Emin = df.loc[df["x"].eq(xmin), "energy_formula"].min()
        Emax = df.loc[df["x"].eq(xmax), "energy_formula"].min()
        f = (df["x"] - xmin) / (xmax - xmin)
        df["E_form"] = df["energy_formula"] - (f*Emax + (1-f)*Emin)
        df.loc[df["x"].isin([xmin, xmax]), "E_form"] = 0

    if not calc_voltage:
        return {"ehull_df": df}

    d = df.loc[df.groupby("x")["energy_formula"].idxmin()].sort_values("x", ascending=False).reset_index(drop=True)
    rows, points = [], []

    for i in range(len(d)-1):
        x1, x2 = d.loc[i, "x"], d.loc[i+1, "x"]
        E1, E2 = d.loc[i, "energy_formula"], d.loc[i+1, "energy_formula"]
        dx = x1 - x2
        if dx == 0:
            continue

        voltage = -(E1 - E2 - dx*ion_energy) / dx

        rows.append({
            "ion": ion,
            "x_start": x1,
            "x_end": x2,
            "formula_start": d.loc[i, "formula_norm"],
            "formula_end": d.loc[i+1, "formula_norm"],
            "delta_x": dx,
            "voltage": voltage
        })

        points += [{"x": x1, "voltage": voltage},
                   {"x": x2, "voltage": voltage}]

    return {
        "ehull_df": df,
        "vol_df": pd.DataFrame(rows),
        "vol_points": pd.DataFrame(points)
    }