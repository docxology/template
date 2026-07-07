"""Canonical pipeline stage names and alias matching from pipeline.yaml."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

_OPT_IN_TAGS = frozenset({"ebook", "metadata", "bundle", "archival", "science", "provenance"})

# Informal tokens → canonical stage name (from pipeline.yaml + single_stage.py keys).
_STAGE_ALIAS_TO_CANONICAL: dict[str, str] = {
    "clean": "Clean Output Directories",
    "setup": "Environment Setup",
    "infra_tests": "Infrastructure Tests",
    "project_tests": "Project Tests",
    "tests": "Infrastructure Tests",
    "analysis": "Project Analysis",
    "project analysis": "Project Analysis",
    "render": "PDF Rendering",
    "render_pdf": "PDF Rendering",
    "pdf rendering": "PDF Rendering",
    "validate": "Output Validation",
    "output validation": "Output Validation",
    "copy": "Copy Outputs",
    "llm_reviews": "LLM Scientific Review",
    "llm_translations": "LLM Translations",
}

_SCRIPT_TO_CANONICAL: dict[str, str] = {
    "00_setup_environment.py": "Environment Setup",
    "01_run_tests.py": "Project Tests",
    "02_run_analysis.py": "Project Analysis",
    "03_render_pdf.py": "PDF Rendering",
    "04_validate_output.py": "Output Validation",
    "05_copy_outputs.py": "Copy Outputs",
    "06_llm_review.py": "LLM Scientific Review",
}


def _default_pipeline_yaml() -> Path:
    return Path(__file__).resolve().parent / "pipeline.yaml"


@lru_cache(maxsize=4)
def _load_stage_entries(yaml_path: str) -> tuple[dict[str, object], ...]:
    path = Path(yaml_path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    stages = data.get("stages") or []
    return tuple(stages)


def all_stage_names(*, yaml_path: Path | None = None) -> tuple[str, ...]:
    """Ordered stage names from pipeline.yaml."""
    path = yaml_path or _default_pipeline_yaml()
    return tuple(str(s["name"]) for s in _load_stage_entries(str(path)) if s.get("name"))


def core_stage_names(*, yaml_path: Path | None = None) -> tuple[str, ...]:
    """Default-run stages: excludes opt-in bundle/archival tagged stages."""
    path = yaml_path or _default_pipeline_yaml()
    names: list[str] = []
    for stage in _load_stage_entries(str(path)):
        name = stage.get("name")
        if not name:
            continue
        tags = set(stage.get("tags") or [])
        if tags & _OPT_IN_TAGS:
            continue
        names.append(str(name))
    return tuple(names)


def menu_stage_names(*, yaml_path: Path | None = None) -> tuple[str, ...]:
    """Stages shown in run.sh menu banners (excludes Clean Output Directories)."""
    return tuple(n for n in core_stage_names(yaml_path=yaml_path) if n != "Clean Output Directories")


def stage_aliases() -> dict[str, str]:
    """Map informal tokens to canonical stage labels."""
    aliases = dict(_STAGE_ALIAS_TO_CANONICAL)
    for name in core_stage_names():
        aliases[name.lower()] = name
    return aliases


def text_mentions_stage(text: str, canonical_name: str) -> bool:
    """True when *text* references *canonical_name* by label, alias, or script."""
    lower = text.lower()
    canonical_lower = canonical_name.lower()
    if canonical_lower in lower:
        return True
    for alias, target in stage_aliases().items():
        if target.lower() == canonical_lower and alias in lower:
            return True
    for script, target in _SCRIPT_TO_CANONICAL.items():
        if target.lower() == canonical_lower and script in lower:
            return True
    return False


def text_mentions_any_stage(text: str) -> bool:
    """True when text references any canonical core stage."""
    return any(text_mentions_stage(text, name) for name in core_stage_names())
