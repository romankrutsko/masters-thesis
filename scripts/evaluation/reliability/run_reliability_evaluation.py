#!/usr/bin/env python3
"""Run execution-based reliability scoring for translated snippets only."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from evaluation_common import (
    DEFAULT_BLACKLIST_FILE,
    DEFAULT_OUTPUT_ROOT,
    REF_ROOTS,
    REPO_ROOT,
    LLM_ROOT,
    Candidate,
    discover_candidates,
    ensure_dir,
    filter_candidates,
    load_module,
    now_stamp,
    write_run_manifest,
    to_rel,
)

BASE_WEIGHTS = {
    "kinds": 0.25,
    "shapes": 0.25,
    "vectors": 0.15,
    "models": 0.20,
    "numeric": 0.15,
}


def finite_float(x: object) -> float | None:
    if isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        fx = float(x)
        if fx == fx and fx not in (float("inf"), float("-inf")):
            return fx
    return None


def collect_numeric_values(x: object, out: list[float]) -> None:
    if isinstance(x, dict):
        for v in x.values():
            collect_numeric_values(v, out)
        return
    if isinstance(x, list):
        for v in x:
            collect_numeric_values(v, out)
        return
    fx = finite_float(x)
    if fx is not None:
        out.append(fx)


def summarize_kind(item: dict) -> tuple[str, tuple[int, int] | tuple[int] | None]:
    typ = str(item.get("type", "unknown"))

    if typ in {"DataFrame", "data.frame"}:
        if "shape" in item and isinstance(item["shape"], list) and len(item["shape"]) == 2:
            return "table", (int(item["shape"][0]), int(item["shape"][1]))
        return "table", (int(item.get("nrow", 0)), int(item.get("ncol", 0)))

    if typ in {"ndarray", "matrix"}:
        dim = item.get("shape", item.get("dim", []))
        if isinstance(dim, list) and len(dim) == 2:
            return "matrix", (int(dim[0]), int(dim[1]))
        return "matrix", None

    if typ in {"Series", "numeric", "factor", "character"}:
        ln = item.get("length", 0)
        try:
            return "vector", (int(ln),)
        except Exception:
            return "vector", None

    if typ in {"scalar"}:
        return "scalar", None

    if typ in {"lm", "glm", "OLSResults", "GLMResults", "cv.glmnet", "tune", "gbm"}:
        return "model", None

    if "params" in item or "coef" in item or "model" in item:
        return "model", None

    return "other", None


def extract_profile(var_summary: dict, digits: int) -> dict[str, Any]:
    kinds = Counter()
    shapes = Counter()
    vector_lengths = Counter()
    model_sizes = Counter()
    numeric_values: list[float] = []

    # Reduce a full execution snapshot into a small structural fingerprint.
    for obj in var_summary.values():
        if not isinstance(obj, dict):
            continue

        kind, shape = summarize_kind(obj)
        kinds[kind] += 1

        if kind in {"table", "matrix"} and shape is not None and len(shape) == 2:
            shapes[(int(shape[0]), int(shape[1]))] += 1
        if kind == "vector" and shape is not None and len(shape) == 1:
            vector_lengths[(int(shape[0]),)] += 1

        if "params" in obj and isinstance(obj["params"], list):
            model_sizes[len(obj["params"])] += 1
        if "coef" in obj:
            if isinstance(obj["coef"], list):
                model_sizes[len(obj["coef"])] += 1
            elif isinstance(obj["coef"], dict):
                model_sizes[len(obj["coef"].keys())] += 1
        if "model" in obj and isinstance(obj["model"], dict):
            model_sizes[len(obj["model"].keys())] += 1

        for k in ("mean", "std", "sd", "sum", "min", "max", "numeric_means", "numeric_sds", "top_rel_inf"):
            if k in obj:
                collect_numeric_values(obj[k], numeric_values)

    rounded = sorted(round(v, digits) for v in numeric_values)
    if len(rounded) > 200:
        rounded = rounded[:200]

    return {
        "kinds": kinds,
        "shapes": shapes,
        "vector_lengths": vector_lengths,
        "model_sizes": model_sizes,
        "numeric_values": rounded,
    }


def counter_overlap(ref: Counter, cand: Counter) -> float:
    total = sum(ref.values())
    if total == 0:
        return 1.0
    matched = sum(min(v, cand.get(k, 0)) for k, v in ref.items())
    return matched / total


def numeric_overlap(ref_vals: list[float], cand_vals: list[float], atol: float, rtol: float) -> float:
    if not ref_vals:
        return 1.0
    if not cand_vals:
        return 0.0

    used = [False] * len(cand_vals)
    matched = 0

    for rv in ref_vals:
        best_idx = -1
        best_dist = float("inf")
        for i, cv in enumerate(cand_vals):
            if used[i]:
                continue
            dist = abs(rv - cv)
            tol = atol + rtol * abs(rv)
            if dist <= tol and dist < best_dist:
                best_dist = dist
                best_idx = i
        if best_idx >= 0:
            used[best_idx] = True
            matched += 1

    return matched / len(ref_vals)


def weighted_score(ref_profile: dict[str, Any], cand_profile: dict[str, Any], atol: float, rtol: float) -> tuple[float, dict[str, float], dict[str, float]]:
    components = {
        "kinds": counter_overlap(ref_profile["kinds"], cand_profile["kinds"]),
        "shapes": counter_overlap(ref_profile["shapes"], cand_profile["shapes"]),
        "vectors": counter_overlap(ref_profile["vector_lengths"], cand_profile["vector_lengths"]),
        "models": counter_overlap(ref_profile["model_sizes"], cand_profile["model_sizes"]),
        "numeric": numeric_overlap(ref_profile["numeric_values"], cand_profile["numeric_values"], atol=atol, rtol=rtol),
    }

    # Ignore empty reference components so we do not reward/penalize noise.
    active_weights: dict[str, float] = {}
    for key, w in BASE_WEIGHTS.items():
        ref_component_empty = False
        if key == "kinds":
            ref_component_empty = sum(ref_profile["kinds"].values()) == 0
        elif key == "shapes":
            ref_component_empty = sum(ref_profile["shapes"].values()) == 0
        elif key == "vectors":
            ref_component_empty = sum(ref_profile["vector_lengths"].values()) == 0
        elif key == "models":
            ref_component_empty = sum(ref_profile["model_sizes"].values()) == 0
        elif key == "numeric":
            ref_component_empty = len(ref_profile["numeric_values"]) == 0
        if not ref_component_empty:
            active_weights[key] = w

    denom = sum(active_weights.values()) or 1.0
    score = sum(components[k] * active_weights[k] for k in active_weights) / denom
    return score, components, active_weights


def run_script(mod, language: str, path: Path, python_bin: str, rscript_bin: str, timeout_sec: float | None = None) -> dict[str, Any]:
    if language == "python":
        return mod.run_python_baseline(path, python_bin=python_bin, timeout_sec=timeout_sec)
    return mod.run_r_baseline(path, rscript_bin=rscript_bin, timeout_sec=timeout_sec)


def evaluate_execution(
    candidates: list[Candidate],
    python_bin: str,
    rscript_bin: str,
    execution_timeout: float | None,
    digits: int,
    atol: float,
    rtol: float,
    score_decimals: int,
    output_dir: Path,
) -> dict[str, Any]:
    gb = load_module(REPO_ROOT / "scripts" / "evaluation" / "reliability" / "generate_baselines.py", "generate_baselines")

    rows: list[dict[str, Any]] = []
    per_slice_scores: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    total = len(candidates)

    for idx, c in enumerate(candidates, start=1):
        print(f"[reliability {idx}/{total}] {c.model}/{c.prompt_type}/{c.language}/{c.category}/{c.snippet_id}")
        ref_root = REF_ROOTS[c.language]
        ref_path = ref_root / c.category / c.path.name

        row: dict[str, Any] = {
            "model": c.model,
            "prompt_type": c.prompt_type,
            "language": c.language,
            "category": c.category,
            "snippet_id": c.snippet_id,
            "candidate_path": to_rel(c.path),
            "reference_path": to_rel(ref_path),
            "status": "ok",
            "score": 0.0,
            "kinds": 0.0,
            "shapes": 0.0,
            "vectors": 0.0,
            "models": 0.0,
            "numeric": 0.0,
            "error": "",
        }

        if not ref_path.exists():
            row["status"] = "missing_reference"
            row["error"] = "Reference file not found"
            rows.append(row)
            print("  -> missing reference")
            continue

        # Run the original reference first so each candidate is compared to the
        # same canonical script for the task.
        ref_run = run_script(gb, c.language, ref_path, python_bin=python_bin, rscript_bin=rscript_bin, timeout_sec=execution_timeout)
        if ref_run.get("status") != "ok":
            row["status"] = "reference_error"
            row["error"] = (ref_run.get("stderr") or "Reference execution failed").splitlines()[-1] if (ref_run.get("stderr") or "") else "Reference execution failed"
            rows.append(row)
            print(f"  -> reference error: {row['error']}")
            continue

        cand_run = run_script(gb, c.language, c.path, python_bin=python_bin, rscript_bin=rscript_bin, timeout_sec=execution_timeout)
        if cand_run.get("status") != "ok":
            row["status"] = "candidate_error"
            row["error"] = (cand_run.get("stderr") or "Candidate execution failed").splitlines()[-1] if (cand_run.get("stderr") or "") else "Candidate execution failed"
            rows.append(row)
            print(f"  -> candidate error: {row['error']}")
            continue

        # This is a structural/numeric similarity score, not literal equivalence.
        ref_profile = extract_profile(ref_run.get("var_summary", {}), digits)
        cand_profile = extract_profile(cand_run.get("var_summary", {}), digits)
        score, components, _active = weighted_score(ref_profile, cand_profile, atol=atol, rtol=rtol)

        row["score"] = round(score, score_decimals)
        row["kinds"] = round(components["kinds"], score_decimals)
        row["shapes"] = round(components["shapes"], score_decimals)
        row["vectors"] = round(components["vectors"], score_decimals)
        row["models"] = round(components["models"], score_decimals)
        row["numeric"] = round(components["numeric"], score_decimals)

        rows.append(row)
        per_slice_scores[(c.model, c.prompt_type, c.language)].append(row["score"])
        print(f"  -> score={row['score']}")

    csv_path = output_dir / "execution_scores.csv"
    json_path = output_dir / "execution_scores.json"

    fields = [
        "model",
        "prompt_type",
        "language",
        "category",
        "snippet_id",
        "candidate_path",
        "reference_path",
        "status",
        "score",
        "kinds",
        "shapes",
        "vectors",
        "models",
        "numeric",
        "error",
    ]

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    avg_all = sum(r["score"] for r in rows) / len(rows) if rows else 0.0
    slice_summary = []
    for k in sorted(per_slice_scores.keys()):
        vals = per_slice_scores[k]
        slice_summary.append(
            {
                "model": k[0],
                "prompt_type": k[1],
                "language": k[2],
                "avg_score": round(sum(vals) / len(vals), score_decimals) if vals else 0.0,
                "n": len(vals),
            }
        )

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_count": len(candidates),
        "row_count": len(rows),
        "avg_score": round(avg_all, score_decimals),
        "rows": rows,
        "slice_summary": slice_summary,
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    return {
        "rows": rows,
        "csv": csv_path,
        "json": json_path,
        "avg_score": round(avg_all, score_decimals),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run execution-based reliability scoring for llm_translations.")
    parser.add_argument("--python-bin", default=str(REPO_ROOT / ".venv" / "bin" / "python3"))
    parser.add_argument("--rscript-bin", default="Rscript")
    parser.add_argument("--digits", type=int, default=4)
    parser.add_argument("--atol", type=float, default=1e-3)
    parser.add_argument("--rtol", type=float, default=1e-3)
    parser.add_argument("--score-decimals", type=int, default=1)
    parser.add_argument("--execution-timeout", type=float, default=120.0)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--run-id", default="")
    parser.add_argument("--models", default="")
    parser.add_argument("--prompt-types", default="")
    parser.add_argument("--languages", default="")
    parser.add_argument("--blacklist-file", type=Path, default=DEFAULT_BLACKLIST_FILE)
    return parser


def run(args: argparse.Namespace) -> int:
    candidates = discover_candidates(LLM_ROOT)
    candidates, blacklist_entries, blacklisted_candidates = filter_candidates(
        candidates,
        models=args.models,
        prompt_types=args.prompt_types,
        languages=args.languages,
        blacklist_file=args.blacklist_file,
    )
    if not candidates:
        print(f"No candidate files found under: {LLM_ROOT}")
        return 2

    run_id = args.run_id.strip() or now_stamp()
    output_dir = args.output_root / run_id
    ensure_dir(output_dir)
    write_run_manifest(output_dir, "execution", args, candidates, blacklist_entries, blacklisted_candidates)

    print(f"Run ID: {run_id}")
    print(f"Candidates discovered: {len(candidates)}")
    if blacklist_entries:
        print(f"Blacklist file: {args.blacklist_file}")
        print(f"Candidates excluded by blacklist: {len(blacklisted_candidates)}")

    result = evaluate_execution(
        candidates,
        python_bin=args.python_bin,
        rscript_bin=args.rscript_bin,
        execution_timeout=args.execution_timeout,
        digits=args.digits,
        atol=args.atol,
        rtol=args.rtol,
        score_decimals=args.score_decimals,
        output_dir=output_dir,
    )
    print(f"Reliability avg score: {result['avg_score']:.4f}")
    print(f"Reliability CSV: {result['csv']}")
    print(f"Reliability JSON: {result['json']}")
    print(f"All outputs stored in: {output_dir}")
    return 0


def main() -> int:
    return run(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
