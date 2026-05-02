#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ORIGINAL_CSV = ROOT / "results/perf_energy_runs/original_30x_60s_cpu2/perf_energy_runs.csv"
DEFAULT_TRANSLATIONS_CSV = ROOT / "results/perf_energy_runs/run_30x_60s_cpu2/perf_energy_runs.csv"
DEFAULT_OUTPUT_DIR = ROOT / "results/statistical_analysis/nonparametric_perf_energy"

# These columns identify the original task that a translation should be compared with.
MATCH_KEYS = ["language", "category", "snippet"]
# These columns identify one translated candidate implementation.
GROUP_KEYS = ["model", "prompt_type", "language", "category", "snippet"]
METRICS = ["elapsed_seconds", "energy_joules", "avg_power_watts"]


@dataclass(frozen=True)
class SpearmanGroup:
    name: str
    columns: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run nonparametric runtime/energy comparisons against original baselines."
    )
    parser.add_argument("--original-csv", type=Path, default=DEFAULT_ORIGINAL_CSV)
    parser.add_argument("--translations-csv", type=Path, default=DEFAULT_TRANSLATIONS_CSV)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def load_data(original_csv: Path, translations_csv: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    # Only successful benchmark rows are valid inputs for statistical comparison.
    original = pd.read_csv(original_csv)
    translations = pd.read_csv(translations_csv)

    original = original.loc[original["status"] == "ok"].copy()
    translations = translations.loc[translations["status"] == "ok"].copy()

    for frame in (original, translations):
        for metric in METRICS:
            frame[metric] = pd.to_numeric(frame[metric], errors="coerce")

    return original, translations


def rank_biserial_from_u(u_stat: float, n1: int, n2: int) -> float:
    # Convert Mann-Whitney U into an effect size in the [-1, 1] range.
    return (2.0 * u_stat) / (n1 * n2) - 1.0


def cliffs_delta(x: np.ndarray, y: np.ndarray) -> float:
    # With n=30 per group, the O(n*m) comparison is still trivial.
    diffs = np.subtract.outer(x, y)
    return (np.sum(diffs > 0) - np.sum(diffs < 0)) / (x.size * y.size)


def cliffs_delta_magnitude(delta: float) -> str:
    # Common Romano-style thresholds for Cliff's delta.
    abs_delta = abs(delta)
    if abs_delta < 0.147:
        return "negligible"
    if abs_delta < 0.33:
        return "small"
    if abs_delta < 0.474:
        return "medium"
    return "large"


def cliffs_delta_direction(delta: float, metric: str) -> str:
    if delta > 0:
        return f"candidate_higher_{metric}"
    if delta < 0:
        return f"candidate_lower_{metric}"
    return "no_direction"


def benjamini_hochberg(p_values: pd.Series) -> pd.Series:
    # FDR correction controls false discoveries across many candidate tests.
    p = p_values.to_numpy(dtype=float)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order]
    adjusted = np.empty(n, dtype=float)
    prev = 1.0
    for i in range(n - 1, -1, -1):
        rank = i + 1
        value = ranked[i] * n / rank
        prev = min(prev, value)
        adjusted[i] = prev
    result = np.empty(n, dtype=float)
    result[order] = np.clip(adjusted, 0.0, 1.0)
    return pd.Series(result, index=p_values.index)


def run_mann_whitney(original: pd.DataFrame, translations: pd.DataFrame) -> pd.DataFrame:
    # Compare each translated candidate against the original script for the same task.
    original_groups = {
        key: group.sort_values("run_id").reset_index(drop=True)
        for key, group in original.groupby(MATCH_KEYS)
    }

    rows: list[dict[str, object]] = []
    for group_key, candidate in translations.groupby(GROUP_KEYS):
        match_key = group_key[2:]
        baseline = original_groups.get(match_key)
        if baseline is None:
            continue

        candidate = candidate.sort_values("run_id").reset_index(drop=True)
        row = dict(zip(GROUP_KEYS, group_key))
        row["matched_original_model"] = "original"
        row["candidate_runs"] = int(len(candidate))
        row["original_runs"] = int(len(baseline))

        for metric in METRICS:
            x = candidate[metric].to_numpy(dtype=float)
            y = baseline[metric].to_numpy(dtype=float)

            test = stats.mannwhitneyu(x, y, alternative="two-sided", method="asymptotic")
            candidate_mean = float(np.mean(x))
            original_mean = float(np.mean(y))
            candidate_median = float(np.median(x))
            original_median = float(np.median(y))

            row[f"{metric}_u_stat"] = float(test.statistic)
            row[f"{metric}_p_value"] = float(test.pvalue)
            row[f"{metric}_candidate_mean"] = candidate_mean
            row[f"{metric}_original_mean"] = original_mean
            row[f"{metric}_candidate_median"] = candidate_median
            row[f"{metric}_original_median"] = original_median
            row[f"{metric}_mean_pct_diff_vs_original"] = (
                (candidate_mean - original_mean) / original_mean * 100.0
            )
            row[f"{metric}_median_pct_diff_vs_original"] = (
                (candidate_median - original_median) / original_median * 100.0
            )
            row[f"{metric}_rank_biserial"] = rank_biserial_from_u(
                float(test.statistic), len(x), len(y)
            )
            delta = float(cliffs_delta(x, y))
            row[f"{metric}_cliffs_delta"] = delta
            row[f"{metric}_cliffs_delta_abs"] = abs(delta)
            row[f"{metric}_cliffs_delta_magnitude"] = cliffs_delta_magnitude(delta)
            row[f"{metric}_cliffs_delta_direction"] = cliffs_delta_direction(delta, metric)

        rows.append(row)

    results = pd.DataFrame(rows).sort_values(GROUP_KEYS).reset_index(drop=True)
    for metric in METRICS:
        p_col = f"{metric}_p_value"
        results[f"{metric}_p_value_fdr_bh"] = benjamini_hochberg(results[p_col])
    return results


