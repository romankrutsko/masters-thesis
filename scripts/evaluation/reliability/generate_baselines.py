#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TASK_EQ_ROOT = REPO_ROOT / "task_equivalents"
PY_ROOT = TASK_EQ_ROOT / "python"
R_ROOT = TASK_EQ_ROOT / "r"
OUT_DIR = TASK_EQ_ROOT / "baselines"
HELPER_DIR = Path(__file__).resolve().parent.parent / "helpers"
PYTHON_CAPTURE_HELPER = HELPER_DIR / "python_capture.py"
R_CAPTURE_HELPER = HELPER_DIR / "r_capture.R"


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


def baseline_env(script_path: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["BASELINE_REPO_ROOT"] = str(REPO_ROOT)
    env["BASELINE_SCRIPT"] = str(script_path)
    return env


def run_python_baseline(script_path: Path, python_bin: str, timeout_sec: float | None = None) -> dict:
    # Run the target in a clean helper process so crashes, imports, and globals from one candidate cannot leak into the evaluator or the next candidate.
    env = baseline_env(script_path)
    env["MPLBACKEND"] = "Agg"
    env["MPLCONFIGDIR"] = "/tmp/mplcfg"
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    try:
        proc = subprocess.run(
            [python_bin, str(PYTHON_CAPTURE_HELPER)],
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
    # The R helper prints marker-delimited script output and summary JSON.
    try:
        proc = subprocess.run(
            [rscript_bin, str(R_CAPTURE_HELPER)],
            cwd=str(REPO_ROOT),
            env=baseline_env(script_path),
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
