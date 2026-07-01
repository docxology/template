#!/usr/bin/env python3
"""Compose the deep-search outputs into a supplemental literature-review section.

Reads:
  output/deep_search/aggregate.json
  output/deep_search/aggregate_report.md
  output/deep_search/<keyword_slug>/reading_report.md
  output/deep_search/<keyword_slug>/per_paper/*.md
  manuscript/references_deep.bib

Writes:
  manuscript/S01_literature_review.md
    A supplemental section (filename prefix ``S01_`` follows the Pandoc
    supplemental convention used across this template). Pandoc orders
    main sections (``01_*`` … ``99_references.md``) ahead of supplemental
    sections (``S01_*`` … ``S99_*``), so the auto-composed literature
    review renders at the back of the PDF as an appendix.

    The section is fully traceable and citable:
      - lists each keyword's coverage and per-source breakdown
      - tabulates every paper with citation key + DOI/URL + year
      - inlines the LLM-generated CONTRIBUTION + SIGNIFICANCE paragraphs
        per paper (if present)
      - cross-references manuscript/references_deep.bib so the combined-PDF
        pipeline (Pandoc ``--natbib`` + BibTeX) resolves every [@key]

  output/manuscript/S01_literature_review.md  (only when that directory
    already exists — defensive parity write so a stale resolver copy
    never references citation keys absent from the regenerated
    ``references_deep.bib``).

  output/deep_search/composition_summary.json
    Machine-readable summary of what was composed.

Execution order: this script must run **before**
``z_generate_manuscript_variables.py`` (which copies
``manuscript/`` → ``output/manuscript/``). The filename prefix ``s_``
keeps it sorted after ``run_*`` and before ``y_*``/``z_*`` in
``scripts/02_run_analysis.py`` lexicographic discovery.

All composition logic (parsing, validation, markdown assembly, artifact
writing) lives in ``src.composition.compose_literature_review`` — this
script only wires up argparse and the config load per the thin-orchestrator
pattern.

Exit codes:
  0   composed successfully (or skipped cleanly when deep_search disabled)
  1   composition failed
  2   no deep-search outputs to compose (graceful skip)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
# Project lives at projects/templates/<name>/; repo root is three levels up.
_repo_root = _project_root.parents[2]
sys.path.insert(0, str(_project_root))
sys.path.insert(0, str(_project_root / "src"))
sys.path.insert(0, str(_repo_root))

from src.composition import compose_literature_review
from src.config import load_project_config
from src.dotenv import load_dotenv

load_dotenv(_project_root / ".env")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--config",
        default=str(_project_root / "manuscript" / "config.yaml"),
    )
    parser.add_argument(
        "--project-root",
        default=str(_project_root),
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output markdown path (defaults to manuscript/S01_literature_review.md).",
    )
    args = parser.parse_args(argv)

    project_root = Path(args.project_root).resolve()
    config = load_project_config(args.config)
    return compose_literature_review(project_root, config, args.output)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
