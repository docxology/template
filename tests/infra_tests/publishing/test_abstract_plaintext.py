"""Tests for plaintext abstract rendering and deposit cross-links."""

from __future__ import annotations

import json
from pathlib import Path

from infrastructure.publishing.abstract_plaintext import (
    DepositCrossLinks,
    build_deposit_description,
    build_github_release_body,
    format_cross_links_footer,
    render_abstract_plaintext,
    zenodo_record_url_from_doi,
)
from infrastructure.prose.markdown import links_to_label_paren_url, normalise_for_deposit


_ABSTRACT_EXCERPT = """\
# Abstract {#sec:abstract}

This paper documents `template_prose_project`, the prose-focused exemplar of the [Research Project Template](https://github.com/docxology/template). It pairs the template's two-layer architecture with the [prose analysis infrastructure](https://github.com/docxology/template/tree/main/infrastructure/prose) (readability metrics, structural outline, editorial quality flags).

**Run snapshot.** The current configuration analyses {{FILES_ANALYSED}} file(s) totalling {{TOTAL_WORDS}} words. Average Flesch-Kincaid grade level is {{AVG_GRADE_LEVEL}}; the manuscript references {{CITATION_COUNT}} unique citation key(s) [@smith2020].

**Keywords:** prose analysis, readability, editorial review
"""


class TestNormaliseForDeposit:
    def test_strips_pandoc_attributes_and_code(self) -> None:
        out = normalise_for_deposit(_ABSTRACT_EXCERPT)
        assert "{#sec:abstract}" not in out
        assert "`template_prose_project`" not in out
        assert "template_prose_project" in out

    def test_links_become_label_paren_url(self) -> None:
        out = normalise_for_deposit(_ABSTRACT_EXCERPT)
        assert "[Research Project Template]" not in out
        assert "Research Project Template (https://github.com/docxology/template)" in out

    def test_strips_emphasis_and_citations(self) -> None:
        out = normalise_for_deposit(_ABSTRACT_EXCERPT)
        assert "**" not in out
        assert "[@smith2020]" not in out

    def test_links_to_label_paren_url_helper(self) -> None:
        text = "See [Pandoc](https://pandoc.org) for details."
        assert links_to_label_paren_url(text) == "See Pandoc (https://pandoc.org) for details."


class TestRenderAbstractPlaintext:
    def test_injects_variables_from_json(self, tmp_path: Path) -> None:
        abstract_path = tmp_path / "00_abstract.md"
        abstract_path.write_text(
            "Analyses {{FILES_ANALYSED}} files with {{TOTAL_WORDS}} words.\n",
            encoding="utf-8",
        )
        variables_path = tmp_path / "manuscript_variables.json"
        variables_path.write_text(
            json.dumps({"FILES_ANALYSED": "3", "TOTAL_WORDS": "1200"}),
            encoding="utf-8",
        )
        out = render_abstract_plaintext(abstract_path, variables_path=variables_path)
        assert "3 files" in out
        assert "1200 words" in out
        assert "{{" not in out

    def test_override_skips_markdown_source(self, tmp_path: Path) -> None:
        abstract_path = tmp_path / "00_abstract.md"
        abstract_path.write_text("# Raw\n\nShould not appear.\n", encoding="utf-8")
        out = render_abstract_plaintext(
            abstract_path,
            override_text="Plain override body.",
        )
        assert out == "Plain override body."


class TestDepositCrossLinks:
    def test_footer_contains_doi_github_and_hash(self) -> None:
        cross_links = DepositCrossLinks(
            project="template_prose_project",
            tag="v0.3.0-release-smoke",
            github_repo="docxology/template-release-smoke",
            pdf_sha256="abc123deadbeef",
            doi="10.5281/zenodo.20415839",
            github_release_url="https://github.com/docxology/template-release-smoke/releases/tag/v0.3.0-release-smoke",
            release_name="Template release smoke v0.3.0",
        )
        footer = format_cross_links_footer(cross_links)
        assert "Associated artifacts" in footer
        assert "GitHub release: Template release smoke v0.3.0" in footer
        assert "https://github.com/docxology/template-release-smoke/releases/tag/v0.3.0-release-smoke" in footer
        assert "DOI: https://doi.org/10.5281/zenodo.20415839" in footer
        assert "PDF SHA-256: abc123deadbeef" in footer

    def test_build_deposit_description_appends_footer(self, tmp_path: Path) -> None:
        abstract_path = tmp_path / "00_abstract.md"
        abstract_path.write_text(_ABSTRACT_EXCERPT, encoding="utf-8")
        cross_links = DepositCrossLinks(
            project="template_prose_project",
            tag="v1.0.0",
            github_repo="owner/repo",
            pdf_sha256="sha256value",
            doi="10.5281/zenodo.12345",
        )
        description = build_deposit_description(
            abstract_source=abstract_path,
            variables_path=None,
            cross_links=cross_links,
        )
        assert "{#sec:abstract}" not in description
        assert "PDF SHA-256: sha256value" in description
        assert "DOI: https://doi.org/10.5281/zenodo.12345" in description

    def test_zenodo_record_url_from_doi(self) -> None:
        assert zenodo_record_url_from_doi("10.5281/zenodo.20415839") == (
            "https://zenodo.org/records/20415839"
        )

    def test_github_release_body_includes_publication_block(self) -> None:
        body = build_github_release_body(
            project_name="template_prose_project",
            tag="v1.0.0",
            abstract_plaintext="Plain abstract excerpt.",
            doi="10.5281/zenodo.12345",
            pdf_sha256="deadbeef",
            zenodo_record_url="https://zenodo.org/records/12345",
            github_release_url="https://github.com/owner/repo/releases/tag/v1.0.0",
            version="1.0",
        )
        assert "## Publication" in body
        assert "- Version: 1.0" in body
        assert "https://github.com/owner/repo/releases/tag/v1.0.0" in body
        assert "https://doi.org/10.5281/zenodo.12345" in body
        assert "`deadbeef`" in body
        assert "## Abstract" in body
        assert "Plain abstract excerpt." in body
