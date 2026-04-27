#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TASK_EQ_ROOT = REPO_ROOT / "task_equivalents"
PY_ROOT = TASK_EQ_ROOT / "python"
R_ROOT = TASK_EQ_ROOT / "r"
OUT_DIR = TASK_EQ_ROOT / "baselines"


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def short_text(s: str, limit: int = 4000) -> str:
    if len(s) <= limit:
        return s
    return s[:limit] + "\n...[truncated]..."


def ensure_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def run_python_baseline(script_path: Path, python_bin: str, timeout_sec: float | None = None) -> dict:
    helper = r'''
import contextlib
import io
import json
import math
import os
import runpy
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
            means = {str(c): r6(num[c].mean()) for c in num.columns}
            sds = {str(c): r6(num[c].std(ddof=1)) for c in num.columns}
            out["numeric_means"] = means
            out["numeric_sds"] = sds
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

    # statsmodels results often expose params.
    if hasattr(v, "params"):
        try:
            params = np.asarray(v.params, dtype=float).ravel().tolist()
            return {"type": type(v).__name__, "params": [r6(x) for x in params]}
        except Exception:
            pass

    # sklearn fitted estimators expose *_ attributes.
    model_bits = {}
    for attr in ["coef_", "intercept_", "feature_importances_", "best_score_", "best_params_", "alpha_", "C"]:
        if hasattr(v, attr):
            try:
                val = getattr(v, attr)
                if isinstance(val, np.ndarray):
                    model_bits[attr] = [r6(x) for x in val.ravel().tolist()[:50]]
                elif isinstance(val, (list, tuple)):
                    model_bits[attr] = [r6(x) if isinstance(x, (int, float, np.integer, np.floating)) else str(x) for x in list(val)[:50]]
                elif isinstance(val, (int, float, np.integer, np.floating)):
                    model_bits[attr] = r6(val)
                elif isinstance(val, dict):
                    model_bits[attr] = {str(k): (r6(vv) if isinstance(vv, (int, float, np.integer, np.floating)) else str(vv)) for k, vv in val.items()}
                else:
                    model_bits[attr] = str(val)
            except Exception:
                pass
    if model_bits:
        return {"type": type(v).__name__, "model": model_bits}

    return None


repo_root = Path(os.environ["BASELINE_REPO_ROOT"])
script_path = Path(os.environ["BASELINE_SCRIPT"])
os.chdir(repo_root)

buffer = io.StringIO()
with contextlib.redirect_stdout(buffer):
    ns = runpy.run_path(str(script_path))
stdout = buffer.getvalue()

var_summary = {}
for key in sorted(ns.keys()):
    if key.startswith("__"):
        continue
    val = ns[key]
    if isinstance(val, types.ModuleType):
        continue
    if callable(val):
        continue
    summary = summarize_value(val)
    if summary is not None:
        var_summary[key] = summary

result = {
    "stdout": stdout,
    "var_summary": var_summary,
}

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

print(json.dumps(sanitize(result)))
'''

    env = os.environ.copy()
    env["BASELINE_REPO_ROOT"] = str(REPO_ROOT)
    env["BASELINE_SCRIPT"] = str(script_path)
    env["MPLBACKEND"] = "Agg"
    env["MPLCONFIGDIR"] = "/tmp/mplcfg"
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    try:
        proc = subprocess.run(
            [python_bin, "-c", helper],
            cwd=str(REPO_ROOT),
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_sec,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = ensure_text(exc.stdout)
        stderr = ensure_text(exc.stderr)
        return {
            "language": "python",
            "path": str(script_path.relative_to(REPO_ROOT)),
            "script_sha256": sha256_file(script_path),
            "exit_code": None,
            "status": "error",
            "error": f"python script timed out after {timeout_sec:.1f}s" if timeout_sec is not None else "python script timed out",
            "stdout": short_text(stdout),
            "stdout_sha256": sha256_text(stdout),
            "stderr": short_text(stderr),
            "stderr_sha256": sha256_text(stderr),
        }

    base = {
        "language": "python",
        "path": str(script_path.relative_to(REPO_ROOT)),
        "script_sha256": sha256_file(script_path),
        "exit_code": proc.returncode,
        "stderr": short_text(proc.stderr),
        "stderr_sha256": sha256_text(proc.stderr),
    }

    if proc.returncode != 0:
        base["status"] = "error"
        base["error"] = "python script execution failed"
        base["stdout"] = short_text(proc.stdout)
        base["stdout_sha256"] = sha256_text(proc.stdout)
        return base

    try:
        parsed = json.loads(proc.stdout)
    except Exception as e:
        base["status"] = "error"
        base["error"] = f"failed to parse helper JSON: {e}"
        base["stdout"] = short_text(proc.stdout)
        base["stdout_sha256"] = sha256_text(proc.stdout)
        return base

    script_stdout = parsed.get("stdout", "")
    var_summary = parsed.get("var_summary", {})

    base["status"] = "ok"
    base["stdout"] = short_text(script_stdout)
    base["stdout_sha256"] = sha256_text(script_stdout)
    base["var_summary"] = var_summary
    base["var_summary_sha256"] = sha256_text(json.dumps(var_summary, sort_keys=True))
    return base


def run_r_baseline(script_path: Path, rscript_bin: str, timeout_sec: float | None = None) -> dict:
    escaped_path = str(script_path).replace("'", "\\'")
    wrapper = f"""
options(stringsAsFactors = FALSE)
options(device = function(...) pdf(file = tempfile(fileext = '.pdf')))
if (!requireNamespace("jsonlite", quietly = TRUE)) {{
  stop("Package 'jsonlite' is required for JSON baseline output. Install via install.packages('jsonlite').")
}}

summarize_obj <- function(x) {{
  cls <- class(x)[1]

  round_num <- function(v) round(as.numeric(v), 6)

  if (is.data.frame(x)) {{
    out <- list(type='data.frame', nrow=nrow(x), ncol=ncol(x), colnames=colnames(x), na_total=sum(is.na(x)))
    num_idx <- vapply(x, is.numeric, logical(1))
    if (any(num_idx)) {{
      num <- x[, num_idx, drop=FALSE]
      out$numeric_means <- lapply(num, function(col) round_num(mean(col)))
      out$numeric_sds <- lapply(num, function(col) round_num(sd(col)))
    }}
    return(out)
  }}

  if (is.matrix(x)) {{
    out <- list(type='matrix', dim=dim(x), na_total=sum(is.na(x)))
    if (is.numeric(x)) {{
      out$mean <- round_num(mean(x))
      out$sd <- round_num(sd(as.vector(x)))
      out$sum <- round_num(sum(x))
    }}
    return(out)
  }}

  if (is.factor(x)) {{
    tbl <- table(x)
    return(list(type='factor', length=length(x), levels=levels(x), counts=as.list(as.integer(tbl))))
  }}

  if (is.numeric(x) || is.integer(x)) {{
    out <- list(type='numeric', length=length(x), na_total=sum(is.na(x)))
    if (length(x) > 0) {{
      out$mean <- round_num(mean(x, na.rm=TRUE))
      out$sd <- round_num(sd(x, na.rm=TRUE))
      out$sum <- round_num(sum(x, na.rm=TRUE))
      out$min <- round_num(min(x, na.rm=TRUE))
      out$max <- round_num(max(x, na.rm=TRUE))
    }}
    return(out)
  }}

  if (is.character(x)) {{
    return(list(type='character', length=length(x), unique_count=length(unique(x))))
  }}

  if (inherits(x, 'lm') || inherits(x, 'glm')) {{
    return(list(type=cls, coef=as.list(round_num(coef(x)))))
  }}

  if (inherits(x, 'tune')) {{
    out <- list(type='tune')
    if (!is.null(x$best.parameters)) out$best_parameters <- as.list(x$best.parameters)
    if (!is.null(x$best.performance)) out$best_performance <- round_num(x$best.performance)
    return(out)
  }}

  if (inherits(x, 'cv.glmnet')) {{
    return(list(type='cv.glmnet', lambda_min=round_num(x$lambda.min), lambda_1se=round_num(x$lambda.1se)))
  }}

  if (inherits(x, 'gbm')) {{
    s <- tryCatch(summary(x, plotit=FALSE), error=function(e) NULL)
    out <- list(type='gbm')
    if (!is.null(s)) {{
      s <- s[order(-s$rel.inf), , drop=FALSE]
      top <- head(s, 10)
      out$top_features <- as.list(as.character(top$var))
      out$top_rel_inf <- as.list(round_num(top$rel.inf))
    }}
    return(out)
  }}

  if (is.list(x)) {{
    return(list(type='list', length=length(x), names=names(x)))
  }}

  return(list(type=cls, length=length(x)))
}}

script_path <- '{escaped_path}'

captured <- capture.output(source(script_path, local=TRUE))
objs <- sort(ls())
out <- list()
for (nm in objs) {{
  val <- get(nm)
  if (is.function(val)) next
  out[[nm]] <- summarize_obj(val)
}}

cat('---SCRIPT_OUTPUT_START---\\n')
if (length(captured) > 0) cat(paste(captured, collapse='\\n'))
cat('\\n---SCRIPT_OUTPUT_END---\\n')
cat('---SUMMARY_JSON_START---\\n')
jsonlite::write_json(out, path = stdout(), auto_unbox = TRUE, na = "null")
cat('\\n---SUMMARY_JSON_END---\\n')
"""

    with tempfile.NamedTemporaryFile("w", suffix=".R", delete=False) as f:
        f.write(wrapper)
        wrapper_path = Path(f.name)

    try:
        try:
            proc = subprocess.run(
                [rscript_bin, str(wrapper_path)],
                cwd=str(REPO_ROOT),
                text=True,
                capture_output=True,
                check=False,
                timeout=timeout_sec,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = ensure_text(exc.stdout)
            stderr = ensure_text(exc.stderr)
            return {
                "language": "r",
                "path": str(script_path.relative_to(REPO_ROOT)),
                "script_sha256": sha256_file(script_path),
                "exit_code": None,
                "status": "error",
                "error": f"R script timed out after {timeout_sec:.1f}s" if timeout_sec is not None else "R script timed out",
                "stdout": short_text(stdout),
                "stdout_sha256": sha256_text(stdout),
                "stderr": short_text(stderr),
                "stderr_sha256": sha256_text(stderr),
            }
    finally:
        wrapper_path.unlink(missing_ok=True)

    base = {
        "language": "r",
        "path": str(script_path.relative_to(REPO_ROOT)),
        "script_sha256": sha256_file(script_path),
        "exit_code": proc.returncode,
        "stderr": short_text(proc.stderr),
        "stderr_sha256": sha256_text(proc.stderr),
    }

    if proc.returncode != 0:
        base["status"] = "error"
        base["error"] = "R script execution failed"
        base["stdout"] = short_text(proc.stdout)
        base["stdout_sha256"] = sha256_text(proc.stdout)
        return base

    text = proc.stdout
    try:
        s1 = text.index("---SCRIPT_OUTPUT_START---") + len("---SCRIPT_OUTPUT_START---")
        e1 = text.index("---SCRIPT_OUTPUT_END---")
        s2 = text.index("---SUMMARY_JSON_START---") + len("---SUMMARY_JSON_START---")
        e2 = text.index("---SUMMARY_JSON_END---")
    except ValueError:
        base["status"] = "error"
        base["error"] = "could not parse R wrapper markers"
        base["stdout"] = short_text(text)
        base["stdout_sha256"] = sha256_text(text)
        return base

    script_stdout = text[s1:e1].strip("\n")
    summary_json = text[s2:e2].strip("\n")
    try:
        var_summary = json.loads(summary_json)
    except Exception as e:
        base["status"] = "error"
        base["error"] = f"failed to parse R summary JSON: {e}"
        base["stdout"] = short_text(script_stdout)
        base["stdout_sha256"] = sha256_text(script_stdout)
        return base

    base["status"] = "ok"
    base["stdout"] = short_text(script_stdout)
    base["stdout_sha256"] = sha256_text(script_stdout)
    base["var_summary"] = var_summary
    base["var_summary_sha256"] = sha256_text(json.dumps(var_summary, sort_keys=True))
    return base


def collect_scripts(root: Path, suffix: str) -> list[Path]:
    return sorted(root.rglob(f"*{suffix}"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate baseline signatures for all task_equivalents snippets.")
    parser.add_argument("--python-bin", default=sys.executable)
    parser.add_argument("--rscript-bin", default="Rscript")
    parser.add_argument("--output", type=Path, default=OUT_DIR / "canonical_baselines.json")
    parser.add_argument("--skip-python", action="store_true")
    parser.add_argument("--skip-r", action="store_true")
    args = parser.parse_args()

    results = []

    if not args.skip_python:
        for py_file in collect_scripts(PY_ROOT, ".py"):
            print(f"[python] {py_file.relative_to(REPO_ROOT)}", flush=True)
            results.append(run_python_baseline(py_file, python_bin=args.python_bin))

    if not args.skip_r:
        for r_file in collect_scripts(R_ROOT, ".R"):
            print(f"[r] {r_file.relative_to(REPO_ROOT)}", flush=True)
            results.append(run_r_baseline(r_file, rscript_bin=args.rscript_bin))

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(REPO_ROOT),
        "python_bin": args.python_bin,
        "rscript_bin": args.rscript_bin,
        "entries": results,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    ok = sum(1 for x in results if x.get("status") == "ok")
    err = sum(1 for x in results if x.get("status") != "ok")
    print(f"Wrote baseline file: {args.output}")
    print(f"Entries: {len(results)}, ok: {ok}, errors: {err}")

    return 0 if err == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
