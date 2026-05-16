#!/usr/bin/env python3
"""Hydrate manuscript variables for the prose project.

Reads ``output/manuscript_report.json``, computes a
:class:`ManuscriptVariables` record, writes it to
``output/data/manuscript_variables.json``.

Exit codes:
    0   variables written
    2   no manuscript report present — graceful skip
"""

from __future__ import annotations

import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
_repo_root = _project_root.parent.parent
sys.path.insert(0, str(_project_root))
sys.path.insert(0, str(_project_root / "src"))
sys.path.insert(0, str(_repo_root))

from infrastructure.core.logging.utils import get_logger

from src.config import load_project_config
from src.manuscript_variables import (
    compute_variables,
    load_manuscript_report,
    write_resolved_manuscript_tree,
    write_variables,
)

logger = get_logger(__name__)


def main() -> int:
    report_path = _project_root / "output" / "manuscript_report.json"
    if not report_path.exists():
        logger.warning("No %s; skipping.", report_path)
        return 2

    config = load_project_config(_project_root / "manuscript" / "config.yaml")
    payload = load_manuscript_report(report_path)
    variables = compute_variables(
        config_title=config.title,
        manuscript_report=payload,
    )

    out_path = _project_root / "output" / "data" / "manuscript_variables.json"
    write_variables(variables, out_path)
    resolved_dir = write_resolved_manuscript_tree(_project_root, variables)
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
