"""Tests for publication release ledger."""

from __future__ import annotations

import json
from pathlib import Path

from infrastructure.publishing.publication_ledger import (
    LEDGER_SCHEMA,
    append_release_entry,
    ledger_path_for_project,
    load_publication_ledger,
    write_publication_ledger,
)


def _sample_receipt(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "project": "demo_project",
        "tag": "v1.0.0",
        "github_repo": "owner/demo",
        "github_release_url": "https://github.com/owner/demo/releases/tag/v1.0.0",
        "doi": "10.5281/zenodo.12345",
        "pdf_sha256": "abc123",
        "timestamp": "2026-05-27T12:00:00+00:00",
        "sandbox": True,
        "dry_run": False,
    }
    base.update(overrides)
    return base


class TestPublicationLedger:
    def test_ledger_path_for_project(self, tmp_path: Path) -> None:
        project_root = tmp_path / "projects" / "demo"
        project_root.mkdir(parents=True)
        assert ledger_path_for_project(project_root) == project_root / "output" / "data" / "publication_ledger.json"

    def test_append_release_entry_creates_ledger(self, tmp_path: Path) -> None:
        ledger_path = tmp_path / "publication_ledger.json"
        ledger = append_release_entry(ledger_path, _sample_receipt())
        assert ledger["schema"] == LEDGER_SCHEMA
        assert len(ledger["releases"]) == 1
        assert ledger["releases"][0]["tag"] == "v1.0.0"
        assert ledger_path.is_file()

    def test_append_release_entry_idempotent(self, tmp_path: Path) -> None:
        ledger_path = tmp_path / "publication_ledger.json"
        append_release_entry(ledger_path, _sample_receipt())
        ledger = append_release_entry(ledger_path, _sample_receipt())
        assert len(ledger["releases"]) == 1

    def test_append_release_entry_allows_new_tag(self, tmp_path: Path) -> None:
        ledger_path = tmp_path / "publication_ledger.json"
        append_release_entry(ledger_path, _sample_receipt(tag="v1.0.0"))
        ledger = append_release_entry(ledger_path, _sample_receipt(tag="v1.1.0", pdf_sha256="def456"))
        assert len(ledger["releases"]) == 2

    def test_load_publication_ledger_from_file(self, tmp_path: Path) -> None:
        project_root = tmp_path / "projects" / "demo"
        ledger_path = ledger_path_for_project(project_root)
        write_publication_ledger(ledger_path, {"schema": LEDGER_SCHEMA, "releases": [_sample_receipt()]})
        loaded = load_publication_ledger(project_root, repo_root=tmp_path, project_name="demo")
        assert len(loaded["releases"]) == 1

    def test_load_publication_ledger_backfills_from_receipt(self, tmp_path: Path) -> None:
        project_root = tmp_path / "projects" / "demo"
        bundle_dir = tmp_path / "output" / "demo" / "release_bundle"
        bundle_dir.mkdir(parents=True)
        receipt = _sample_receipt()
        (bundle_dir / "RELEASE_RECEIPT.json").write_text(json.dumps(receipt), encoding="utf-8")
        loaded = load_publication_ledger(project_root, repo_root=tmp_path, project_name="demo")
        assert len(loaded["releases"]) == 1
        assert loaded["releases"][0]["doi"] == "10.5281/zenodo.12345"