def spearman_table(df: pd.DataFrame, group_name: str, group_cols: list[str]) -> pd.DataFrame:
    # Summarize whether elapsed time and energy move together within each grouping.
    rows: list[dict[str, object]] = []
    for key, group in df.groupby(group_cols):
        if not isinstance(key, tuple):
            key = (key,)
        rho, p_value = stats.spearmanr(group["elapsed_seconds"], group["energy_joules"])
        row = {
            "group_name": group_name,
            "n_runs": int(len(group)),
            "spearman_rho_elapsed_vs_energy": float(rho),
            "p_value": float(p_value),
            "elapsed_mean": float(group["elapsed_seconds"].mean()),
            "energy_mean": float(group["energy_joules"].mean()),
        }
        row.update(dict(zip(group_cols, key)))
        rows.append(row)
    return pd.DataFrame(rows)


def run_spearman(original: pd.DataFrame, translations: pd.DataFrame) -> pd.DataFrame:
    # Combine originals and translations so the correlation is reported at several granularities.
    combined = pd.concat([original, translations], ignore_index=True)
    combined["dataset"] = np.where(combined["model"].eq("original"), "original", "translation")

    group_specs = [
        SpearmanGroup("overall_by_dataset", ["dataset"]),
        SpearmanGroup("by_model_prompt_language", ["model", "prompt_type", "language"]),
        SpearmanGroup("by_candidate", GROUP_KEYS),
    ]

    tables = [spearman_table(combined, spec.name, spec.columns) for spec in group_specs]
    results = pd.concat(tables, ignore_index=True, sort=False)
    results["p_value_fdr_bh"] = benjamini_hochberg(results["p_value"])
    return results


def build_summary(mw: pd.DataFrame, sp: pd.DataFrame) -> dict[str, object]:
    # Keep a compact JSON overview for thesis tables and quick sanity checks.
    summary: dict[str, object] = {
        "mann_whitney_candidate_count": int(len(mw)),
        "spearman_group_count": int(len(sp)),
        "mann_whitney_significant_counts_fdr_bh": {},
        "spearman_significant_count_fdr_bh": int((sp["p_value_fdr_bh"] < 0.05).sum()),
    }

    for metric in METRICS:
        summary["mann_whitney_significant_counts_fdr_bh"][metric] = int(
            (mw[f"{metric}_p_value_fdr_bh"] < 0.05).sum()
        )

    overall = sp.loc[sp["group_name"].eq("overall_by_dataset"), [
        "dataset",
        "n_runs",
        "spearman_rho_elapsed_vs_energy",
        "p_value",
        "p_value_fdr_bh",
    ]]
    summary["overall_spearman_elapsed_vs_energy"] = overall.to_dict(orient="records")
    return summary


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    original, translations = load_data(args.original_csv.resolve(), args.translations_csv.resolve())
    mann_whitney = run_mann_whitney(original, translations)
    spearman = run_spearman(original, translations)
    summary = build_summary(mann_whitney, spearman)

    mann_whitney.to_csv(output_dir / "mann_whitney_vs_original.csv", index=False)
    spearman.to_csv(output_dir / "spearman_elapsed_vs_energy.csv", index=False)
    with open(output_dir / "summary.json", "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    print(f"Wrote {output_dir / 'mann_whitney_vs_original.csv'}")
    print(f"Wrote {output_dir / 'spearman_elapsed_vs_energy.csv'}")
    print(f"Wrote {output_dir / 'summary.json'}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
