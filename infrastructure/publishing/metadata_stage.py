"""Metadata package generation orchestrator (thin delegate)."""

from __future__ import annotations
from pathlib import Path
from typing import Any
from infrastructure.core.logging.utils import get_logger, log_success
from infrastructure.project.discovery import resolve_project_root
from infrastructure.publishing.metadata_package import ebook_metadata_from_config, generate_metadata_package

logger = get_logger(__name__)


def _load_config(project_root: Path) -> dict[str, Any] | None:
    config_path = project_root / "manuscript" / "config.yaml"
    if not config_path.is_file():
        return None
    try:
        import yaml
    except ImportError:
        from infrastructure.core.config.loader import load_config as _load

        loaded = _load(config_path)
        return dict(loaded) if isinstance(loaded, dict) else None
    with config_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
        return data if isinstance(data, dict) else None


def run_metadata_package(repo_root: Path, project: str) -> int:
    """Run the metadata packaging stage."""
    project_root = resolve_project_root(repo_root, project)
    config = _load_config(project_root)
    if config is None:
        logger.warning("No manuscript/config.yaml — skipping metadata package stage")
        return 2
    meta = ebook_metadata_from_config(config, project_root.name)
    out_dir = project_root / "output" / "metadata"
    try:
        paths = generate_metadata_package(meta, out_dir)
    except OSError as exc:
        logger.error("Metadata generation failed: %s", exc, exc_info=True)
        return 1
    project_opf = out_dir / f"{project_root.name}.opf"
    if paths["opf"] != project_opf:
        project_opf.write_text(paths["opf"].read_text(encoding="utf-8"), encoding="utf-8")
    log_success(f"Metadata package complete — {len(paths)} file(s) in {out_dir}", logger)
    return 0


__all__ = ["run_metadata_package"]
