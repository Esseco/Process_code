"""Theoretical stoichiometric capacity, not an experimental prediction."""
from Process_Struct import theoretical_specific_capacity
FORMULA = "NaFeO2"
MIGRATING_ION = "Na"
def main():
    value = theoretical_specific_capacity(FORMULA, migrating_ion=MIGRATING_ION)
    print(f"{float(value):.6f} mAh/g")
if __name__ == "__main__":
    main()
