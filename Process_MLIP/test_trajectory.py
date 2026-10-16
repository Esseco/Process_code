"""轨迹抽帧：实际 ASE 写入/读回，不加载模型。"""
from pathlib import Path
import tempfile
import unittest

import numpy as np
from ase import Atoms
from ase.io import read
from ase.io.trajectory import Trajectory
from Process_MLIP import export_traj_frames


class TrajectoryExportTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent, prefix="tmp_frames_")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.root / "md.traj"
        self.images = []
        with Trajectory(str(self.source), "w") as writer:
            for i in range(4):
                atoms = Atoms("LiOLi", positions=[[i*.1, 0, 0], [1, 1, 1], [2, 2, 2]],
                              cell=[[5+i*.1, 0, 0], [1, 5, 0], [0, 0, 5]], pbc=True)
                atoms.set_momenta(np.ones((3, 3)) * (i+1))
                writer.write(atoms)
                self.images.append(atoms)

    def test_vasp_indices_geometry_and_atom_order(self):
        result = export_traj_frames(self.source, self.root / "out", [0, 2, -1])
        self.assertEqual(result["frame_indices"], [0, 2, 3])
        for index, path in zip(result["frame_indices"], result["structure_files"]):
            actual = read(path)
            np.testing.assert_allclose(actual.positions, self.images[index].positions, atol=1e-12)
            np.testing.assert_allclose(actual.cell, self.images[index].cell)
            self.assertEqual(actual.get_chemical_symbols(), ["Li", "O", "Li"])

    def test_default_last_all_slice_and_traj_momenta(self):
        beside = export_traj_frames(self.source)
        self.assertEqual(Path(beside["structure_files"][0]).parent, self.root.resolve())
        self.assertEqual(export_traj_frames(self.source, self.root/"last")["frame_indices"], [3])
        self.assertEqual(export_traj_frames(self.source, self.root/"all", None)["frame_indices"], [0,1,2,3])
        result = export_traj_frames(self.source, self.root/"slice", slice(None, None, -2), format="traj")
        self.assertEqual(result["frame_indices"], [3,1])
        for index, path in zip(result["frame_indices"], result["structure_files"]):
            np.testing.assert_allclose(read(path).get_momenta(), self.images[index].get_momenta())

    def test_other_formats(self):
        for fmt in ("cif", "xyz", "extxyz"):
            with self.subTest(format=fmt):
                result = export_traj_frames(self.source, self.root/fmt, 1, format=fmt)
                self.assertEqual(len(read(result["structure_files"][0])), 3)

    def test_invalid_selection_writes_nothing(self):
        output = self.root/"invalid"
        for frames, error in (([0,4], IndexError), (-5, IndexError), ([0,-4], ValueError),
                              ([], ValueError), (True, TypeError), ([1.0], TypeError),
                              ("1", TypeError), (slice(0,0), ValueError)):
            with self.subTest(frames=frames), self.assertRaises(error):
                export_traj_frames(self.source, output, frames)
            self.assertFalse(output.exists())

    def test_output_protection_and_overwrite(self):
        output = self.root/"out"
        export_traj_frames(self.source, output, 0)
        with self.assertRaises(FileExistsError):
            export_traj_frames(self.source, output, [1,0])
        self.assertFalse((output/"frame_000001.vasp").exists())
        export_traj_frames(self.source, output, 0, overwrite=True)
        protected = self.root/"frame_000000.traj"
        protected.write_bytes(self.source.read_bytes())
        before = protected.read_bytes()
        with self.assertRaises(ValueError):
            export_traj_frames(protected, self.root, 0, format="traj", overwrite=True)
        self.assertEqual(protected.read_bytes(), before)

    def test_no_cell_and_empty_trajectory(self):
        path = self.root/"molecule.traj"
        with Trajectory(str(path), "w") as writer:
            writer.write(Atoms("H", positions=[[0,0,0]]))
        with self.assertRaises(ValueError):
            export_traj_frames(path, self.root/"bad")
        export_traj_frames(path, self.root/"xyz_out", format="xyz")
        empty = self.root/"empty.traj"
        with Trajectory(str(empty), "w"):
            pass
        with self.assertRaises(ValueError):
            export_traj_frames(empty, self.root/"empty_out", None)


if __name__ == "__main__":
    unittest.main()
