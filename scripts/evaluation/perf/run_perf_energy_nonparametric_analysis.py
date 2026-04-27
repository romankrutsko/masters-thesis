#!/usr/bin/env python3

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parents[3]
ORIGINAL_CSV = ROOT / "results/perf_energy_runs/original_100x_60s_cpu2/perf_energy_runs.csv"
TRANSLATIONS_CSV = ROOT / "results/perf_energy_runs/run_100x_60s_cpu2/perf_energy_runs.csv"
OUTPUT_DIR = ROOT / "results/statistical_analysis/nonparametric_perf_energy"

MATCH_KEYS = ["language", "category", "snippet"]
GROUP_KEYS = ["model", "prompt_type", "language", "category", "snippet"]
METRICS = ["elapsed_seconds", "energy_joules", "avg_power_watts"]


@dataclass(frozen=True)
class SpearmanGroup:
    name: str
    columns: list[str]


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    original = pd.read_csv(ORIGINAL_CSV)
    translations = pd.read_csv(TRANSLATIONS_CSV)

    original = original.loc[original["status"] == "ok"].copy()
    translations = translations.loc[translations["status"] == "ok"].copy()

    for frame in (original, translations):
        for metric in METRICS:
            frame[metric] = pd.to_numeric(frame[metric], errors="coerce")

    return original, translations


def rank_biserial_from_u(u_stat: float, n1: int, n2: int) -> float:
    return (2.0 * u_stat) / (n1 * n2) - 1.0


def cliffs_delta(x: np.ndarray, y: np.ndarray) -> float:
    # With n=100 per group, the O(n*m) comparison is still trivial.
    diffs = np.subtract.outer(x, y)
    return (np.sum(diffs > 0) - np.sum(diffs < 0)) / (x.size * y.size)


def benjamini_hochberg(p_values: pd.Series) -> pd.Series:
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
            row[f"{metric}_cliffs_delta"] = float(cliffs_delta(x, y))

        rows.append(row)

    results = pd.DataFrame(rows).sort_values(GROUP_KEYS).reset_index(drop=True)
    for metric in METRICS:
        p_col = f"{metric}_p_value"
        results[f"{metric}_p_value_fdr_bh"] = benjamini_hochberg(results[p_col])
    return results


def spearman_table(df: pd.DataFrame, group_name: str, group_cols: list[str]) -> pd.DataFrame:
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
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    original, translations = load_data()
    mann_whitney = run_mann_whitney(original, translations)
    spearman = run_spearman(original, translations)
    summary = build_summary(mann_whitney, spearman)

    mann_whitney.to_csv(OUTPUT_DIR / "mann_whitney_vs_original.csv", index=False)
    spearman.to_csv(OUTPUT_DIR / "spearman_elapsed_vs_energy.csv", index=False)
    with open(OUTPUT_DIR / "summary.json", "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    print(f"Wrote {OUTPUT_DIR / 'mann_whitney_vs_original.csv'}")
    print(f"Wrote {OUTPUT_DIR / 'spearman_elapsed_vs_energy.csv'}")
    print(f"Wrote {OUTPUT_DIR / 'summary.json'}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
