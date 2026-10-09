"""Run an allowlisted JSON recipe; preview by default, execute with --run."""
import argparse
import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
RECIPES = {
    "vasp_dos": ("Process_Vasp", "read_dos"),
    "vasp_excited": ("Process_Vasp", "generate_excited_input"),
    "vasp_workflow": ("Process_Vasp", "generate_atomate_input"),
    "vasp_followup": ("Process_Vasp", "generate_followup_task"),
    "vasp_task": ("Process_Vasp", "continue_task"),
    "amset_crt": ("Process_Vasp", "run_amset_crt"),
    "amset_task": ("Process_Vasp", "generate_amset_task"),
    "amset_postprocess": ("Process_Vasp", "run_amset_postprocess"),
    "capacity": ("Process_Struct", "theoretical_specific_capacity"),
    "wyckoff": ("Process_Struct", "get_wyckoff_sites"),
    "mace_relax": ("Process_MLIP.mace_relax", "relax_structure_mace"),
}


def load_config(path):
    config = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(config, dict) or config.get("recipe") not in RECIPES:
        raise ValueError(f"recipe must be one of {list(RECIPES)}")
    if not isinstance(config.get("parameters"), dict):
        raise ValueError("parameters must be a JSON object")
    if set(config) - {"recipe", "parameters"}:
        raise ValueError("Unknown configuration fields")
    return config


def execute(config):
    module, name = RECIPES[config["recipe"]]
    function = getattr(importlib.import_module(module), name)
    parameters = dict(config["parameters"])
    if config["recipe"] == "wyckoff":
        from pymatgen.core import Structure
        parameters["structure"] = Structure.from_file(parameters["structure"])
    if config["recipe"] == "vasp_workflow":
        target = Path(parameters["directory"])
        if target.exists() and (not target.is_dir() or any(target.iterdir())):
            raise ValueError("Workflow target must be absent or empty; edit existing workflow.json to resume")
    if config["recipe"] == "vasp_dos" and parameters.get("output_csv"):
        if Path(parameters["output_csv"]).exists():
            raise FileExistsError("CSV already exists; choose a new output_csv")
    return function(**parameters)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    config = load_config(args.config)
    print(json.dumps(config, indent=2, ensure_ascii=False))
    if args.run:
        result = execute(config)
        if config["recipe"] == "vasp_dos":
            print({key: value for key, value in result.items() if key != "df"})
            print(f"DataFrame shape: {result['df'].shape}")
        else:
            print(result)
    else:
        print("Preview only. Add --run to execute. Paths use the current working directory.")


if __name__ == "__main__":
    main()
