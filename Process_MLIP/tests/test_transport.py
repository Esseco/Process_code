"""扩散系数/导率拟合及单位换算。"""
import csv
import json
import unittest
from unittest.mock import Mock, patch

import numpy as np
from pymatgen.analysis.diffusion.analyzer import get_diffusivity_from_msd

from Process_MLIP import fit_msd
from Process_MLIP.tests._support import TemporaryDirectoryMixin


class TransportTests(TemporaryDirectoryMixin, unittest.TestCase):
    def setUp(self):
        self.root = self.make_temp_directory()
        self.source = self.root / 'msd.csv'
        self.write()

    def write(self, slope=6):
        with self.source.open('w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['segment','species','atom_count','time_ps','msd_x_A2','msd_y_A2','msd_z_A2','msd_total_A2'])
            for segment in (1, 2):
                for species, n in [('Na', 2), ('Li', 1)]:
                    for t in [0, 1, 2, 4, 5]:
                        a = 20 + slope * t / 3
                        w.writerow([segment, species, n, t, a, a, a, 3*a])

    def fit(self, **kw):
        config = dict(fit_start_ps=1, fit_end_ps=5, temperature_K=800,
                      volume_A3=1000, ion_charge={'Na': 1, 'Li': 2})
        config.update(kw)
        return fit_msd(self.source, **config)

    def test_analytic_units_free_intercept_segments_and_charge(self):
        result = self.fit(output_json=self.root / 'transport.json')
        self.assertEqual(len(result['results']), 4)
        rows = {r['species']: r for r in result['results']}
        for row in rows.values():
            self.assertAlmostEqual(row['diffusion_m2_s'], 1e-8)
            self.assertAlmostEqual(row['diffusion_cm2_s'], 1e-4)
            self.assertAlmostEqual(row['intercept_A2']['total'], 60)
            self.assertEqual(row['r_squared']['total'], 1)
            self.assertEqual(row['samples'], 4)
        expected = 2 / 1e-27 * (1.602176634e-19)**2 * 1e-8 / (1.380649e-23 * 800)
        self.assertAlmostEqual(rows['Na']['conductivity_NE_S_m'], expected)
        self.assertAlmostEqual(rows['Li']['conductivity_NE_S_m'], 2 * expected)
        self.assertAlmostEqual(result['conductivity_NE_sum_S_m']['1'], 3 * expected)
        self.assertEqual(json.loads((self.root / 'transport.json').read_text()), result)
        self.assertAlmostEqual(self.fit(species='Na', ion_charge=-1)['results'][0]['conductivity_NE_S_m'], expected)

    def test_invalid_and_protected_outputs(self):
        for kw in [dict(fit_start_ps=5), dict(fit_end_ps=6), dict(fit_end_ps=2, fit_start_ps=1),
                   dict(temperature_K=0), dict(volume_A3=float('nan')), dict(ion_charge=0),
                   dict(ion_charge={'Na':1}), dict(species='O'), dict(overwrite=1)]:
            with self.subTest(kw=kw), self.assertRaises((ValueError, TypeError)):
                self.fit(**kw)
        with self.assertRaises(ValueError):
            self.fit(output_json=self.source, overwrite=True)
        path = self.root / 'out.json'
        path.write_text('keep')
        with self.assertRaises(FileExistsError):
            self.fit(output_json=path)
        self.assertEqual(path.read_text(), 'keep')

    def test_nonphysical_negative_and_zero_slope(self):
        for slope in (-1, 0):
            with self.subTest(slope=slope):
                self.write(slope=slope)
                row = self.fit()['results'][0]
                np.testing.assert_allclose(row['diffusion_m2_s'], 1e-15/60*1e-4,
                                           rtol=1e-12, atol=0)
                self.assertTrue(row['pymatgen_slope_floor_applied']['total'])
                if slope == 0:
                    self.assertIsNone(row['r_squared']['total'])

    def test_malformed_data_rejected(self):
        original = self.source.read_text()
        for old, new in [('1,Na,2,1,', '1,Na,3,1,'),
                         ('1,Na,2,1,', '1,Na,2,0,'),
                         ('1,Na,2,0,20.0', '1,Na,2,0,nan')]:
            with self.subTest(new=new):
                self.source.write_text(original.replace(old, new))
                with self.assertRaises(ValueError):
                    self.fit()

    def write_noisy_curve(self):
        with self.source.open('w', newline='') as handle:
            writer = csv.writer(handle)
            writer.writerow(['segment','species','atom_count','time_ps',
                             'msd_x_A2','msd_y_A2','msd_z_A2','msd_total_A2'])
            for time, noise in zip([0, 1, 2, 4, 5], [500, 0, 2, 15, 40]):
                total = 60 + 6*time + noise
                writer.writerow([1, 'Na', 2, time, total/6, total/3, total/2, total])

    def test_default_calls_native_weighted_fit_on_manual_window_in_fs(self):
        self.write_noisy_curve()
        native = Mock(wraps=get_diffusivity_from_msd)
        with patch('Process_MLIP.transport._load_pymatgen_fitter',
                   return_value=native) as loader:
            result = self.fit(species='Na', ion_charge=1, fit_end_ps=4)
        loader.assert_called_once()
        time = np.array([1, 2, 4], dtype=float)
        values = np.array([66, 74, 99], dtype=float)
        self.assertEqual(native.call_count, 4)  # Cartesian axes, then total
        np.testing.assert_array_equal(native.call_args.args[0], values)
        np.testing.assert_array_equal(native.call_args.args[1], time*1000)
        self.assertEqual(native.call_args.kwargs, {})  # All native defaults
        expected, _ = get_diffusivity_from_msd(values, time*1000, smoothed='max')
        row = result['results'][0]
        self.assertEqual(result['fit_method'], 'pymatgen')
        self.assertEqual(row['actual_fit_range_ps'], [1, 4])
        self.assertEqual(row['samples'], 3)
        np.testing.assert_allclose(row['diffusion_cm2_s'], expected, rtol=1e-12)
        design = np.column_stack([time, np.ones(3)])
        root_weights = np.sqrt(1/time)
        slope, intercept = np.linalg.lstsq(design*root_weights[:, None],
                                           values*root_weights, rcond=None)[0]
        self.assertAlmostEqual(row['slope_A2_per_ps']['total'], slope)
        self.assertAlmostEqual(row['intercept_A2']['total'], intercept)
        np.testing.assert_allclose(row['directional_diffusion_m2_s'],
                                   slope*np.array([1/6, 1/3, 1/2])/2*1e-8)
        ols_slope = np.linalg.lstsq(design, values, rcond=None)[0][0]
        self.assertNotAlmostEqual(row['slope_A2_per_ps']['total'],
                                 ols_slope)

    def test_native_defaults_used_for_all_species_and_segments(self):
        native = Mock(wraps=get_diffusivity_from_msd)
        with patch('Process_MLIP.transport._load_pymatgen_fitter',
                   return_value=native):
            self.fit()
        self.assertEqual(native.call_count, 16)
        for call in native.call_args_list:
            self.assertEqual(call.kwargs, {})
            np.testing.assert_array_equal(call.args[1], [1000, 2000, 4000, 5000])

    def test_weighted_zero_lag_and_missing_dependency(self):
        with self.assertRaisesRegex(ValueError, 'positive lag'):
            self.fit(fit_start_ps=0)
        with patch.dict('sys.modules', {'pymatgen.analysis.diffusion.analyzer': None}):
            with self.assertRaisesRegex(ImportError, 'pymatgen-analysis-diffusion'):
                self.fit(output_json=self.root/'missing.json')
        self.assertFalse((self.root/'missing.json').exists())

    def test_tiny_positive_slope_uses_native_floor(self):
        with self.source.open('w', newline='') as handle:
            writer = csv.writer(handle)
            writer.writerow(['segment','species','atom_count','time_ps',
                             'msd_x_A2','msd_y_A2','msd_z_A2','msd_total_A2'])
            for time in [1, 2, 3, 5]:
                value = time * 1e-14
                writer.writerow([1, 'Na', 2, time, value, value, value, 3*value])
        row = self.fit(species='Na', fit_end_ps=5)['results'][0]
        np.testing.assert_allclose(row['diffusion_m2_s'], 1e-15/60*1e-4, rtol=1e-12, atol=0)
        self.assertTrue(row['pymatgen_slope_floor_applied']['total'])

    def test_negative_direction_uses_native_floor_and_conductivity_uses_total(self):
        with self.source.open('w', newline='') as handle:
            writer = csv.writer(handle)
            writer.writerow(['segment','species','atom_count','time_ps',
                             'msd_x_A2','msd_y_A2','msd_z_A2','msd_total_A2'])
            for time in [1, 2, 4, 5]:
                writer.writerow([1, 'Na', 2, time, 10-time, 2*time, 3*time, 10+4*time])
        row = self.fit(species='Na')['results'][0]
        self.assertLess(row['slope_A2_per_ps']['x'], 0)
        np.testing.assert_allclose(row['directional_diffusion_m2_s'][0], 1e-15/60*3e-4,
                                   rtol=1e-12, atol=0)
        self.assertTrue(row['pymatgen_slope_floor_applied']['x'])
        expected, _ = get_diffusivity_from_msd(np.array([14,18,26,30]),
                                              np.array([1000,2000,4000,5000]))
        np.testing.assert_allclose(row['diffusion_m2_s'], expected*1e-4)

    def test_omitted_bounds_use_all_positive_lags_and_record_actual_ranges(self):
        output = self.root/'automatic.json'
        result = fit_msd(self.source, temperature_K=800, volume_A3=1000,
                         ion_charge=1, output_json=output)
        self.assertEqual(result['fit_range_ps'], [None, None])
        for row in result['results']:
            self.assertEqual(row['actual_fit_range_ps'], [1, 5])
            self.assertEqual(row['samples'], 4)  # zero lag is not fitted
            np.testing.assert_allclose(row['diffusion_m2_s'], 1e-8)
        self.assertEqual(json.loads(output.read_text()), result)

    def test_none_on_one_side_preserves_manual_other_bound(self):
        for start, end, expected in ((None, 4, [1, 4]), (2, None, [2, 5]),
                                     (1, 4, [1, 4])):
            with self.subTest(start=start, end=end):
                result = self.fit(fit_start_ps=start, fit_end_ps=end)
                self.assertEqual(result['results'][0]['actual_fit_range_ps'], expected)
                self.assertEqual(result['results'][0]['samples'], 3)

    def test_automatic_ranges_are_resolved_per_species_and_segment(self):
        with self.source.open('w', newline='') as handle:
            writer = csv.writer(handle)
            writer.writerow(['segment','species','atom_count','time_ps',
                             'msd_x_A2','msd_y_A2','msd_z_A2','msd_total_A2'])
            for segment in (1, 2):
                for species, times in [('Na', [0, 1, 2, 4, 5]), ('Li', [0, 2, 3, 4])]:
                    for original_time in times:
                        time = original_time * segment
                        axis = 20 + 2*time
                        writer.writerow([segment, species, 1, time, axis, axis, axis, 3*axis])
        result = self.fit(fit_start_ps=None, fit_end_ps=None)
        for row in result['results']:
            expected = [1, 5] if row['species']=='Na' else [2, 4]
            self.assertEqual(row['actual_fit_range_ps'], [t*row['segment'] for t in expected])

    def test_invalid_optional_bounds_and_too_few_points_do_not_write(self):
        output = self.root/'bad.json'
        for start, end in ((None, 1), (5, None), (6, None), (None, 0),
                           (float('nan'), None), (None, float('inf')), (True, None)):
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                self.fit(fit_start_ps=start, fit_end_ps=end, output_json=output)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
