"""Small synthetic geometry/style checks; outputs live only in TemporaryDirectory."""

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.colors import to_rgba
import numpy as np

from Process_Phasediagram import DEFAULT_PHASE_STYLES, plot_phase_diagram
from Process_Phasediagram.plotting import _phase_hull


class PhasePlotTests(unittest.TestCase):
    def tearDown(self):
        plt.close("all")

    def test_lower_hull_duplicates_ties_and_degenerate(self):
        x = np.array([1, 0.5, 0, 0.5, 0.5, 0.25])
        e = np.array([0, -2, 0, -1, -2, -1])
        vertices, on_hull = _phase_hull(x, e, 1e-10)
        np.testing.assert_array_equal(x[vertices], [0, 0.5, 1])
        np.testing.assert_array_equal(on_hull, [True, True, True, False, True, True])
        for xs, es, expected in (([0], [1], [True]), ([0, 1], [0, 0], [True, True]),
                                 ([0, 0.5, 1], [0, 0, 0], [True] * 3),
                                 ([0, 0], [1, 2], [True, False])):
            _, mask = _phase_hull(np.array(xs), np.array(es), 0)
            np.testing.assert_array_equal(mask, expected)

    def test_global_flags_styles_and_no_mutation(self):
        x = np.array([1, 0.5, 0, 0.25])
        e = np.array([0, -2, 0, -0.5])
        before = e.copy()
        styles = {"O3": {"color": "purple", "marker": "D"}}
        fig, ax = plot_phase_diagram(x, e, ["O3"] * 4, [1, 1, 1, 0], phase_styles=styles)
        self.assertEqual(len(ax.lines), 1)
        np.testing.assert_array_equal(ax.lines[0].get_xdata(), [0, 0.5, 1])
        self.assertEqual(ax.lines[0].get_color(), "black")
        faint, stable = ax.collections
        self.assertEqual(faint.get_alpha(), 0.22)
        self.assertEqual(stable.get_alpha(), 0.95)
        np.testing.assert_allclose(stable.get_edgecolors(), [to_rgba("black", 0.95)])
        np.testing.assert_allclose(stable.get_facecolors(), [to_rgba("purple", 0.95)])
        self.assertGreater(stable.get_sizes()[0], faint.get_sizes()[0])
        np.testing.assert_array_equal(e, before)
        self.assertEqual(DEFAULT_PHASE_STYLES["O3"]["marker"], "s")
        self.assertEqual(styles["O3"]["color"], "purple")
        self.assertIs(fig, ax.figure)

    def test_phase_lines_and_global_precedence(self):
        _, ax = plot_phase_diagram([0, 0.5, 1] * 2, [0, -2, 0, 1, -1, 1],
                                   ["O3"] * 3 + ["P3"] * 3, [1, 1, 1, 0, 0, 0],
                                   phase_hulls=True)
        dashed = [line for line in ax.lines if line.get_linestyle() == "--"]
        self.assertEqual(len(dashed), 2)
        self.assertEqual([line.get_color() for line in dashed],
                         [DEFAULT_PHASE_STYLES[p]["color"] for p in ("O3", "P3")])
        self.assertEqual(ax.collections[0].get_alpha(), 0.95)
        self.assertEqual(ax.collections[1].get_alpha(), 0.9)
        self.assertEqual(ax.collections[1].get_sizes()[0], 50)
        self.assertEqual(len(ax.collections[1].get_edgecolors()), 0)
        self.assertEqual(sum(len(c.get_offsets()) for c in ax.collections), 6)

    def test_font_major_ticks_and_phase_hull_size_override(self):
        with matplotlib.rc_context():
            before = list(matplotlib.rcParams["font.family"])
            fig, ax = plot_phase_diagram([0, 1], [0, 0], ["O3"] * 2, [0, 0],
                                        phase_hulls=True, phase_hull_size=60)
            fig.canvas.draw()
            self.assertEqual(ax.collections[0].get_sizes()[0], 60)
            self.assertEqual(len(ax.xaxis.get_minorticklocs()), 0)
            self.assertEqual(len(ax.yaxis.get_minorticklocs()), 0)
            for text in [ax.xaxis.label, ax.yaxis.label, *ax.get_xticklabels(),
                         *ax.get_yticklabels(), *ax.get_legend().get_texts()]:
                self.assertEqual(text.get_fontfamily(), ["Arial"])
                self.assertEqual(text.get_fontsize(), 13)
            for axis in (ax.xaxis, ax.yaxis):
                for tick in axis.get_major_ticks():
                    self.assertTrue(tick.tick1line.get_visible())
                    self.assertFalse(tick.tick2line.get_visible())
            self.assertEqual(matplotlib.rcParams["font.family"], before)

    def test_render_layer_order_and_stable_alpha_override(self):
        _, ax = plot_phase_diagram([0, 0.5, 1, 0.5], [0, -1, 0, 1], ["O3"] * 4,
                                   [1, 0, 1, 0], phase_hulls=True, stable_alpha=0.8)
        ordinary, phase, globally_stable = ax.collections
        phase_line, global_line = ax.lines
        self.assertLess(ordinary.get_zorder(), phase_line.get_zorder())
        self.assertLess(phase_line.get_zorder(), phase.get_zorder())
        self.assertLess(phase.get_zorder(), global_line.get_zorder())
        self.assertLess(global_line.get_zorder(), globally_stable.get_zorder())
        self.assertEqual(globally_stable.get_alpha(), 0.8)

    def test_axis_limits_auto_explicit_and_existing_axes(self):
        args = ([0, 1], [-2, 0], ["O3"] * 2, [1, 1])
        _, ax = plot_phase_diagram(*args)
        self.assertTrue(ax.get_autoscalex_on())
        self.assertTrue(ax.get_autoscaley_on())
        self.assertLess(ax.get_xlim()[0], 0)
        self.assertGreater(ax.get_xlim()[1], 1)
        _, ax = plot_phase_diagram(*args, xlim=(0, 1), ylim=(-3, 1))
        np.testing.assert_allclose(ax.get_xlim(), [0, 1])
        np.testing.assert_allclose(ax.get_ylim(), [-3, 1])
        plot_phase_diagram(*args, ax=ax)
        np.testing.assert_allclose(ax.get_xlim(), [0, 1])
        np.testing.assert_allclose(ax.get_ylim(), [-3, 1])

    def test_all_default_phases_existing_axes_and_empty_stability(self):
        labels = list(DEFAULT_PHASE_STYLES) + ["custom"]
        fig, ax = plt.subplots()
        result = plot_phase_diagram(range(len(labels)), [0] * len(labels), labels,
                                    [False] * len(labels), ax=ax, phase_hulls=True)
        self.assertIs(result[1], ax)
        self.assertEqual(len(ax.lines), 0)
        fig.canvas.draw()

    def test_global_flags_are_trusted_and_duplicate_x_only_deduplicates_line(self):
        _, ax = plot_phase_diagram([1, 0.5, 0, 0.5, 0.25], [0, 2, 0, 3, -9],
                                   ["O3"] * 5, [1, 1, 1, 1, 0])
        np.testing.assert_array_equal(ax.lines[0].get_ydata(), [0, 2, 0])
        self.assertEqual(len(ax.collections[-1].get_offsets()), 4)

    def test_invalid_data(self):
        valid = ([0, 1], [0, 0], ["O3", "P3"], [True, False])
        for position, value in ((0, []), (0, [0, np.inf]), (1, [0, np.nan]),
                                (1, [0, 1j]), (2, ["", "O3"]), (2, [None, "O3"]),
                                (3, ["False", "True"]), (3, [0, np.nan]), (3, [0, 2]),
                                (0, [[0, 1]])):
            args = list(valid)
            args[position] = value
            with self.subTest(position=position, value=value), self.assertRaises(ValueError):
                plot_phase_diagram(*args)

    def test_package_import_does_not_load_matplotlib(self):
        subprocess.run([sys.executable, "-B", "-c",
                        "import sys; import Process_Phasediagram; assert 'matplotlib' not in sys.modules"],
                       check=True)

    def test_example_demo_csv_export_and_protection(self):
        path = Path(__file__).resolve().parents[1] / "Process_Phasediagram/examples/plot_phase_diagram.py"
        spec = importlib.util.spec_from_file_location("phase_plot_example", path)
        example = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(example)
        with tempfile.TemporaryDirectory(dir=path.parents[2]) as directory:
            folder = Path(directory)
            example.OUTPUT = folder / "demo.png"
            example.main()
            self.assertGreater(example.OUTPUT.stat().st_size, 1000)
            with self.assertRaises(FileExistsError):
                example.main()
            example.INPUT_CSV = folder / "input.csv"
            example.INPUT_CSV.write_text("Na_content,eform,phase,is_stable\n0,0,O3,True\n0.5,-1,P3,False\n1,0,O3,True\n")
            example.OUTPUT = folder / "csv.pdf"
            example.main()
            self.assertTrue(example.OUTPUT.read_bytes().startswith(b"%PDF"))
            example.OUTPUT = example.INPUT_CSV
            example.OVERWRITE = True
            with self.assertRaisesRegex(ValueError, "INPUT_CSV"):
                example.main()


if __name__ == "__main__":
    unittest.main()
