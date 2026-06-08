#!/usr/bin/env python3
"""API documentation generation — thin wrapper over src.documentation."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
for _path in (PROJECT_ROOT, PROJECT_ROOT / "src", PROJECT_ROOT.parents[2]):
    path_text = str(_path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

from infrastructure.core.logging.utils import get_logger, log_success  # noqa: E402

from src.documentation import run_api_doc_generation  # noqa: E402

logger = get_logger(__name__)


def main() -> int:
    logger.info("Starting API documentation generation...")
    docs_files = run_api_doc_generation(PROJECT_ROOT)
    if not docs_files:
        logger.error("API documentation generation failed")
        return 1
    log_success("API documentation generation completed", logger=logger)
    for doc_type, file_path in docs_files.items():
        if file_path:
            logger.info("  - %s: %s", doc_type, file_path)
            print(file_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
