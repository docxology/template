#!/usr/bin/env python3
"""Manuscript variable injection script (thin wrapper)."""

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

from config import PROJECT_NAME
from infrastructure.core.logging.utils import get_logger, log_operation
from manuscript.variables import compute_variables, inject_variables

logger = get_logger(__name__)


def resolve_project_dir(project_name: str) -> Path:
    """Locate a project directory, accepting a bare or typed-subfolder name.

    Walks up from this script's own project to the repository root (the directory
    that holds ``infrastructure/``) so that nested exemplars under
    ``projects/templates/<name>`` resolve correctly, then accepts a qualified
    ``<subfolder>/<name>`` or bare ``<name>``. Falls back to this script's own
    project when the name matches it.
    """
    repo_root = PROJECT_ROOT
    for parent in (PROJECT_ROOT, *PROJECT_ROOT.parents):
        if (parent / "infrastructure").is_dir():
            repo_root = parent
            break
    for base in ("projects", "projects_archive", "projects_in_progress"):
        candidate = repo_root / base / project_name
        if candidate.exists():
            return candidate
    if PROJECT_ROOT.name == Path(project_name).name:
        return PROJECT_ROOT
    return repo_root / "projects" / project_name


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Inject pipeline variables into manuscript templates")
    parser.add_argument("--project", default=PROJECT_NAME)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    project_dir = resolve_project_dir(args.project)
    manuscript_dir = project_dir / "manuscript"
    output_dir = project_dir / "output"
    rendered_dir = output_dir / "manuscript"

    if not manuscript_dir.exists():
        logger.error("Manuscript directory not found: %s", manuscript_dir)
        return 1
    if not output_dir.exists():
        logger.error("Output directory not found: %s", output_dir)
        return 1

    with log_operation("Manuscript variable injection"):
        variables = compute_variables(output_dir)
        rendered_dir.mkdir(parents=True, exist_ok=True)
        files_changed = 0
        total_injected = 0

        # Authoring docs are not manuscript content: they describe the token
        # system (and so legitimately contain example placeholders). They must
        # not be injected or rendered into the paper.
        skip_docs = {"README.md", "AGENTS.md", "SYNTAX.md"}
        for md_file in sorted(manuscript_dir.glob("*.md")):
            if md_file.name in skip_docs:
                continue
            content = md_file.read_text(encoding="utf-8")
            lenient = md_file.name == "02e_methods_viz_injection.md"
            rendered = inject_variables(content, variables, filename=md_file.name, lenient=lenient)
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
            "Variable injection complete: %d variables injected across %d files",
            total_injected,
            files_changed,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
