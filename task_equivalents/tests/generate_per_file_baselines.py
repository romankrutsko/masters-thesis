#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TASK_EQ = REPO_ROOT / "task_equivalents"
PY_ROOT = TASK_EQ / "python"
R_ROOT = TASK_EQ / "r"


def safe_name(path: str) -> str:
    base = path.strip().replace("/", "__")
    base = re.sub(r"[^A-Za-z0-9_.-]", "_", base)
    return f"{base}.json"


def load_generate_baselines_module():
    mod_path = TASK_EQ / "tests" / "generate_baselines.py"
    spec = importlib.util.spec_from_file_location("generate_baselines", mod_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate fresh per-file baseline JSONs by executing each snippet."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=TASK_EQ / "baselines" / "per_file_generated",
    )
    parser.add_argument("--skip-python", action="store_true")
    parser.add_argument("--skip-r", action="store_true")
    parser.add_argument("--python-bin", default=str(REPO_ROOT / ".venv" / "bin" / "python3"))
    parser.add_argument("--rscript-bin", default="Rscript")
    args = parser.parse_args()

    if args.skip_python and args.skip_r:
        print("Nothing to do: both --skip-python and --skip-r are set.")
        return 2

    gb = load_generate_baselines_module()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    index = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(REPO_ROOT),
        "python_bin": args.python_bin,
        "rscript_bin": args.rscript_bin,
        "files": [],
    }

    total = 0
    ok = 0

    if not args.skip_python:
        out_lang_dir = args.output_dir / "python"
        out_lang_dir.mkdir(parents=True, exist_ok=True)
        for p in sorted(PY_ROOT.rglob("*.py")):
            rel = str(p.relative_to(REPO_ROOT))
            result = gb.run_python_baseline(p, python_bin=args.python_bin)
            out_file = out_lang_dir / safe_name(rel)
            payload = {
                "meta": {
                    "language": "python",
                    "path": rel,
                    "generated_at_utc": index["generated_at_utc"],
                },
                "entry": result,
            }
            out_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            index["files"].append({"language": "python", "path": rel, "file": str(out_file.relative_to(args.output_dir)), "status": result.get("status")})
            total += 1
            if result.get("status") == "ok":
                ok += 1

    if not args.skip_r:
        out_lang_dir = args.output_dir / "r"
        out_lang_dir.mkdir(parents=True, exist_ok=True)
        for p in sorted(R_ROOT.rglob("*.R")):
            rel = str(p.relative_to(REPO_ROOT))
            result = gb.run_r_baseline(p, rscript_bin=args.rscript_bin)
            out_file = out_lang_dir / safe_name(rel)
            payload = {
                "meta": {
                    "language": "r",
                    "path": rel,
                    "generated_at_utc": index["generated_at_utc"],
                },
                "entry": result,
            }
            out_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            index["files"].append({"language": "r", "path": rel, "file": str(out_file.relative_to(args.output_dir)), "status": result.get("status")})
            total += 1
            if result.get("status") == "ok":
                ok += 1

    idx_file = args.output_dir / "index.json"
    idx_file.write_text(json.dumps(index, indent=2), encoding="utf-8")

    print(f"Wrote per-file baselines to: {args.output_dir}")
    print(f"Index: {idx_file}")
    print(f"Entries: {total}, ok: {ok}, errors: {total-ok}")
    return 0 if ok == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
