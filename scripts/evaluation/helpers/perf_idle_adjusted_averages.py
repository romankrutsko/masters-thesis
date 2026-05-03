#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean, median, stdev


ID_RE = re.compile(r"^script_(\d+)$")
METRICS = [
    "elapsed_seconds",
    "energy_joules",
    "avg_power_watts",
    "idle_adjusted_energy_joules",
    "idle_adjusted_avg_power_watts",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build final per-script perf averages with idle-adjusted CPU package "
            "energy and power. Elapsed time is not adjusted."
        )
    )
    parser.add_argument(
        "--input-csv",
        action="append",
        required=True,
        metavar="LABEL=PATH",
        help="Raw perf CSV to include, tagged with a dataset label. Can be repeated.",
    )
    parser.add_argument(
        "--idle-runs-csv",
        type=Path,
        required=True,
        help="CSV produced by measure_idle_perf.py.",
    )
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-summary-json", type=Path, default=None)
    return parser.parse_args()


def script_number(script_id: str) -> int:
    match = ID_RE.match(script_id)
    if not match:
        raise SystemExit(f"Invalid script_id format: {script_id}")
    return int(match.group(1))


def parse_labelled_path(raw: str) -> tuple[str, Path]:
    if "=" not in raw:
        raise SystemExit(f"--input-csv must use LABEL=PATH format: {raw}")
    label, path = raw.split("=", 1)
    label = label.strip()
    if not label:
        raise SystemExit(f"Input label is empty: {raw}")
    return label, Path(path).resolve()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def successful_float_values(rows: list[dict[str, str]], metric: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        if row.get("status") != "ok":
            continue
        raw = row.get(metric, "").strip()
        if raw:
            values.append(float(raw))
    return values


def stats(values: list[float], prefix: str) -> dict[str, str]:
    if not values:
        return {
            f"{prefix}_mean": "",
            f"{prefix}_median": "",
            f"{prefix}_std": "",
            f"{prefix}_min": "",
            f"{prefix}_max": "",
        }
    return {
        f"{prefix}_mean": f"{mean(values):.9f}",
        f"{prefix}_median": f"{median(values):.9f}",
        f"{prefix}_std": "" if len(values) < 2 else f"{stdev(values):.9f}",
        f"{prefix}_min": f"{min(values):.9f}",
        f"{prefix}_max": f"{max(values):.9f}",
    }


def idle_power_mean(idle_rows: list[dict[str, str]]) -> float:
    values = successful_float_values(idle_rows, "avg_power_watts")
    if not values:
        raise SystemExit("Idle CSV has no successful avg_power_watts values")
    return mean(values)


def add_idle_adjusted_values(rows: list[dict[str, str]], idle_power_watts: float) -> None:
    for row in rows:
        if row.get("status") != "ok":
            row["idle_adjusted_energy_joules"] = ""
            row["idle_adjusted_avg_power_watts"] = ""
            continue

        elapsed = float(row["elapsed_seconds"])
        energy = float(row["energy_joules"])
        adjusted_energy = energy - idle_power_watts * elapsed
        # Negative values would mean the run consumed less package energy than the
        # measured idle baseline over the same window. Clamp to zero for reporting.
        adjusted_energy = max(0.0, adjusted_energy)
        row["idle_adjusted_energy_joules"] = f"{adjusted_energy:.9f}"
        row["idle_adjusted_avg_power_watts"] = f"{adjusted_energy / elapsed:.9f}"


def build_rows(labelled_inputs: list[tuple[str, Path]], idle_power_watts: float) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)

    for dataset_label, path in labelled_inputs:
        rows = read_csv(path)
        if not rows:
            raise SystemExit(f"Input CSV is empty: {path}")
        if "script_id" not in rows[0]:
            raise SystemExit(f"Input CSV must contain script_id: {path}")
        add_idle_adjusted_values(rows, idle_power_watts)
        for row in rows:
            row["_dataset"] = dataset_label
            grouped[(dataset_label, row["script_id"])].append(row)

    out: list[dict[str, str]] = []
    for (dataset_label, script_id), script_rows in grouped.items():
        first = script_rows[0]
        ok_rows = [row for row in script_rows if row.get("status") == "ok"]
        error_rows = [row for row in script_rows if row.get("status") != "ok"]
        out_row = {
            "dataset": dataset_label,
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
            values = successful_float_values(script_rows, metric)
            out_row.update(stats(values, metric))
        out.append(out_row)

    return sorted(
        out,
        key=lambda row: (
            row["dataset"],
            int(row["script_number"]),
            row["model"],
            row["prompt_type"],
            row["language"],
        ),
    )


def fieldnames() -> list[str]:
    metric_fields: list[str] = []
    for metric in METRICS:
        metric_fields.extend([
            f"{metric}_mean",
            f"{metric}_median",
            f"{metric}_std",
            f"{metric}_min",
            f"{metric}_max",
        ])
    return [
        "dataset",
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


def write_summary(
    path: Path,
    rows: list[dict[str, str]],
    idle_rows: list[dict[str, str]],
    idle_power_watts: float,
    labelled_inputs: list[tuple[str, Path]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "idle_runs": len(idle_rows),
        "idle_successful_runs": len([row for row in idle_rows if row.get("status") == "ok"]),
        "idle_avg_power_watts_mean": idle_power_watts,
        "idle_energy_joules_mean": mean(successful_float_values(idle_rows, "energy_joules")),
        "idle_elapsed_seconds_mean": mean(successful_float_values(idle_rows, "elapsed_seconds")),
        "scripts_summarized": len(rows),
        "inputs": [
            {"dataset": label, "csv": str(path)}
            for label, path in labelled_inputs
        ],
        "adjustment": (
            "idle_adjusted_energy_joules = max(0, energy_joules - "
            "idle_avg_power_watts_mean * elapsed_seconds); "
            "idle_adjusted_avg_power_watts = idle_adjusted_energy_joules / elapsed_seconds"
        ),
    }
    path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    labelled_inputs = [parse_labelled_path(raw) for raw in args.input_csv]
    idle_rows = read_csv(args.idle_runs_csv.resolve())
    idle_power_watts = idle_power_mean(idle_rows)
    out_rows = build_rows(labelled_inputs, idle_power_watts)

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames())
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Wrote {args.output_csv.resolve()}")
    print(f"Scripts summarized: {len(out_rows)}")
    print(f"Idle average power used: {idle_power_watts:.9f} W")

    if args.output_summary_json:
        write_summary(
            args.output_summary_json.resolve(),
            out_rows,
            idle_rows,
            idle_power_watts,
            labelled_inputs,
        )
        print(f"Wrote {args.output_summary_json.resolve()}")


if __name__ == "__main__":
    main()
