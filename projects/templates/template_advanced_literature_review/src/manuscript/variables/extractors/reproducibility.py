"""Reproducibility-assessment aggregate scores and low-scoring-paper table.

Reads the two artifacts written by :func:`reproducibility.runner.run_reproducibility_pipeline`:

- ``reproducibility_summary.json`` -- corpus-level aggregates
  (``mean_composite_score``, ``n_papers_scored``, ``n_low_score``,
  ``low_score_threshold``).
- ``reproducibility_scores.json`` -- per-paper
  :class:`~reproducibility.scoring.ReproducibilityScore` dicts, keyed by
  ``paper_id``.

Both files are optional (the reproducibility-assessment stage is opt-in, same
as the knowledge-graph stage in :mod:`manuscript.variables.extractors.hypotheses`):
when either is not yet generated, ``ctx.load_json`` returns ``{}`` and this
extractor emits placeholder values rather than raising.
"""

from __future__ import annotations

from manuscript.variables._logging import logger
from manuscript.variables.context import ExtractContext

_DEFAULT_LOW_SCORE_THRESHOLD = 0.5
_MAX_TABLE_ROWS = 15
_TABLE_HEADER = [
    "| Paper | Composite | Content | Structural |",
    "| --- | --- | --- | --- |",
]


def extract_reproducibility(ctx: ExtractContext) -> dict[str, str]:
    """Process extract reproducibility."""
    variables: dict[str, str] = {}
    summary = ctx.load_json("reproducibility_summary.json")
    if summary:
        variables["REPRODUCIBILITY_MEAN_SCORE"] = f"{summary.get('mean_composite_score', 0.0):.3f}"
        variables["REPRODUCIBILITY_N_PAPERS_SCORED"] = str(summary.get("n_papers_scored", 0))
        variables["REPRODUCIBILITY_LOW_SCORE_COUNT"] = str(summary.get("n_low_score", 0))
        low_score_threshold = summary.get("low_score_threshold", _DEFAULT_LOW_SCORE_THRESHOLD)
    else:
        logger.info("reproducibility_summary.json not found; reproducibility variables skipped")
        variables["REPRODUCIBILITY_MEAN_SCORE"] = "pending"
        variables["REPRODUCIBILITY_N_PAPERS_SCORED"] = "0"
        variables["REPRODUCIBILITY_LOW_SCORE_COUNT"] = "0"
        low_score_threshold = _DEFAULT_LOW_SCORE_THRESHOLD

    scores = ctx.load_json("reproducibility_scores.json")
    table_rows = list(_TABLE_HEADER)
    if scores:
        low_scoring = [
            (paper_id, data)
            for paper_id, data in scores.items()
            if isinstance(data, dict) and data.get("composite_score", 1.0) < low_score_threshold
        ]
        low_scoring.sort(key=lambda item: item[1].get("composite_score", 0.0))
        for paper_id, data in low_scoring[:_MAX_TABLE_ROWS]:
            table_rows.append(
                f"| {str(paper_id)[:40]} | {data.get('composite_score', 0.0):.3f} "
                f"| {data.get('content_score', 0.0):.3f} | {data.get('structural_score', 0.0):.3f} |"
            )
    else:
        logger.info("reproducibility_scores.json not found; REPRODUCIBILITY_TABLE emits header only")
    variables["REPRODUCIBILITY_TABLE"] = "\n".join(table_rows)
    return variables
