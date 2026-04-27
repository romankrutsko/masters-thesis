#!/usr/bin/env python3
"""
Stage the original task scripts under a repo-local benchmark layout and then
invoke scripts/evaluation/perf/measure_perf_energy.py unchanged.

This avoids the original script's assumption that discovered files live under
the repository root while still benchmarking the original implementations.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_STAGE_DIR = REPO_ROOT / ".tmp" / "perf_energy_original_layout"
PYTHON_SOURCE_DIR = REPO_ROOT / "task_equivalents" / "python"
R_SOURCE_DIR = REPO_ROOT / "task_equivalents" / "r"


def parse_args() -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
        description=(
            "Create a repo-local staging layout for the original Python/R task "
            "scripts and forward benchmark arguments to measure_perf_energy.py."
        )
    )
    parser.add_argument(
        "--stage-dir",
        type=Path,
        default=DEFAULT_STAGE_DIR,
        help="Repo-local staging root to create before invoking the benchmark.",
    )
    parser.add_argument(
        "--keep-stage-dir",
        action="store_true",
        help="Keep the staged symlink layout after the benchmark finishes.",
    )
    args, forwarded_args = parser.parse_known_args()
    return args, forwarded_args


def ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def stage_language(source_root: Path, target_root: Path) -> None:
    if not source_root.exists():
        raise SystemExit(f"Source directory does not exist: {source_root}")

    for category_dir in sorted(source_root.iterdir()):
        if not category_dir.is_dir():
            continue
        target_category_dir = target_root / category_dir.name
        target_category_dir.mkdir(parents=True, exist_ok=True)
        for script_path in sorted(category_dir.iterdir()):
            if not script_path.is_file():
                continue
            (target_category_dir / script_path.name).symlink_to(script_path.resolve())


def build_stage_layout(stage_dir: Path) -> Path:
    base_dir = stage_dir / "original" / "base"
    ensure_clean_dir(stage_dir)
    stage_language(PYTHON_SOURCE_DIR, base_dir / "python")
    stage_language(R_SOURCE_DIR, base_dir / "r")
    return stage_dir


def validate_forwarded_args(forwarded_args: list[str]) -> None:
    blocked_flags = {"--base-dir"}
    for arg in forwarded_args:
        if arg == "--base-dir" or any(arg.startswith(f"{flag}=") for flag in blocked_flags):
            raise SystemExit("Do not pass --base-dir to this wrapper; it is managed automatically.")


def run_benchmark(stage_dir: Path, forwarded_args: list[str]) -> int:
    command = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "evaluation" / "perf" / "measure_perf_energy.py"),
        "--base-dir",
        str(stage_dir),
        *forwarded_args,
    ]
    return subprocess.run(command, cwd=REPO_ROOT, check=False).returncode


def main() -> None:
    args, forwarded_args = parse_args()
    validate_forwarded_args(forwarded_args)

    stage_dir = args.stage_dir.resolve()
    if REPO_ROOT not in stage_dir.parents and stage_dir != REPO_ROOT:
        raise SystemExit(f"--stage-dir must be inside the repository: {stage_dir}")

    build_stage_layout(stage_dir)
    try:
        raise SystemExit(run_benchmark(stage_dir, forwarded_args))
    finally:
        if not args.keep_stage_dir and stage_dir.exists():
            shutil.rmtree(stage_dir)


if __name__ == "__main__":
    main()
