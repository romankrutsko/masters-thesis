#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT = (
    ROOT
    / "results/statistical_analysis/nonparametric_perf_energy_30x_60s_cpu2_idle_adjusted_final/mann_whitney_vs_original.csv"
)
DEFAULT_OUTPUT = (
    ROOT
    / "results/statistical_analysis/nonparametric_perf_energy_30x_60s_cpu2_idle_adjusted_final/summary_tables/mann_whitney_by_model_runtime_energy.csv"
)

METRICS = {
    "elapsed_seconds": "Runtime",
    "energy_joules": "Energy",
}

MODEL_LABELS = {
    "gemini": "Gemini 3.1 Pro",
    "gpt": "GPT-5.4",
    "llama": "Llama 4 Maverick Instruct",
    "starcoder": "StarCoder2-15B Instruct",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize existing Mann-Whitney runtime and energy results by model."
    )
    parser.add_argument("--input-csv", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--alpha", type=float, default=0.05)
    return parser.parse_args()


def summarize(df: pd.DataFrame, alpha: float) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for model, group in df.groupby("model", sort=True):
        for metric, metric_label in METRICS.items():
            p_col = f"{metric}_p_value_fdr_bh"
            diff_col = f"{metric}_mean_pct_diff_vs_original"
            significant = group[p_col] < alpha
            lower = group[diff_col] < 0
            higher = group[diff_col] > 0

            rows.append(
                {
                    "model": MODEL_LABELS.get(model, model),
                    "metric": metric_label,
                    "tested_snippets": int(len(group)),
                    "significant_snippets": int(significant.sum()),
                    "significant_share_pct": round(float(significant.mean() * 100.0), 2),
                    "significant_lower": int((significant & lower).sum()),
                    "significant_higher": int((significant & higher).sum()),
                    "not_significant": int((~significant).sum()),
                    "mean_pct_diff_vs_original": round(float(group[diff_col].mean()), 3),
                    "median_pct_diff_vs_original": round(float(group[diff_col].median()), 3),
                }
            )

    order = {label: i for i, label in enumerate(MODEL_LABELS.values())}
    result = pd.DataFrame(rows)
    result["_model_order"] = result["model"].map(order)
    result["_metric_order"] = result["metric"].map({"Runtime": 0, "Energy": 1})
    result = result.sort_values(["_model_order", "_metric_order"]).drop(
        columns=["_model_order", "_metric_order"]
    )
    return result


def main() -> None:
    args = parse_args()
    df = pd.read_csv(args.input_csv)
    result = summarize(df, args.alpha)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output_csv, index=False)
    print(f"Wrote {args.output_csv}")
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
