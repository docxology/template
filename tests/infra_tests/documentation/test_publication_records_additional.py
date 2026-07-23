"""Additional tests for publication_records.py.

Targets branches below 80%: monorepo URL parsing, DOI extraction,
sidecar findings for version/DOI mismatches, book-schema exemplars,
external_status verification logic, and markdown rendering edge cases.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from infrastructure.documentation.publication_records import (
    PublicationRecord,
    _authors_from_config,
    _doi_url,
    _github_repo_url,
    _load_json_mapping,
    _markdown_link,
    _published_artifacts,
    _record_id_from_doi,
    _record_url_from_doi,
    _section_mapping,
    _sidecar_findings,
    load_publication_records,
    refresh_external_records,
)
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES


def _scaffold_project(
    root: Path,
    name: str,
    *,
    version: str = "1.0.0",
    github_repo: str = "",
    repository_url: str = "",
    doi: str = "",
    version_doi: str = "",
    use_book_schema: bool = False,
) -> None:
    project_root = root / "projects" / name
    (project_root / "src").mkdir(parents=True)
    (project_root / "tests").mkdir()
    (project_root / "manuscript").mkdir()
    (project_root / "src" / "__init__.py").write_text("", encoding="utf-8")
    (project_root / "tests" / "__init__.py").write_text("", encoding="utf-8")

    schema_key = "book" if use_book_schema else "paper"
    lines = [
        f"{schema_key}:",
        f"  title: {name}",
        f"  version: '{version}'",
        "authors:",
        "  - name: Daniel Ari Friedman",
        "publication:",
        f"  doi: '{doi}'",
        f"  version_doi: '{version_doi}'",
    ]
    if github_repo:
        lines.append(f"  github_repository: '{github_repo}'")
    if repository_url:
        lines.append(f"  repository_url: '{repository_url}'")
    lines.append("")
    (project_root / "manuscript" / "config.yaml").write_text("\n".join(lines), encoding="utf-8")
    (project_root / "STANDALONE.md").write_text(f"# {name}\n", encoding="utf-8")
    (project_root / "CITATION.cff").write_text(
        f"cff-version: 1.2.0\ntitle: {name}\ndoi: {doi}\nversion: '{version}'\n",
        encoding="utf-8",
    )
    (project_root / ".zenodo.json").write_text(json.dumps({"title": name, "version": version}), encoding="utf-8")
    (project_root / "codemeta.json").write_text(
        json.dumps({"name": name, "version": version, "identifier": doi}),
        encoding="utf-8",
    )


class TestUtilityFunctions:
    """Test pure utility functions."""

    def test_doi_url_with_doi(self) -> None:
        assert _doi_url("10.5281/zenodo.123") == "https://doi.org/10.5281/zenodo.123"

    def test_doi_url_empty(self) -> None:
        assert _doi_url("") == ""

    def test_github_repo_url_with_slug(self) -> None:
        assert _github_repo_url("docxology/template") == "https://github.com/docxology/template"

    def test_github_repo_url_empty(self) -> None:
        assert _github_repo_url("") == ""

    def test_record_id_from_zenodo_doi(self) -> None:
        assert _record_id_from_doi("10.5281/zenodo.123456") == "123456"

    def test_record_id_from_non_zenodo_doi(self) -> None:
        assert _record_id_from_doi("10.1000/abc") == ""

    def test_record_id_from_empty(self) -> None:
        assert _record_id_from_doi("") == ""

    def test_record_url_from_doi(self) -> None:
        assert _record_url_from_doi("10.5281/zenodo.123456") == "https://zenodo.org/records/123456"

    def test_record_url_from_empty(self) -> None:
        assert _record_url_from_doi("") == ""

    def test_markdown_link_with_label_and_url(self) -> None:
        assert _markdown_link("text", "https://example.com") == "[text](https://example.com)"

    def test_markdown_link_with_label_no_url(self) -> None:
        assert _markdown_link("text", "") == "text"

    def test_markdown_link_empty_label(self) -> None:
        assert _markdown_link("", "https://example.com") == "n/a"

    def test_load_json_mapping_missing_file(self, tmp_path: Path) -> None:
        assert _load_json_mapping(tmp_path / "missing.json") == {}

    def test_load_json_mapping_valid(self, tmp_path: Path) -> None:
        path = tmp_path / "test.json"
        path.write_text('{"key": "value"}', encoding="utf-8")
        assert _load_json_mapping(path) == {"key": "value"}

    def test_load_json_mapping_non_dict(self, tmp_path: Path) -> None:
        path = tmp_path / "test.json"
        path.write_text("[1, 2, 3]", encoding="utf-8")
        assert _load_json_mapping(path) == {}

    def test_section_mapping_valid(self) -> None:
        assert _section_mapping({"a": {"b": 1}}, "a") == {"b": 1}

    def test_section_mapping_missing(self) -> None:
        assert _section_mapping({"a": {}}, "b") == {}

    def test_section_mapping_non_dict(self) -> None:
        assert _section_mapping({"a": "not a dict"}, "a") == {}

    def test_authors_from_config_list_of_dicts(self) -> None:
        config = {"authors": [{"name": "Alice"}, {"name": "Bob"}]}
        assert _authors_from_config(config) == ("Alice", "Bob")

    def test_authors_from_config_empty_list(self) -> None:
        assert _authors_from_config({"authors": []}) == ()

    def test_authors_from_config_non_list(self) -> None:
        assert _authors_from_config({"authors": "Alice"}) == ()

    def test_authors_from_config_missing_key(self) -> None:
        assert _authors_from_config({}) == ()

    def test_authors_strips_whitespace(self) -> None:
        config = {"authors": [{"name": "  Alice  "}, {"name": ""}, {"name": "Bob"}]}
        assert _authors_from_config(config) == ("Alice", "Bob")

    def test_authors_skips_non_dict_entries(self) -> None:
        config = {"authors": ["not a dict", {"name": "Alice"}]}
        assert _authors_from_config(config) == ("Alice",)

    def test_published_artifacts_sorted(self) -> None:
        pub = {
            "published_artifacts": {
                "zenodo": "https://zenodo.org/123",
                "github_pages": "https://example.github.io/repo/",
            }
        }
        result = _published_artifacts(pub)
        assert len(result) == 2
        assert result[0][0] == "github_pages"  # sorted alphabetically
        assert result[1][0] == "zenodo"

    def test_published_artifacts_empty(self) -> None:
        assert _published_artifacts({}) == ()

    def test_published_artifacts_strips_empty_values(self) -> None:
        pub = {"published_artifacts": {"valid": "https://example.com", "empty": "  "}}
        result = _published_artifacts(pub)
        assert len(result) == 1
        assert result[0][0] == "valid"

    def test_published_artifacts_non_dict(self) -> None:
        assert _published_artifacts({"published_artifacts": "not a dict"}) == ()


class TestSidecarFindings:
    """Test _sidecar_findings with various mismatch scenarios."""

    def test_all_sidecars_missing(self) -> None:
        findings = _sidecar_findings(
            paper_version="1.0.0",
            concept_doi="10.5281/zenodo.123",
            citation={},
            zenodo_json={},
            codemeta={},
            standalone_exists=False,
        )
        assert "missing STANDALONE.md" in findings
        assert "missing CITATION.cff" in findings
        assert "missing .zenodo.json" in findings
        assert "missing codemeta.json" in findings

    def test_citation_version_mismatch(self) -> None:
        findings = _sidecar_findings(
            paper_version="2.0.0",
            concept_doi="10.5281/zenodo.123",
            citation={"version": "1.0.0", "doi": "10.5281/zenodo.123"},
            zenodo_json={"version": "2.0.0"},
            codemeta={"version": "2.0.0", "identifier": "10.5281/zenodo.123"},
            standalone_exists=True,
        )
        assert any("CITATION version" in f for f in findings)

    def test_citation_doi_mismatch(self) -> None:
        findings = _sidecar_findings(
            paper_version="1.0.0",
            concept_doi="10.5281/zenodo.123",
            citation={"version": "1.0.0", "doi": "10.5281/zenodo.999"},
            zenodo_json={"version": "1.0.0"},
            codemeta={"version": "1.0.0", "identifier": "10.5281/zenodo.123"},
            standalone_exists=True,
        )
        assert any("CITATION DOI" in f for f in findings)

    def test_zenodo_version_mismatch(self) -> None:
        findings = _sidecar_findings(
            paper_version="2.0.0",
            concept_doi="",
            citation={"version": "2.0.0"},
            zenodo_json={"version": "1.0.0"},
            codemeta={"version": "2.0.0"},
            standalone_exists=True,
        )
        assert any(".zenodo version" in f for f in findings)

    def test_codemeta_version_mismatch(self) -> None:
        findings = _sidecar_findings(
            paper_version="2.0.0",
            concept_doi="",
            citation={"version": "2.0.0"},
            zenodo_json={"version": "2.0.0"},
            codemeta={"version": "1.0.0"},
            standalone_exists=True,
        )
        assert any("codemeta version" in f for f in findings)

    def test_codemeta_doi_mismatch(self) -> None:
        findings = _sidecar_findings(
            paper_version="1.0.0",
            concept_doi="10.5281/zenodo.123",
            citation={"version": "1.0.0", "doi": "10.5281/zenodo.123"},
            zenodo_json={"version": "1.0.0"},
            codemeta={"version": "1.0.0", "identifier": "10.5281/zenodo.999"},
            standalone_exists=True,
        )
        assert any("codemeta DOI" in f for f in findings)

    def test_all_consistent(self) -> None:
        findings = _sidecar_findings(
            paper_version="1.0.0",
            concept_doi="10.5281/zenodo.123",
            citation={"version": "1.0.0", "doi": "10.5281/zenodo.123"},
            zenodo_json={"version": "1.0.0"},
            codemeta={"version": "1.0.0", "identifier": "10.5281/zenodo.123"},
            standalone_exists=True,
        )
        assert findings == ()

    def test_empty_paper_version_skips_version_checks(self) -> None:
        """When paper_version is empty, version-mismatch checks are skipped."""
        findings = _sidecar_findings(
            paper_version="",
            concept_doi="10.5281/zenodo.123",
            citation={"version": "9.9.9", "doi": "10.5281/zenodo.123"},
            zenodo_json={"version": "9.9.9"},
            codemeta={"version": "9.9.9", "identifier": "10.5281/zenodo.123"},
            standalone_exists=True,
        )
        assert findings == ()


class TestPublicationRecordProperties:
    """Test PublicationRecord computed properties."""

    def _make_record(self, **overrides: Any) -> PublicationRecord:
        defaults: dict[str, Any] = dict(
            project_name="test_project",
            title="Test",
            paper_version="1.0.0",
            authors=("Author",),
            concept_doi="",
            version_doi="",
            version_record="",
            github_repository="",
            repository_url="",
            published_artifacts=(),
            standalone_path=Path("/tmp/STANDALONE.md"),
            config_path=Path("/tmp/config.yaml"),
            citation_path=Path("/tmp/CITATION.cff"),
            zenodo_json_path=Path("/tmp/.zenodo.json"),
            codemeta_path=Path("/tmp/codemeta.json"),
        )
        defaults.update(overrides)
        return PublicationRecord(**defaults)

    def test_github_repo_slug_from_repository(self) -> None:
        record = self._make_record(github_repository="docxology/template")
        assert record.github_repo_slug == "docxology/template"

    def test_github_repo_slug_from_url(self) -> None:
        record = self._make_record(repository_url="https://github.com/docxology/template")
        assert record.github_repo_slug == "docxology/template"

    def test_github_repo_slug_empty(self) -> None:
        record = self._make_record()
        assert record.github_repo_slug == ""

    def test_monorepo_path_detection(self) -> None:
        record = self._make_record(repository_url="https://github.com/docxology/template/tree/main/projects/test")
        assert record.is_monorepo_publication_path is True
        assert record.monorepo_slug == "docxology/template"

    def test_non_monorepo_path(self) -> None:
        record = self._make_record(github_repository="docxology/template")
        assert record.is_monorepo_publication_path is False

    def test_github_display_label_with_repo(self) -> None:
        record = self._make_record(github_repository="docxology/template")
        assert record.github_display_label == "docxology/template"

    def test_github_display_label_monorepo(self) -> None:
        record = self._make_record(repository_url="https://github.com/docxology/template/tree/main/projects/test")
        assert "docxology/template path" in record.github_display_label

    def test_github_display_label_empty(self) -> None:
        record = self._make_record()
        assert record.github_display_label == ""

    def test_github_display_url_with_repo(self) -> None:
        record = self._make_record(github_repository="docxology/template")
        assert record.github_display_url == "https://github.com/docxology/template"

    def test_github_display_url_monorepo(self) -> None:
        url = "https://github.com/docxology/template/tree/main/projects/test"
        record = self._make_record(repository_url=url)
        assert record.github_display_url == url

    def test_declared_location_count(self) -> None:
        record = self._make_record(
            github_repository="docxology/template",
            concept_doi="10.5281/zenodo.123",
            published_artifacts=(("osf", "https://osf.io/123"),),
        )
        # github_display_url + concept_doi + 1 published_artifact
        assert record.declared_location_count == 3

    def test_external_status_unverified_when_not_checked(self) -> None:
        record = self._make_record()
        assert "unverified" in record.external_status

    def test_external_status_verified(self) -> None:
        record = self._make_record(github_repository="docxology/template")
        record.github_repo_status = "200"
        record.github_release_status = "200"
        record.zenodo_status = "200"
        assert "verified" in record.external_status

    def test_external_status_incomplete_with_findings(self) -> None:
        record = self._make_record(github_repository="docxology/template")
        record.github_repo_status = "200"
        record.github_release_status = "404"
        record.zenodo_status = "200"
        assert "incomplete" in record.external_status

    def test_external_status_unverified_with_error(self) -> None:
        record = self._make_record(github_repository="docxology/template")
        record.github_repo_status = "error: ConnectionError"
        record.github_release_status = "200"
        record.zenodo_status = "200"
        assert "unverified" in record.external_status

    def test_external_status_monorepo_verified(self) -> None:
        record = self._make_record(repository_url="https://github.com/docxology/template/tree/main/projects/test")
        refresh_external_records([record])
        assert "verified" in record.external_status or "incomplete" in record.external_status

    def test_sidecar_status_ok(self) -> None:
        record = self._make_record()
        assert record.sidecar_status == "ok"

    def test_sidecar_status_with_findings(self) -> None:
        record = self._make_record(sidecar_findings=("missing STANDALONE.md",))
        assert "missing STANDALONE.md" in record.sidecar_status


class TestRefreshExternalRecords:
    """Test refresh_external_records without network (monorepo/missing paths)."""

    def test_monorepo_path_sets_status(self, tmp_path: Path) -> None:
        record = PublicationRecord(
            project_name="test",
            title="Test",
            paper_version="1.0.0",
            authors=(),
            concept_doi="",
            version_doi="",
            version_record="",
            github_repository="",
            repository_url="https://github.com/docxology/template/tree/main/projects/test",
            published_artifacts=(),
            standalone_path=tmp_path / "STANDALONE.md",
            config_path=tmp_path / "config.yaml",
            citation_path=tmp_path / "CITATION.cff",
            zenodo_json_path=tmp_path / ".zenodo.json",
            codemeta_path=tmp_path / "codemeta.json",
        )
        refresh_external_records([record])
        assert record.github_repo_status == "monorepo path"
        assert record.github_release_status == "covered by root release"
        assert record.zenodo_status == "not published separately"

    def test_missing_repository_sets_status(self, tmp_path: Path) -> None:
        record = PublicationRecord(
            project_name="test",
            title="Test",
            paper_version="1.0.0",
            authors=(),
            concept_doi="",
            version_doi="",
            version_record="",
            github_repository="",
            repository_url="",
            published_artifacts=(),
            standalone_path=tmp_path / "STANDALONE.md",
            config_path=tmp_path / "config.yaml",
            citation_path=tmp_path / "CITATION.cff",
            zenodo_json_path=tmp_path / ".zenodo.json",
            codemeta_path=tmp_path / "codemeta.json",
        )
        refresh_external_records([record])
        assert record.github_repo_status == "missing repository"
        assert "missing github_repository" in record.external_findings

    def test_invalid_version_doi_sets_status(self, tmp_path: Path) -> None:
        record = PublicationRecord(
            project_name="test",
            title="Test",
            paper_version="1.0.0",
            authors=(),
            concept_doi="10.5281/zenodo.123",
            version_doi="not-a-doi",
            version_record="",
            github_repository="docxology/test",
            repository_url="",
            published_artifacts=(),
            standalone_path=tmp_path / "STANDALONE.md",
            config_path=tmp_path / "config.yaml",
            citation_path=tmp_path / "CITATION.cff",
            zenodo_json_path=tmp_path / ".zenodo.json",
            codemeta_path=tmp_path / "codemeta.json",
        )
        refresh_external_records([record])
        assert record.zenodo_status == "invalid version DOI"
        assert "invalid version_doi" in record.external_findings

    def test_missing_version_doi_with_concept_doi(self, tmp_path: Path) -> None:
        record = PublicationRecord(
            project_name="test",
            title="Test",
            paper_version="1.0.0",
            authors=(),
            concept_doi="10.5281/zenodo.123",
            version_doi="",
            version_record="",
            github_repository="docxology/test",
            repository_url="",
            published_artifacts=(),
            standalone_path=tmp_path / "STANDALONE.md",
            config_path=tmp_path / "config.yaml",
            citation_path=tmp_path / "CITATION.cff",
            zenodo_json_path=tmp_path / ".zenodo.json",
            codemeta_path=tmp_path / "codemeta.json",
        )
        refresh_external_records([record])
        assert record.zenodo_status == "missing version DOI"
        assert "missing version_doi" in record.external_findings


class TestLoadPublicationRecordsBookSchema:
    """Test loading records for book-schema exemplars."""

    def test_book_schema_exemplar(self, tmp_path: Path) -> None:
        name = PUBLIC_PROJECT_NAMES[0]
        _scaffold_project(
            tmp_path,
            name,
            use_book_schema=True,
            github_repo=f"docxology/{name}",
            doi="10.5281/zenodo.999999",
            version_doi="10.5281/zenodo.1000000",
        )
        records = load_publication_records(tmp_path)
        assert len(records) == 1
        assert records[0].title == name
        assert records[0].paper_version == "1.0.0"
