"""Generate follow-ups locally; source paths are resolved on the supercomputer."""
from Process_Vasp import generate_followup_task

PREVIOUS_TASK = "/data/home/lichaoyue/26-10-LHL_cal/Dos/Full_TM"
OUTPUT_TASK = "amset_followup"


def main():
    generate_followup_task(
        OUTPUT_TASK, PREVIOUS_TASK, "amset", source_stage="dos",
        amset_settings={"doping": [-1e18, 1e18], "temperatures": [300], "nworkers": 2},
    )


if __name__ == "__main__":
    main()
