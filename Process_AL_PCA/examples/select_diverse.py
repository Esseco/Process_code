"""Local feature diversity selection; requires a FAISS environment."""
from pathlib import Path
POOL_CSV = Path("E:/data/pool_features.csv")
TRAIN_CSV = Path("E:/data/train_features.csv")
OUTPUT_CSV = Path("E:/results/selected.csv")
FEATURE_COLS = ["d_std", "BAV"]
STRUCTURE_COL = "structure_id"
SELECT_N = 10
def main():
    import pandas as pd
    from Process_AL_PCA import DiverseSelector_struct
    if OUTPUT_CSV.exists():
        raise FileExistsError(OUTPUT_CSV)
    selector = DiverseSelector_struct(feature_cols=FEATURE_COLS, use_gpu=False)
    selected = selector.select(pd.read_csv(POOL_CSV), pd.read_csv(TRAIN_CSV),
                               struct_col=STRUCTURE_COL, select_n=SELECT_N)
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    selected.to_csv(OUTPUT_CSV, index=False)
if __name__ == "__main__":
    main()
