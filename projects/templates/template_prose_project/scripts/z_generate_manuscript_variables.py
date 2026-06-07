#!/usr/bin/env python3
"""Hydrate manuscript variables for the prose project.

Reads ``<project_root>/output/manuscript_report.json``, computes a
:class:`ManuscriptVariables` record, writes it to
``<project_root>/output/data/manuscript_variables.json``, and writes
token-substituted copies of every ``manuscript/*.md`` under
``<project_root>/output/manuscript/``.

Exit codes:
    0   variables written
    2   no manuscript report present — graceful skip
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_DEFAULT_PROJECT_ROOT = _SCRIPT_DIR.parent
# Project lives at projects/templates/<name>/; repo root is three levels up.
_REPO_ROOT = _DEFAULT_PROJECT_ROOT.parents[2]

sys.path.insert(0, str(_DEFAULT_PROJECT_ROOT))
sys.path.insert(0, str(_DEFAULT_PROJECT_ROOT / "src"))
sys.path.insert(0, str(_REPO_ROOT))

from infrastructure.core.logging.utils import get_logger  # noqa: E402

from src.config import load_project_config  # noqa: E402
from src.manuscript_variables import (  # noqa: E402
    compute_variables,
    load_report_payload,
    write_resolved_manuscript_tree,
    write_variables,
)

logger = get_logger(__name__)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=_DEFAULT_PROJECT_ROOT,
        help="Project root directory (default: the bundled template_prose_project).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Override path to config.yaml (default: <project_root>/manuscript/config.yaml).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    project_root: Path = args.project_root.resolve()
    config_path: Path = (args.config or (project_root / "manuscript" / "config.yaml")).resolve()

    report_path = project_root / "output" / "manuscript_report.json"
    if not report_path.exists():
        logger.warning("No %s; skipping.", report_path)
        return 2

    config = load_project_config(config_path)
    payload = load_report_payload(report_path)
    variables = compute_variables(
        config_title=config.title,
        manuscript_report=payload,
    )

    out_path = project_root / "output" / "data" / "manuscript_variables.json"
    write_variables(variables, out_path)
    resolved_dir = write_resolved_manuscript_tree(project_root, variables)
    logger.info(
        "Wrote %d manuscript variables → %s; resolved manuscript → %s",
        len(variables.as_dict()),
        out_path,
        resolved_dir,
    )
    print(str(out_path))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
