#!/usr/bin/env python
"""Run the repository MD screening workflow for one selected MLIP model."""
import json
import os
from pathlib import Path

from md_screening import ScreeningConfig, run_screening, screening_preset


ROOT = Path("/data/home/lichaoyue/26-7-AEA/MLIP_SOC_MD")
SOURCES = {
    "LCO": Path("/data/home/lichaoyue/26-7-AEA/MLIP_MD_test/LCO.vasp"),
    "NVP": Path("/data/home/lichaoyue/26-7-AEA/MLIP_MD_test/NVP.vasp"),
}
MODELS = {
    "nep89": dict(model_type="nep", model_path="/data/app/gpumd/5.0-cuda129/potentials/nep/nep89_20250409/nep89_20250409.txt", device="cuda", backend="gpu", gpumd_command="/data/app/gpumd/5.9.1-cuda129/bin/gpumd"),
    "mace_omat_sym": dict(model_type="mace", model_path="/data/home/lichaoyue/Process_code/MLIP_model/mace/mace-omat-0-medium.model", device="cuda", default_dtype="float32", enable_symmetrix=True, symmetrix_use_kokkos=True),
    "nip_l": dict(model_type="nequip", model_path="/data/home/lichaoyue/26-7-AEA/MLIP_nequip_oeq_speed_20261028/compiled/NequIP-OAM-L-0.2-oeq.nequip.pth", device="cuda", enable_openequivariance=True),
    "orbv3_direct": dict(model_type="orb", model_path="/data/home/lichaoyue/Process_code/MLIP_model/orb/orb-v3-direct-inf-omat-20250404.ckpt", device="cuda", model_name="orb-v3-direct-inf-omat", precision="float32-highest", compile_model=True),
    "grace_2l": dict(model_type="grace", model_path="/data/home/lichaoyue/Process_code/MLIP_model/grace/GRACE-2L-SMAX-OMAT-medium", device="cuda"),
    "7netnano6_flash": dict(model_type="sevennet", model_path="/data/home/lichaoyue/Process_code/MLIP_model/7net/checkpoint_7net_nano_6.0.pth", device="cuda", modal="mpa", enable_flash=True),
}


def main() -> None:
    model_id = os.environ["MLIP_MODEL_ID"]
    if model_id not in MODELS:
        raise ValueError(f"unknown MLIP_MODEL_ID={model_id!r}")
    model_options = MODELS[model_id]
    results_root = ROOT / "results" / model_id
    results_root.mkdir(parents=True, exist_ok=True)
    summary = []
    for structure in sorted((ROOT / "structures").glob("*.vasp")):
        system = structure.stem.split("_", 1)[0]
        output_dir = results_root / structure.stem
        if output_dir.exists():
            print(f"SKIP existing {structure.stem}", flush=True)
            continue
        config_options = dict(model_options)
        config_options["enable_symmetrix"] = model_options.get("model_type") == "mace"
        config_options["symmetrix_use_kokkos"] = model_options.get("model_type") == "mace"
        config = screening_preset(
            **config_options,
            mobile_species="Li" if system == "LCO" else "Na",
            target_atoms=None,
            temperature_K=800,
            precheck_ps=5,
            check_interval_ps=10,
            max_production_ps=200,
            timestep_fs=2,
            trajectory_interval=10,
            seed=42,
            jump_analysis=False,
        )
        result = run_screening(
            structure,
            reference_sites=SOURCES[system],
            output_dir=output_dir,
            config=config,
        )
        summary.append({"id": structure.stem, "status": result.status, "output_dir": str(output_dir)})
        print(f"DONE {structure.stem} {result.status}", flush=True)
    (results_root / "summary.json").write_text(
        json.dumps({"model": model_id, "workflow": "MD_Screening_Workflow.run_screening", "results": summary}, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
