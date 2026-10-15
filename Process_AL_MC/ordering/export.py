"""Global and exact-H TM rankings, retaining every evaluated Na companion."""

import csv
from pathlib import Path
import json

from .common import write_json


FIELDS = [
    "global_rank",
    "matrix_rank",
    "matrix_id",
    "det_H",
    "H",
    "tm_key",
    "occupation_key",
    "energy_per_atom",
    "model_version",
    "seed",
    "phase",
    "converged",
    "ranking_eligible",
    "structure_path",
    "na_occupation",
    "tm_occupation",
    "charge_source",
    "charge_scheme",
    "tm_charge_discriminating",
    "record_status",
    "error",
]


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: json.dumps(value, ensure_ascii=False)
                    if isinstance(value, (dict, list))
                    else value
                    for key, value in row.items()
                    if key in FIELDS
                }
            )


def export_results(plan, root, stores, chains):
    root = Path(root)
    representatives, all_joint, diagnostics = [], [], []
    for matrix in plan["matrices"]:
        records = stores[matrix["matrix_id"]].records()
        groups = {}
        for record in records:
            observation = record["result"] or {}
            row = {
                **observation,
                "matrix_id": matrix["matrix_id"],
                "H": matrix["H"],
                "det_H": matrix["det_H"],
                "tm_key": record["tm_key"],
                "occupation_key": record["key"],
                "na_occupation": record["occupation"]["na"],
                "tm_occupation": record["occupation"]["tm"],
                "charge_scheme": matrix["charge_scheme"],
                "charge_source": matrix["charge_source"],
                "tm_charge_discriminating": matrix["tm_charge_discriminating"],
                "record_status": record["status"],
                "error": record["error"],
            }
            if observation.get("structure_path"):
                row["structure_path"] = str(
                    Path("matrices") / matrix["matrix_id"] / "structures" / f"{record['key']}.vasp"
                )
            all_joint.append(row)
            if not observation.get("ranking_eligible"):
                diagnostics.append(row)
                continue
            old = groups.get(record["tm_key"])
            if old is None or (row["energy_per_atom"], row["occupation_key"]) < (
                old["energy_per_atom"],
                old["occupation_key"],
            ):
                groups[record["tm_key"]] = row
        local = sorted(
            groups.values(), key=lambda row: (row["energy_per_atom"], row["occupation_key"])
        )
        for rank, row in enumerate(local, 1):
            row["matrix_rank"] = rank
        representatives.extend(local)
        write_csv(root / "matrices" / matrix["matrix_id"] / "ranking.csv", local)
        write_json(
            root / "matrices" / matrix["matrix_id"] / "top_structures.json",
            local[: plan["options"]["top_k"]],
        )
    representatives.sort(key=lambda row: (row["energy_per_atom"], row["matrix_id"], row["tm_key"]))
    for rank, row in enumerate(representatives, 1):
        row["global_rank"] = rank
    for matrix in plan["matrices"]:
        local = [row for row in representatives if row["matrix_id"] == matrix["matrix_id"]]
        local.sort(key=lambda row: row["matrix_rank"])
        write_csv(root / "matrices" / matrix["matrix_id"] / "ranking.csv", local)
        write_json(
            root / "matrices" / matrix["matrix_id"] / "top_structures.json",
            local[: plan["options"]["top_k"]],
        )
    all_joint.sort(
        key=lambda row: (
            row.get("energy_per_atom", float("inf")),
            row["matrix_id"],
            row["occupation_key"],
        )
    )
    write_csv(root / "global_ranking.csv", representatives)
    write_csv(root / "all_joint_records.csv", all_joint)
    write_csv(root / "diagnostics.csv", diagnostics)
    write_json(root / "top_structures.json", representatives[: plan["options"]["top_k"]])
    result = {
        "status": "partial_failure"
        if any(row.get("status") == "failed" for row in chains)
        else "completed",
        "plan_id": plan["plan_id"],
        "joint_count": len(all_joint),
        "representative_count": len(representatives),
        "diagnostic_count": len(diagnostics),
        "global_ranking_csv": str(root / "global_ranking.csv"),
        "all_joint_csv": str(root / "all_joint_records.csv"),
        "diagnostics_csv": str(root / "diagnostics.csv"),
        "chains": chains,
        "ranking_meaning": "minimum observed Na companion for each TM ordering; no cross-H deduplication",
        "converged": None,
    }
    write_json(root / "result.json", result)
    return result
