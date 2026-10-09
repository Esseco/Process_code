"""Use the legacy trajectory exporter, not trace.json or pool_summary.json."""
from pathlib import Path
TRAJECTORY_JSON = Path("E:/results/run_001/pool/rank_001_step_0100_relax_traj.json")
OUTPUT_DIR = Path("E:/results/extracted_structures")
SELECT_NUM = 3
def main():
    from Process_AL_MC.Auc_code import extract_data_from_mcjson
    if OUTPUT_DIR.exists():
        raise FileExistsError(OUTPUT_DIR)
    if SELECT_NUM < 1:
        raise ValueError("SELECT_NUM must be positive")
    import pandas as pd
    df = pd.read_json(TRAJECTORY_JSON)
    required = {"structure", "energy_mean_per_atom", "energy_std_per_atom",
                "force_uncertainty_per_atom", "force_uncertainty_max"}
    if df.empty or not required.issubset(df.columns):
        raise ValueError("Need a nonempty relaxation trajectory with expected committee fields")
    OUTPUT_DIR.mkdir(parents=True)
    print(extract_data_from_mcjson(TRAJECTORY_JSON, OUTPUT_DIR, select_num=SELECT_NUM))
if __name__ == "__main__":
    main()
