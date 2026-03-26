"""Bibliography processing and PDF success logging utilities."""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


def process_bibliography(tex_file: Path, output_dir: Path, bib_file: Path) -> bool:
    """Process bibliography using bibtex.

    Copies the .bib file into the compilation directory (BibTeX's paranoid mode
    restricts cross-directory access), then runs bibtex against the .aux file.
    """
    if not bib_file.exists():
        logger.warning(
            f"Bibliography file not found: {bib_file} (bibliography processing will be skipped)"
        )
        return False

    bibtex_cmd = "bibtex"
    aux_file = output_dir / f"{tex_file.stem}.aux"

    if not aux_file.exists():
        logger.warning(f"Auxiliary file not found: {aux_file}")
        return False

    try:
        local_bib = output_dir / bib_file.name
        shutil.copy2(str(bib_file), str(local_bib))
        logger.debug(f"Copied bibliography file to: {local_bib}")

        cmd = [bibtex_cmd, aux_file.name]
        logger.info(f"Processing bibliography with {bibtex_cmd}...")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(output_dir),
            timeout=(8 if os.environ.get("PYTEST_CURRENT_TEST") else 600),
        )

        if result.returncode != 0 and result.stderr.strip():
            logger.warning(f"Bibliography processing warning: {result.stderr[:200]}")

        logger.debug(f"✓ Bibliography processed: {bibtex_cmd} {aux_file.stem}")
        return True

    except Exception as e:  # noqa: BLE001
        logger.warning(f"Bibliography processing failed: {e}", exc_info=True)
        return False


def log_pdf_success(output_file: Path, source_files: list[Path], start_time: float) -> None:
    """Log successful PDF generation with size and duration metrics."""
    output_size_kb = output_file.stat().st_size / 1024
    logger.info(f"\nSuccessfully combined {len(source_files)} sections")
    logger.info(f"   Output: {output_file.name}")
    logger.info(f"   Size: {output_size_kb:.1f} KB ({output_size_kb / 1024:.2f} MB)")
    logger.info(f"   Location: {output_file.parent}")
    end_time = time.time()
    total_duration = end_time - start_time
    logger.info(f"   Duration: {total_duration:.2f} seconds")
