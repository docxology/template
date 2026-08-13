"""Configuration loading for the provenance module."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable
from importlib import import_module
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any


def _validated_relative_path(value: str, *, label: str, filename: bool = False) -> Path:
    """Return a normalized project-relative path or reject an escape."""
    if not value or "\x00" in value or "\\" in value:
        raise ValueError(f"provenance.{label} must be a non-empty relative POSIX path")
    normalized = value.strip()
    parts = PurePosixPath(normalized).parts
    if (
        not parts
        or normalized.startswith("/")
        or any(part in {"", ".", ".."} for part in parts)
        or (filename and len(parts) != 1)
    ):
        suffix = " file" if filename else " path"
        raise ValueError(f"provenance.{label} must be a confined relative{suffix}")
    return Path(*parts)


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
        root = Path(project_dir).resolve()
        output_dir = _validated_relative_path(self.output_dir, label="output_dir")
        filename = _validated_relative_path(self.filename, label="filename", filename=True)
        raw = root / output_dir / filename
        resolved = raw.resolve(strict=False)
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise ValueError("provenance DAG path escapes the project root") from exc
        current = root
        for component in (*output_dir.parts, filename.name):
            current = current / component
            if current.is_symlink():
                raise ValueError(f"provenance DAG path may not contain symlinks: {current}")
        return raw

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

    output_dir_value = payload.get("output_dir", "output/provenance")
    filename_value = payload.get("filename", "dag.json")
    if not isinstance(output_dir_value, str):
        raise ValueError("provenance.output_dir must be a string")
    if not isinstance(filename_value, str):
        raise ValueError("provenance.filename must be a string")
    output_dir = output_dir_value
    filename = filename_value
    _validated_relative_path(output_dir, label="output_dir")
    _validated_relative_path(filename, label="filename", filename=True)

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
