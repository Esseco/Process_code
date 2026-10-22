"""Analytic, synthetic checks; no project data or temporary outputs."""

import unittest

import numpy as np

from Process_Phasediagram import calculate_hull_error, calculate_phase_iou_error


class HullErrorTests(unittest.TestCase):
    def test_identical_and_no_mutation(self):
        hull = np.array([[1, 0], [0, 0], [0.5, -2.0]])
        before = hull.copy()
        self.assertEqual(calculate_hull_error(hull, hull)["hull_error"], 0)
        np.testing.assert_array_equal(hull, before)

    def test_triangle_and_energy_units(self):
        result = calculate_hull_error([[0, 0], [1, -4], [2, 0]], [[0, 0], [2, 0]])
        self.assertEqual(result, {"hull_error": 2.0, "integral_error": 4.0})

    def test_crossing_between_joint_vertices(self):
        # Difference at x=(0, 1/4, 3/4, 1) is (0, -2/3, 2/3, 0).
        # Exact triangle areas sum to 1/3; naive trapezoids would give 1/2.
        pred = [[0, 0], [0.25, -1], [1, 0]]
        ref = [[0, 0], [0.75, -1], [1, 0]]
        result = calculate_hull_error(pred, ref, return_curves=True)
        self.assertAlmostEqual(result["integral_error"], 1 / 3)
        np.testing.assert_array_equal(result["x"], [0, 0.25, 0.75, 1])
        self.assertEqual(calculate_hull_error(ref, pred)["hull_error"], result["hull_error"])

    def test_affine_invariance_and_columns(self):
        ref = np.array([[0, 0], [0.4, -3], [1, 0]])
        pred = {"x": ref[:, 0], "energy": ref[:, 1] + 7 + 13 * ref[:, 0]}
        self.assertAlmostEqual(calculate_hull_error(pred, ref)["hull_error"], 0)

    def test_common_coverage_and_interpolated_chords(self):
        pred = [[0, 0], [0.5, -2], [1, 0]]
        ref = [[0.25, 5], [0.75, 5]]
        result = calculate_hull_error(pred, ref, return_curves=True)
        self.assertAlmostEqual(result["hull_error"], 0.5)
        self.assertAlmostEqual(result["integral_error"], 0.25)
        np.testing.assert_array_equal(result["pred_relative_energy"], [0, -1, 0])
        subrange = calculate_hull_error(pred, ref, (0.3, 0.7))
        self.assertAlmostEqual(subrange["hull_error"], 0.4)
        self.assertAlmostEqual(subrange["integral_error"], 0.16)

    def test_collinear_and_tiny_nonconvex(self):
        self.assertEqual(calculate_hull_error([[0, 0], [0.5, 0], [1, 0]], [[0, 1], [1, 2]])["hull_error"], 0)
        with self.assertRaisesRegex(ValueError, "lower convex hull"):
            calculate_hull_error([[0, 0], [0.5, 1e-20], [1, 0]], [[0, 0], [1, 0]])

    def test_invalid_vertices(self):
        invalid = [[], [[0, 0]], [[0, 0], [0, 1]], [[0, 0], [0, 0]],
                   [[0, 0], [0.5, 1], [1, 0]], [[0, np.nan], [1, 0]],
                   [[0, 0], [np.inf, 0]], [[0, 1j], [1, 0]],
                   [[0, 0, 0], [1, 0, 0]], {"x": [0, 1]},
                   {"x": [0, 1], "energy": [0]}, {"x": [[0, 1]], "energy": [[0, 0]]}]
        for hull in invalid:
            for pred, ref in ((hull, [[0, 0], [1, 0]]), ([[0, 0], [1, 0]], hull)):
                with self.subTest(hull=hull), self.assertRaises(ValueError):
                    calculate_hull_error(pred, ref)

    def test_invalid_ranges(self):
        hull = [[0, 0], [1, 0]]
        for bounds in ((0, 0), (1, 0), (-0.1, 1), (0, 1.1), (0, np.nan), [0], [0, 1, 2]):
            with self.subTest(bounds=bounds), self.assertRaises(ValueError):
                calculate_hull_error(hull, hull, bounds)
        for ref in ([[1, 0], [2, 0]], [[2, 0], [3, 0]]):
            with self.assertRaises(ValueError):
                calculate_hull_error(hull, ref)


