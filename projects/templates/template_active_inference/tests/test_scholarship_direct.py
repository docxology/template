"""Direct tests for ``roadmap_tracks.scholarship``.

The scholarship-source matrix binds each configured citation to bib evidence,
manuscript citations, a backing artifact, and a scope-guarded claim boundary,
then re-derives every aggregate from the rows on validation. On the tracked
snapshot the matrix validates cleanly, so its failure arms only ran on rebuild.

Pure locator / scope / path helpers are exercised with constructed strings and
tmp paths. ``build`` and ``validate`` run against one module-scoped project-tree
copy: the writer-then-validate baseline is asserted clean, then defects are
injected into the written artifact and each exact issue string is asserted, with
every mutation restored byte-for-byte.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from roadmap_tracks.scholarship import (
    SCHOLARSHIP_SCHEMA,
    SCHOLARSHIP_SOURCES,
    _citation_sections,
    _has_locator,
    _locator_kind,
    _row_key,
    _scope_guarded,
    _section_id_from_path,
    build_scholarship_source_matrix,
    validate_scholarship_source_matrix,
    write_scholarship_source_matrix,
)

from direct_recompute_support import copy_project_tree


# ---------------------------------------------------------------------------
# pure helpers
# ---------------------------------------------------------------------------


def test_has_locator_and_locator_kind() -> None:
    assert _has_locator("doi = {10.1/x}") is True
    assert _has_locator("url = {http://a}") is True
    assert _has_locator("see https://b") is True
    assert _has_locator("title = {no locator}") is False
    assert _locator_kind("doi = {10.1} url = {http://a}") == "doi+url"
    assert _locator_kind("doi = {10.1}") == "doi"
    assert _locator_kind("url = {https://a}") == "url"
    assert _locator_kind("title only") == ""


def test_scope_guarded_true_and_false() -> None:
    assert _scope_guarded("finite toy state spaces only") is True
    assert _scope_guarded("not an empirical claim") is True
    assert _scope_guarded("background context") is False  # forcing-false control
    assert _scope_guarded("") is False


def test_row_key_is_identity_tuple() -> None:
    row = {"citation_key": "k", "method_role": "r", "artifact": "output/data/a.json"}
    assert _row_key(row) == ("k", "r", "output/data/a.json")


def test_section_id_from_path_imrad_and_numeric_prefix(tmp_path: Path) -> None:
    imrad_path = tmp_path / "manuscript" / "sections" / "imrad" / "methods_pymdp" / "01_body.md"
    assert _section_id_from_path(tmp_path, imrad_path) == "methods_pymdp"
    numeric_path = tmp_path / "manuscript" / "03_02_results.md"
    assert _section_id_from_path(tmp_path, numeric_path) == "results"


def test_citation_sections_uses_provided_files() -> None:
    files = [("intro", "text citing @friston2010fep here"), ("methods", "no citation")]
    assert _citation_sections(Path("/unused"), "friston2010fep", files=files) == ["intro"]
    assert _citation_sections(Path("/unused"), "absent_key", files=files) == []


# ---------------------------------------------------------------------------
# build / validate against an isolated project-tree copy
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def copied_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return copy_project_tree(tmp_path_factory.mktemp("scholarship_tree"))


@pytest.mark.timeout(300)
def test_build_matrix_connects_all_configured_sources(copied_root: Path) -> None:
    payload = build_scholarship_source_matrix(copied_root)
    assert payload["schema"] == SCHOLARSHIP_SCHEMA
    assert payload["source_count"] == len(SCHOLARSHIP_SOURCES)
    assert payload["all_expected_sources_present"] is True
    assert payload["all_sources_connected"] is True

    # forcing-false control: without the bibliography no row can be connected
    bib = copied_root / "manuscript" / "references.bib"
    original = bib.read_bytes()
    try:
        bib.unlink()
        broken = build_scholarship_source_matrix(copied_root)
        assert broken["all_sources_connected"] is False
    finally:
        bib.write_bytes(original)


@pytest.mark.timeout(300)
def test_writer_then_validate_is_clean(copied_root: Path) -> None:
    write_scholarship_source_matrix(copied_root)
    assert validate_scholarship_source_matrix(copied_root) == []


@pytest.mark.timeout(300)
def test_injected_schema_mismatch_is_reported(copied_root: Path) -> None:
    write_scholarship_source_matrix(copied_root)
    path = copied_root / "output" / "data" / "scholarship_source_matrix.json"
    original = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(original)
        payload["schema"] = "wrong.schema"
        path.write_text(json.dumps(payload), encoding="utf-8")
        assert "scholarship_source_matrix.json schema mismatch" in validate_scholarship_source_matrix(copied_root)
    finally:
        path.write_text(original, encoding="utf-8")


@pytest.mark.timeout(300)
def test_injected_missing_source_is_reported(copied_root: Path) -> None:
    write_scholarship_source_matrix(copied_root)
    path = copied_root / "output" / "data" / "scholarship_source_matrix.json"
    original = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(original)
        # drop every row for one uniquely-keyed source so the observed key set shrinks
        payload["rows"] = [row for row in payload["rows"] if row.get("citation_key") != "friston2010fep"]
        path.write_text(json.dumps(payload), encoding="utf-8")
        assert "scholarship_source_matrix.json source set is incomplete" in validate_scholarship_source_matrix(
            copied_root
        )
    finally:
        path.write_text(original, encoding="utf-8")


@pytest.mark.timeout(300)
def test_injected_disconnected_flag_is_reported(copied_root: Path) -> None:
    write_scholarship_source_matrix(copied_root)
    path = copied_root / "output" / "data" / "scholarship_source_matrix.json"
    original = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(original)
        payload["all_sources_connected"] = False  # contradicts the still-connected rows
        path.write_text(json.dumps(payload), encoding="utf-8")
        assert "scholarship_source_matrix.json has disconnected source rows" in validate_scholarship_source_matrix(
            copied_root
        )
    finally:
        path.write_text(original, encoding="utf-8")


def test_validate_missing_file(tmp_path: Path) -> None:
    assert validate_scholarship_source_matrix(tmp_path) == ["scholarship_source_matrix.json missing"]


def test_validate_malformed_json(tmp_path: Path) -> None:
    path = tmp_path / "output" / "data" / "scholarship_source_matrix.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{ not valid json", encoding="utf-8")
    assert validate_scholarship_source_matrix(tmp_path) == ["scholarship_source_matrix.json is not valid JSON"]
