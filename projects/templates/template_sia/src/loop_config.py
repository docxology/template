"""Load SIA loop settings from manuscript config."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class SiaLoopSettings:
    """Project-level SIA loop configuration."""

    task_name: str
    run_id: int
    max_generations: int
    live: bool
    target_timeout_sec: int
    llm_model: str

    @property
    def task_dir(self) -> str:
        return f"tasks/{self.task_name}"


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def load_sia_settings(project_root: Path) -> SiaLoopSettings:
    """Read sia block from manuscript/config.yaml."""
    config_path = project_root / "manuscript" / "config.yaml"
    raw = _load_yaml_mapping(config_path)
    sia_raw = raw.get("sia")
    sia_block: dict[str, Any] = sia_raw if isinstance(sia_raw, dict) else {}
    return SiaLoopSettings(
        task_name=str(sia_block.get("task_name", "mini_classify")),
        run_id=int(sia_block.get("run_id", 1)),
        max_generations=int(sia_block.get("max_generations", 3)),
        live=bool(sia_block.get("live", False)),
        target_timeout_sec=int(sia_block.get("target_timeout_sec", 60)),
        llm_model=str(sia_block.get("llm_model", "")),
    )


def load_paper_title(project_root: Path) -> str:
    """Return paper title from config."""
    config_path = project_root / "manuscript" / "config.yaml"
    raw = _load_yaml_mapping(config_path)
    paper = raw.get("paper") or {}
    return str(paper.get("title", "template_sia"))


__all__ = ["SiaLoopSettings", "load_paper_title", "load_sia_settings"]