class PhaseIoUTests(unittest.TestCase):
    def score(self, pred, ref, delta=0, bounds=(0, 1)):
        return calculate_phase_iou_error(pred, ref, x_range=bounds, delta=delta)

    def test_identical_and_coexistence(self):
        phases = {"O3": [(0, 0.6)], "P3": [(0.3, 1)]}
        self.assertEqual(self.score(phases, phases), {
            "phase_error": 0.0, "mean_iou": 1.0, "phase_iou": {"O3": 1.0, "P3": 1.0}})

    def test_requested_example(self):
        ref = {"O3": [(0, 0.3)], "P3": [(0.3, 0.6)], "OP2": [(0.6, 1)]}
        pred = {"O3": [(0, 0.35)], "P3": [(0.35, 0.65)], "OP2": [(0.65, 1)]}
        result = self.score(pred, ref)
        expected = {"O3": 6 / 7, "P3": 5 / 7, "OP2": 7 / 8}
        for label, value in expected.items():
            self.assertAlmostEqual(result["phase_iou"][label], value)
        self.assertAlmostEqual(result["phase_error"], 1 - np.mean(list(expected.values())))

    def test_narrow_shift_and_delta(self):
        pred, ref = {"P3": [(0.51, 0.52)]}, {"P3": [(0.49, 0.50)]}
        for delta, expected in ((0, 0), (0.01, 0.2), (0.02, 3 / 7), (1, 1)):
            with self.subTest(delta=delta):
                self.assertAlmostEqual(self.score(pred, ref, delta)["mean_iou"], expected)

    def test_missing_phase_macro_average(self):
        pred = {"O3": [(0, 0.5)], "P3": [(0.5, 1)]}
        ref = {"O3": [(0, 0.5)]}
        self.assertEqual(self.score(pred, ref)["phase_iou"], {"O3": 1.0, "P3": 0.0})
        self.assertEqual(self.score(pred, ref)["phase_error"], 0.5)
        self.assertEqual(self.score({}, ref)["phase_error"], 1.0)

    def test_disconnected_overlap_touching_and_no_mutation(self):
        pred = {"O3": [(0.7, 0.9), (0, 0.2), (0.1, 0.3), (0.3, 0.4)]}
        ref = {"O3": [(0.2, 0.8)]}
        before = list(pred["O3"])
        self.assertAlmostEqual(self.score(pred, ref)["mean_iou"], 1 / 3)
        self.assertEqual(pred["O3"], before)
        # Expanded prediction: [0, .5] + [.6, 1]; reference: [.1, .9].
        self.assertAlmostEqual(self.score(pred, ref, 0.1)["mean_iou"], 0.7)

    def test_clip_and_expand_before_clipping(self):
        self.assertEqual(self.score({"O3": [(-2, 3)]}, {"O3": [(0, 1)]})["mean_iou"], 1)
        self.assertAlmostEqual(self.score({"O3": [(-0.2, -0.1)]}, {"O3": [(0, 0.1)]}, 0.2)["mean_iou"], 1 / 3)

    def test_empty_set_conventions(self):
        self.assertEqual(self.score({"O3": []}, {"O3": []})["mean_iou"], 1)
        self.assertEqual(self.score({"O3": [(2, 3)]}, {"O3": []})["mean_iou"], 1)
        self.assertEqual(self.score({"O3": []}, {})["mean_iou"], 0)
        self.assertEqual(self.score({"O3": []}, {"O3": [(0, 1)]})["mean_iou"], 0)
        with self.assertRaises(ValueError):
            self.score({}, {})

    def test_invalid_inputs(self):
        valid = {"O3": [(0, 1)]}
        for intervals in ([(0, 0)], [(1, 0)], [(2, 1)], [(0, np.nan)], [(0, np.inf)],
                          [(0, 1j)], [0, 1], [(0, 1, 2)]):
            with self.subTest(intervals=intervals), self.assertRaises(ValueError):
                self.score({"O3": intervals}, valid)
        for delta in (-0.1, np.nan, np.inf, [0.1], 1j):
            with self.subTest(delta=delta), self.assertRaises(ValueError):
                self.score(valid, valid, delta)
        for bounds in ((0, 0), (1, 0), (0, np.inf), [0]):
            with self.subTest(bounds=bounds), self.assertRaises(ValueError):
                self.score(valid, valid, bounds=bounds)
        for phases in ([], {1: [(0, 1)]}):
            with self.assertRaises(ValueError):
                self.score(phases, valid)


if __name__ == "__main__":
    unittest.main()
