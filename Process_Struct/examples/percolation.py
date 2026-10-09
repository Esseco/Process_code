"""Geometric channel connectivity; requires the existing CCNB/CAVD environment."""
from pathlib import Path
from Process_Struct import analyze_percolation
STRUCTURE_FILE = Path("E:/structures/initial.cif")
MIGRANT = "Na"
PROBE_RADIUS = 1.0  # angstrom; set for the intended physical model
OUTPUT_DIR = Path("E:/results/percolation")
def main():
    if OUTPUT_DIR.exists():
        raise FileExistsError("Choose a new output directory")
    print(analyze_percolation(STRUCTURE_FILE, migrant=MIGRANT,
              cutoff_radius=PROBE_RADIUS, output_dir=OUTPUT_DIR))
if __name__ == "__main__":
    main()
