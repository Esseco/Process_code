"""Check shared matching semantics and legacy exports."""
import unittest
import pandas as pd
from pymatgen.core import Lattice, Structure
from Process_Struct import deduplicate, deduplicate_dict, deduplicate_df


class DeduplicationTests(unittest.TestCase):
    def test_compatibility_and_order(self):
        from Process_Vasp import deduplicate as old
        self.assertIs(old, deduplicate)
        s = Structure(Lattice.cubic(4), ["Na"], [[0, 0, 0]])
        duplicate = s.copy()
        duplicate.translate_sites([0], [.2, .3, .4])
        different = Structure(Lattice.cubic(4), ["Li"], [[0, 0, 0]])
        unique = deduplicate([s, duplicate, different])
        self.assertEqual(len(unique), 2)
        self.assertIsNot(unique[0], s)
        grouped = deduplicate_dict({"first": [s], "second": [duplicate], "third": [different]})
        self.assertEqual(list(grouped), ["first", "third"])
        df = pd.DataFrame({"struct": [s, duplicate, different],
                           "energy_mean_per_atom": [2., 1., 3.]})
        result = deduplicate_df(df, n_keep=2)
        self.assertEqual(result.index.tolist(), [1, 2])


if __name__ == "__main__":
    unittest.main()
