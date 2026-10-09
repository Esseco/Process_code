"""Use total energies in eV per NaxTMO2 and a consistent Na reference."""
from pathlib import Path
import pandas as pd
from Process_LayeredOxide import get_voltage
INPUT_CSV = Path("E:/data/formula_energies.csv")
OUTPUT_CSV = Path("E:/results/voltage.csv")
NA_COL = "Na_content"
ENERGY_COL = "formula_e"  # eV/NaxTMO2, not meV formation_e
MU_NA = None  # set eV/Na from a consistent reference calculation
def main():
    if MU_NA is None:
        raise ValueError("Set MU_NA from a consistent Na reference")
    if OUTPUT_CSV.exists():
        raise FileExistsError(OUTPUT_CSV)
    df = pd.read_csv(INPUT_CSV)
    if df[NA_COL].nunique() < 3:
        raise ValueError("Current convex-hull implementation needs at least three non-collinear points")
    result = get_voltage(df, Na_col=NA_COL, e_col=ENERGY_COL, μ_Na=MU_NA)
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_CSV, index=False)
if __name__ == "__main__":
    main()
