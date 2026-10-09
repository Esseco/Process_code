"""Read MC acceptance trace; output is an in-memory DataFrame."""
from pathlib import Path
import pandas as pd
TRACE = Path("E:/results/mc_new_run/trace.json")
def main():
    df = pd.read_json(TRACE)
    print(df.columns.tolist())
    print(df.tail())
if __name__ == "__main__":
    main()
