"""Temporary, synthetic CPU tests; no model weights, GPU or production copies."""
from contextlib import contextmanager
import json
import io
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout

from ase.build import bulk
from ase.calculators.emt import EMT
import numpy as np
import yaml

from Process_MLIP.benchmark.config import load_config
from Process_MLIP.benchmark.ehull import compute_hull, compare_reference, read_reference
from Process_MLIP.benchmark.examples.make_demo import make_demo
from Process_MLIP.benchmark.operations import Measurement, molecular_dynamics
from Process_MLIP.benchmark.registry import create_calculator, register_model
from Process_MLIP.benchmark.runner import run_benchmark
from Process_MLIP.benchmark.storage import output_lock, source_hash


@contextmanager
def demo():
    with TemporaryDirectory(prefix="mlip_benchmark_") as directory:
        path = make_demo(Path(directory) / "demo", quick=True)
        yield path, path.parent / "results"


def analytic_records():
    return [dict(structure_id=name, composition=list(symbols), energy_eV=energy,
                 converged=True, status="completed", model_id="analytic")
            for name, symbols, energy in (("Cu", ["Cu"], 0), ("Au", ["Au"], 0),
                                          ("alloy", ["Cu", "Au"], -2),
                                          ("metastable", ["Cu", "Au"], -1),
                                          ("supercell", ["Cu", "Au"] * 2, -4))]


