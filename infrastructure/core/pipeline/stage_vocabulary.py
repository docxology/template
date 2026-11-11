"""Canonical declaration labels, default stage selection, and stage aliases."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any, cast

import yaml

from infrastructure.core.pipeline.dag import StageDefinition, load_opt_in_tags, opt_in_tags_from_mapping
from infrastructure.core.pipeline.target_contracts import selects_default_stage

_DEFAULT_YAML = Path(__file__).resolve().with_name("pipeline.yaml")


def _load_opt_in_tags() -> frozenset[str]:
    """Retain the canonical opt-in tags exported by the pipeline CLI."""
    try:
        return load_opt_in_tags(_DEFAULT_YAML)
    except (OSError, yaml.YAMLError):  # pragma: no cover - a broken DAG fails elsewhere
        return frozenset()


_OPT_IN_TAGS = _load_opt_in_tags()

_STAGE_ALIAS_TO_KEY = {
    "clean": "clean",
    "setup": "setup",
    "infra_tests": "infra_tests",
    "project_tests": "project_tests",
    "tests": "infra_tests",
    "analysis": "analysis",
    "project analysis": "analysis",
    "render": "render_pdf",
    "render_pdf": "render_pdf",
    "pdf rendering": "render_pdf",
    "validate": "validate",
    "output validation": "validate",
    "copy": "copy",
    "llm_reviews": "llm_reviews",
    "llm_translations": "llm_translations",
}

# Stage 01 belongs to project tests and Stage 06 to manuscript review for
# script-name matching. Other declarations may reuse those executable targets.
_SCRIPT_ALIAS_OWNERS = {"setup", "project_tests", "analysis", "render_pdf", "validate", "copy", "llm_reviews"}
_CANONICAL_SCRIPT_DIRECTORY = Path("scripts/pipeline")


def _read_vocabulary(path: Path | None) -> Mapping[str, Any]:
    return cast("Mapping[str, Any]", yaml.safe_load((path or _DEFAULT_YAML).read_text(encoding="utf-8")))


def _declared_stages(data: Mapping[str, Any]) -> Iterator[StageDefinition]:
    """Read the fields used by vocabulary without requiring an executable DAG."""
    for entry in data.get("stages") or []:
        name = entry.get("name")
        if name:
            tags, args = entry.get("tags"), entry.get("args")
            script, method, key = entry.get("script"), entry.get("method"), entry.get("key")
            yield StageDefinition(
                name=str(name),
                key=key if isinstance(key, str) else None,
                script=script if isinstance(script, str) else None,
                method=method if isinstance(method, str) else None,
                tags=[str(tag) for tag in tags] if isinstance(tags, list) else [],
                args=args if isinstance(args, list) else [],
            )


def _selected_stages(data: Mapping[str, Any], mode: str, *, skip_clean: bool = False) -> Iterator[StageDefinition]:
    opt_in_tags = opt_in_tags_from_mapping(data)
    return (
        stage
        for stage in _declared_stages(data)
        if selects_default_stage(stage, mode=mode, opt_in_tags=opt_in_tags, skip_clean=skip_clean)
    )


def stage_names_from_mapping(data: Mapping[str, Any], *, mode: str | None = None) -> tuple[str, ...]:
    """Project one YAML snapshot into declared or selected names in declared order."""
    if mode is None:
        return tuple(stage.name for stage in _declared_stages(data))
    if mode not in {"core", "live"}:
        raise ValueError("Execution mode must be core or live")
    return tuple(stage.name for stage in _selected_stages(data, mode))


def all_stage_names(*, yaml_path: Path | None = None) -> tuple[str, ...]:
    """Ordered stage names from pipeline.yaml."""
    return stage_names_from_mapping(_read_vocabulary(yaml_path))


def live_stage_names(*, yaml_path: Path | None = None) -> tuple[str, ...]:
    """Default live stage names in declaration order."""
    return stage_names_from_mapping(_read_vocabulary(yaml_path), mode="live")


def core_stage_names(*, yaml_path: Path | None = None) -> tuple[str, ...]:
    """Default core stage names in declaration order."""
    return stage_names_from_mapping(_read_vocabulary(yaml_path), mode="core")


def default_run_stage_count(*, mode: str = "core", yaml_path: Path | None = None) -> int:
    """Stage count for the default full run or ``--mode core``."""
    if mode not in {"core", "live"}:
        raise ValueError("Execution mode must be core or live")
    return sum(1 for _ in _selected_stages(_read_vocabulary(yaml_path), mode))


def menu_stage_names(*, yaml_path: Path | None = None) -> tuple[str, ...]:
    """Stage labels for the menu's live selection, with cleanup omitted."""
    return tuple(stage.name for stage in _selected_stages(_read_vocabulary(yaml_path), "live", skip_clean=True))


def _label_aliases(stages: tuple[StageDefinition, ...]) -> dict[str, str]:
    labels = {stage.key: stage.name for stage in stages}
    aliases = {alias: labels[key] for alias, key in _STAGE_ALIAS_TO_KEY.items() if key in labels}
    aliases.update((stage.name.lower(), stage.name) for stage in stages)
    return aliases


def stage_aliases() -> dict[str, str]:
    """Map informal tokens to canonical stage labels."""
    return _label_aliases(tuple(_selected_stages(_read_vocabulary(None), "live")))


def _mention_aliases(stages: tuple[StageDefinition, ...]) -> Iterator[tuple[str, str]]:
    yield from _label_aliases(stages).items()
    for stage in stages:
        if stage.key not in _SCRIPT_ALIAS_OWNERS or not stage.script:
            continue
        script = Path(stage.script)
        if script.parent == _CANONICAL_SCRIPT_DIRECTORY:
            yield script.name.lower(), stage.name


def text_mentions_stage(text: str, canonical_name: str) -> bool:
    """True when *text* references *canonical_name* by label, alias, or script."""
    lower = text.lower()
    canonical_lower = canonical_name.lower()
    if canonical_lower in lower:
        return True
    stages = tuple(_selected_stages(_read_vocabulary(None), "live"))
    return any(target.lower() == canonical_lower and alias in lower for alias, target in _mention_aliases(stages))


def text_mentions_any_stage(text: str) -> bool:
    """True when *text* references a default stage by label, alias, or script."""
    stages = tuple(_selected_stages(_read_vocabulary(None), "live"))
    lower = text.lower()
    return any(alias in lower for alias, _ in _mention_aliases(stages))
