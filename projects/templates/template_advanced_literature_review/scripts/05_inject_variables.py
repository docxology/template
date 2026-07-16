#!/usr/bin/env python3
"""Inject computed pipeline variables into the advanced manuscript."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from _bootstrap import bootstrap_project

PROJECT_ROOT = bootstrap_project(include_infrastructure=True)

from infrastructure.core.logging.utils import get_logger, log_operation

from config import PROJECT_NAME
from manuscript.variables import compute_variables, inject_variables

logger = get_logger(__name__)


def main() -> int:
    """Compute variables and render manuscript Markdown files."""
    parser = argparse.ArgumentParser(description="Inject pipeline variables into manuscript templates")
    parser.add_argument("--project", default=PROJECT_NAME)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if Path(args.project).name != PROJECT_NAME:
        parser.error(
            f"this project-local entrypoint only renders {PROJECT_NAME!r}; use the target project's own stage-05 script"
        )

    manuscript_dir = PROJECT_ROOT / "manuscript"
    output_dir = PROJECT_ROOT / "output"
    rendered_dir = output_dir / "manuscript"
    if not manuscript_dir.is_dir():
        logger.error("Manuscript directory not found: %s", manuscript_dir)
        return 1
    if not output_dir.is_dir():
        logger.error("Output directory not found: %s", output_dir)
        return 1

    with log_operation("Manuscript variable injection"):
        variables = compute_variables(output_dir)
        rendered_dir.mkdir(parents=True, exist_ok=True)
        files_changed = 0
        total_injected = 0
        skip_docs = {"README.md", "AGENTS.md", "SYNTAX.md"}

        for md_file in sorted(manuscript_dir.glob("*.md")):
            if md_file.name in skip_docs:
                continue
            content = md_file.read_text(encoding="utf-8")
            rendered = inject_variables(
                content,
                variables,
                filename=md_file.name,
                lenient=md_file.name == "02e_methods_viz_injection.md",
            )
            if rendered != content:
                files_changed += 1
                total_injected += len(re.findall(r"\{\{(\w+)\}\}", content)) - len(
                    re.findall(r"\{\{(\w+)\}\}", rendered)
                )
            if not args.dry_run:
                (rendered_dir / md_file.name).write_text(rendered, encoding="utf-8")

        if not args.dry_run:
            for other_file in manuscript_dir.iterdir():
                if other_file.suffix != ".md" and other_file.is_file():
                    shutil.copy2(other_file, rendered_dir / other_file.name)

        logger.info(
            "Variable injection complete: %d variables across %d files",
            total_injected,
            files_changed,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
