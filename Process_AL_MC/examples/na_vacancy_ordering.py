"""Run a new MC ordering calculation; this is not checkpoint resume."""
from pathlib import Path
STRUCTURE = Path("E:/structures/ordered_oxide.cif")
OUTPUT_DIR = Path("E:/results/mc_new_run")
MODEL_PATHS = ["E:/models/model.model"]
MODEL_TYPE = "mace"  # mace / chgnet
DEVICE = "cuda"
SEED = 0
TEMPERATURE = 300  # K
MAX_STEPS = 1000
FULL_NA_STRUCTURE = Path("E:/structures/full_na_template.cif")
def main():
    from Process_AL_MC.MC_sample import LayeredOxide_MCOrderingClass
    if OUTPUT_DIR.exists():
        raise FileExistsError("Choose a new MC output directory")
    if any(not Path(path).is_file() for path in MODEL_PATHS):
        raise FileNotFoundError("Check all model paths before loading")
    runner = LayeredOxide_MCOrderingClass(
        model_paths=MODEL_PATHS, model_type=MODEL_TYPE, device=DEVICE, seed=SEED)
    runner.run(structure=STRUCTURE, mode="Na_MC_input", out_dir=OUTPUT_DIR,
               temperature=TEMPERATURE, max_steps=MAX_STEPS,
               save_every=100, save_relax_traj=False, full_na_structure=FULL_NA_STRUCTURE)
if __name__ == "__main__":
    main()
