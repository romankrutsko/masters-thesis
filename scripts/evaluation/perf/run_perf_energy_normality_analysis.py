#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ORIGINAL_CSV = ROOT / "results/perf_energy_runs/original_30x_60s_cpu2/perf_energy_runs.csv"
DEFAULT_TRANSLATIONS_CSV = ROOT / "results/perf_energy_runs/run_30x_60s_cpu2/perf_energy_runs.csv"
DEFAULT_OUTPUT_DIR = ROOT / "results/statistical_analysis/perf_energy_normality"

METRICS = ["elapsed_seconds", "energy_joules", "avg_power_watts"]
BASE_GROUP_KEYS = ["model", "prompt_type", "language", "category", "snippet"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Assess normality of completed runtime/energy benchmark samples."
    )
    parser.add_argument("--original-csv", type=Path, default=DEFAULT_ORIGINAL_CSV)
    parser.add_argument("--translations-csv", type=Path, default=DEFAULT_TRANSLATIONS_CSV)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def load_dataset(path: Path, dataset: str) -> pd.DataFrame:
    # Normality is assessed only on successful measured runs, not warmups or failures.
    frame = pd.read_csv(path)
    frame = frame.loc[frame["status"].eq("ok")].copy()
    frame["dataset"] = dataset
    if "script_id" not in frame.columns:
        frame["script_id"] = ""
    else:
        frame["script_id"] = frame["script_id"].fillna("")
    for metric in METRICS:
        frame[metric] = pd.to_numeric(frame[metric], errors="coerce")
    return frame


def group_keys_for(frame: pd.DataFrame) -> list[str]:
    return ["dataset", "script_id"] + BASE_GROUP_KEYS


def shapiro(values: np.ndarray) -> tuple[float | None, float | None, str]:
    # Shapiro-Wilk needs at least 3 observations and cannot assess a constant sample.
    values = values[np.isfinite(values)]
    if values.size < 3:
        return None, None, "too_few_values"
    if np.all(values == values[0]):
        return None, None, "constant_values"
    test = stats.shapiro(values)
    return float(test.statistic), float(test.pvalue), ""


def describe_group(group_key: tuple[object, ...], group_cols: list[str], metric: str, group: pd.DataFrame) -> dict[str, object]:
    # Analyze the 30 measured values for one script and one metric.
    values = group[metric].dropna().to_numpy(dtype=float)

    # run Shapiro-Wilk tests.
    shapiro_w, shapiro_p, note = shapiro(values)

    # Constant samples cannot have meaningful skewness or kurtosis.
    has_variation = values.size > 1 and not np.all(values == values[0])

    row: dict[str, object] = dict(zip(group_cols, group_key))
    row.update(
        {
            "metric": metric,
            "n": int(values.size),
            "mean": float(np.mean(values)) if values.size else np.nan,
            "median": float(np.median(values)) if values.size else np.nan,
            "std": float(np.std(values, ddof=1)) if values.size > 1 else np.nan,
            "min": float(np.min(values)) if values.size else np.nan,
            "max": float(np.max(values)) if values.size else np.nan,
            "skewness": float(stats.skew(values, bias=False)) if values.size > 2 and has_variation else np.nan,
            "kurtosis_excess": float(stats.kurtosis(values, bias=False)) if values.size > 3 and has_variation else np.nan,
            "shapiro_w": np.nan if shapiro_w is None else shapiro_w,
            "shapiro_p_value": np.nan if shapiro_p is None else shapiro_p,
            # True means p < 0.05, so the sample is treated as non-normal for reporting.
            "normality_rejected_0_05": bool(shapiro_p < 0.05) if shapiro_p is not None else "",
            "note": note,
        }
    )
    return row


def build_normality_table(frame: pd.DataFrame) -> pd.DataFrame:
    group_cols = group_keys_for(frame)
    rows: list[dict[str, object]] = []
    for group_key, group in frame.groupby(group_cols):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        for metric in METRICS:
            rows.append(describe_group(group_key, group_cols, metric, group))
    return pd.DataFrame(rows).sort_values(group_cols + ["metric"]).reset_index(drop=True)


def build_summary(normality: pd.DataFrame) -> dict[str, object]:
    # Summarize how often normality was rejected by dataset and metric.
    tested = normality.loc[normality["note"].eq("")].copy()
    summary: dict[str, object] = {
        "total_rows": int(len(normality)),
        "tested_rows": int(len(tested)),
        "untested_rows": int(len(normality) - len(tested)),
        "normality_rejected_0_05": int(tested["normality_rejected_0_05"].sum()) if not tested.empty else 0,
        "by_dataset_metric": [],
    }

    for (dataset, metric), group in tested.groupby(["dataset", "metric"]):
        summary["by_dataset_metric"].append(
            {
                "dataset": dataset,
                "metric": metric,
                "tested_groups": int(len(group)),
                "normality_rejected_0_05": int(group["normality_rejected_0_05"].sum()),
                "normality_rejected_share": float(group["normality_rejected_0_05"].mean()),
                "median_shapiro_p_value": float(group["shapiro_p_value"].median()),
            }
        )
    return summary


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    original = load_dataset(args.original_csv.resolve(), "original")
    translations = load_dataset(args.translations_csv.resolve(), "translation")
    combined = pd.concat([original, translations], ignore_index=True, sort=False)

    normality = build_normality_table(combined)
    summary = build_summary(normality)

    normality.to_csv(output_dir / "normality_by_script_metric.csv", index=False)
    with open(output_dir / "summary.json", "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    print(f"Wrote {output_dir / 'normality_by_script_metric.csv'}")
    print(f"Wrote {output_dir / 'summary.json'}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
