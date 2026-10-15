"""Explicit library CLI: plan first, prepare/run only when requested."""

import argparse
import json
from pathlib import Path
from .api import plan_ordering_search, prepare_ordering_search, run_ordering_search


def main():
    parser = argparse.ArgumentParser(description="Standalone TM-focused ordering search")
    parser.add_argument("request", help="JSON request with reference and keyword parameters")
    parser.add_argument("--output", required=True)
    parser.add_argument("--prepare", action="store_true", help="Write approved inputs only")
    parser.add_argument("--run", action="store_true", help="Explicitly load models and compute")
    args = parser.parse_args()
    request = json.loads(Path(args.request).read_text(encoding="utf-8"))
    plan = plan_ordering_search(**request)
    print(
        json.dumps(
            {
                "plan_id": plan["plan_id"],
                "workload": plan["workload"],
                "matrices": [
                    {
                        "H": m["H"],
                        "matrix_id": m["matrix_id"],
                        "move_kind": m["move_kind"],
                        "charge_scheme": m["charge_scheme"],
                    }
                    for m in plan["matrices"]
                ],
                "skipped": plan["skipped"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if args.prepare or args.run:
        prepare_ordering_search(plan, args.output)
    if args.run:
        print(json.dumps(run_ordering_search(args.output), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
