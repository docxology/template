#!/usr/bin/env python3
"""API documentation generation — infrastructure glossary over ``src/``."""

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

logger = get_logger(__name__)


def run_api_doc_generation(project_root: Path) -> Path | None:
    """Generate a glossary-style API index for ``src/methods_dsl``."""
    output_dir = project_root / "output" / "docs"
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        src_dir = project_root / "src"
        entries = build_api_index(str(src_dir))
        glossary_path = output_dir / "api_glossary.md"
        glossary_path.write_text(generate_markdown_table(entries), encoding="utf-8")
        return glossary_path
    except (OSError, ImportError, ValueError, SyntaxError) as exc:
        logger.warning("API index generation failed: %s", exc)
        return None


def main() -> int:
    """CLI entry point."""
    logger.info("Starting API documentation generation...")
    glossary_path = run_api_doc_generation(PROJECT_ROOT)
    if glossary_path is None:
        logger.error("API documentation generation failed")
        return 1
    log_success("API documentation generation completed", logger=logger)
    print(str(glossary_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
