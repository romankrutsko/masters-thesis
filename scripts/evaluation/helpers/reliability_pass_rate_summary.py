#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize reliability pass/fail counts and pass rates."
    )
    parser.add_argument("--input-csv", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SystemExit(f"Input CSV is empty: {path}")
    for column in ("model", "language", "status"):
        if column not in rows[0]:
            raise SystemExit(f"Input CSV is missing required column: {column}")
    return rows


def score(row: dict[str, str]) -> float:
    if row["status"] != "ok":
        return 0.0
    raw = row.get("score", "").strip()
    return float(raw) if raw else 0.0


def ok_score(row: dict[str, str]) -> float | None:
    if row["status"] != "ok":
        return None
    raw = row.get("score", "").strip()
    return float(raw) if raw else None


def label(value: str) -> str:
    names = {
        "gemini": "Gemini",
        "gpt": "GPT",
        "llama": "Llama",
        "starcoder": "StarCoder",
        "python": "Python",
        "r": "R",
        "base": "Base",
        "optimized": "Optimized",
    }
    return names.get(value, value)


def summarize(rows: list[dict[str, str]], group_columns: list[str]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[column] for column in group_columns)].append(row)

    out: list[dict[str, str]] = []
    for group_values in sorted(grouped):
        group_rows = grouped[group_values]
        total = len(group_rows)
        passed = sum(1 for row in group_rows if row["status"] == "ok")
        failed = total - passed
        ok_scores = [
            value for value in (ok_score(row) for row in group_rows)
            if value is not None
        ]
        penalized_mean = sum(score(row) for row in group_rows) / total
        ok_mean = sum(ok_scores) / len(ok_scores) if ok_scores else 0.0
        out_row = {
            "Total": str(total),
            "Passed": str(passed),
            "Failed": str(failed),
            "Pass rate": f"{passed / total:.4f}",
            "Pass rate (%)": f"{passed / total * 100:.2f}",
            "Mean reliability score": f"{penalized_mean:.4f}",
            "Mean reliability score (%)": f"{penalized_mean * 100:.2f}",
            "Mean score among passed": f"{ok_mean:.4f}",
        }
        for column, value in reversed(list(zip(group_columns, group_values))):
            out_row = {label(column): label(value), **out_row}
        out.append(out_row)
    return out


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        raise SystemExit(f"No rows to write: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    input_csv = args.input_csv.resolve()
    output_dir = args.output_dir.resolve()
    rows = read_rows(input_csv)

    by_model = summarize(rows, ["model"])
    by_language = summarize(rows, ["language"])
    by_prompt_type = summarize(rows, ["prompt_type"])
    by_model_prompt_type = summarize(rows, ["model", "prompt_type"])

    model_csv = output_dir / "reliability_pass_rate_by_model.csv"
    language_csv = output_dir / "reliability_pass_rate_by_language.csv"
    prompt_type_csv = output_dir / "reliability_pass_rate_by_prompt_type.csv"
    model_prompt_type_csv = output_dir / "reliability_pass_rate_by_model_prompt_type.csv"
    summary_json = output_dir / "reliability_pass_rate_summary.json"

    write_csv(model_csv, by_model)
    write_csv(language_csv, by_language)
    write_csv(prompt_type_csv, by_prompt_type)
    write_csv(model_prompt_type_csv, by_model_prompt_type)

    total = len(rows)
    passed = sum(1 for row in rows if row["status"] == "ok")
    ok_scores = [
        value for value in (ok_score(row) for row in rows)
        if value is not None
    ]
    penalized_mean = sum(score(row) for row in rows) / total
    ok_mean = sum(ok_scores) / len(ok_scores) if ok_scores else 0.0
    summary = {
        "input_csv": str(input_csv),
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": passed / total,
        "pass_rate_percent": passed / total * 100,
        "mean_reliability_score": penalized_mean,
        "mean_reliability_score_percent": penalized_mean * 100,
        "mean_score_among_passed": ok_mean,
        "by_model_csv": str(model_csv),
        "by_language_csv": str(language_csv),
        "by_prompt_type_csv": str(prompt_type_csv),
        "by_model_prompt_type_csv": str(model_prompt_type_csv),
    }
    summary_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {model_csv}")
    print(f"Wrote {language_csv}")
    print(f"Wrote {prompt_type_csv}")
    print(f"Wrote {model_prompt_type_csv}")
    print(f"Wrote {summary_json}")


if __name__ == "__main__":
    main()
