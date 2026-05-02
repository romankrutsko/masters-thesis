#!/usr/bin/env python3
"""Run Sonar-based maintainability checks for translated snippets only."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

THIS_DIR = Path(__file__).resolve().parent
EVALUATION_DIR = THIS_DIR.parent
# Direct script execution puts this subdirectory on sys.path, so add repo root for package imports.
REPO_IMPORT_ROOT = THIS_DIR.parents[2]
if str(REPO_IMPORT_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_IMPORT_ROOT))

from scripts.evaluation.helpers.evaluation_common import (
    Candidate,
    DEFAULT_BLACKLIST_FILE,
    DEFAULT_OUTPUT_ROOT,
    REPO_ROOT,
    LLM_ROOT,
    Slice,
    discover_candidates,
    discover_slices,
    ensure_dir,
    filter_candidates,
    now_stamp,
    to_rel,
    write_run_manifest,
)

LINTR_TO_SONAR_HELPER = EVALUATION_DIR / "helpers" / "lintr_to_sonar.R"


def sanitize_key(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.:-]+", "_", s)


def read_report_task(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def sonar_api_get(url: str, token: str | None, params: dict[str, str] | None = None) -> dict[str, Any]:
    if params:
        url = f"{url}?{urlencode(params)}"
    req = Request(url)
    if token:
        auth = (token + ":").encode("utf-8")
        import base64

        req.add_header("Authorization", "Basic " + base64.b64encode(auth).decode("ascii"))
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def poll_sonar_analysis(sonar_host_url: str, ce_task_id: str, token: str | None, timeout_sec: int = 300) -> dict[str, Any]:
    deadline = time.time() + timeout_sec
    last = None
    while time.time() < deadline:
        data = sonar_api_get(f"{sonar_host_url.rstrip('/')}/api/ce/task", token, {"id": ce_task_id})
        task = data.get("task", {})
        last = task
        status = task.get("status")
        if status in {"SUCCESS", "FAILED", "CANCELED"}:
            return task
        time.sleep(3)
    return last or {}


def generate_lintr_external_issues(
    slice_root: Path,
    out_json: Path,
    rscript_bin: str,
    repo_root: Path,
    target_file: Path | None = None,
) -> tuple[bool, str]:
    env = os.environ.copy()
    env["LINTR_SLICE_ROOT"] = str(slice_root)
    env["LINTR_OUT_JSON"] = str(out_json)
    env["LINTR_REPO_ROOT"] = str(repo_root)
    if target_file is not None:
        env["LINTR_TARGET_FILE"] = str(target_file)
    proc = subprocess.run([rscript_bin, str(LINTR_TO_SONAR_HELPER)], capture_output=True, text=True, check=False, env=env)
    if proc.returncode == 0:
        return True, ""
    return False, (proc.stderr or proc.stdout or "lintr failed").strip()


def sonar_metrics() -> list[str]:
    return [
        "bugs",
        "vulnerabilities",
        "code_smells",
        "reliability_rating",
        "security_rating",
        "sqale_rating",
        "duplicated_lines_density",
        "ncloc",
        "coverage",
    ]


def empty_result_row(
    *,
    model: str,
    prompt_type: str,
    language: str,
    analysis_granularity: str,
    source_root: Path,
    project_key: str,
    scanner_log: Path,
    script_id: str = "",
    category: str = "",
    snippet_id: str = "",
    script_path: Path | None = None,
) -> dict[str, Any]:
    return {
        "script_id": script_id,
        "model": model,
        "prompt_type": prompt_type,
        "language": language,
        "category": category,
        "snippet_id": snippet_id,
        "script_path": to_rel(script_path) if script_path is not None else "",
        "analysis_granularity": analysis_granularity,
        "source_root": to_rel(source_root),
        "project_key": project_key,
        "sonar_status": "",
        "sonar_scanner_exit_code": "",
        "quality_gate": "",
        "bugs": "",
        "vulnerabilities": "",
        "code_smells": "",
        "reliability_rating": "",
        "security_rating": "",
        "sqale_rating": "",
        "duplicated_lines_density": "",
        "ncloc": "",
        "coverage": "",
        "analysis_id": "",
        "ce_task_id": "",
        "error": "",
        "scanner_log": to_rel(scanner_log),
    }


def finish_sonar_row(
    row: dict[str, Any],
    *,
    proc: subprocess.CompletedProcess[str],
    report_task: Path,
    sonar_host_url: str,
    sonar_token: str | None,
    project_key: str,
) -> dict[str, Any]:
    row["sonar_status"] = "ok" if proc.returncode == 0 else "scanner_error"
    row["sonar_scanner_exit_code"] = proc.returncode

    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "sonar-scanner failed").splitlines()
        row["error"] = err[-1] if err else "sonar-scanner failed"
        return row

    if not report_task.exists():
        row["sonar_status"] = "missing_report_task"
        row["error"] = f"Missing report task file: {report_task}"
        return row

    task_info = read_report_task(report_task)
    ce_task_id = task_info.get("ceTaskId", "")
    row["ce_task_id"] = ce_task_id

    if not ce_task_id:
        row["sonar_status"] = "missing_ce_task_id"
        row["error"] = "No ceTaskId in report-task.txt"
        return row

    try:
        ce_task = poll_sonar_analysis(sonar_host_url, ce_task_id, sonar_token, timeout_sec=300)
    except (HTTPError, URLError, TimeoutError, OSError) as e:
        row["sonar_status"] = "api_error"
        row["error"] = f"Failed polling CE task: {e}"
        return row

    ce_status = ce_task.get("status", "")
    if ce_status != "SUCCESS":
        row["sonar_status"] = f"ce_{ce_status.lower() or 'unknown'}"
        row["error"] = f"Compute Engine status: {ce_status}"
        return row

    analysis_id = ce_task.get("analysisId", "")
    row["analysis_id"] = analysis_id

    try:
        qg = sonar_api_get(f"{sonar_host_url.rstrip('/')}/api/qualitygates/project_status", sonar_token, {"analysisId": analysis_id})
        row["quality_gate"] = qg.get("projectStatus", {}).get("status", "")

        ms = sonar_api_get(
            f"{sonar_host_url.rstrip('/')}/api/measures/component",
            sonar_token,
            {"component": project_key, "metricKeys": ",".join(sonar_metrics())},
        )
        for m in ms.get("component", {}).get("measures", []):
            key = m.get("metric")
            if key in row:
                row[key] = m.get("value", "")
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as e:
        row["sonar_status"] = "api_error"
        row["error"] = f"Failed fetching Sonar metrics: {e}"
        return row

    return row


def run_sonar_for_slice(
    sl: Slice,
    output_dir: Path,
    sonar_scanner_bin: str,
    sonar_host_url: str,
    sonar_token: str | None,
    sonar_project_prefix: str,
    rscript_bin: str,
) -> dict[str, Any]:
    slice_out = output_dir / "static" / sl.slug
    ensure_dir(slice_out)

    project_key = sanitize_key(f"{sonar_project_prefix}_{sl.model}_{sl.prompt_type}_{sl.language}")
    project_name = f"{sonar_project_prefix}:{sl.model}:{sl.prompt_type}:{sl.language}"

    scanner_log = slice_out / "sonar-scanner.log"
    report_task = sl.root / ".scannerwork" / "report-task.txt"
    row = empty_result_row(
        model=sl.model,
        prompt_type=sl.prompt_type,
        language=sl.language,
        analysis_granularity="slice",
        source_root=sl.root,
        project_key=project_key,
        scanner_log=scanner_log,
    )

    properties = [
        f"-Dsonar.projectKey={project_key}",
        f"-Dsonar.projectName={project_name}",
        "-Dsonar.projectVersion=1",
        f"-Dsonar.host.url={sonar_host_url}",
        "-Dsonar.sourceEncoding=UTF-8",
        "-Dsonar.scm.disabled=true",
        "-Dsonar.sources=.",
    ]

    if sl.language == "python":
        properties.append("-Dsonar.inclusions=**/*.py")
    else:
        # Sonar is the reporting layer here, but R lint findings come from lintr.
        properties.append("-Dsonar.inclusions=**/*.R,**/*.r")
        lintr_report = slice_out / "lintr-sonar-external-issues.json"
        ok, msg = generate_lintr_external_issues(sl.root, lintr_report, rscript_bin=rscript_bin, repo_root=REPO_ROOT)
        if ok:
            properties.append(f"-Dsonar.externalIssuesReportPaths={lintr_report}")
        else:
            (slice_out / "lintr-error.log").write_text(msg + "\n", encoding="utf-8")

    cmd = [sonar_scanner_bin] + properties
    env = os.environ.copy()
    if sonar_token:
        env["SONAR_TOKEN"] = sonar_token

    # Run inside the slice root so relative paths line up with Sonar metadata.
    proc = subprocess.run(cmd, cwd=str(sl.root), capture_output=True, text=True, check=False, env=env)
    scanner_log.write_text((proc.stdout or "") + "\n" + (proc.stderr or ""), encoding="utf-8")

    return finish_sonar_row(
        row,
        proc=proc,
        report_task=report_task,
        sonar_host_url=sonar_host_url,
        sonar_token=sonar_token,
        project_key=project_key,
    )


def run_sonar_for_candidate(
    candidate: Candidate,
    output_dir: Path,
    sonar_scanner_bin: str,
    sonar_host_url: str,
    sonar_token: str | None,
    sonar_project_prefix: str,
    rscript_bin: str,
) -> dict[str, Any]:
    snippet_out = output_dir / "static" / candidate.slug
    ensure_dir(snippet_out)

    project_key = sanitize_key(f"{sonar_project_prefix}_{candidate.script_id}_{candidate.slug}")
    project_name = (
        f"{sonar_project_prefix}:{candidate.model}:{candidate.prompt_type}:{candidate.language}:"
        f"{candidate.category}:{candidate.snippet_id}"
    )

    source_root = candidate.path.parent
    source_name = candidate.path.name
    scanner_log = snippet_out / "sonar-scanner.log"
    report_task = source_root / ".scannerwork" / "report-task.txt"
    row = empty_result_row(
        model=candidate.model,
        prompt_type=candidate.prompt_type,
        language=candidate.language,
        category=candidate.category,
        snippet_id=candidate.snippet_id,
        script_path=candidate.path,
        script_id=candidate.script_id,
        analysis_granularity="snippet",
        source_root=source_root,
        project_key=project_key,
        scanner_log=scanner_log,
    )

    properties = [
        f"-Dsonar.projectKey={project_key}",
        f"-Dsonar.projectName={project_name}",
        "-Dsonar.projectVersion=1",
        f"-Dsonar.host.url={sonar_host_url}",
        "-Dsonar.sourceEncoding=UTF-8",
        "-Dsonar.scm.disabled=true",
        f"-Dsonar.sources={source_name}",
    ]

    if candidate.language == "python":
        properties.append(f"-Dsonar.inclusions={source_name}")
    else:
        properties.append(f"-Dsonar.inclusions={source_name}")
        lintr_report = snippet_out / "lintr-sonar-external-issues.json"
        ok, msg = generate_lintr_external_issues(
            source_root,
            lintr_report,
            rscript_bin=rscript_bin,
            repo_root=REPO_ROOT,
            target_file=candidate.path,
        )
        if ok:
            properties.append(f"-Dsonar.externalIssuesReportPaths={lintr_report}")
        else:
            (snippet_out / "lintr-error.log").write_text(msg + "\n", encoding="utf-8")

    cmd = [sonar_scanner_bin] + properties
    env = os.environ.copy()
    if sonar_token:
        env["SONAR_TOKEN"] = sonar_token

    proc = subprocess.run(cmd, cwd=str(source_root), capture_output=True, text=True, check=False, env=env)
    scanner_log.write_text((proc.stdout or "") + "\n" + (proc.stderr or ""), encoding="utf-8")

    return finish_sonar_row(
        row,
        proc=proc,
        report_task=report_task,
        sonar_host_url=sonar_host_url,
        sonar_token=sonar_token,
        project_key=project_key,
    )


def evaluate_static(
    targets: list[Candidate] | list[Slice],
    output_dir: Path,
    sonar_scanner_bin: str,
    sonar_host_url: str,
    sonar_token: str | None,
    sonar_project_prefix: str,
    rscript_bin: str,
    granularity: str,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    total = len(targets)

    for idx, target in enumerate(targets, start=1):
        if granularity == "slice":
            assert isinstance(target, Slice)
            print(f"[maintainability {idx}/{total}] {target.model}/{target.prompt_type}/{target.language}")
            row = run_sonar_for_slice(
                target,
                output_dir=output_dir,
                sonar_scanner_bin=sonar_scanner_bin,
                sonar_host_url=sonar_host_url,
                sonar_token=sonar_token,
                sonar_project_prefix=sonar_project_prefix,
                rscript_bin=rscript_bin,
            )
        else:
            assert isinstance(target, Candidate)
            print(
                f"[maintainability {idx}/{total}] "
                f"{target.model}/{target.prompt_type}/{target.language}/{target.category}/{target.snippet_id}"
            )
            row = run_sonar_for_candidate(
                target,
                output_dir=output_dir,
                sonar_scanner_bin=sonar_scanner_bin,
                sonar_host_url=sonar_host_url,
                sonar_token=sonar_token,
                sonar_project_prefix=sonar_project_prefix,
                rscript_bin=rscript_bin,
            )
        rows.append(row)
        print(f"  -> status={rows[-1].get('sonar_status', '')}")

    csv_path = output_dir / "static_sonar_results.csv"
    json_path = output_dir / "static_sonar_results.json"

    fields = [
        "script_id",
        "model",
        "prompt_type",
        "language",
        "category",
        "snippet_id",
        "script_path",
        "analysis_granularity",
        "source_root",
        "project_key",
        "sonar_status",
        "sonar_scanner_exit_code",
        "quality_gate",
        "bugs",
        "vulnerabilities",
        "code_smells",
        "reliability_rating",
        "security_rating",
        "sqale_rating",
        "duplicated_lines_density",
        "ncloc",
        "coverage",
        "analysis_id",
        "ce_task_id",
        "error",
        "scanner_log",
    ]

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "granularity": granularity,
        "target_count": len(targets),
        "rows": rows,
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    return {"rows": rows, "csv": csv_path, "json": json_path}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Sonar-based maintainability checks for llm_translations.")
    parser.add_argument("--rscript-bin", default="Rscript")
    parser.add_argument("--sonar-scanner-bin", default="sonar-scanner")
    parser.add_argument("--sonar-host-url", default=os.environ.get("SONAR_HOST_URL", "http://localhost:9000"))
    parser.add_argument("--sonar-token", default=os.environ.get("SONAR_TOKEN", ""))
    parser.add_argument("--sonar-project-prefix", default="masters_thesis_translations")
    parser.add_argument(
        "--granularity",
        choices=("snippet", "slice"),
        default="snippet",
        help="Analyze each candidate file separately, or keep the old model/prompt/language slice behavior.",
    )
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
    ensure_dir(output_dir / "static")
    write_run_manifest(output_dir, "static", args, candidates, blacklist_entries, blacklisted_candidates)

    print(f"Run ID: {run_id}")
    print(f"Candidates discovered: {len(candidates)}")
    if blacklist_entries:
        print(f"Blacklist file: {args.blacklist_file}")
        print(f"Candidates excluded by blacklist: {len(blacklisted_candidates)}")

    targets = discover_slices(candidates) if args.granularity == "slice" else candidates
    result = evaluate_static(
        targets,
        output_dir=output_dir,
        sonar_scanner_bin=args.sonar_scanner_bin,
        sonar_host_url=args.sonar_host_url,
        sonar_token=args.sonar_token.strip() or None,
        sonar_project_prefix=args.sonar_project_prefix,
        rscript_bin=args.rscript_bin,
        granularity=args.granularity,
    )
    print(f"Maintainability CSV: {result['csv']}")
    print(f"Maintainability JSON: {result['json']}")
    print(f"All outputs stored in: {output_dir}")
    return 0


def main() -> int:
    return run(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
