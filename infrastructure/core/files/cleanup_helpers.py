"""Internal helpers for directory cleanup.

Contains selective-clean, log-archival, and content-removal helpers
used by the public clean_output_directories function.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


def clean_dir_preserving(
    dir_path: Path,
    output_dir: Path,
    preserved_relative_paths: set[Path],
    log: Any,
) -> None:
    """Remove all files inside *dir_path* except those in *preserved_relative_paths*.

    Paths in *preserved_relative_paths* are relative to *output_dir*.
    After removing files, any empty directories are cleaned up bottom-up.
    """
    preserved_count = 0
    removed_count = 0

    for file_path in list(dir_path.rglob("*")):
        if not file_path.is_file():
            continue
        rel = file_path.relative_to(output_dir)
        if rel in preserved_relative_paths:
            log.info(f"  Preserving file for incremental processing: {rel}")
            preserved_count += 1
        else:
            file_path.unlink()
            removed_count += 1

    # Clean up empty directories bottom-up
    for sub in sorted(dir_path.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if sub.is_dir() and not any(sub.iterdir()):
            sub.rmdir()

    if preserved_count:
        log.info(
            f"  Selectively cleaned {dir_path.name}/: "
            f"removed {removed_count} files, preserved {preserved_count}"
        )


def archive_output_logs(output_dir: Path) -> None:
    """Archive all .log files in output_dir/logs/ to output_dir/logs/archive/.

    Best-effort: failures are logged as warnings and do not raise.
    """
    logs_dir = output_dir / "logs"
    if not logs_dir.exists():
        return

    archive_dir = logs_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    log_files = list(logs_dir.glob("*.log"))
    if not log_files:
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archived_count = 0
    for log_file in log_files:
        try:
            archive_path = archive_dir / f"{log_file.stem}_{timestamp}{log_file.suffix}"
            shutil.copy2(log_file, archive_path)
            archived_count += 1
            logger.debug(f"  Archived log file: {log_file.name} -> {archive_path.name}")
        except (OSError, shutil.Error) as e:  # noqa: BLE001 -- archive is best-effort; continue with remaining files
            logger.warning(f"  Failed to archive log file {log_file.name}: {e}")

    if archived_count > 0:
        logger.info(f"  Archived {archived_count} log file(s) to logs/archive/")


def clean_output_dir_contents(
    output_dir: Path, preserved_relative_paths: set[Path]
) -> None:
    """Remove all contents of output_dir except .checkpoints and preserved paths.

    Paths in preserved_relative_paths are relative to output_dir.
    The .checkpoints directory is always kept to support pipeline resume.
    """
    for item in output_dir.iterdir():
        if item.is_dir():
            # Preserve .checkpoints directory to maintain pipeline resume capability
            if item.name == ".checkpoints":
                logger.debug(f"  Preserving {item.name}/ directory for checkpoint resume")
                continue

            # Check if this subdirectory contains any preserved files
            has_preserved = any(p.parts[0] == item.name for p in preserved_relative_paths)
            if has_preserved:
                # Selectively clean: remove everything except preserved files
                clean_dir_preserving(item, output_dir, preserved_relative_paths, logger)
            else:
                shutil.rmtree(item)
        else:
            # Root-level files: preserve if in the preserve set (incremental pipeline)
            if Path(item.name) in preserved_relative_paths:
                logger.debug(f"  Preserving file for incremental processing: {item.name}")
            else:
                item.unlink()
