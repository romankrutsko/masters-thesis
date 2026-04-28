#!/usr/bin/env python3
"""Shared discovery and run-manifest helpers for translation evaluation."""

from __future__ import annotations

import argparse
import importlib.util
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TASK_EQ_ROOT = REPO_ROOT / "task_equivalents"
LLM_ROOT = TASK_EQ_ROOT / "llm_translations"
REF_ROOTS = {
    "python": TASK_EQ_ROOT / "python",
    "r": TASK_EQ_ROOT / "r",
}
DEFAULT_OUTPUT_ROOT = TASK_EQ_ROOT / "evaluation_outputs"
DEFAULT_BLACKLIST_FILE = Path(__file__).resolve().parent / "evaluation_blacklist.txt"


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

    # Expected layout: model/prompt_type/language/category/file
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


def discover_slices(candidates: list[Candidate]) -> list[Slice]:
    seen: dict[tuple[str, str, str], Path] = {}
    for c in candidates:
        # Maintainability checks run once per model/prompt/language slice.
        key = (c.model, c.prompt_type, c.language)
        slice_root = LLM_ROOT / c.model / c.prompt_type / c.language
        seen[key] = slice_root

    return [
        Slice(model=k[0], prompt_type=k[1], language=k[2], root=v)
        for k, v in sorted(seen.items(), key=lambda x: x[0])
    ]


def parse_csv_set(raw: str) -> set[str]:
    vals = [x.strip() for x in raw.split(",") if x.strip()]
    return set(vals)


def load_blacklist(path: Path) -> set[str]:
    if not path.exists():
        return set()

    entries: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if line:
            entries.add(line)
    return entries


def to_rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except Exception:
        return str(path)


def filter_candidates(
    candidates: list[Candidate],
    models: str,
    prompt_types: str,
    languages: str,
    blacklist_file: Path,
) -> tuple[list[Candidate], set[str], list[str]]:
    if models.strip():
        allowed = parse_csv_set(models)
        candidates = [c for c in candidates if c.model in allowed]
    if prompt_types.strip():
        allowed = parse_csv_set(prompt_types)
        candidates = [c for c in candidates if c.prompt_type in allowed]
    if languages.strip():
        allowed = parse_csv_set(languages)
        candidates = [c for c in candidates if c.language in allowed]

    blacklist_entries = load_blacklist(blacklist_file)
    blacklisted_candidates: list[str] = []
    if blacklist_entries:
        kept: list[Candidate] = []
        for c in candidates:
            rel = to_rel(c.path)
            if rel in blacklist_entries:
                blacklisted_candidates.append(rel)
                continue
            kept.append(c)
        candidates = kept

    return candidates, blacklist_entries, blacklisted_candidates


def write_run_manifest(
    output_dir: Path,
    mode: str,
    args: argparse.Namespace,
    candidates: list[Candidate],
    blacklist_entries: set[str],
    blacklisted_candidates: list[str],
) -> Path:
    path = output_dir / "run_manifest.json"
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(REPO_ROOT),
        "llm_root": str(LLM_ROOT),
        "candidate_count": len(candidates),
        "blacklist_count": len(blacklist_entries),
        "blacklisted_candidates": blacklisted_candidates,
        "args": {
            "mode": mode,
            "python_bin": getattr(args, "python_bin", ""),
            "rscript_bin": getattr(args, "rscript_bin", ""),
            "digits": getattr(args, "digits", None),
            "atol": getattr(args, "atol", None),
            "rtol": getattr(args, "rtol", None),
            "score_decimals": getattr(args, "score_decimals", None),
            "execution_timeout": getattr(args, "execution_timeout", None),
            "sonar_scanner_bin": getattr(args, "sonar_scanner_bin", ""),
            "sonar_host_url": getattr(args, "sonar_host_url", ""),
            "sonar_project_prefix": getattr(args, "sonar_project_prefix", ""),
            "output_dir": str(output_dir),
            "models": getattr(args, "models", ""),
            "prompt_types": getattr(args, "prompt_types", ""),
            "languages": getattr(args, "languages", ""),
            "blacklist_file": str(getattr(args, "blacklist_file", "")),
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
