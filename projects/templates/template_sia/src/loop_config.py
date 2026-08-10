"""Load SIA loop settings from manuscript config."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import yaml

from .approval import ApprovalMode


@dataclass(frozen=True)
class SiaLoopSettings:
    """Project-level SIA loop configuration."""

    task_name: str
    run_id: int
    max_generations: int
    live: bool
    target_timeout_sec: int
    llm_model: str
    approval_mode: ApprovalMode = "fixture_replay"

    def __post_init__(self) -> None:
        """Reject ambiguous loop settings before the harness is invoked."""
        if not self.task_name.strip():
            raise ValueError("sia.task_name must be non-empty")
        if self.run_id < 1:
            raise ValueError("sia.run_id must be positive")
        if self.max_generations < 1:
            raise ValueError("sia.max_generations must be positive")
        if self.target_timeout_sec < 1:
            raise ValueError("sia.target_timeout_sec must be positive")
        if self.approval_mode not in {"fixture_replay", "live_proposal", "live_apply"}:
            raise ValueError(f"sia.approval_mode is unknown: {self.approval_mode!r}")

    @property
    def task_dir(self) -> str:
        """Process task dir."""
        return f"tasks/{self.task_name}"


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def load_sia_settings(project_root: Path) -> SiaLoopSettings:
    """Read the namespaced SIA block, with legacy-root compatibility."""
    config_path = project_root / "manuscript" / "config.yaml"
    raw = _load_yaml_mapping(config_path)
    project_raw = raw.get("project_config")
    project_block = project_raw if isinstance(project_raw, dict) else {}
    sia_raw = project_block.get("sia", raw.get("sia"))
    sia_block: dict[str, Any] = sia_raw if isinstance(sia_raw, dict) else {}
    return SiaLoopSettings(
        task_name=str(sia_block.get("task_name", "mini_classify")),
        run_id=int(sia_block.get("run_id", 1)),
        max_generations=int(sia_block.get("max_generations", 3)),
        live=_parse_bool(sia_block.get("live", False), "sia.live"),
        target_timeout_sec=int(sia_block.get("target_timeout_sec", 60)),
        llm_model=str(sia_block.get("llm_model", "")),
        approval_mode=_parse_approval_mode(sia_block.get("approval_mode", "fixture_replay")),
    )


def _parse_bool(value: Any, field_name: str) -> bool:
    """Parse YAML booleans without treating the string ``"false"`` as true."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "on", "1"}:
            return True
        if normalized in {"false", "no", "off", "0"}:
            return False
    raise ValueError(f"{field_name} must be a boolean")


def _parse_approval_mode(value: Any) -> ApprovalMode:
    """Parse the explicit fork mode without accepting arbitrary strings."""
    if value in {"fixture_replay", "live_proposal", "live_apply"}:
        return cast(ApprovalMode, value)
    raise ValueError("sia.approval_mode must be fixture_replay, live_proposal, or live_apply")


def load_paper_title(project_root: Path) -> str:
    """Return paper title from config."""
    config_path = project_root / "manuscript" / "config.yaml"
    raw = _load_yaml_mapping(config_path)
    paper = raw.get("paper") or {}
    return str(paper.get("title", "template_sia"))


__all__ = ["ApprovalMode", "SiaLoopSettings", "load_paper_title", "load_sia_settings"]
