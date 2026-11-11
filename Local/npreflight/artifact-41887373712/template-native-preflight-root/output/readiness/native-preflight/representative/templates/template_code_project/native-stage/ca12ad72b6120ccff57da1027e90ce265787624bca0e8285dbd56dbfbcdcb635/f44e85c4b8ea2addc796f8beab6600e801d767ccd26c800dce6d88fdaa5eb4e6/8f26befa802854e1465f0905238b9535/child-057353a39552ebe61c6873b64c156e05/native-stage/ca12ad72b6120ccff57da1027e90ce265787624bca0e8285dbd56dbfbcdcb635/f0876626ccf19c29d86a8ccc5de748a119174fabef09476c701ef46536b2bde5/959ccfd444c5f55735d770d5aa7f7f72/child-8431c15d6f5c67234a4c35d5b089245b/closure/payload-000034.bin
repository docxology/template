"""Shared runtime helpers for template_code_project src modules."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .experiment_config import ExperimentConfig, load_experiment_config
from .project_paths import resolve_project_root


def project_root(caller: str = "src") -> Path:
    """Process project root."""
    return resolve_project_root(caller)


def get_logger(module_name: str | None = None) -> logging.Logger:
    """Get logger."""
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
    """Process experiment config."""
    return load_experiment_config(project_root())


def save_figure_data(data: object, name: str, output_dir: Path) -> Path:
    """Save figure data to the output path."""
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    data_path = data_dir / f"{name}.json"
    if analysis_metadata_observation(output_dir.parent) is not None:
        write_analysis_bytes(output_dir.parent, data_path, json.dumps(data, indent=2, default=str).encode())
    else:
        with open(data_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
    return data_path


def read_analysis_bytes(root: Path, path: Path) -> bytes:
    """Read exact workflow input bytes through the Source-owned runtime adapter.

    The real supervised worker records the body returned to this caller. A
    standalone project keeps ordinary read behavior without claiming custody.
    Mathematical optimizer/invariant modules do not use this adapter.
    """
    try:
        from infrastructure.core.analysis_read_custody import read_analysis_bytes as read_supervised
    except ImportError:  # pragma: no cover — standalone package without the SDK
        return path.read_bytes()
    return read_supervised(root, path)


def write_analysis_bytes(root: Path, path: Path, content: bytes) -> Path:
    """Persist exact workflow bytes through the real supervised Source write API."""
    try:
        from infrastructure.core.analysis_write_custody import (
            current_analysis_write_project,
            write_analysis_bytes as write_supervised,
        )
    except ImportError:  # pragma: no cover — standalone package without SDK
        path.write_bytes(content)
        return path
    actual = current_analysis_write_project()
    if actual is None:
        path.write_bytes(content)
        return path
    if root.absolute() != actual:
        raise ValueError("Code output writer differs from its genuine actual project scope")
    return write_supervised(actual, path, content)


def analysis_metadata_observation(root: Path) -> dict[str, Any] | None:
    """Allocate DATA only inside the existing genuine supervised write scope."""
    try:
        from infrastructure.core.analysis_write_custody import current_analysis_write_project
    except ImportError:  # pragma: no cover — standalone package without SDK
        return None
    actual = current_analysis_write_project()
    if actual is None:
        return None
    if root.absolute() != actual:
        raise ValueError("Code metadata observation differs from its actual project scope")
    return {}


def retain_analysis_metadata(root: Path, observation: dict[str, Any]) -> dict[str, Any]:
    """Use the existing completed-write and returned-read Source APIs once.

    Only a real active analysis scope emits this hydration companion. Ordinary
    standalone generation keeps its existing flat variables/output behavior.
    No DATA dictionary supplies ownership, process facts or a native pass.
    """
    if analysis_metadata_observation(root) is None:
        raise ValueError("Code metadata retention lost its actual supervised project")
    path = root / "output/data/manuscript_metadata.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(observation, sort_keys=True, separators=(",", ":")).encode()
    write_analysis_bytes(root, path, body)
    returned = json.loads(read_analysis_bytes(root, path))
    if not isinstance(returned, dict) or returned != observation:
        raise ValueError("Code metadata returned body differs from the actual captured Source calls")
    return returned


def save_analysis_figure(root: Path, path: Path, figure: Any) -> bool:
    """Hook only the genuine actual analysis scope; preserve ordinary save calls."""
    if analysis_metadata_observation(root) is None:
        return False
    from infrastructure.core.analysis_figure_custody import save_native_figure

    save_native_figure(root, path, figure)
    return True


__all__ = [
    "experiment_config",
    "get_logger",
    "project_root",
    "save_figure_data",
    "read_analysis_bytes",
    "write_analysis_bytes",
    "analysis_metadata_observation",
    "retain_analysis_metadata",
    "save_analysis_figure",
]
