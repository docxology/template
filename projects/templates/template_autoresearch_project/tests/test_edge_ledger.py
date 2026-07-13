"""Edge-case tests for manuscript source ledger validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.source_ledger import (
    load_source_ledger,
    source_age_summary,
    validate_source_ledger_contract,
)


def test_source_ledger_rejects_duplicate_citekey(tmp_path: Path) -> None:
    ledger = tmp_path / "source_ledger.yaml"

    ledger.write_text(
        "schema: template-autoresearch-source-ledger-v1\n"
        "sources:\n"
        "  - citekey: dup_key\n"
        "    canonical_url: https://example.org/1\n"
        "    source_tier: scholarly_preprint\n"
        "    checked_as_of: 2026-05-26\n"
        "  - citekey: dup_key\n"
        "    canonical_url: https://example.org/2\n"
        "    source_tier: scholarly_preprint\n"
        "    checked_as_of: 2026-05-26\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate source ledger citekey"):
        load_source_ledger(ledger)


def test_source_ledger_rejects_wrong_schema(tmp_path: Path) -> None:
    ledger = tmp_path / "source_ledger.yaml"

    ledger.write_text(
        "schema: wrong-schema-v0\nsources: []\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="schema must be"):
        load_source_ledger(ledger)


def test_source_ledger_rejects_non_mapping_row(tmp_path: Path) -> None:
    ledger = tmp_path / "source_ledger.yaml"

    ledger.write_text(
        "schema: template-autoresearch-source-ledger-v1\nsources:\n  - just_a_string\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="must be a mapping"):
        load_source_ledger(ledger)


def test_source_ledger_rejects_non_list_sources(tmp_path: Path) -> None:
    ledger = tmp_path / "source_ledger.yaml"

    ledger.write_text(
        "schema: template-autoresearch-source-ledger-v1\nsources: not_a_list\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="must be a list"):
        load_source_ledger(ledger)


def test_source_ledger_rejects_missing_citekey(tmp_path: Path) -> None:
    ledger = tmp_path / "source_ledger.yaml"

    ledger.write_text(
        "schema: template-autoresearch-source-ledger-v1\n"
        "sources:\n"
        "  - canonical_url: https://example.org/no-key\n"
        "    source_tier: scholarly_preprint\n"
        "    checked_as_of: 2026-05-26\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing citekey"):
        load_source_ledger(ledger)


def test_source_ledger_rejects_bad_date(tmp_path: Path) -> None:
    ledger = tmp_path / "source_ledger.yaml"

    ledger.write_text(
        "schema: template-autoresearch-source-ledger-v1\n"
        "sources:\n"
        "  - citekey: bad_date\n"
        "    canonical_url: https://example.org/\n"
        "    source_tier: scholarly_preprint\n"
        "    checked_as_of: not-a-date\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="checked_as_of must be an ISO date"):
        load_source_ledger(ledger)


def test_source_age_summary_returns_correct_buckets(tmp_path: Path) -> None:
    """source_age_summary correctly buckets entries across age thresholds."""

    from datetime import date

    from src.source_ledger import SourceLedgerEntry

    today = date(2026, 6, 1)

    entries = (
        SourceLedgerEntry(
            citekey="recent",
            canonical_url="https://a.org/",
            source_tier="scholarly_preprint",
            checked_as_of=date(2026, 5, 1),  # ~31 days old → 0-180d
        ),
        SourceLedgerEntry(
            citekey="mid",
            canonical_url="https://b.org/",
            source_tier="peer_reviewed_article",
            checked_as_of=date(2025, 12, 1),  # ~182 days old → 181-365d
        ),
        SourceLedgerEntry(
            citekey="old",
            canonical_url="https://c.org/",
            source_tier="conference_proceeding",
            checked_as_of=date(2024, 6, 1),  # ~366 days old → 366d+
        ),
    )

    summary = source_age_summary(entries, today=today)

    assert summary.get("0-180d", 0) >= 1

    assert summary.get("181-365d", 0) >= 1

    assert summary.get("366d+", 0) >= 1


def test_validate_source_ledger_contract_propagates_load_error(tmp_path: Path) -> None:
    """If the ledger itself fails to load, contract validation returns that error."""

    manuscript = tmp_path / "manuscript"

    manuscript.mkdir()

    (manuscript / "source_ledger.yaml").write_text(
        "schema: template-autoresearch-source-ledger-v1\nsources:\n  - just_a_string\n",
        encoding="utf-8",
    )

    issues = validate_source_ledger_contract(tmp_path)

    assert issues  # error from load propagates as an issue string

    assert any("mapping" in issue for issue in issues)
