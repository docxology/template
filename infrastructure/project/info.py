"""Project introspection helpers for CLI display."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from infrastructure.core.exceptions import FileNotFoundError


def collect_project_info(project_name: str, repo_root: Path) -> dict[str, Any]:
    """Collect and return project metadata."""
    project_dir = repo_root / "projects" / project_name
    if not project_dir.exists():
        raise FileNotFoundError(
            f"Project directory not found: {project_dir}",
            context={"file": str(project_dir)},
        )

    info: dict[str, Any] = {
        "name": project_name,
        "directory": str(project_dir),
        "manuscript": {},
        "source": {},
        "output": {},
        "tests": {},
    }

    manuscript_dir = project_dir / "manuscript"
    if manuscript_dir.exists():
        info["manuscript"]["location"] = str(manuscript_dir)
        info["manuscript"]["md_files"] = len(list(manuscript_dir.glob("*.md")))
        config_file = manuscript_dir / "config.yaml"
        info["manuscript"]["has_config"] = config_file.exists()
        if config_file.exists():
            config = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
            if not isinstance(config, dict):
                config = {}
            paper = config.get("paper", {})
            info["manuscript"]["title"] = paper.get("title", "") if isinstance(paper, dict) else ""
            authors = config.get("authors", [])
            info["manuscript"]["authors"] = authors if isinstance(authors, list) else []

    src_dir = project_dir / "src"
    if src_dir.exists():
        info["source"]["location"] = str(src_dir)
        info["source"]["py_files"] = len(list(src_dir.rglob("*.py")))

    output_dir = project_dir / "output"
    if output_dir.exists():
        info["output"]["location"] = str(output_dir)
        if (output_dir / "pdf").exists():
            info["output"]["pdf_count"] = len(list((output_dir / "pdf").glob("*.pdf")))
        if (output_dir / "figures").exists():
            info["output"]["figure_count"] = len(list((output_dir / "figures").glob("*.png")))

    tests_dir = project_dir / "tests"
    if tests_dir.exists():
        info["tests"]["location"] = str(tests_dir)
        info["tests"]["test_files"] = len(list(tests_dir.glob("test_*.py")))

    return info


def display_project_info(info: dict[str, Any], *, logger: Any) -> None:
    """Log formatted project information."""
    from infrastructure.core.logging.utils import log_header, log_substep

    log_header(f"PROJECT INFORMATION: {info['name']}", logger)
    logger.info("Project Directory: %s", info["directory"])

    if info["manuscript"]:
        log_substep("Manuscript", logger)
        logger.info("  Location: %s", info["manuscript"].get("location", "N/A"))
        logger.info("  Markdown files: %s", info["manuscript"].get("md_files", 0))
        if info["manuscript"].get("has_config"):
            logger.info("  Config: ✓ (config.yaml found)")
            if info["manuscript"].get("title"):
                logger.info("  Title: %s", info["manuscript"]["title"])
        else:
            logger.info("  Config: ✗ (config.yaml not found)")

    if info["source"]:
        log_substep("Source Code", logger)
        logger.info("  Location: %s", info["source"].get("location", "N/A"))
        logger.info("  Python files: %s", info["source"].get("py_files", 0))

    if info["output"]:
        log_substep("Output", logger)
        logger.info("  Location: %s", info["output"].get("location", "N/A"))
        if "pdf_count" in info["output"]:
            logger.info("  PDFs: %s", info["output"]["pdf_count"])
        if "figure_count" in info["output"]:
            logger.info("  Figures: %s", info["output"]["figure_count"])

    if info["tests"]:
        log_substep("Tests", logger)
        logger.info("  Location: %s", info["tests"].get("location", "N/A"))
        logger.info("  Test files: %s", info["tests"].get("test_files", 0))
