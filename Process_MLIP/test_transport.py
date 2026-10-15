import csv
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from Process_MLIP import fit_msd
from Process_MLIP.test_md_example import MDExampleTests as _ExampleHarness
from Process_MLIP.examples import mlip_md as example


class TransportTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(dir=Path(__file__).parent, prefix='tmp_transport_')
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
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
        self.write(slope=-1)
        with self.assertRaises(ValueError):
            self.fit()
        self.write(slope=0)
        row = self.fit()['results'][0]
        self.assertEqual(row['diffusion_m2_s'], 0)
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


class TransportExampleTests(unittest.TestCase):
    setUp = _ExampleHarness.setUp
    run_example = _ExampleHarness.run_example
    def test_transport_integration(self):
        # Fits a short EMT trajectory only to test plumbing, not diffusion physics.
        config = dict(enabled=True, fit_start_ps=0, fit_end_ps=0.0015,
                      ion_charge=1, output_json=None, overwrite=False)
        with patch.object(example, 'TRANSPORT_FIT', config):
            text = self.run_example(dict(enabled=True, species='Cu'))
        self.assertIn('Transport:', text)
        path = self.root / 'md' / '02_final' / 'transport.json'
        result = json.loads(path.read_text())
        self.assertEqual(result['temperature_K'], 300)
        self.assertAlmostEqual(result['volume_A3'], 3.6**3)

    def test_requires_msd_before_model_loading(self):
        with patch.object(example, 'TRANSPORT_FIT', dict(enabled=True)):
            with self.assertRaises(ValueError):
                self.run_example(dict(enabled=False))
        self.loader.assert_not_called()

    def test_invalid_fit_window_before_model_loading(self):
        with patch.object(example, 'TRANSPORT_FIT', dict(enabled=True,
                          fit_start_ps=2, fit_end_ps=8, ion_charge=1)):
            with self.assertRaises(ValueError):
                self.run_example(dict(enabled=True, species='Cu'))
        self.loader.assert_not_called()


del _ExampleHarness

if __name__ == '__main__':
    unittest.main()