class HullTests(unittest.TestCase):
    def test_normalization_polymorphs_and_supercell(self):
        _, rows = compute_hull(analytic_records())
        result = {r["structure_id"]: r for r in rows}
        self.assertAlmostEqual(result["metastable"]["ehull_eV_per_atom"], 0.5)
        self.assertAlmostEqual(result["supercell"]["ehull_eV_per_atom"], 0)
        self.assertFalse(result["metastable"]["stable"])
        self.assertTrue(result["alloy"]["stable"])

    def test_missing_terminal_and_unconverged_rejected(self):
        with self.assertRaisesRegex(ValueError, "endmembers"):
            compute_hull(analytic_records()[2:])
        records = analytic_records()
        records[-1]["converged"] = False
        with self.assertRaisesRegex(ValueError, "converged"):
            compute_hull(records)

    def test_reference_metrics_and_coverage(self):
        _, rows = compute_hull(analytic_records())
        output, metrics = compare_reference(rows, {"Cu": 0, "metastable": 0.3, "unused": 1})
        self.assertAlmostEqual(metrics["MAE_eV_per_atom"], 0.1)
        self.assertAlmostEqual(metrics["Bias_eV_per_atom"], 0.1)
        self.assertAlmostEqual(metrics["RMSE_eV_per_atom"], np.sqrt(0.02))
        self.assertEqual(metrics["n_matched"], 2)
        self.assertEqual(metrics["true_positive"], 1)
        self.assertEqual(metrics["unused_reference_ids"], ["unused"])
        self.assertEqual(output[2]["reference_ehull_eV_per_atom"], None)
        with self.assertRaisesRegex(ValueError, "No matching"):
            compare_reference(rows, {"unknown": 0})

    def test_invalid_reference(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "reference.csv"
            for text in ("id,ehull_eV_per_atom\na,0\na,1\n", "id,ehull_eV_per_atom\na,nan\n",
                         "id,ehull_eV_per_atom\na,-1\n", "id,wrong\na,0\n"):
                path.write_text(text, encoding="utf-8")
                with self.assertRaises(ValueError):
                    read_reference(path)


class ConfigTests(unittest.TestCase):
    def test_fp32_defaults_and_explicit_override(self):
        with demo() as (path, _):
            config = yaml.safe_load(path.read_text())
            config["models"] = [
                dict(id="mace32", type="mace"),
                dict(id="mace64", type="mace", parameters={"default_dtype": "float64"}),
                dict(id="orb32", type="orb"),
                dict(id="sevennet", type="sevennet"),
            ]
            path.write_text(yaml.safe_dump(config))
            models = load_config(path)["models"]
            self.assertEqual(models[0]["parameters"]["default_dtype"], "float32")
            self.assertEqual(models[1]["parameters"]["default_dtype"], "float64")
            self.assertEqual(models[2]["parameters"]["precision"], "float32-highest")
            self.assertEqual(models[3]["parameters"], {})

    def test_defaults_and_relative_paths(self):
        with demo() as (path, root):
            config = load_config(path)
            self.assertEqual(config["output_dir"], str(root))
            self.assertEqual(config["relax"], dict(fmax=0.1, maxstep=0.2, steps=2000))
            self.assertEqual(config["md"]["temperature_K"], 800)
            self.assertEqual(config["md"]["timestep_fs"], 2)
            self.assertFalse(root.exists())

    def test_gpu_accelerator_defaults_and_overrides(self):
        with demo() as (path, _):
            checkpoint = path.parent / "mace-omat-0.model"
            checkpoint.write_bytes(b"checkpoint")
            config = yaml.safe_load(path.read_text())
            config["models"] = [
                dict(id="omat", type="mace", device="cuda", parameters={"model_path": str(checkpoint)}),
                dict(id="manual", type="mace", device="cuda", parameters={"model_path": str(checkpoint), "enable_symmetrix": False}),
                dict(id="sevennet", type="sevennet", device="cuda"),
                dict(id="no_flash", type="sevennet", device="cuda", parameters={"enable_flash": False}),
            ]
            path.write_text(yaml.safe_dump(config))
            models = load_config(path)["models"]
            self.assertTrue(models[0]["parameters"]["enable_symmetrix"])
            self.assertTrue(models[0]["parameters"]["symmetrix_use_kokkos"])
            self.assertFalse(models[1]["parameters"]["enable_symmetrix"])
            self.assertTrue(models[2]["parameters"]["enable_flash"])
            self.assertFalse(models[3]["parameters"]["enable_flash"])

    def test_reject_typos_bad_ids_and_parameters(self):
        with demo() as (path, _):
            original = yaml.safe_load(path.read_text())
            for mutate in (lambda c: c.update(extra=1),
                           lambda c: c["md"].update(steps=0),
                           lambda c: c["models"][0].update(id="../escape"),
                           lambda c: c["structures"].append(dict(c["structures"][0])),
                           lambda c: c["models"][0].update(parameters={"device": "cuda"})):
                config = json.loads(json.dumps(original))
                mutate(config)
                path.write_text(yaml.safe_dump(config))
                with self.assertRaises(ValueError):
                    load_config(path)

    def test_registry_extension_and_unsupported(self):
        name = "unit_test_custom"
        if name not in __import__("Process_MLIP.benchmark.registry", fromlist=["_FACTORIES"])._FACTORIES:
            register_model(name, lambda config: EMT())
        self.assertIsInstance(create_calculator(dict(type=name, device="cpu", parameters={})), EMT)
        with self.assertRaises(ValueError):
            register_model(name, lambda config: EMT())
        with self.assertRaises(NotImplementedError):
            create_calculator(dict(type="unknown_model", device="cpu", parameters={}))

    def test_saved_model_hash_tracks_files_and_names(self):
        with TemporaryDirectory() as directory:
            model = Path(directory) / "model"
            model.mkdir()
            (model / "saved_model.pb").write_bytes(b"model")
            first = source_hash(model)
            (model / "saved_model.pb").write_bytes(b"updated")
            self.assertNotEqual(first, source_hash(model))
            second = source_hash(model)
            (model / "variables").mkdir()
            (model / "variables" / "data").write_bytes(b"weights")
            self.assertNotEqual(second, source_hash(model))

    def test_nequip_rejects_uncompiled_package(self):
        with self.assertRaisesRegex(ValueError, "compile"):
            create_calculator(dict(type="nequip", device="cuda", parameters={"model_path": "model.nequip.zip"}))

    def test_nep_gpu_dispatch_and_device_validation(self):
        with patch("Process_MLIP.calculators.create_mlip_calculator", return_value=EMT()):
            model = dict(type="nep", device="cuda", parameters={"model_path": "model.txt", "backend": "gpu"})
            calculator = create_calculator(model)
            self.assertTrue(calculator.benchmark_external_gpu)
            for device in ("cpu", "cuda:1"):
                with self.assertRaises(ValueError):
                    create_calculator(dict(model, device=device))

    def test_external_gpu_does_not_report_parent_memory(self):
        with patch.dict("sys.modules", torch=None):
            with Measurement("cuda", external_gpu=True) as meter:
                pass
        self.assertIsNone(meter.result["peak_gpu_allocated_MiB"])
        self.assertEqual(meter.result["gpu_memory_scope"], "unavailable_external_gpu_subprocess")

    def test_validate_cli_does_not_load_model_or_write_results(self):
        from Process_MLIP.benchmark.__main__ import main
        with demo() as (path, root):
            with patch("Process_MLIP.benchmark.runner.create_calculator") as loader, redirect_stdout(io.StringIO()):
                self.assertEqual(main(["validate", str(path)]), 0)
            loader.assert_not_called()
            self.assertFalse(root.exists())


class RuntimeTests(unittest.TestCase):
    def test_speed_runs_without_hull_dependencies(self):
        code = '''
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
sys.modules["monty"] = None
sys.modules["pymatgen"] = None
from Process_MLIP.benchmark.examples.make_demo import make_demo
from Process_MLIP.benchmark.runner import run_benchmark
with TemporaryDirectory() as directory:
    config = make_demo(Path(directory) / "demo", quick=True)
    result = run_benchmark(config, "speed")
    assert result["status"] == "completed" and result["failed"] == 0
'''
        subprocess.run([sys.executable, "-c", code], check=True, capture_output=True, text=True)

    def test_real_speed_and_resume(self):
        with demo() as (path, root):
            result = run_benchmark(path, "speed")
            self.assertEqual(result["failed"], 0)
            relax_rows = json.loads((root / "speed/relax.json").read_text())
            md_rows = json.loads((root / "speed/md.json").read_text())
            self.assertEqual(len(relax_rows), 4)
            self.assertEqual([r["natoms"] for r in md_rows], [4, 4, 4, 32])
            for row in relax_rows:
                self.assertTrue(row["converged"])
                self.assertGreater(row["force_evaluations"], 0)
                self.assertIsNone(row["peak_gpu_allocated_MiB"])
                self.assertTrue(Path(row["final_structure"]).is_file())
            for row in md_rows:
                self.assertEqual(row["steps_completed"], 20)
                self.assertAlmostEqual(row["simulated_time_ps"], 0.04)
                self.assertAlmostEqual(row["steps_per_second"] * row["elapsed_seconds"], 20)
            self.assertTrue((root / "speed/relax_elapsed_seconds.png").is_file())
            self.assertTrue((root / "speed/md_steps_per_second.png").is_file())
            with patch("Process_MLIP.benchmark.runner.create_calculator", side_effect=AssertionError("reload")):
                self.assertEqual(run_benchmark(path, "speed")["failed"], 0)
            self.assertFalse((root / ".benchmark.lock").exists())

    def test_real_ehull_and_comparison(self):
        with demo() as (path, root):
            config = yaml.safe_load(path.read_text())
            reference = path.parent / "reference.csv"
            reference.write_text("id,ehull_eV_per_atom\nCu,0\nAu,0\nCu3Au,0\n", encoding="utf-8")
            config["ehull"]["reference_csv"] = "reference.csv"
            path.write_text(yaml.safe_dump(config))
            result = run_benchmark(path, "ehull")
            self.assertEqual(result["failed"], 0, result)
            hull = result["hulls"][0]
            self.assertEqual(hull["metrics"]["n_matched"], 3)
            directory = root / "ehull/emt_demo"
            self.assertTrue((directory / "phase_diagram.png").is_file())
            self.assertTrue((directory / "phase_diagram.json").is_file())
            self.assertEqual(len(json.loads((directory / "ehull.json").read_text())), 4)

    def test_failures_isolated_and_retried(self):
        with demo() as (path, root):
            config = yaml.safe_load(path.read_text())
            config["models"].append(dict(id="unavailable", type="unknown_model", device="cpu"))
            path.write_text(yaml.safe_dump(config))
            result = run_benchmark(path, "speed")
            self.assertEqual(result["failed"], 8)
            rows = json.loads((root / "speed/md.json").read_text())
            self.assertEqual(sum(r["status"] == "completed" for r in rows), 4)
            self.assertTrue(all("not implemented" in r["error"] for r in rows if r["status"] == "failed"))
            with patch("Process_MLIP.benchmark.runner.create_calculator", return_value=EMT()) as factory:
                self.assertEqual(run_benchmark(path, "speed")["failed"], 0)
                self.assertEqual(factory.call_count, 1)

    def test_changed_input_or_checkpoint_refuses_resume(self):
        with demo() as (path, root):
            config = yaml.safe_load(path.read_text())
            checkpoint = path.parent / "dummy.bin"
            checkpoint.write_bytes(b"one")
            config["models"][0]["parameters"] = dict(model_path="dummy.bin")
            path.write_text(yaml.safe_dump(config))
            # No real checkpoint is loaded: factory replaces EMT parameters only for this test.
            with patch("Process_MLIP.benchmark.runner.create_calculator", return_value=EMT()):
                run_benchmark(path, "speed")
            checkpoint.write_bytes(b"two")
            with self.assertRaisesRegex(ValueError, "changed"):
                run_benchmark(path, "speed")
            self.assertFalse((root / ".benchmark.lock").exists())

    def test_unconverged_hull_not_written(self):
        with demo() as (path, root):
            config = yaml.safe_load(path.read_text())
            config["relax"].update(steps=1, fmax=1e-12)
            path.write_text(yaml.safe_dump(config))
            result = run_benchmark(path, "ehull")
            self.assertGreater(result["failed"], 0)
            self.assertFalse((root / "ehull/emt_demo/ehull.csv").exists())

    def test_output_lock_and_model_subset(self):
        with demo() as (path, root):
            with output_lock(root):
                with self.assertRaisesRegex(RuntimeError, "locked"):
                    run_benchmark(path, "speed")
            with self.assertRaisesRegex(ValueError, "select"):
                run_benchmark(path, "speed", ["unknown"])

    def test_modified_structure_refuses_resume(self):
        with demo() as (path, root):
            run_benchmark(path, "speed")
            source = path.parent / "Cu.extxyz"
            source.write_text(source.read_text() + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "changed"):
                run_benchmark(path, "speed")

    def test_missing_final_reruns_only_affected_stage(self):
        with demo() as (path, root):
            run_benchmark(path, "speed")
            target = root / "speed/emt_demo/Cu/md/final.traj"
            target.unlink()
            from Process_MLIP.benchmark.operations import molecular_dynamics as actual_md
            with patch("Process_MLIP.benchmark.runner.molecular_dynamics", wraps=actual_md) as md, \
                    patch("Process_MLIP.benchmark.runner.relax", side_effect=AssertionError("unneeded relax")):
                result = run_benchmark(path, "speed")
            self.assertEqual(result["failed"], 0)
            self.assertEqual(md.call_count, 1)
            self.assertTrue(target.is_file())

    def test_md_failure_preserves_steps_and_does_not_fail_relax(self):
        with demo() as (path, root):
            def fail_md(atoms, calculator, directory, **kwargs):
                directory = Path(directory)
                (directory / "report.json").write_text(json.dumps(dict(status="failed", steps_completed=7)))
                raise RuntimeError("unstable MD")
            with patch("Process_MLIP.benchmark.operations.run_md", side_effect=fail_md):
                result = run_benchmark(path, "speed")
            self.assertEqual(result["failed"], 4)
            rows = json.loads((root / "speed/relax.json").read_text())
            self.assertTrue(all(r["status"] == "completed" for r in rows))
            rows = json.loads((root / "speed/md.json").read_text())
            self.assertTrue(all("unstable MD" in r["error"] for r in rows))
            self.assertTrue(all(r["steps_completed"] == 7 for r in rows))
            self.assertTrue(all(r["elapsed_seconds"] is None for r in rows))
            self.assertTrue(all(r["stage_wall_seconds"] >= 0 for r in rows))

    def test_ehull_missing_endmember_before_model_load(self):
        with demo() as (path, root):
            config = yaml.safe_load(path.read_text())
            config["structures"] = config["structures"][2:]
            path.write_text(yaml.safe_dump(config))
            with patch("Process_MLIP.benchmark.runner.create_calculator") as loader:
                with self.assertRaisesRegex(ValueError, "endmembers"):
                    run_benchmark(path, "ehull")
            loader.assert_not_called()
            self.assertFalse(root.exists())

    def test_subsets_aggregate_without_running_other_models(self):
        with demo() as (path, root):
            config = yaml.safe_load(path.read_text())
            config["models"].append(dict(id="second_emt", type="emt", device="cpu"))
            path.write_text(yaml.safe_dump(config))
            result = run_benchmark(path, "speed", ["emt_demo"])
            self.assertEqual(result["status"], "partial")
            self.assertEqual(result["stages_missing"], 8)
            self.assertFalse((root / "speed/second_emt").exists())
            result = run_benchmark(path, "speed", ["second_emt"])
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["stages_recorded"], 16)
            self.assertEqual(result["stages_missing"], 0)

    def test_pure_md_timer_excludes_setup(self):
        fake = dict(steps_completed=1000, steps_per_second=250, final_structure="unused")
        with patch("Process_MLIP.benchmark.operations.run_md", return_value=fake) as md:
            row = molecular_dynamics(bulk("Cu"), EMT(), "unused", {"timestep_fs": 2}, "cpu", 42)
        self.assertEqual(row["elapsed_seconds"], 4)
        self.assertEqual(row["simulated_time_ps"], 2)
        self.assertTrue(md.call_args.kwargs["measure_steps_per_second"])

    def test_cuda_synchronization_and_peak_reset(self):
        calls = []
        class FakeCuda:
            def is_available(self): return True
            def synchronize(self, device): calls.append("sync")
            def reset_peak_memory_stats(self, device): calls.append("reset")
            def max_memory_allocated(self, device): return 5 * 1024**2
            def max_memory_reserved(self, device): return 8 * 1024**2
        class FakeTorch:
            cuda = FakeCuda()
        with patch.dict("sys.modules", torch=FakeTorch()):
            with Measurement("cuda:0") as meter:
                calls.append("operation")
        self.assertEqual(calls, ["sync", "reset", "operation", "sync"])
        self.assertEqual(meter.result["peak_gpu_allocated_MiB"], 5)


if __name__ == "__main__":
    unittest.main()
