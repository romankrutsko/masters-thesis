#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import re
import subprocess
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[2]
TASK_EQ_ROOT = REPO_ROOT / "task_equivalents"
LLM_ROOT = TASK_EQ_ROOT / "llm_translations"
REF_ROOTS = {
    "python": TASK_EQ_ROOT / "python",
    "r": TASK_EQ_ROOT / "r",
}
DEFAULT_OUTPUT_ROOT = TASK_EQ_ROOT / "evaluation_outputs"

BASE_WEIGHTS = {
    "kinds": 0.25,
    "shapes": 0.25,
    "vectors": 0.15,
    "models": 0.20,
    "numeric": 0.15,
}


@dataclass(frozen=True)
class Candidate:
    path: Path
    rel_path: Path
    model: str
    prompt_type: str
    language: str
    category: str
    snippet_id: str

    @property
    def slug(self) -> str:
        return f"{self.model}__{self.prompt_type}__{self.language}__{self.category}__{self.snippet_id}"


@dataclass(frozen=True)
class Slice:
    model: str
    prompt_type: str
    language: str
    root: Path

    @property
    def slug(self) -> str:
        return f"{self.model}__{self.prompt_type}__{self.language}"


def load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def discover_candidates(root: Path) -> list[Candidate]:
    out: list[Candidate] = []

    for ext, language in ((".py", "python"), (".R", "r"), (".r", "r")):
        for file_path in sorted(root.rglob(f"*{ext}")):
            rel = file_path.relative_to(root)
            parts = rel.parts
            if len(parts) < 5:
                continue
            model, prompt_type, lang_dir = parts[0], parts[1], parts[2]
            if prompt_type not in {"base", "optimized"}:
                continue
            if lang_dir not in {"python", "r"}:
                continue
            if lang_dir != language:
                continue

            category = parts[3]
            snippet_id = Path(parts[-1]).stem
            out.append(
                Candidate(
                    path=file_path,
                    rel_path=rel,
                    model=model,
                    prompt_type=prompt_type,
                    language=language,
                    category=category,
                    snippet_id=snippet_id,
                )
            )

    return sorted(out, key=lambda c: (c.model, c.prompt_type, c.language, c.category, c.snippet_id))


def parse_csv_set(raw: str) -> set[str]:
    vals = [x.strip() for x in raw.split(",") if x.strip()]
    return set(vals)


def discover_slices(candidates: list[Candidate]) -> list[Slice]:
    seen: dict[tuple[str, str, str], Path] = {}
    for c in candidates:
        key = (c.model, c.prompt_type, c.language)
        slice_root = LLM_ROOT / c.model / c.prompt_type / c.language
        seen[key] = slice_root

    return [
        Slice(model=k[0], prompt_type=k[1], language=k[2], root=v)
        for k, v in sorted(seen.items(), key=lambda x: x[0])
    ]


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


def run_script(mod, language: str, path: Path, python_bin: str, rscript_bin: str) -> dict[str, Any]:
    if language == "python":
        return mod.run_python_baseline(path, python_bin=python_bin)
    return mod.run_r_baseline(path, rscript_bin=rscript_bin)


def to_rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except Exception:
        return str(path)


def evaluate_execution(
    candidates: list[Candidate],
    python_bin: str,
    rscript_bin: str,
    digits: int,
    atol: float,
    rtol: float,
    score_decimals: int,
    output_dir: Path,
) -> dict[str, Any]:
    gb = load_module(TASK_EQ_ROOT / "tests" / "generate_baselines.py", "generate_baselines")

    rows: list[dict[str, Any]] = []
    per_slice_scores: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    total = len(candidates)

    for idx, c in enumerate(candidates, start=1):
        print(
            f"[execution {idx}/{total}] {c.model}/{c.prompt_type}/{c.language}/"
            f"{c.category}/{c.snippet_id}"
        )
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

        ref_run = run_script(gb, c.language, ref_path, python_bin=python_bin, rscript_bin=rscript_bin)
        if ref_run.get("status") != "ok":
            row["status"] = "reference_error"
            row["error"] = (ref_run.get("stderr") or "Reference execution failed").splitlines()[-1] if (ref_run.get("stderr") or "") else "Reference execution failed"
            rows.append(row)
            print(f"  -> reference error: {row['error']}")
            continue

        cand_run = run_script(gb, c.language, c.path, python_bin=python_bin, rscript_bin=rscript_bin)
        if cand_run.get("status") != "ok":
            row["status"] = "candidate_error"
            row["error"] = (cand_run.get("stderr") or "Candidate execution failed").splitlines()[-1] if (cand_run.get("stderr") or "") else "Candidate execution failed"
            rows.append(row)
            print(f"  -> candidate error: {row['error']}")
            continue

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


