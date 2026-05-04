#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create per-run perf CSVs with idle-adjusted energy_joules and "
            "avg_power_watts columns for downstream statistical analysis."
        )
    )
    parser.add_argument("--input-csv", type=Path, required=True)
    parser.add_argument("--idle-runs-csv", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-summary-json", type=Path, default=None)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def successful_idle_power_mean(rows: list[dict[str, str]]) -> float:
    values = [
        float(row["avg_power_watts"])
        for row in rows
        if row.get("status") == "ok" and row.get("avg_power_watts", "").strip()
    ]
    if not values:
        raise SystemExit("Idle CSV has no successful avg_power_watts values")
    return mean(values)


def adjust_rows(rows: list[dict[str, str]], idle_power_watts: float) -> list[dict[str, str]]:
    adjusted: list[dict[str, str]] = []
    for row in rows:
        out = dict(row)
        out["energy_joules_raw"] = row.get("energy_joules", "")
        out["avg_power_watts_raw"] = row.get("avg_power_watts", "")

        if row.get("status") == "ok":
            elapsed = float(row["elapsed_seconds"])
            energy = float(row["energy_joules"])
            adjusted_energy = max(0.0, energy - idle_power_watts * elapsed)
            out["energy_joules"] = f"{adjusted_energy:.9f}"
            out["avg_power_watts"] = f"{adjusted_energy / elapsed:.9f}"
        adjusted.append(out)
    return adjusted


def fieldnames(rows: list[dict[str, str]]) -> list[str]:
    names = list(rows[0].keys())
    for extra in ("energy_joules_raw", "avg_power_watts_raw"):
        if extra not in names:
            names.append(extra)
    return names


def main() -> None:
    args = parse_args()
    input_csv = args.input_csv.resolve()
    idle_runs_csv = args.idle_runs_csv.resolve()
    output_csv = args.output_csv.resolve()

    rows = read_csv(input_csv)
    idle_rows = read_csv(idle_runs_csv)
    if not rows:
        raise SystemExit(f"Input CSV is empty: {input_csv}")

    idle_power_watts = successful_idle_power_mean(idle_rows)
    adjusted = adjust_rows(rows, idle_power_watts)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames(adjusted))
        writer.writeheader()
        writer.writerows(adjusted)

    print(f"Wrote {output_csv}")
    print(f"Rows adjusted: {len(adjusted)}")
    print(f"Idle average power used: {idle_power_watts:.9f} W")

    if args.output_summary_json:
        summary = {
            "input_csv": str(input_csv),
            "idle_runs_csv": str(idle_runs_csv),
            "output_csv": str(output_csv),
            "rows_adjusted": len(adjusted),
            "idle_avg_power_watts_mean": idle_power_watts,
            "adjustment": (
                "energy_joules = max(0, energy_joules_raw - "
                "idle_avg_power_watts_mean * elapsed_seconds); "
                "avg_power_watts = energy_joules / elapsed_seconds"
            ),
        }
        summary_path = args.output_summary_json.resolve()
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {summary_path}")


if __name__ == "__main__":
    main()
