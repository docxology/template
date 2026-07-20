"""YAML-backed stage-key dispatch for single-stage pipeline runs.

The canonical script paths and fixed arguments come from ``pipeline.yaml``.
Only compatibility aliases that do not correspond one-to-one with a DAG stage
remain declared here.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

import yaml

from infrastructure.core.pipeline.dag import PipelineDAG, StageDefinition

__all__ = [
    "MENU_KEY_TO_STAGE",
    "STAGE_DISPATCH",
    "StageDispatch",
    "known_stage_keys",
    "normalize_stage_key",
    "script_argv_for_stage",
    "resolve_stage_definition",
]


@dataclass(frozen=True, slots=True)
class StageDispatch:
    """Repository-relative script path plus fixed CLI arguments."""

    script: str
    args: tuple[str, ...] = ()


_PIPELINE_YAML = Path(__file__).with_name("pipeline.yaml")


def _dispatch_from_yaml(path: Path = _PIPELINE_YAML) -> dict[str, StageDispatch]:
    """Load dispatchable stages from the canonical pipeline definition."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    stages = raw.get("stages") if isinstance(raw, dict) else None
    if not isinstance(stages, list):
        raise ValueError(f"pipeline.yaml must contain a stages list: {path}")

    result: dict[str, StageDispatch] = {}
    for entry in stages:
        if not isinstance(entry, dict):
            raise ValueError(f"pipeline.yaml contains a non-mapping stage: {path}")
        key = entry.get("key")
        script = entry.get("script")
        if key is None or script is None:
            continue
        if not isinstance(key, str) or not isinstance(script, str):
            raise ValueError("Pipeline stage key and script must be strings")
        if key in result:
            raise ValueError(f"Duplicate pipeline stage key: {key}")
        args = entry.get("args", [])
        if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
            raise ValueError(f"Pipeline stage '{key}' args must be a list of strings")
        result[key] = StageDispatch(script, tuple(args))
    return result


_YAML_DISPATCH = _dispatch_from_yaml()
STAGE_DISPATCH: Final[dict[str, StageDispatch]] = {
    **_YAML_DISPATCH,
    # Compatibility aggregate: run both test lanes through their shared script.
    "tests": StageDispatch(
        _YAML_DISPATCH["infra_tests"].script,
        ("--verbose", "--infra-scope", "pipeline-smoke"),
    ),
    # Standalone report generation is intentionally outside the default DAG.
    "executive_report": StageDispatch("scripts/pipeline/stage_07_executive_report.py"),
}

MENU_KEY_TO_STAGE: Final[dict[str, str]] = {
    "0": "setup",
    "1": "tests",
    "2": "analysis",
    "3": "render_pdf",
    "4": "validate",
    "5": "copy",
    "6": "llm_reviews",
    "7": "llm_translations",
}


def known_stage_keys() -> frozenset[str]:
    """Return valid single-stage execution keys."""
    return frozenset(STAGE_DISPATCH)


def normalize_stage_key(stage: str) -> str:
    """Normalize a user-provided stage key."""
    return stage.strip().lower()


def script_argv_for_stage(stage: str) -> tuple[str, ...]:
    """Return ``(script_rel, *args)`` for *stage* or raise ``SystemExit``."""
    key = normalize_stage_key(stage)
    if key not in STAGE_DISPATCH:
        valid = ", ".join(sorted(STAGE_DISPATCH))
        raise SystemExit(f"Unknown stage '{stage}'. Valid: {valid}")
    dispatch = STAGE_DISPATCH[key]
    return (dispatch.script, *dispatch.args)


def resolve_stage_definition(dag: PipelineDAG, stage: str) -> StageDefinition:
    """Resolve a DAG stage by stable key or compatible canonical display name."""
    token = normalize_stage_key(stage)
    by_key = {definition.key: definition for definition in dag.stages if definition.key}
    if token in by_key:
        return by_key[token]

    by_name = {definition.name.strip().lower(): definition for definition in dag.stages}
    if token in by_name:
        return by_name[token]
    normalized_names = {
        definition.name.strip().lower().replace(" ", "_").replace("-", "_"): definition for definition in dag.stages
    }
    if token in normalized_names:
        return normalized_names[token]

    valid = sorted({*(key for key in by_key if key), *by_name})
    raise SystemExit(f"Unknown stage '{stage}'. Valid: {', '.join(valid)}")