def generate_lintr_external_issues(slice_root: Path, out_json: Path, rscript_bin: str, repo_root: Path) -> tuple[bool, str]:
    script = r"""
args <- commandArgs(trailingOnly=TRUE)
slice_root <- normalizePath(args[[1]], winslash='/', mustWork=TRUE)
out_json <- args[[2]]
repo_root <- normalizePath(args[[3]], winslash='/', mustWork=TRUE)

if (!requireNamespace('lintr', quietly=TRUE)) {
  stop("Package 'lintr' is required.")
}
if (!requireNamespace('jsonlite', quietly=TRUE)) {
  stop("Package 'jsonlite' is required.")
}

to_rel <- function(path) {
  p <- normalizePath(path, winslash='/', mustWork=FALSE)
  rr <- repo_root
  if (startsWith(p, rr)) {
    sub(paste0('^', rr, '/?'), '', p)
  } else {
    p
  }
}

linters <- lintr::lint_dir(slice_root)
issues <- list()
for (i in seq_along(linters)) {
  l <- linters[[i]]
  filename <- to_rel(l$filename)
  line <- ifelse(is.null(l$line_number) || is.na(l$line_number), 1L, as.integer(l$line_number))
  col <- ifelse(is.null(l$column_number) || is.na(l$column_number), 1L, as.integer(l$column_number))
  end_col <- max(col + 1L, col)

  issues[[length(issues) + 1]] <- list(
    engineId = 'lintr',
    ruleId = as.character(l$linter),
    severity = 'MINOR',
    type = 'CODE_SMELL',
    primaryLocation = list(
      message = as.character(l$message),
      filePath = filename,
      textRange = list(startLine = line, endLine = line, startColumn = col, endColumn = end_col)
    )
  )
}

payload <- list(issues = issues)
jsonlite::write_json(payload, path = out_json, auto_unbox = TRUE, pretty = TRUE)
"""

    proc = subprocess.run(
        [rscript_bin, "-e", script, str(slice_root), str(out_json), str(repo_root)],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0:
        return True, ""
    return False, (proc.stderr or proc.stdout or "lintr failed").strip()


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

    proc = subprocess.run(
        cmd,
        cwd=str(sl.root),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    scanner_log.write_text((proc.stdout or "") + "\n" + (proc.stderr or ""), encoding="utf-8")

    row: dict[str, Any] = {
        "model": sl.model,
        "prompt_type": sl.prompt_type,
        "language": sl.language,
        "slice_root": to_rel(sl.root),
        "project_key": project_key,
        "sonar_status": "ok" if proc.returncode == 0 else "scanner_error",
        "sonar_scanner_exit_code": proc.returncode,
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
        qg = sonar_api_get(
            f"{sonar_host_url.rstrip('/')}/api/qualitygates/project_status",
            sonar_token,
            {"analysisId": analysis_id},
        )
        row["quality_gate"] = qg.get("projectStatus", {}).get("status", "")

        metrics = [
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
        ms = sonar_api_get(
            f"{sonar_host_url.rstrip('/')}/api/measures/component",
            sonar_token,
            {
                "component": project_key,
                "metricKeys": ",".join(metrics),
            },
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


def evaluate_static(
    slices: list[Slice],
    output_dir: Path,
    sonar_scanner_bin: str,
    sonar_host_url: str,
    sonar_token: str | None,
    sonar_project_prefix: str,
    rscript_bin: str,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    total = len(slices)

    for idx, sl in enumerate(slices, start=1):
        print(f"[static {idx}/{total}] {sl.model}/{sl.prompt_type}/{sl.language}")
        rows.append(
            run_sonar_for_slice(
                sl,
                output_dir=output_dir,
                sonar_scanner_bin=sonar_scanner_bin,
                sonar_host_url=sonar_host_url,
                sonar_token=sonar_token,
                sonar_project_prefix=sonar_project_prefix,
                rscript_bin=rscript_bin,
            )
        )
        print(f"  -> status={rows[-1].get('sonar_status', '')}")

    csv_path = output_dir / "static_sonar_results.csv"
    json_path = output_dir / "static_sonar_results.json"

    fields = [
        "model",
        "prompt_type",
        "language",
        "slice_root",
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
        "slice_count": len(slices),
        "rows": rows,
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    return {
        "rows": rows,
        "csv": csv_path,
        "json": json_path,
    }


def write_run_manifest(output_dir: Path, args: argparse.Namespace, candidates: list[Candidate]) -> Path:
    path = output_dir / "run_manifest.json"
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(REPO_ROOT),
        "llm_root": str(LLM_ROOT),
        "candidate_count": len(candidates),
        "args": {
            "mode": args.mode,
            "python_bin": args.python_bin,
            "rscript_bin": args.rscript_bin,
            "digits": args.digits,
            "atol": args.atol,
            "rtol": args.rtol,
            "score_decimals": args.score_decimals,
            "sonar_scanner_bin": args.sonar_scanner_bin,
            "sonar_host_url": args.sonar_host_url,
            "sonar_project_prefix": args.sonar_project_prefix,
            "output_dir": str(output_dir),
            "models": args.models,
            "prompt_types": args.prompt_types,
            "languages": args.languages,
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run execution-based reliability scoring (0.0-1.0) and Sonar static checks for llm_translations."
    )
    parser.add_argument("--mode", choices=["all", "execution", "static"], default="all")
    parser.add_argument("--python-bin", default=str(REPO_ROOT / ".venv" / "bin" / "python3"))
    parser.add_argument("--rscript-bin", default="Rscript")
    parser.add_argument("--digits", type=int, default=4)
    parser.add_argument("--atol", type=float, default=1e-3)
    parser.add_argument("--rtol", type=float, default=1e-3)
    parser.add_argument("--score-decimals", type=int, default=1)

    parser.add_argument("--sonar-scanner-bin", default="sonar-scanner")
    parser.add_argument("--sonar-host-url", default=os.environ.get("SONAR_HOST_URL", "http://localhost:9000"))
    parser.add_argument("--sonar-token", default=os.environ.get("SONAR_TOKEN", ""))
    parser.add_argument("--sonar-project-prefix", default="masters_thesis_translations")

    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--run-id", default="")
    parser.add_argument("--models", default="")
    parser.add_argument("--prompt-types", default="")
    parser.add_argument("--languages", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    candidates = discover_candidates(LLM_ROOT)
    if args.models.strip():
        allowed = parse_csv_set(args.models)
        candidates = [c for c in candidates if c.model in allowed]
    if args.prompt_types.strip():
        allowed = parse_csv_set(args.prompt_types)
        candidates = [c for c in candidates if c.prompt_type in allowed]
    if args.languages.strip():
        allowed = parse_csv_set(args.languages)
        candidates = [c for c in candidates if c.language in allowed]
    if not candidates:
        print(f"No candidate files found under: {LLM_ROOT}")
        return 2

    run_id = args.run_id.strip() or now_stamp()
    output_dir = args.output_root / run_id
    ensure_dir(output_dir)
    ensure_dir(output_dir / "static")

    write_run_manifest(output_dir, args, candidates)

    print(f"Run ID: {run_id}")
    print(f"Candidates discovered: {len(candidates)}")

    if args.mode in {"all", "execution"}:
        print("Running execution scoring...")
        exec_result = evaluate_execution(
            candidates,
            python_bin=args.python_bin,
            rscript_bin=args.rscript_bin,
            digits=args.digits,
            atol=args.atol,
            rtol=args.rtol,
            score_decimals=args.score_decimals,
            output_dir=output_dir,
        )
        print(f"Execution avg score: {exec_result['avg_score']:.4f}")
        print(f"Execution CSV: {exec_result['csv']}")
        print(f"Execution JSON: {exec_result['json']}")

    if args.mode in {"all", "static"}:
        print("Running static Sonar checks...")
        slices = discover_slices(candidates)
        static_result = evaluate_static(
            slices,
            output_dir=output_dir,
            sonar_scanner_bin=args.sonar_scanner_bin,
            sonar_host_url=args.sonar_host_url,
            sonar_token=args.sonar_token.strip() or None,
            sonar_project_prefix=args.sonar_project_prefix,
            rscript_bin=args.rscript_bin,
        )
        print(f"Static CSV: {static_result['csv']}")
        print(f"Static JSON: {static_result['json']}")

    print(f"All outputs stored in: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
