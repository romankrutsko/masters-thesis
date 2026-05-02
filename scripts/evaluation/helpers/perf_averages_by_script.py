#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean, median, stdev


METRICS = ["elapsed_seconds", "energy_joules", "avg_power_watts"]
ID_RE = re.compile(r"^script_(\d+)$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Average perf measurements by stable script_id and sort by script number."
    )
    parser.add_argument("--input-csv", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, default=None)
    return parser.parse_args()


def script_number(script_id: str) -> int:
    match = ID_RE.match(script_id)
    if not match:
        raise SystemExit(f"Invalid script_id format: {script_id}")
    return int(match.group(1))


def output_path(input_csv: Path, explicit_output: Path | None) -> Path:
    if explicit_output is not None:
        return explicit_output
    return input_csv.with_name("perf_energy_script_averages.csv")


def float_values(rows: list[dict[str, str]], metric: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        raw = row.get(metric, "").strip()
        if raw:
            values.append(float(raw))
    return values


def metric_stats(rows: list[dict[str, str]], metric: str) -> dict[str, str]:
    # Averages are computed from successful measured runs only.
    values = float_values(rows, metric)
    if not values:
        return {
            f"{metric}_mean": "",
            f"{metric}_median": "",
            f"{metric}_std": "",
            f"{metric}_min": "",
            f"{metric}_max": "",
        }
    return {
        f"{metric}_mean": f"{mean(values):.9f}",
        f"{metric}_median": f"{median(values):.9f}",
        f"{metric}_std": "" if len(values) < 2 else f"{stdev(values):.9f}",
        f"{metric}_min": f"{min(values):.9f}",
        f"{metric}_max": f"{max(values):.9f}",
    }


def build_average_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["script_id"]].append(row)

    out: list[dict[str, str]] = []
    for script_id, script_rows in grouped.items():
        first = script_rows[0]
        ok_rows = [row for row in script_rows if row.get("status") == "ok"]
        error_rows = [row for row in script_rows if row.get("status") != "ok"]

        # Keep the identifying columns so averaged rows remain traceable to source files.
        average_row = {
            "script_id": script_id,
            "script_number": str(script_number(script_id)),
            "model": first.get("model", ""),
            "prompt_type": first.get("prompt_type", ""),
            "language": first.get("language", ""),
            "category": first.get("category", ""),
            "snippet": first.get("snippet", ""),
            "script_path": first.get("script_path", ""),
            "ok_runs": str(len(ok_rows)),
            "failed_runs": str(len(error_rows)),
            "total_runs": str(len(script_rows)),
        }

        for metric in METRICS:
            average_row.update(metric_stats(ok_rows, metric))
        out.append(average_row)

    return sorted(out, key=lambda row: int(row["script_number"]))


def fieldnames() -> list[str]:
    metric_fields = []
    for metric in METRICS:
        metric_fields.extend([
            f"{metric}_mean",
            f"{metric}_median",
            f"{metric}_std",
            f"{metric}_min",
            f"{metric}_max",
        ])
    return [
        "script_id",
        "script_number",
        "model",
        "prompt_type",
        "language",
        "category",
        "snippet",
        "script_path",
        "ok_runs",
        "failed_runs",
        "total_runs",
        *metric_fields,
    ]


def main() -> None:
    args = parse_args()
    input_csv = args.input_csv.resolve()
    out_csv = output_path(input_csv, args.output_csv.resolve() if args.output_csv else None)

    with input_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SystemExit(f"Input CSV is empty: {input_csv}")
    if "script_id" not in rows[0]:
        raise SystemExit("Input CSV must contain a script_id column")

    averages = build_average_rows(rows)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames())
        writer.writeheader()
        writer.writerows(averages)

    print(f"Wrote {out_csv}")
    print(f"Scripts summarized: {len(averages)}")


if __name__ == "__main__":
    main()
