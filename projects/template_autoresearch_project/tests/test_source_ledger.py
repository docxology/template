"""Tests for offline source-ledger validation."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from src.source_ledger import load_source_ledger, source_ledger_citekeys, source_tier_counts


def test_source_ledger_loads_current_survey_sources(project_root: Path) -> None:
    entries = load_source_ledger(project_root / "manuscript" / "source_ledger.yaml")

    assert len(entries) == 23
    assert "baulin_discovery_engine_2025" in {entry.citekey for entry in entries}
    assert source_tier_counts(entries)["scholarly_preprint"] >= 1
    assert all(entry.canonical_url.startswith("https://") for entry in entries)


def test_source_ledger_citekeys_are_stable(project_root: Path) -> None:
    citekeys = source_ledger_citekeys(project_root / "manuscript" / "source_ledger.yaml")

    assert citekeys[0] == "baulin_discovery_engine_2025"
    assert len(citekeys) == len(set(citekeys))


def test_source_ledger_rejects_future_dates(tmp_path: Path) -> None:
    ledger = tmp_path / "source_ledger.yaml"
    ledger.write_text(
        """
schema: template-autoresearch-source-ledger-v1
sources:
  - citekey: future_source
    canonical_url: https://example.org/source
    source_tier: scholarly_preprint
    checked_as_of: 2026-05-27
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="future-dated"):
        load_source_ledger(ledger, today=date(2026, 5, 26))


def test_source_ledger_rejects_non_https_urls(tmp_path: Path) -> None:
    ledger = tmp_path / "source_ledger.yaml"
    ledger.write_text(
        """
schema: template-autoresearch-source-ledger-v1
sources:
  - citekey: insecure_source
    canonical_url: http://example.org/source
    source_tier: scholarly_preprint
    checked_as_of: 2026-05-26
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="HTTPS"):
        load_source_ledger(ledger)
