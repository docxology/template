"""Tests for infrastructure/publishing/release_workflow_zenodo.py.

No mocks: exercises the deterministic dry-run and config-writing paths plus the
fail-closed reserve-first guards with real on-disk config files. The networked
Zenodo publish path is covered by the Zenodo client tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.core.exceptions import PublishingError
from infrastructure.publishing.models import PublicationMetadata
from infrastructure.publishing.release_workflow_zenodo import (
    _reserve_doi_dry_run,
    reserve_zenodo_doi_pair,
    write_reserved_dois_to_config,
)


def _metadata() -> PublicationMetadata:
    return PublicationMetadata(
        title="Deterministic Exemplar",
        authors=["Ada Lovelace"],
        abstract="A short abstract.",
        keywords=["reproducibility"],
    )


class TestReserveDryRun:
    def test_dry_run_without_existing_uses_placeholder_concept(self) -> None:
        concept, version = _reserve_doi_dry_run(None)
        assert concept == "10.5281/zenodo.1000000"
        assert version == "10.5281/zenodo.1000001"

    def test_dry_run_preserves_existing_concept(self) -> None:
        concept, version = _reserve_doi_dry_run("10.5281/zenodo.42")
        assert concept == "10.5281/zenodo.42"
        assert version == "10.5281/zenodo.1000001"

    def test_reserve_pair_dry_run_returns_pair_and_no_deposition(self) -> None:
        concept, version, deposition = reserve_zenodo_doi_pair(
            dry_run=True,
            zenodo_token=None,
            sandbox=True,
            zenodo_base_url=None,
            new_version=False,
            metadata=_metadata(),
            existing_doi=None,
        )
        assert concept == "10.5281/zenodo.1000000"
        assert version == "10.5281/zenodo.1000001"
        assert deposition is None


class TestReserveGuards:
    def test_requires_token_when_not_dry_run(self) -> None:
        with pytest.raises(PublishingError, match="token is required"):
            reserve_zenodo_doi_pair(
                dry_run=False,
                zenodo_token=None,
                sandbox=True,
                zenodo_base_url=None,
                new_version=False,
                metadata=_metadata(),
                existing_doi=None,
            )

    def test_existing_doi_without_new_version_is_rejected(self) -> None:
        with pytest.raises(PublishingError, match="first releases"):
            reserve_zenodo_doi_pair(
                dry_run=False,
                zenodo_token="tok",
                sandbox=True,
                zenodo_base_url=None,
                new_version=False,
                metadata=_metadata(),
                existing_doi="10.5281/zenodo.7",
            )

    def test_new_version_with_existing_doi_not_implemented(self) -> None:
        with pytest.raises(PublishingError, match="not implemented"):
            reserve_zenodo_doi_pair(
                dry_run=False,
                zenodo_token="tok",
                sandbox=True,
                zenodo_base_url=None,
                new_version=True,
                metadata=_metadata(),
                existing_doi="10.5281/zenodo.7",
            )


class TestWriteReservedDois:
    @staticmethod
    def _config(tmp_path: Path) -> Path:
        p = tmp_path / "config.yaml"
        p.write_text(
            "paper:\n"
            '  title: "Deterministic Exemplar"\n'
            '  version: "1.0"\n'
            "authors:\n"
            '  - name: "Ada Lovelace"\n'
            "publication:\n"
            '  doi: ""\n'
            '  version_doi: ""\n'
            '  year: "2026"\n',
            encoding="utf-8",
        )
        return p

    def test_dry_run_does_not_mutate_file(self, tmp_path: Path) -> None:
        cfg = self._config(tmp_path)
        before = cfg.read_text(encoding="utf-8")
        write_reserved_dois_to_config(
            cfg,
            concept_doi="10.5281/zenodo.5",
            version_doi="10.5281/zenodo.6",
            dry_run=True,
        )
        assert cfg.read_text(encoding="utf-8") == before

    def test_commit_writes_both_dois(self, tmp_path: Path) -> None:
        cfg = self._config(tmp_path)
        changed = write_reserved_dois_to_config(
            cfg,
            concept_doi="10.5281/zenodo.5",
            version_doi="10.5281/zenodo.6",
            dry_run=False,
        )
        assert changed is True
        text = cfg.read_text(encoding="utf-8")
        assert "10.5281/zenodo.5" in text
        assert "10.5281/zenodo.6" in text
