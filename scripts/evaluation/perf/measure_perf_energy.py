#!/usr/bin/env python3
"""
Benchmark translated candidate scripts for runtime, CPU package energy, and
average power using Linux perf and Intel RAPL.

This script discovers translated Python and R candidate scripts under the
project's llm_translations directory, optionally performs warm-up runs, then
records one CSV row per measured execution. Measurements reflect full
subprocess lifetime, including interpreter startup, imports, script execution,
and process exit. Each run is executed in a separate process group so timeouts
can terminate the entire process tree.

Outputs:
- CSV with one row per measured run
- JSON summary with aggregate counts and configuration

Requirements:
- Ubuntu/Linux with perf available
- Intel CPU with power/energy-pkg/ support
- perf_event_paranoid configured to allow measurements
- Python and R dependencies already installed
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import signal
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BASE_DIR = REPO_ROOT / "task_equivalents" / "llm_translations"
DEFAULT_RESULTS_ROOT = REPO_ROOT / "results" / "perf_energy_runs"
DEFAULT_BLACKLIST = REPO_ROOT / "scripts" / "evaluation" / "reliability" / "evaluation_blacklist.txt"

PERF_ELAPSED_RE = re.compile(r"([0-9][0-9,]*(?:\.[0-9]+)?)\s+seconds\s+time\s+elapsed")
PERF_ENERGY_RE = re.compile(r"([0-9][0-9,]*(?:\.[0-9]+)?)\s+Joules\s+power/energy-pkg/")
STDERR_EXCERPT_LIMIT = 400


@dataclass(frozen=True)
class CandidateScript:
    implementation_type: str
    model: str
    prompt_type: str
    language: str
    category: str
    snippet: str
    script_path: Path


@dataclass
class RunResult:
    status: str
    elapsed_seconds: float | None
    energy_joules: float | None
    avg_power_watts: float | None
    error_message: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Measure runtime, energy, and average power for translated candidate scripts using perf."
    )
    parser.add_argument("--runs", type=int, default=1, help="Measured runs per script.")
    parser.add_argument("--warmup-runs", type=int, default=1, help="Warm-up runs per script.")
    parser.add_argument("--pause-seconds", type=float, default=60.0, help="Pause after each script.")
    parser.add_argument("--timeout", type=float, default=120.0, help="Timeout per execution in seconds.")
    parser.add_argument("--output", type=Path, default=None, help="Output CSV path.")
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=None,
        help="Output JSON summary path.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional output directory for this run. Defaults to results/perf_energy_runs/<timestamp>/",
    )
    parser.add_argument("--base-dir", type=Path, default=DEFAULT_BASE_DIR, help="Root directory to scan.")
    parser.add_argument(
        "--blacklist-file",
        type=Path,
        default=DEFAULT_BLACKLIST,
        help="Optional path blacklist file; matching scripts are skipped.",
    )
    return parser.parse_args()


def build_interpreter_command(script_path: Path) -> list[str]:
    suffix = script_path.suffix.lower()
    if suffix == ".py":
        return ["python3", str(script_path)]
    if suffix == ".r":
        return ["Rscript", str(script_path)]
    raise ValueError(f"Unsupported script type: {script_path}")


def load_blacklist(path: Path | None) -> set[str]:
    if path is None or not path.exists():
        return set()
    entries: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if line:
            entries.add(line)
    return entries


def discover_scripts(base_dir: Path, blacklist_entries: set[str]) -> tuple[list[CandidateScript], int]:
    out: list[CandidateScript] = []
    skipped = 0

    for path in sorted(base_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".py", ".r"}:
            continue

        try:
            rel = path.relative_to(base_dir)
        except ValueError:
            continue

        parts = rel.parts
        if len(parts) < 5:
            continue

        model, prompt_type, language, category = parts[0], parts[1], parts[2], parts[3]
        if prompt_type not in {"base", "optimized"}:
            continue
        if language not in {"python", "r"}:
            continue

        repo_rel = str(path.relative_to(REPO_ROOT))
        abs_path = str(path.resolve())
        if repo_rel in blacklist_entries or abs_path in blacklist_entries:
            skipped += 1
            continue

        out.append(
            CandidateScript(
                implementation_type="candidate",
                model=model,
                prompt_type=prompt_type,
                language=language,
                category=category,
                snippet=path.stem,
                script_path=path.resolve(),
            )
        )

    return out, skipped


def parse_perf_stderr(stderr_text: str) -> tuple[float, float]:
    elapsed_matches = PERF_ELAPSED_RE.findall(stderr_text)
    energy_matches = PERF_ENERGY_RE.findall(stderr_text)

    if not elapsed_matches or not energy_matches:
        excerpt = compact_error(stderr_text)
        raise ValueError(f"Could not parse perf output: {excerpt}")

    elapsed_seconds = float(elapsed_matches[-1].replace(",", ""))
    energy_joules = float(energy_matches[-1].replace(",", ""))
    return elapsed_seconds, energy_joules


def compact_error(text: str) -> str:
    cleaned = " | ".join(line.strip() for line in text.splitlines() if line.strip())
    if not cleaned:
        return "No stderr output"
    return cleaned[:STDERR_EXCERPT_LIMIT]


def terminate_process_group(proc: subprocess.Popen[str]) -> None:
    try:
        pgid = os.getpgid(proc.pid)
    except ProcessLookupError:
        return

    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(pgid, sig)
        except ProcessLookupError:
            return
        try:
            proc.wait(timeout=5)
            return
        except subprocess.TimeoutExpired:
            continue


def execute_with_perf(command: Sequence[str], timeout_seconds: float) -> RunResult:
    perf_command = ["perf", "stat", "-e", "power/energy-pkg/", "--", *command]

    proc = subprocess.Popen(
        perf_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(REPO_ROOT),
        start_new_session=True,
    )

    try:
        stdout_text, stderr_text = proc.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        terminate_process_group(proc)
        return RunResult(
            status="error",
            elapsed_seconds=None,
            energy_joules=None,
            avg_power_watts=None,
            error_message=f"Timed out after {timeout_seconds:.1f}s",
        )
    except Exception as exc:
        terminate_process_group(proc)
        return RunResult(
            status="error",
            elapsed_seconds=None,
            energy_joules=None,
            avg_power_watts=None,
            error_message=f"Execution failed: {exc}",
        )

    if proc.returncode != 0:
        err = compact_error(stderr_text or stdout_text)
        return RunResult(
            status="error",
            elapsed_seconds=None,
            energy_joules=None,
            avg_power_watts=None,
            error_message=f"Command failed with exit code {proc.returncode}: {err}",
        )

    try:
        elapsed_seconds, energy_joules = parse_perf_stderr(stderr_text)
    except ValueError as exc:
        return RunResult(
            status="error",
            elapsed_seconds=None,
            energy_joules=None,
            avg_power_watts=None,
            error_message=str(exc),
        )

    avg_power_watts = energy_joules / elapsed_seconds if elapsed_seconds > 0 else None
    if avg_power_watts is None:
        return RunResult(
            status="error",
            elapsed_seconds=None,
            energy_joules=None,
            avg_power_watts=None,
            error_message="Elapsed time was zero; average power is undefined",
        )

    return RunResult(
        status="ok",
        elapsed_seconds=elapsed_seconds,
        energy_joules=energy_joules,
        avg_power_watts=avg_power_watts,
        error_message="",
    )


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def csv_fieldnames() -> list[str]:
    return [
        "implementation_type",
        "model",
        "prompt_type",
        "language",
        "category",
        "snippet",
        "script_path",
        "run_id",
        "status",
        "elapsed_seconds",
        "energy_joules",
        "avg_power_watts",
        "error_message",
    ]


def write_csv_row(writer: csv.DictWriter, row: dict[str, object], handle) -> None:
    writer.writerow(row)
    handle.flush()


def sync_file(handle) -> None:
    handle.flush()
    os.fsync(handle.fileno())


def write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    ensure_parent_dir(path)
    tmp_path = path.with_suffix(f"{path.suffix}.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(tmp_path, path)


def make_csv_row(candidate: CandidateScript, run_id: int, result: RunResult) -> dict[str, object]:
    return {
        "implementation_type": candidate.implementation_type,
        "model": candidate.model,
        "prompt_type": candidate.prompt_type,
        "language": candidate.language,
        "category": candidate.category,
        "snippet": candidate.snippet,
        "script_path": str(candidate.script_path),
        "run_id": run_id,
        "status": result.status,
        "elapsed_seconds": "" if result.elapsed_seconds is None else f"{result.elapsed_seconds:.9f}",
        "energy_joules": "" if result.energy_joules is None else f"{result.energy_joules:.9f}",
        "avg_power_watts": "" if result.avg_power_watts is None else f"{result.avg_power_watts:.9f}",
        "error_message": result.error_message,
    }


def validate_args(args: argparse.Namespace) -> None:
    if args.runs < 1:
        raise SystemExit("--runs must be >= 1")
    if args.warmup_runs < 0:
        raise SystemExit("--warmup-runs must be >= 0")
    if args.pause_seconds < 0:
        raise SystemExit("--pause-seconds must be >= 0")
    if args.timeout <= 0:
        raise SystemExit("--timeout must be > 0")


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def resolve_output_paths(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    if args.output_dir is not None:
        run_dir = Path(args.output_dir).resolve()
    elif args.output is not None:
        run_dir = Path(args.output).resolve().parent
    elif args.summary_output is not None:
        run_dir = Path(args.summary_output).resolve().parent
    else:
        run_dir = (DEFAULT_RESULTS_ROOT / now_stamp()).resolve()

    output_csv = Path(args.output).resolve() if args.output is not None else run_dir / "perf_energy_runs.csv"
    output_json = Path(args.summary_output).resolve() if args.summary_output is not None else run_dir / "perf_energy_summary.json"
    return run_dir, output_csv, output_json


def summary_payload(
    *,
    args: argparse.Namespace,
    run_dir: Path,
    output_csv: Path,
    output_json: Path,
    scripts: list[CandidateScript],
    blacklist_skipped: int,
    total_attempted_runs: int,
    successful_runs: int,
    failed_runs: int,
    started_at: str,
    finished_at: str,
    completed_scripts: int,
    total_scripts: int,
    status: str,
    current_script: str,
) -> dict[str, object]:
    return {
        "generated_at_utc": finished_at,
        "started_at_utc": started_at,
        "base_dir": str(Path(args.base_dir).resolve()),
        "run_dir": str(run_dir.resolve()),
        "output_csv": str(output_csv.resolve()),
        "output_json": str(output_json.resolve()),
        "runs_per_script": args.runs,
        "warmup_runs": args.warmup_runs,
        "pause_seconds": args.pause_seconds,
        "timeout_seconds": args.timeout,
        "blacklist_file": str(Path(args.blacklist_file).resolve()) if args.blacklist_file else "",
        "scripts_discovered": len(scripts),
        "scripts_skipped_by_blacklist": blacklist_skipped,
        "completed_scripts": completed_scripts,
        "remaining_scripts": max(total_scripts - completed_scripts, 0),
        "measured_runs_attempted": total_attempted_runs,
        "successful_runs": successful_runs,
        "failed_runs": failed_runs,
        "status": status,
        "current_script": current_script,
    }


def print_summary(payload: dict[str, object]) -> None:
    print("\nSummary")
    print(f"Total scripts discovered: {payload['scripts_discovered']}")
    print(f"Total measured runs attempted: {payload['measured_runs_attempted']}")
    print(f"Successful runs: {payload['successful_runs']}")
    print(f"Failed runs: {payload['failed_runs']}")
    print(f"Output CSV path: {payload['output_csv']}")


def run_benchmark(args: argparse.Namespace) -> int:
    validate_args(args)

    base_dir = Path(args.base_dir).resolve()
    if not base_dir.exists():
        raise SystemExit(f"Base directory does not exist: {base_dir}")

    blacklist_entries = load_blacklist(Path(args.blacklist_file).resolve() if args.blacklist_file else None)
    scripts, blacklist_skipped = discover_scripts(base_dir, blacklist_entries)
    run_dir, output_csv, output_json = resolve_output_paths(args)
    run_dir.mkdir(parents=True, exist_ok=True)

    started_at = datetime.now(timezone.utc).isoformat()
    total_attempted_runs = 0
    successful_runs = 0
    failed_runs = 0
    total_scripts = len(scripts)

    def checkpoint(*, completed_scripts: int, status: str, current_script: str) -> None:
        payload = summary_payload(
            args=args,
            run_dir=run_dir,
            output_csv=output_csv,
            output_json=output_json,
            scripts=scripts,
            blacklist_skipped=blacklist_skipped,
            total_attempted_runs=total_attempted_runs,
            successful_runs=successful_runs,
            failed_runs=failed_runs,
            started_at=started_at,
            finished_at=datetime.now(timezone.utc).isoformat(),
            completed_scripts=completed_scripts,
            total_scripts=total_scripts,
            status=status,
            current_script=current_script,
        )
        write_json_atomic(output_json, payload)

    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=csv_fieldnames())
        writer.writeheader()
        sync_file(handle)
        checkpoint(completed_scripts=0, status="running", current_script="")

        for script_index, candidate in enumerate(scripts, start=1):
            script_label = (
                f"{candidate.model}/{candidate.prompt_type}/{candidate.language}/"
                f"{candidate.category}/{candidate.snippet}"
            )
            print(
                f"[{script_index}/{total_scripts}] {script_label}"
            )

            command = build_interpreter_command(candidate.script_path)

            for warmup_index in range(1, args.warmup_runs + 1):
                print(f"  warm-up {warmup_index}/{args.warmup_runs} ...", flush=True)
                warmup_result = execute_with_perf(command, timeout_seconds=args.timeout)
                print(f"    -> {warmup_result.status}", flush=True)

            for measured_index in range(1, args.runs + 1):
                total_attempted_runs += 1
                print(f"  measured {measured_index}/{args.runs} ...", flush=True)
                result = execute_with_perf(command, timeout_seconds=args.timeout)
                if result.status == "ok":
                    successful_runs += 1
                    print(
                        "    -> ok "
                        f"elapsed={result.elapsed_seconds:.6f}s "
                        f"energy={result.energy_joules:.6f}J "
                        f"power={result.avg_power_watts:.6f}W",
                        flush=True,
                    )
                else:
                    failed_runs += 1
                    print(f"    -> error: {result.error_message}", flush=True)

                row = make_csv_row(candidate, measured_index, result)
                write_csv_row(writer, row, handle)

            sync_file(handle)
            checkpoint(completed_scripts=script_index, status="running", current_script=script_label)

            if script_index < total_scripts and args.pause_seconds > 0:
                print(f"  sleeping {args.pause_seconds:.1f}s before next script", flush=True)
                time.sleep(args.pause_seconds)

    summary = summary_payload(
        args=args,
        run_dir=run_dir,
        output_csv=output_csv,
        output_json=output_json,
        scripts=scripts,
        blacklist_skipped=blacklist_skipped,
        total_attempted_runs=total_attempted_runs,
        successful_runs=successful_runs,
        failed_runs=failed_runs,
        started_at=started_at,
        finished_at=datetime.now(timezone.utc).isoformat(),
        completed_scripts=total_scripts,
        total_scripts=total_scripts,
        status="completed",
        current_script="",
    )
    write_json_atomic(output_json, summary)
    print_summary(summary)
    return 0


def main() -> None:
    args = parse_args()
    raise SystemExit(run_benchmark(args))


if __name__ == "__main__":
    main()
