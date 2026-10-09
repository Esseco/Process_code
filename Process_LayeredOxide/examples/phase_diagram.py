"""Use explicit Na content to avoid the legacy composition parsing branch."""
from pathlib import Path
import pandas as pd
from Process_LayeredOxide import LayerOxidePhaseDiagram
INPUT_CSV = Path("E:/data/energies.csv")
OUTPUT_CSV = Path("E:/results/formation_energy.csv")
NA_COL = "Na_content"  # x in NaxTMO2
ENERGY_COL = "energy"  # eV/atom
CALC_EHULL = False
def main():
    if OUTPUT_CSV.exists():
        raise FileExistsError(OUTPUT_CSV)
    df = pd.read_csv(INPUT_CSV)
    if df[[NA_COL, ENERGY_COL]].isna().any().any():
        raise ValueError("Missing composition or energy values")
    if not any(abs(df[NA_COL]) < 0.01) or not any(abs(df[NA_COL]-1) < 0.01):
        raise ValueError("Need endpoint data at x=0 and x=1")
    processor = LayerOxidePhaseDiagram(parse_composition=False, na_col=NA_COL,
                    energy_col=ENERGY_COL, calc_ehull=CALC_EHULL)
    result = processor.process(df)
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_CSV, index=False)
if __name__ == "__main__":
    main()
