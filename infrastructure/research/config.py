"""Configuration loading for the research workflow module."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ResearchWorkflowConfig:
    """Runtime configuration for the research workflow.

    Attributes:
        enabled: Whether workflow tracking is active.
        active_stage: Name of the currently active stage, or empty string.
        skip_stages: Stage names that should be auto-skipped.
        strict: When ``True``, gate failures block downstream stages.
        source_path: Absolute path of the loaded config file.
    """

    enabled: bool = True
    active_stage: str = ""
    skip_stages: tuple[str, ...] = field(default_factory=tuple)
    strict: bool = False
    source_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "active_stage": self.active_stage,
            "skip_stages": list(self.skip_stages),
            "strict": self.strict,
        }


_CONFIG_KEYS = frozenset(
    {
        "enabled",
        "active_stage",
        "skip_stages",
        "strict",
    }
)

_VALID_STAGES = frozenset(
    {
        "scope",
        "survey",
        "hypothesise",
        "experiment",
        "validate",
        "review",
        "write",
    }
)


def load_research_workflow_config(project_dir: Path | str) -> ResearchWorkflowConfig:
    """Load optional ``research_workflow.yaml`` from *project_dir*.

    Falls back to defaults when the file is absent.

    Args:
        project_dir: Project root directory.

    Returns:
        A populated :class:`ResearchWorkflowConfig`.

    Raises:
        ValueError: On unknown keys or invalid stage names.
    """
    project_dir = Path(project_dir)
    config_path = project_dir / "research_workflow.yaml"
    if not config_path.exists():
        return ResearchWorkflowConfig()

    try:
        import yaml

        payload: dict[str, Any] = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except ImportError:
        import json as _json

        payload = _json.loads(config_path.read_text(encoding="utf-8"))

    if not isinstance(payload, dict):
        raise ValueError(f"research_workflow.yaml must be a mapping: {config_path}")

    unknown = set(payload) - _CONFIG_KEYS
    if unknown:
        raise ValueError(f"unknown research_workflow key(s): {', '.join(sorted(str(k) for k in unknown))}")

    enabled = payload.get("enabled", True)
    if not isinstance(enabled, bool):
        raise ValueError("research_workflow.enabled must be a boolean")

    active_stage = str(payload.get("active_stage", "") or "")
    if active_stage and active_stage not in _VALID_STAGES:
        raise ValueError(
            f"research_workflow.active_stage '{active_stage}' is not a valid stage. "
            f"Valid: {', '.join(sorted(_VALID_STAGES))}"
        )

    raw_skip = payload.get("skip_stages") or []
    if not isinstance(raw_skip, list):
        raise ValueError("research_workflow.skip_stages must be a list")
    skip_stages: tuple[str, ...] = tuple(str(s) for s in raw_skip)
    invalid_skip = set(skip_stages) - _VALID_STAGES
    if invalid_skip:
        raise ValueError(f"research_workflow.skip_stages contains invalid stages: {', '.join(sorted(invalid_skip))}")

    strict = payload.get("strict", False)
    if not isinstance(strict, bool):
        raise ValueError("research_workflow.strict must be a boolean")

    return ResearchWorkflowConfig(
        enabled=enabled,
        active_stage=active_stage,
        skip_stages=skip_stages,
        strict=strict,
        source_path=str(config_path),
    )


__all__ = ["ResearchWorkflowConfig", "load_research_workflow_config"]
