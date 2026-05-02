#!/usr/bin/env python3
"""Summarize variation across one or more perf measurement CSV files."""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path


DEFAULT_METRICS = ["energy_joules", "elapsed_seconds", "avg_power_watts"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calculate mean, variance, standard deviation, and coefficient of variation for perf CSVs."
    )
    parser.add_argument("csv_files", nargs="+", type=Path, help="One or more perf_energy_runs.csv files.")
    parser.add_argument(
        "--metrics",
        default=",".join(DEFAULT_METRICS),
        help="Comma-separated metric columns to summarize.",
    )
    parser.add_argument(
        "--stable-cv-threshold",
        type=float,
        default=0.05,
        help="Coefficient-of-variation threshold used for the stable flag. Default: 0.05 means 5%%.",
    )
    parser.add_argument("--json-output", type=Path, default=None, help="Optional JSON output path.")
    return parser.parse_args()


def read_ok_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                if row.get("status") == "ok":
                    row["_source_csv"] = str(path)
                    rows.append(row)
    return rows


def as_float(value: str) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(out) or math.isinf(out):
        return None
    return out


def summarize(values: list[float], threshold: float) -> dict[str, float | int | bool | None]:
    n = len(values)
    if n == 0:
        return {
            "n": 0,
            "mean": None,
            "variance": None,
            "std": None,
            "cv": None,
            "cv_percent": None,
            "min": None,
            "max": None,
            "range": None,
            "range_percent_of_mean": None,
            "stable": False,
        }

    mean = statistics.fmean(values)
    variance = statistics.variance(values) if n > 1 else 0.0
    std = math.sqrt(variance)
    cv = std / mean if mean else None
    value_range = max(values) - min(values)
    range_percent = (value_range / mean * 100.0) if mean else None

    return {
        "n": n,
        "mean": mean,
        "variance": variance,
        "std": std,
        "cv": cv,
        "cv_percent": None if cv is None else cv * 100.0,
        "min": min(values),
        "max": max(values),
        "range": value_range,
        "range_percent_of_mean": range_percent,
        "stable": False if cv is None else cv < threshold,
    }


def fmt(value: object, *, percent: bool = False) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, int):
        return str(value)
    number = float(value)
    if percent:
        return f"{number:.2f}%"
    return f"{number:.6f}"


def main() -> int:
    args = parse_args()
    metrics = [metric.strip() for metric in args.metrics.split(",") if metric.strip()]
    rows = read_ok_rows(args.csv_files)
    if not rows:
        raise SystemExit("No successful rows found in the provided CSV files.")

    by_script: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_script[row.get("script_id") or "unknown"].append(row)

    payload: dict[str, object] = {
        "csv_files": [str(path) for path in args.csv_files],
        "stable_cv_threshold": args.stable_cv_threshold,
        "scripts": {},
    }

    for script_id, script_rows in sorted(by_script.items()):
        first = script_rows[0]
        label = "/".join(
            [
                first.get("model", ""),
                first.get("prompt_type", ""),
                first.get("language", ""),
                first.get("category", ""),
                first.get("snippet", ""),
            ]
        )
        print(f"{script_id} {label}".strip())

        script_summary: dict[str, object] = {
            "label": label,
            "runs": len(script_rows),
            "metrics": {},
        }
        for metric in metrics:
            values = [v for row in script_rows if (v := as_float(row.get(metric, ""))) is not None]
            stats = summarize(values, args.stable_cv_threshold)
            script_summary["metrics"][metric] = stats
            print(
                f"  {metric}: "
                f"n={fmt(stats['n'])} "
                f"mean={fmt(stats['mean'])} "
                f"std={fmt(stats['std'])} "
                f"variance={fmt(stats['variance'])} "
                f"cv={fmt(stats['cv_percent'], percent=True)} "
                f"range_pct={fmt(stats['range_percent_of_mean'], percent=True)} "
                f"stable={fmt(stats['stable'])}"
            )
        payload["scripts"][script_id] = script_summary

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Wrote {args.json_output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
