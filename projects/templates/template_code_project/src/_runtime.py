"""Shared runtime helpers for template_code_project src modules."""

from __future__ import annotations

import json
import logging
from pathlib import Path

try:
    from .experiment_config import ExperimentConfig, load_experiment_config
    from .project_paths import resolve_project_root
except ImportError:  # standalone load (no package context) — mirror the src/ import pattern
    from experiment_config import ExperimentConfig, load_experiment_config  # type: ignore[no-redef]
    from project_paths import resolve_project_root  # type: ignore[no-redef]


def project_root(caller: str = "src") -> Path:
    return resolve_project_root(caller)


def get_logger(module_name: str | None = None) -> logging.Logger:
    try:
        from infrastructure.core.logging.utils import get_logger as infra_get_logger

        return infra_get_logger(module_name or __name__)
    except ImportError:  # pragma: no cover
        logger = logging.getLogger(module_name or __name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger


def experiment_config() -> ExperimentConfig:
    return load_experiment_config(project_root())


def save_figure_data(data: object, name: str, output_dir: Path) -> Path:
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    data_path = data_dir / f"{name}.json"
    with open(data_path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    return data_path


__all__ = [
    "experiment_config",
    "get_logger",
    "project_root",
    "save_figure_data",
]
