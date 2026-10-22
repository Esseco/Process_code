"""Edit parameters below; run: python -m Process_Phasediagram.examples.plot_phase_diagram"""

from pathlib import Path

from Process_Phasediagram import plot_phase_diagram

# None uses small synthetic demo data. Set your CSV path to use real data.
INPUT_CSV = None  # Path("E:/data/formation_energy.csv")
X_COL = "Na_content"
EFORM_COL = "eform"
PHASE_COL = "phase"
STABLE_COL = "is_stable"  # CSV values: True/False or 1/0, no missing values

OUTPUT = Path("phase_diagram.png")  # PNG/PDF/SVG; None disables saving
OVERWRITE = False
SHOW = False
DPI = 300
PHASE_HULLS = True  # False: show only supplied global hull
PHASE_STYLES = {
    "O3": {"color": "#397CA5", "marker": "s"},
    "P3": {"color": "#F24B5B", "marker": "^"},
    # Add P2/O2/OP2/OP4/O1/X or new phase names here to override defaults.
}
PLOT_OPTIONS = {
    "point_size": 28, "phase_hull_size": 50, "stable_size": 85,
    "unstable_alpha": 0.22, "phase_hull_alpha": 0.9, "stable_alpha": 0.95,
    "hull_atol": 1e-10,  # same energy unit as EFORM_COL
    "linewidth": 1.6, "edgewidth": 1.2,
    "xlabel": r"$\mathregular{x}$ in $\mathregular{Na_xTMO_2}$",
    "ylabel": "Formation energy (meV / formula unit)",
    "figsize": (6.5, 4.8), "legend": True, "font_family": "Arial", "font_size": 13,
}
XLIM = None  # automatic; or e.g. (0, 1)
YLIM = None  # automatic; or e.g. (-420, 100)


def main():
    """Read the configured CSV or demo arrays, plot, and optionally save/show."""
    if OUTPUT is not None:
        if INPUT_CSV is not None and OUTPUT.resolve() == Path(INPUT_CSV).resolve():
            raise ValueError("OUTPUT must not overwrite INPUT_CSV")
        if OUTPUT.exists() and not OVERWRITE:
            raise FileExistsError(OUTPUT)
    if INPUT_CSV is None:
        # Synthetic values for demonstration only; eform is already meV/formula.
        x = [0, 0.25, 0.5, 0.75, 1] * 3
        energy = [0, -190, -330, -280, 0,
                  40, -150, -310, -350, 80,
                  10, -210, -290, -240, 50]
        phase = ["O3"] * 5 + ["P3"] * 5 + ["OP2"] * 5
        stable = [True, False, True, False, True,
                  False, False, False, True, False,
                  False, True, False, False, False]
        x += [0.25, 0.5, 0.75] * 3
        energy += [-130, -240, -200, -100, -230, -260, -120, -200, -150]
        phase += ["O3"] * 3 + ["P3"] * 3 + ["OP2"] * 3
        stable += [False] * 9
    else:
        import pandas as pd
        data = pd.read_csv(INPUT_CSV)
        x, energy, phase, stable = (data[c] for c in (X_COL, EFORM_COL, PHASE_COL, STABLE_COL))
    from matplotlib import pyplot as plt
    fig, ax = plot_phase_diagram(x, energy, phase, stable, phase_hulls=PHASE_HULLS,
                                phase_styles=PHASE_STYLES, xlim=XLIM, ylim=YLIM,
                                **PLOT_OPTIONS)
    try:
        if OUTPUT is not None:
            OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(OUTPUT, dpi=DPI, bbox_inches="tight")
        if SHOW:
            plt.show()
    finally:
        plt.close(fig)


if __name__ == "__main__":
    main()
