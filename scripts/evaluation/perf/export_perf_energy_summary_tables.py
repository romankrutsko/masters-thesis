#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
INPUT_CSV = ROOT / "results/statistical_analysis/nonparametric_perf_energy/mann_whitney_vs_original.csv"
OUTPUT_DIR = ROOT / "results/statistical_analysis/nonparametric_perf_energy/summary_tables"

METRICS = ["elapsed_seconds", "energy_joules"]
GROUPINGS = {
    "by_language": ["language"],
    "by_model": ["model"],
    "by_prompt_type": ["prompt_type"],
    "by_model_language": ["model", "language"],
    "by_model_prompt_type": ["model", "prompt_type"],
}


def summarize_group(group: pd.DataFrame, metric: str) -> pd.Series:
    diff = f"{metric}_mean_pct_diff_vs_original"
    sig = f"{metric}_p_value_fdr_bh"
    return pd.Series(
        {
            "n_candidates": len(group),
            "lower_than_original": int((group[diff] < 0).sum()),
            "higher_than_original": int((group[diff] > 0).sum()),
            "significant_lower": int(((group[diff] < 0) & (group[sig] < 0.05)).sum()),
            "significant_higher": int(((group[diff] > 0) & (group[sig] < 0.05)).sum()),
            "nonsignificant": int((group[sig] >= 0.05).sum()),
            "median_pct_diff": float(group[diff].median()),
            "median_abs_pct_diff": float(group[diff].abs().median()),
            "min_pct_diff": float(group[diff].min()),
            "max_pct_diff": float(group[diff].max()),
        }
    )


def write_group_tables(df: pd.DataFrame) -> None:
    for metric in METRICS:
        for name, columns in GROUPINGS.items():
            summary = (
                df.groupby(columns)
                .apply(lambda g: summarize_group(g, metric), include_groups=False)
                .reset_index()
                .sort_values(columns)
            )
            summary.to_csv(OUTPUT_DIR / f"{metric}_{name}.csv", index=False)


def write_top_tables(df: pd.DataFrame, top_n: int = 10) -> None:
    id_cols = ["model", "prompt_type", "language", "category", "snippet"]
    for metric in METRICS:
        diff = f"{metric}_mean_pct_diff_vs_original"
        sig = f"{metric}_p_value_fdr_bh"
        cols = id_cols + [diff, sig]

        fastest = df.sort_values(diff).head(top_n)[cols]
        slowest = df.sort_values(diff, ascending=False).head(top_n)[cols]

        fastest.to_csv(OUTPUT_DIR / f"{metric}_top_lower.csv", index=False)
        slowest.to_csv(OUTPUT_DIR / f"{metric}_top_higher.csv", index=False)


def write_overview(df: pd.DataFrame) -> None:
    rows = []
    for metric in METRICS:
        diff = f"{metric}_mean_pct_diff_vs_original"
        sig = f"{metric}_p_value_fdr_bh"
        rows.append(
            {
                "metric": metric,
                "n_candidates": len(df),
                "lower_than_original": int((df[diff] < 0).sum()),
                "higher_than_original": int((df[diff] > 0).sum()),
                "significant_lower": int(((df[diff] < 0) & (df[sig] < 0.05)).sum()),
                "significant_higher": int(((df[diff] > 0) & (df[sig] < 0.05)).sum()),
                "nonsignificant": int((df[sig] >= 0.05).sum()),
                "median_pct_diff": float(df[diff].median()),
                "median_abs_pct_diff": float(df[diff].abs().median()),
            }
        )
    pd.DataFrame(rows).to_csv(OUTPUT_DIR / "overview.csv", index=False)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT_CSV)
    write_overview(df)
    write_group_tables(df)
    write_top_tables(df)
    print(f"Wrote summary tables to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
