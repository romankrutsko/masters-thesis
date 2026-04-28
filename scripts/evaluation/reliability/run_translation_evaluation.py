#!/usr/bin/env python3
"""Compatibility wrapper for the split translation evaluation runners.

Use this if you want the old single entry point.
For clearer runs, prefer:
- run_reliability_evaluation.py
- run_maintainability_evaluation.py
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from evaluation_common import DEFAULT_BLACKLIST_FILE, DEFAULT_OUTPUT_ROOT
from run_maintainability_evaluation import run as run_maintainability
from run_reliability_evaluation import run as run_reliability


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run execution-based reliability scoring and/or Sonar-based "
            "maintainability checks for llm_translations."
        )
    )
    parser.add_argument("--mode", choices=["all", "execution", "static"], default="all")

    # Reliability args
    parser.add_argument("--python-bin", default=str(Path(__file__).resolve().parents[3] / ".venv" / "bin" / "python3"))
    parser.add_argument("--rscript-bin", default="Rscript")
    parser.add_argument("--digits", type=int, default=4)
    parser.add_argument("--atol", type=float, default=1e-3)
    parser.add_argument("--rtol", type=float, default=1e-3)
    parser.add_argument("--score-decimals", type=int, default=1)
    parser.add_argument("--execution-timeout", type=float, default=120.0)

    # Maintainability args
    parser.add_argument("--sonar-scanner-bin", default="sonar-scanner")
    parser.add_argument("--sonar-host-url", default=os.environ.get("SONAR_HOST_URL", "http://localhost:9000"))
    parser.add_argument("--sonar-token", default=os.environ.get("SONAR_TOKEN", ""))
    parser.add_argument("--sonar-project-prefix", default="masters_thesis_translations")

    # Shared run-selection args
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--run-id", default="")
    parser.add_argument("--models", default="")
    parser.add_argument("--prompt-types", default="")
    parser.add_argument("--languages", default="")
    parser.add_argument("--blacklist-file", type=Path, default=DEFAULT_BLACKLIST_FILE)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    run_id = args.run_id.strip()
    if not run_id:
        # Keep both modes in the same output directory when using --mode all.
        from evaluation_common import now_stamp

        args.run_id = now_stamp()

    if args.mode in {"all", "execution"}:
        print("Running reliability evaluation...")
        rc = run_reliability(args)
        if rc != 0:
            return rc

    if args.mode in {"all", "static"}:
        print("Running maintainability evaluation...")
        rc = run_maintainability(args)
        if rc != 0:
            return rc

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
