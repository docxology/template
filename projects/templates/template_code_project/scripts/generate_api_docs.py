#!/usr/bin/env python3
"""API documentation generation — infrastructure glossary + src static reference."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
for _path in (PROJECT_ROOT, PROJECT_ROOT / "src", PROJECT_ROOT.parents[2]):
    path_text = str(_path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

from infrastructure.core.logging.utils import get_logger, log_success  # noqa: E402
from infrastructure.documentation.glossary_gen import (  # noqa: E402
    build_api_index,
    generate_markdown_table,
)

from src.documentation import build_api_reference_markdown  # noqa: E402

logger = get_logger(__name__)


def run_api_doc_generation(project_root: Path) -> dict[str, str | None] | None:
    """Generate glossary-style API index and static API reference markdown."""
    output_dir = project_root / "output" / "docs"
    output_dir.mkdir(parents=True, exist_ok=True)

    glossary_path = None
    try:
        src_dir = project_root / "src"
        entries = build_api_index(str(src_dir))
        glossary_path = output_dir / "api_glossary.md"
        glossary_path.write_text(generate_markdown_table(entries), encoding="utf-8")
    except (OSError, ImportError, ValueError, SyntaxError) as exc:
        logger.warning("API index generation failed: %s", exc)

    api_ref_path = output_dir / "api_reference.md"
    api_ref_path.write_text(build_api_reference_markdown(), encoding="utf-8")

    return {
        "api_reference": str(api_ref_path),
        "glossary": str(glossary_path) if glossary_path and glossary_path.exists() else None,
    }


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
