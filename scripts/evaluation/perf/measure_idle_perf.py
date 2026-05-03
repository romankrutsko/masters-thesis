#!/usr/bin/env python3
"""Measure idle CPU package energy with Linux perf and Intel RAPL."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "results" / "perf_energy_runs" / "idle_30x_60s"

PERF_ELAPSED_RE = re.compile(r"([0-9][0-9,]*(?:\.[0-9]+)?)\s+seconds\s+time\s+elapsed")
PERF_ENERGY_RE = re.compile(r"([0-9][0-9,]*(?:\.[0-9]+)?)\s+Joules\s+power/energy-pkg/")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Measure idle CPU package energy by running perf stat around sleep."
    )
    parser.add_argument("--runs", type=int, default=30, help="Number of idle measurements.")
    parser.add_argument("--sleep-seconds", type=float, default=60.0, help="Idle interval measured by each run.")
    parser.add_argument("--pause-between-runs", type=float, default=1.0, help="Pause after each measured idle interval.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def parse_perf_stderr(stderr_text: str) -> tuple[float, float]:
    elapsed_matches = PERF_ELAPSED_RE.findall(stderr_text)
    energy_matches = PERF_ENERGY_RE.findall(stderr_text)
    if not elapsed_matches or not energy_matches:
        excerpt = " | ".join(line.strip() for line in stderr_text.splitlines() if line.strip())
        raise ValueError(f"Could not parse perf output: {excerpt[:400]}")

    elapsed_seconds = float(elapsed_matches[-1].replace(",", ""))
    energy_joules = float(energy_matches[-1].replace(",", ""))
    return elapsed_seconds, energy_joules


def measure_idle_once(sleep_seconds: float) -> dict[str, object]:
    command = ["perf", "stat", "-e", "power/energy-pkg/", "--", "sleep", f"{sleep_seconds:g}"]
    proc = subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    if proc.returncode != 0:
        error = " | ".join(
            line.strip()
            for line in (proc.stderr or proc.stdout or "").splitlines()
            if line.strip()
        )
        return {
            "status": "error",
            "elapsed_seconds": "",
            "energy_joules": "",
            "avg_power_watts": "",
            "error_message": f"perf failed with exit code {proc.returncode}: {error[:400]}",
        }

    try:
        elapsed_seconds, energy_joules = parse_perf_stderr(proc.stderr)
    except ValueError as exc:
        return {
            "status": "error",
            "elapsed_seconds": "",
            "energy_joules": "",
            "avg_power_watts": "",
            "error_message": str(exc),
        }

    avg_power_watts = energy_joules / elapsed_seconds if elapsed_seconds > 0 else None
    return {
        "status": "ok",
        "elapsed_seconds": f"{elapsed_seconds:.9f}",
        "energy_joules": f"{energy_joules:.9f}",
        "avg_power_watts": "" if avg_power_watts is None else f"{avg_power_watts:.9f}",
        "error_message": "",
    }


def summarize(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"n": 0, "mean": None, "variance": None, "std": None, "min": None, "max": None, "cv": None}

    n = len(values)
    mean = sum(values) / n
    variance = sum((value - mean) ** 2 for value in values) / (n - 1) if n > 1 else 0.0
    std = variance ** 0.5
    return {
        "n": n,
        "mean": mean,
        "variance": variance,
        "std": std,
        "min": min(values),
        "max": max(values),
        "cv": std / mean if mean else None,
    }


def main() -> int:
    args = parse_args()
    if args.runs < 1:
        raise SystemExit("--runs must be >= 1")
    if args.sleep_seconds <= 0:
        raise SystemExit("--sleep-seconds must be > 0")
    if args.pause_between_runs < 0:
        raise SystemExit("--pause-between-runs must be >= 0")

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "idle_perf_runs.csv"
    json_path = output_dir / "idle_perf_summary.json"

    rows: list[dict[str, object]] = []
    started_at = datetime.now(timezone.utc).isoformat()

    for run_id in range(1, args.runs + 1):
        print(f"idle run {run_id}/{args.runs} ...", flush=True)
        row = measure_idle_once(args.sleep_seconds)
        row["run_id"] = run_id
        rows.append(row)
        if row["status"] == "ok":
            print(
                "  -> ok "
                f"elapsed={row['elapsed_seconds']}s "
                f"energy={row['energy_joules']}J "
                f"power={row['avg_power_watts']}W",
                flush=True,
            )
        else:
            print(f"  -> error: {row['error_message']}", flush=True)

        if run_id < args.runs and args.pause_between_runs > 0:
            time.sleep(args.pause_between_runs)

    fields = ["run_id", "status", "elapsed_seconds", "energy_joules", "avg_power_watts", "error_message"]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    ok_rows = [row for row in rows if row["status"] == "ok"]
    elapsed = [float(row["elapsed_seconds"]) for row in ok_rows]
    energy = [float(row["energy_joules"]) for row in ok_rows]
    power = [float(row["avg_power_watts"]) for row in ok_rows]

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "started_at_utc": started_at,
        "runs_requested": args.runs,
        "sleep_seconds": args.sleep_seconds,
        "pause_between_runs_seconds": args.pause_between_runs,
        "successful_runs": len(ok_rows),
        "failed_runs": len(rows) - len(ok_rows),
        "elapsed_seconds": summarize(elapsed),
        "energy_joules": summarize(energy),
        "avg_power_watts": summarize(power),
        "output_csv": str(csv_path),
        "output_json": str(json_path),
    }
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Wrote {csv_path}")
    print(f"Wrote {json_path}")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Example:
# python3 scripts/evaluation/perf/measure_idle_perf.py \
#     --runs 30 \
#     --sleep-seconds 60 \
#     --pause-between-runs 1 \
#     --output-dir results/perf_energy_runs/idle_30x_60s_final
