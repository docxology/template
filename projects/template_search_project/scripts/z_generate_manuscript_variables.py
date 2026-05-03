#!/usr/bin/env python3
"""Hydrate manuscript variables for the search project.

Mirrors ``projects/template_code_project/scripts/z_generate_manuscript_variables.py``:
reads the run's diagnostic outputs, computes substitution variables, writes them
to JSON, and writes resolved markdown plus auxiliary files under
``output/manuscript/`` so the PDF-rendering stage renders substituted prose (see
``infrastructure.rendering.pipeline._resolve_manuscript_dir``).

Substitution markers are ``{{UPPER_SNAKE}}`` so unresolved tokens stand out
in PDFs if this script was not run.

Exit codes:
    0   variables written
    2   no search results available — graceful skip
"""

from __future__ import annotations

import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root))
sys.path.insert(0, str(_project_root / "src"))

from infrastructure.core.logging.utils import get_logger

from src.config import load_project_config
from src.manuscript_variables import (
    compute_variables,
    load_aggregate_payload,
    load_search_result_payload,
    write_resolved_manuscript_tree,
    write_variables,
)

logger = get_logger(__name__)


def main() -> int:
    results_path = _project_root / "output" / "search" / "results.json"
    if not results_path.exists():
        logger.warning("No search results at %s; skipping.", results_path)
        return 2

    config_path = _project_root / "manuscript" / "config.yaml"
    config = load_project_config(config_path)
    payload = load_search_result_payload(results_path)

    deep_dir = (_project_root / config.deep_search.output_dir).resolve()
    aggregate_path = deep_dir / "aggregate.json"
    aggregate = load_aggregate_payload(aggregate_path)

    variables = compute_variables(
        config_query=config.search.query,
        config_max_results=config.search.max_results,
        config_sources=list(config.search.sources),
        search_result_payload=payload,
        deep_search=config.deep_search,
        aggregate_payload=aggregate,
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
