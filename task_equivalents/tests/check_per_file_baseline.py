#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_generate_baselines_module():
    mod_path = REPO_ROOT / "task_equivalents" / "tests" / "generate_baselines.py"
    spec = importlib.util.spec_from_file_location("generate_baselines", mod_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def compare_dict_keys(ref: dict, cur: dict, keys: list[str]) -> list[tuple[str, object, object]]:
    diffs = []
    for k in keys:
        if ref.get(k) != cur.get(k):
            diffs.append((k, ref.get(k), cur.get(k)))
    return diffs


def is_number(x: object) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def compare_values(ref: object, cur: object, path: str, atol: float, rtol: float, diffs: list[str]) -> None:
    if is_number(ref) and is_number(cur):
        if not math.isclose(float(ref), float(cur), rel_tol=rtol, abs_tol=atol):
            diffs.append(f"{path}: expected {ref}, got {cur}")
        return

    if type(ref) != type(cur):
        diffs.append(f"{path}: type mismatch ({type(ref).__name__} vs {type(cur).__name__})")
        return

    if isinstance(ref, dict):
        ref_keys = set(ref.keys())
        cur_keys = set(cur.keys())
        if ref_keys != cur_keys:
            missing = sorted(ref_keys - cur_keys)
            extra = sorted(cur_keys - ref_keys)
            if missing:
                diffs.append(f"{path}: missing keys {missing}")
            if extra:
                diffs.append(f"{path}: extra keys {extra}")
        for k in sorted(ref_keys & cur_keys):
            compare_values(ref[k], cur[k], f"{path}.{k}", atol, rtol, diffs)
        return

    if isinstance(ref, list):
        if len(ref) != len(cur):
            diffs.append(f"{path}: length mismatch ({len(ref)} vs {len(cur)})")
            return
        for i, (rv, cv) in enumerate(zip(ref, cur)):
            compare_values(rv, cv, f"{path}[{i}]", atol, rtol, diffs)
        return

    if ref != cur:
        diffs.append(f"{path}: expected {ref}, got {cur}")


def check_python_syntax(python_bin: str, candidate: Path) -> tuple[bool, str]:
    path = str(candidate).replace("\\", "\\\\").replace("'", "\\'")
    proc = subprocess.run(
        [python_bin, "-c", f"import ast; ast.parse(open('{path}','r',encoding='utf-8').read())"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0:
        return True, ""
    return False, (proc.stderr or proc.stdout).strip()


def check_r_parse(rscript_bin: str, candidate: Path) -> tuple[bool, str]:
    path = str(candidate).replace("'", "\\'")
    proc = subprocess.run(
        [rscript_bin, "-e", f"parse(file='{path}')"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0:
        return True, ""
    return False, (proc.stderr or proc.stdout).strip()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run one candidate file and compare it to one per-file baseline JSON."
    )
    parser.add_argument("--baseline-file", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--python-bin", default=str(REPO_ROOT / ".venv" / "bin" / "python3"))
    parser.add_argument("--rscript-bin", default="Rscript")
    parser.add_argument("--strict-stderr", action="store_true")
    parser.add_argument(
        "--include-stdout",
        action="store_true",
        help="Also compare stdout hash. Disabled by default to avoid false mismatches from timestamps.",
    )
    parser.add_argument("--atol", type=float, default=1e-4)
    parser.add_argument("--rtol", type=float, default=1e-4)
    args = parser.parse_args()

    payload = json.loads(args.baseline_file.read_text(encoding="utf-8"))
    ref = payload["entry"]
    language = payload["meta"]["language"]

    gb = load_generate_baselines_module()

    candidate_abs = args.candidate if args.candidate.is_absolute() else (REPO_ROOT / args.candidate)

    if language == "python":
        ok, err = check_python_syntax(args.python_bin, candidate_abs)
        if not ok:
            print(f"Baseline: {args.baseline_file}")
            print(f"Candidate: {candidate_abs}")
            print("Language: python")
            print("FAIL: python compilation error")
            print(err)
            return 1
        cur = gb.run_python_baseline(candidate_abs, python_bin=args.python_bin)
        keys = ["status", "exit_code"]
        if args.include_stdout:
            keys.append("stdout_sha256")
        if args.strict_stderr:
            keys.append("stderr_sha256")
    elif language == "r":
        ok, err = check_r_parse(args.rscript_bin, candidate_abs)
        if not ok:
            print(f"Baseline: {args.baseline_file}")
            print(f"Candidate: {candidate_abs}")
            print("Language: r")
            print("FAIL: R parse error")
            print(err)
            return 1
        cur = gb.run_r_baseline(candidate_abs, rscript_bin=args.rscript_bin)
        keys = ["status", "exit_code"]
        if args.include_stdout:
            keys.append("stdout_sha256")
        if args.strict_stderr:
            keys.append("stderr_sha256")
    else:
        raise ValueError(f"Unsupported language in baseline: {language}")

    diffs = compare_dict_keys(ref, cur, keys)

    print(f"Baseline: {args.baseline_file}")
    print(f"Candidate: {candidate_abs}")
    print(f"Language: {language}")

    summary_diffs: list[str] = []
    compare_values(ref.get("var_summary"), cur.get("var_summary"), "var_summary", args.atol, args.rtol, summary_diffs)

    if not diffs and not summary_diffs:
        print("PASS: candidate matches baseline.")
        return 0

    print("FAIL: differences detected:")
    for k, a, b in diffs:
        print(f"- {k}")
        print(f"  baseline: {a}")
        print(f"  current : {b}")
    for d in summary_diffs[:100]:
        print(f"- {d}")
    if len(summary_diffs) > 100:
        print(f"- ... and {len(summary_diffs) - 100} more summary differences")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
