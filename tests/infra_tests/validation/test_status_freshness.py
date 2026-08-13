"""Function-level tests for infrastructure.validation.status_freshness.

The freshness parser and findings engine were moved from
``scripts/gates/status_freshness.py`` into this module (thin-script policy);
these tests pin the parsing and findings behaviour. The ``scripts/gates/``
CLI wiring is covered separately by ``tests/infra_tests/gates/test_status_freshness.py``.
"""

from __future__ import annotations

from datetime import date

from infrastructure.validation.status_freshness import freshness_findings, parse_status_rows


def _status_text(last_updated: str, row_date: str) -> str:
    return f"""# Subsystem Status

**Last updated:** {last_updated}

| ID | Subsystem | Last verified | Verified by | Verification scope | Command | Receipt | Mode | Health |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| STATUS-PIPELINE-1 | Pipeline | {row_date} | Maintainer | real run | `uv run pytest tests -q` | docs/_generated/status_evidence.json | automated | healthy |
"""


def test_parse_status_rows_extracts_subsystem_dates() -> None:
    rows = parse_status_rows(_status_text("2026-08-08", "2026-08-07"))
    assert [(row.subsystem, row.verified_on, row.line_number) for row in rows] == [("Pipeline", date(2026, 8, 7), 7)]


def test_freshness_accepts_current_ledger() -> None:
    assert (
        freshness_findings(
            _status_text("2026-08-08", "2026-05-21"),
            as_of=date(2026, 8, 8),
        )
        == []
    )


def test_freshness_rejects_stale_row_and_header() -> None:
    findings = freshness_findings(
        _status_text("2025-12-01", "2025-12-01"),
        as_of=date(2026, 8, 8),
    )
    assert len(findings) == 2
    assert "Pipeline" in findings[0]
    assert "Last updated" in findings[1]


def test_freshness_rejects_future_dates() -> None:
    findings = freshness_findings(
        _status_text("2026-08-09", "2026-08-09"),
        as_of=date(2026, 8, 8),
    )
    assert any("future" in finding for finding in findings)


def test_freshness_requires_ledger_rows() -> None:
    findings = freshness_findings("**Last updated:** 2026-08-08\n", as_of=date(2026, 8, 8))
    assert findings == ["STATUS.md has no dated subsystem verification rows"]


def test_freshness_rejects_invalid_header_date() -> None:
    findings = freshness_findings(_status_text("2026-02-30", "2026-08-07"), as_of=date(2026, 8, 8))
    assert findings == ["STATUS.md **Last updated:** date is invalid"]


def test_freshness_rejects_missing_typed_status_evidence() -> None:
    text = _status_text("2026-08-08", "2026-08-07").replace("docs/_generated/status_evidence.json", "")
    findings = freshness_findings(text, as_of=date(2026, 8, 8))
    assert any("missing receipt" in finding for finding in findings)
