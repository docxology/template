"""Configuration loading for AutoResearch readiness checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from infrastructure.autoresearch.models import AutoResearchConfig, DEFAULT_QUALITY_CHECKS

_CONFIG_KEYS = frozenset(
    {
        "enabled",
        "strict",
        "topic",
        "quality_checks",
        "stage_gates",
        "required_artifacts",
    }
)


def load_autoresearch_config(project_root: Path) -> AutoResearchConfig:
    """Load optional ``autoresearch.yaml`` from a project root."""
    path = project_root / "autoresearch.yaml"
    if not path.exists():
        return AutoResearchConfig()

    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"autoresearch.yaml must be a mapping: {path}")
    unknown = set(payload) - _CONFIG_KEYS
    if unknown:
        keys = ", ".join(sorted(str(key) for key in unknown))
        raise ValueError(f"unsupported autoresearch key(s): {keys}")

    return AutoResearchConfig(
        enabled=_bool_value(payload.get("enabled", True), "enabled"),
        strict=_bool_value(payload.get("strict", False), "strict"),
        topic=str(payload.get("topic", "") or ""),
        quality_checks=parse_string_sequence(payload.get("quality_checks"), default=DEFAULT_QUALITY_CHECKS),
        stage_gates=parse_string_sequence(payload.get("stage_gates"), default=()),
        required_artifacts=parse_string_sequence(payload.get("required_artifacts"), default=()),
        source_path=str(path),
    )


def _bool_value(value: Any, key: str) -> bool:
    if isinstance(value, bool):
        return value
    raise ValueError(f"autoresearch {key} must be a boolean")


def parse_string_sequence(value: Any, *, default: tuple[str, ...]) -> tuple[str, ...]:
    """Parse YAML sequence values into a tuple of strings."""
    if value is None:
        return default
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list | tuple):
        if not all(isinstance(item, str) for item in value):
            raise ValueError("autoresearch list values must be strings")
        return tuple(value)
    raise ValueError("autoresearch sequence values must be strings or lists of strings")
