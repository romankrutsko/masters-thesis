#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import io
import json
import math
import os
import runpy
import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd


def r6(v):
    if isinstance(v, (float, np.floating)):
        if math.isnan(float(v)) or math.isinf(float(v)):
            return None
        return round(float(v), 6)
    return v


def summarize_scalar(v):
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating, float)):
        return r6(v)
    if isinstance(v, (np.bool_, bool)):
        return bool(v)
    if isinstance(v, str):
        return v
    return None


def summarize_value(v):
    if isinstance(v, pd.DataFrame):
        out = {
            "type": "DataFrame",
            "shape": [int(v.shape[0]), int(v.shape[1])],
            "columns": [str(c) for c in v.columns.tolist()],
            "na_total": int(v.isna().sum().sum()),
        }
        num = v.select_dtypes(include=[np.number])
        if num.shape[1] > 0:
            out["numeric_means"] = {str(c): r6(num[c].mean()) for c in num.columns}
            out["numeric_sds"] = {str(c): r6(num[c].std(ddof=1)) for c in num.columns}
        return out

    if isinstance(v, pd.Series):
        out = {
            "type": "Series",
            "name": str(v.name),
            "length": int(v.shape[0]),
            "dtype": str(v.dtype),
            "na_total": int(v.isna().sum()),
            "unique_count": int(v.nunique(dropna=True)),
        }
        if pd.api.types.is_numeric_dtype(v):
            out["sum"] = r6(v.sum())
            out["mean"] = r6(v.mean())
            out["std"] = r6(v.std(ddof=1))
            vals = sorted(v.dropna().unique().tolist())
            out["unique_values_head"] = [r6(x) for x in vals[:20]]
        return out

    if isinstance(v, np.ndarray):
        out = {
            "type": "ndarray",
            "shape": [int(x) for x in v.shape],
            "dtype": str(v.dtype),
        }
        if np.issubdtype(v.dtype, np.number):
            vv = v.astype(float)
            out["mean"] = r6(np.mean(vv))
            out["std"] = r6(np.std(vv, ddof=1)) if vv.size > 1 else None
            out["sum"] = r6(np.sum(vv))
            out["min"] = r6(np.min(vv))
            out["max"] = r6(np.max(vv))
        return out

    if isinstance(v, (list, tuple)):
        out = {"type": type(v).__name__, "length": len(v)}
        if len(v) and all(isinstance(x, (int, float, np.integer, np.floating)) for x in v):
            arr = np.array(v, dtype=float)
            out["mean"] = r6(arr.mean())
            out["std"] = r6(arr.std(ddof=1)) if arr.size > 1 else None
            out["sum"] = r6(arr.sum())
        return out

    if isinstance(v, (int, float, str, bool, np.integer, np.floating, np.bool_)):
        return {"type": "scalar", "value": summarize_scalar(v)}

    if hasattr(v, "params"):
        try:
            params = np.asarray(v.params, dtype=float).ravel().tolist()
            return {"type": type(v).__name__, "params": [r6(x) for x in params]}
        except Exception:
            pass

    model_bits = {}
    for attr in ["coef_", "intercept_", "feature_importances_", "best_score_", "best_params_", "alpha_", "C"]:
        if not hasattr(v, attr):
            continue
        try:
            val = getattr(v, attr)
            if isinstance(val, np.ndarray):
                model_bits[attr] = [r6(x) for x in val.ravel().tolist()[:50]]
            elif isinstance(val, (list, tuple)):
                model_bits[attr] = [
                    r6(x) if isinstance(x, (int, float, np.integer, np.floating)) else str(x)
                    for x in list(val)[:50]
                ]
            elif isinstance(val, (int, float, np.integer, np.floating)):
                model_bits[attr] = r6(val)
            elif isinstance(val, dict):
                model_bits[attr] = {
                    str(k): (r6(vv) if isinstance(vv, (int, float, np.integer, np.floating)) else str(vv))
                    for k, vv in val.items()
                }
            else:
                model_bits[attr] = str(val)
        except Exception:
            pass
    if model_bits:
        return {"type": type(v).__name__, "model": model_bits}

    return None


def sanitize(x):
    if isinstance(x, dict):
        return {str(k): sanitize(v) for k, v in x.items()}
    if isinstance(x, list):
        return [sanitize(v) for v in x]
    if isinstance(x, tuple):
        return [sanitize(v) for v in x]
    if isinstance(x, np.integer):
        return int(x)
    if isinstance(x, np.floating):
        return r6(x)
    if isinstance(x, np.bool_):
        return bool(x)
    return x


def main() -> int:
    repo_root = Path(os.environ["BASELINE_REPO_ROOT"])
    script_path = Path(os.environ["BASELINE_SCRIPT"])
    os.chdir(repo_root)

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        # Match `python script.py`: run guarded main blocks and expose a normal argv.
        old_argv = sys.argv[:]
        sys.argv = [str(script_path)]
        try:
            ns = runpy.run_path(str(script_path), run_name="__main__")
        finally:
            sys.argv = old_argv
    stdout = buffer.getvalue()

    var_summary = {}
    for key in sorted(ns.keys()):
        if key.startswith("__"):
            continue
        val = ns[key]
        if isinstance(val, types.ModuleType) or callable(val):
            continue
        summary = summarize_value(val)
        if summary is not None:
            var_summary[key] = summary

    print(json.dumps(sanitize({"stdout": stdout, "var_summary": var_summary})))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
