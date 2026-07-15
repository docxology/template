"""Configuration loading for the provenance module."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable
from importlib import import_module
from pathlib import Path
from typing import Any


@dataclass
class ProvenanceConfig:
    """Runtime configuration for the provenance DAG.

    Attributes:
        enabled: Whether provenance tracking is active.
        output_dir: Directory for the DAG JSON file, relative to project root.
        filename: JSON file name (default: ``dag.json``).
        auto_hash_artifacts: Compute content hashes for artifact nodes
            automatically on record.
        source_path: Absolute path of the config file that was loaded, or
            empty string if defaults were used.
    """

    enabled: bool = True
    output_dir: str = "output/provenance"
    filename: str = "dag.json"
    auto_hash_artifacts: bool = False
    source_path: str = ""

    def dag_path(self, project_dir: Path | str) -> Path:
        """Return the absolute path to the DAG JSON file."""
        return Path(project_dir) / self.output_dir / self.filename

    def to_dict(self) -> dict[str, Any]:
        """Serialize this object to a plain dict for JSON output."""
        return {
            "enabled": self.enabled,
            "output_dir": self.output_dir,
            "filename": self.filename,
            "auto_hash_artifacts": self.auto_hash_artifacts,
        }


_CONFIG_KEYS = frozenset(
    {
        "enabled",
        "output_dir",
        "filename",
        "auto_hash_artifacts",
    }
)


def load_provenance_config(
    project_dir: Path | str,
    *,
    yaml_importer: Callable[[str], Any] = import_module,
) -> ProvenanceConfig:
    """Load optional ``provenance.yaml`` from *project_dir*.

    Falls back to defaults when the file is absent.

    Args:
        project_dir: Project root directory.

    Returns:
        A populated :class:`ProvenanceConfig`.

    Raises:
        ValueError: On unknown keys or invalid values.
    """
    project_dir = Path(project_dir)
    config_path = project_dir / "provenance.yaml"
    if not config_path.exists():
        return ProvenanceConfig()

    try:
        yaml = yaml_importer("yaml")

        payload: dict[str, Any] = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except ImportError:
        import json as _json

        payload = _json.loads(config_path.read_text(encoding="utf-8"))

    if not isinstance(payload, dict):
        raise ValueError(f"provenance.yaml must be a mapping: {config_path}")

    unknown = set(payload) - _CONFIG_KEYS
    if unknown:
        raise ValueError(f"unknown provenance key(s): {', '.join(sorted(str(k) for k in unknown))}")

    enabled = payload.get("enabled", True)
    if not isinstance(enabled, bool):
        raise ValueError("provenance.enabled must be a boolean")

    output_dir = str(payload.get("output_dir", "output/provenance"))
    filename = str(payload.get("filename", "dag.json"))

    auto_hash = payload.get("auto_hash_artifacts", False)
    if not isinstance(auto_hash, bool):
        raise ValueError("provenance.auto_hash_artifacts must be a boolean")

    return ProvenanceConfig(
        enabled=enabled,
        output_dir=output_dir,
        filename=filename,
        auto_hash_artifacts=auto_hash,
        source_path=str(config_path),
    )


__all__ = ["ProvenanceConfig", "load_provenance_config"]
