#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import math
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_generate_baselines_module():
    mod_path = REPO_ROOT / "task_equivalents" / "tests" / "generate_baselines.py"
    spec = importlib.util.spec_from_file_location("generate_baselines", mod_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def finite_float(x: object) -> float | None:
    if isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        fx = float(x)
        if math.isfinite(fx):
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


def extract_profile(var_summary: dict, digits: int) -> dict:
    kinds = Counter()
    shapes = Counter()
    vector_lengths = Counter()
    model_sizes = Counter()
    numeric_values: list[float] = []

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

    rounded = sorted(round(v, digits) for v in numeric_values if math.isfinite(v))
    # Keep this bounded for stable comparisons and readable reporting.
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


def run_script(mod, language: str, path: Path, python_bin: str, rscript_bin: str) -> dict:
    if language == "python":
        return mod.run_python_baseline(path, python_bin=python_bin)
    return mod.run_r_baseline(path, rscript_bin=rscript_bin)


def collect_files(root: Path, language: str) -> list[Path]:
    suffix = ".py" if language == "python" else ".R"
    return sorted(root.rglob(f"*{suffix}"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Relaxed behavioral verification against canonical task_equivalents scripts."
    )
    parser.add_argument("--language", choices=["python", "r"], required=True)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--reference-root", type=Path, required=True)
    parser.add_argument("--python-bin", default=str(REPO_ROOT / ".venv" / "bin" / "python3"))
    parser.add_argument("--rscript-bin", default="Rscript")
    parser.add_argument("--digits", type=int, default=4, help="Rounding digits for numeric fingerprints.")
    parser.add_argument("--atol", type=float, default=1e-3)
    parser.add_argument("--rtol", type=float, default=1e-3)
    parser.add_argument("--min-score", type=float, default=0.65, help="Minimum weighted similarity score per file.")
    parser.add_argument("--max-details", type=int, default=30)
    parser.add_argument(
        "--skip-reference-errors",
        action="store_true",
        help="Skip files whose reference execution fails in the current environment.",
    )
    args = parser.parse_args()

    cand_root = args.candidate_root if args.candidate_root.is_absolute() else (REPO_ROOT / args.candidate_root)
    ref_root = args.reference_root if args.reference_root.is_absolute() else (REPO_ROOT / args.reference_root)

    mod = load_generate_baselines_module()
    files = collect_files(cand_root, args.language)

    if not files:
        print(f"No {args.language} files found under: {cand_root}")
        return 2

    passed = 0
    failed = 0

    for cand in files:
        rel = cand.relative_to(cand_root)
        ref = ref_root / rel
        print(f"===== {cand.relative_to(REPO_ROOT)}")

        if not ref.exists():
            print(f"FAIL: missing reference file: {ref.relative_to(REPO_ROOT)}")
            failed += 1
            print()
            continue

        ref_run = run_script(mod, args.language, ref, args.python_bin, args.rscript_bin)
        cand_run = run_script(mod, args.language, cand, args.python_bin, args.rscript_bin)

        if ref_run.get("status") != "ok":
            msg = f"reference execution failed: {ref.relative_to(REPO_ROOT)}"
            err = (ref_run.get("stderr") or "").strip()
            if args.skip_reference_errors:
                print(f"SKIP: {msg}")
                if err:
                    print(err.splitlines()[-1])
            else:
                print(f"FAIL: {msg}")
                if err:
                    print(err.splitlines()[-1])
                failed += 1
            print()
            continue

        if cand_run.get("status") != "ok":
            print("FAIL: candidate execution failed")
            err = (cand_run.get("stderr") or "").strip()
            if err:
                print(err.splitlines()[-1])
            failed += 1
            print()
            continue

        ref_profile = extract_profile(ref_run.get("var_summary", {}), args.digits)
        cand_profile = extract_profile(cand_run.get("var_summary", {}), args.digits)

        kinds_score = counter_overlap(ref_profile["kinds"], cand_profile["kinds"])
        shapes_score = counter_overlap(ref_profile["shapes"], cand_profile["shapes"])
        vectors_score = counter_overlap(ref_profile["vector_lengths"], cand_profile["vector_lengths"])
        models_score = counter_overlap(ref_profile["model_sizes"], cand_profile["model_sizes"])
        numeric_score = numeric_overlap(
            ref_profile["numeric_values"],
            cand_profile["numeric_values"],
            atol=args.atol,
            rtol=args.rtol,
        )

        components = {
            "kinds": kinds_score,
            "shapes": shapes_score,
            "vectors": vectors_score,
            "models": models_score,
            "numeric": numeric_score,
        }

        # Dynamic weighting: if a reference component is empty, drop its weight.
        base_weights = {
            "kinds": 0.25,
            "shapes": 0.25,
            "vectors": 0.15,
            "models": 0.20,
            "numeric": 0.15,
        }
        active_weights = {}
        for key, w in base_weights.items():
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

        detail = ", ".join(f"{k}={components[k]:.2f}" for k in ("kinds", "shapes", "vectors", "models", "numeric"))
        if score >= args.min_score:
            print(f"PASS: score={score:.2f} ({detail})")
            passed += 1
        else:
            print(f"FAIL: score={score:.2f} < {args.min_score:.2f} ({detail})")
            failed += 1
        print()

    print(f"SUMMARY language={args.language} pass={passed} fail={failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
