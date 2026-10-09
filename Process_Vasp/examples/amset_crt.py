"""Edit paths, then run in an environment containing AMSET. Import is safe."""
from Process_Vasp import run_amset_crt

# Actual server DOS directory, not the local folder containing only metadata.
SOURCE_DIR = "/data/home/lichaoyue/26-10-LHL_cal/Dos/Full_TM/runs/dos/attempt_002"
OUTPUT_DIR = "/data/home/lichaoyue/26-10-LHL_cal/Dos/Full_TM/amset_crt"


def main():
    result = run_amset_crt(SOURCE_DIR, OUTPUT_DIR, doping=[-1e18, 1e18],
                          temperatures=[300], nworkers=1)
    print(result["sigma_over_tau_S_m_s"])


if __name__ == "__main__":
    main()
