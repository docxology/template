"""Live-sourced per-exemplar coverage data for the deck's coverage bar chart.

Parses every exemplar row out of ``docs/_generated/COUNTS.md`` (the same
generated factsheet ``deck_tokens.py`` reads a single row from — it imports
`COUNTS_ROW_RE` from here rather than keeping its own copy, so the two
readers can never silently drift onto different patterns) — real measured
numbers, never fabricated or hand-typed. `scripts/16_generate_charts.py`
consumes this to render a real matplotlib bar chart; this module holds only
the data-reading logic, no plotting (thin-orchestrator split: computation
here, visualization in the script — see root `CLAUDE.md`'s "Adding a New
Analysis Script" pattern).
"""

from __future__ import annotations

import re
from pathlib import Path

#: Shared with `deck_tokens.py` (imported from here) — the one pattern both
#: COUNTS.md readers use, so they can't silently diverge (red-team finding,
#: 2026-07-09: a prior version had two independent copies of this regex).
COUNTS_ROW_RE = re.compile(
    r"^\|\s*`(?P<name>[\w.]+)`\s*\|\s*(?P<tests>\d+)\s*\|\s*(?P<coverage>[\d.]+)\s*%\s*\|", re.MULTILINE
)


def read_all_exemplar_coverage(repo_root: Path) -> list[tuple[str, int, float]]:
    """Return ``(exemplar_name, test_count, coverage_pct)`` for every row in COUNTS.md.

    Sorted by coverage percentage descending, so the rendered chart reads
    highest-first. Raises `FileNotFoundError` if COUNTS.md is absent, and
    returns an empty list only if the file exists but the table itself is
    empty (never silently fabricates a row).
    """
    counts_path = repo_root / "docs" / "_generated" / "COUNTS.md"
    text = counts_path.read_text(encoding="utf-8")
    rows = [
        (match.group("name"), int(match.group("tests")), float(match.group("coverage")))
        for match in COUNTS_ROW_RE.finditer(text)
    ]
    return sorted(rows, key=lambda row: row[2], reverse=True)


__all__ = ["COUNTS_ROW_RE", "read_all_exemplar_coverage"]
