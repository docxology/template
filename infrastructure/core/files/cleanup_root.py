"""Root output directory cleanup.

Removes root-level directories (data/, figures/, pdf/, etc.) from output/
that are not project-specific folders.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from infrastructure.core.logging.utils import get_logger, log_success

logger = get_logger(__name__)


def clean_root_output_directory(repo_root: Path, project_names: list[str]) -> bool:
    """Clean root-level directories from output/ directory.

    Removes root-level directories (data/, figures/, pdf/, etc.) from output/
    that aren't project folders. Only project-specific folders should remain.

    Args:
        repo_root: Repository root directory
        project_names: List of discovered project names

    Returns:
        True if cleanup successful, False otherwise
    """
    output_dir = repo_root / "output"

    if not output_dir.exists():
        logger.debug("Output directory does not exist, nothing to clean")
        return True

    logger.info("Cleaning root-level directories from output/ directory...")

    try:
        # Track what we remove and keep
        removed_items: list[str] = []
        kept_items: list[str] = []

        for item in output_dir.iterdir():
            if item.is_dir():
                item_name = item.name

                # Keep project-specific folders
                if item_name in project_names:
                    kept_items.append(item_name)
                    continue

                # Keep special directories that might be needed
                special_dirs = {
                    ".gitkeep",
                    ".gitignore",
                    "multi_project_summary",  # Multi-project summary reports
                    "executive_summary",  # Executive reporting outputs
                }
                if item_name in special_dirs:
                    kept_items.append(item_name)
                    continue

                # Remove root-level directories that shouldn't exist
                # These are directories that should only exist within project folders
                root_level_dirs = {
                    "data",
                    "figures",
                    "pdf",
                    "web",
                    "slides",
                    "reports",
                    "simulations",
                    "llm",
                    "logs",
                    "tex",
                }

                if item_name in root_level_dirs:
                    logger.debug(f"  Removing root-level directory: {item_name}")
                    shutil.rmtree(item)
                    removed_items.append(item_name)
                else:
                    # Unknown directory - keep it but log it
                    logger.warning(f"  Unknown directory in output/: {item_name} (keeping)")
                    kept_items.append(item_name)

            else:
                # Keep non-directory items (files)
                kept_items.append(item.name)

        if removed_items:
            logger.info(f"Removed root-level directories: {', '.join(removed_items)}")
        if kept_items:
            logger.debug(f"Kept items: {', '.join(kept_items)}")

        log_success("Root output directory cleaned", logger)
        return True

    except OSError as e:  # noqa: BLE001 -- caller receives False; bool return avoids forcing caller to catch
        logger.error(f"Failed to clean root output directory: {e}", exc_info=True)
        return False
