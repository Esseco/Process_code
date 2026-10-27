"""Headless, separate speed curves and standard pymatgen phase diagrams."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt


def speed_plots(rows, root, stage):
    """Separate curves per stage; same atom count replicates remain separate points."""
    metrics = [("elapsed_seconds", "Elapsed time (s)"),
               ("peak_gpu_allocated_MiB", "Peak CUDA allocated memory (MiB)")]
    metrics += ([("optimization_steps", "Optimization steps"),
                 ("force_evaluations", "Force evaluations")]
                if stage == "relax" else [("steps_per_second", "MD steps / s")])
    for key, label in metrics:
        path = Path(root) / f"{stage}_{key}.png"
        path.unlink(missing_ok=True)
        fig, ax = plt.subplots(figsize=(6.4, 4.2), layout="constrained")
        plotted = False
        for model_id in sorted({row["model_id"] for row in rows}):
            points = sorted((row for row in rows if row["model_id"] == model_id
                             and row["status"] == "completed" and row.get(key) is not None),
                            key=lambda row: row["natoms"])
            if points:
                ax.plot([row["natoms"] for row in points], [row[key] for row in points],
                        "o-", label=model_id)
                plotted = True
        if plotted:
            ax.set(xlabel="Number of atoms", ylabel=label, title=f"{stage}: {label}")
            ax.legend()
            ax.grid(alpha=0.2)
            fig.savefig(path, dpi=180)
        plt.close(fig)


def phase_plot(diagram, root, rows):
    """Plot <=4-component hulls; always provide an ID/Ehull plot for any dimension."""
    from pymatgen.analysis.phase_diagram import PDPlotter
    files = []
    if len(diagram.elements) <= 4:
        ax = PDPlotter(diagram, backend="matplotlib", show_unstable=1000).get_plot()
        path = Path(root) / "phase_diagram.png"
        ax.figure.savefig(path, dpi=180, bbox_inches="tight")
        plt.close(ax.figure)
        files.append(str(path))
    fig, ax = plt.subplots(figsize=(max(6, min(len(rows) * 0.25, 16)), 4.2), layout="constrained")
    x = list(range(len(rows)))
    ax.scatter(x, [row["ehull_eV_per_atom"] for row in rows], label="MLIP")
    matched = [(i, row["reference_ehull_eV_per_atom"]) for i, row in enumerate(rows)
               if row.get("reference_ehull_eV_per_atom") is not None]
    if matched:
        ax.scatter([i for i, _ in matched], [value for _, value in matched], marker="x", label="DFT")
    ax.set(xlabel="Structure ID", ylabel="Ehull (eV/atom)")
    ax.set_xticks(x, [row["structure_id"] for row in rows], rotation=90, fontsize=7)
    ax.legend()
    path = Path(root) / "ehull_by_id.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    files.append(str(path))
    return dict(files=files, phase_diagram_note=None if len(diagram.elements) <= 4 else
                "More than four elements: full composition hull is in phase_diagram.json; no geometric PNG")
