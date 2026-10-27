"""python -m Process_MLIP.benchmark {speed,ehull,validate} CONFIG.yaml."""
import argparse
import json

from .config import load_config


def main(argv=None):
    """CLI; validate never loads models, runs MD, or creates output files."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("speed", "ehull", "validate"))
    parser.add_argument("config")
    parser.add_argument("--model", action="append", help="Configured model ID; repeat for a subset")
    args = parser.parse_args(argv)
    try:
        if args.mode == "validate":
            print(json.dumps(load_config(args.config), ensure_ascii=False, indent=2))
            return 0
        from .runner import run_benchmark
        result = run_benchmark(args.config, args.mode, args.model)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result["failed"] else 0
    except Exception as exc:
        parser.exit(2, f"{type(exc).__name__}: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
