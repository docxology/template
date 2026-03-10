"""Tests for infrastructure/publishing/metadata.py.

Tests metadata extraction with real temp files. No mocks.
"""

from __future__ import annotations

from infrastructure.publishing.metadata import extract_publication_metadata
from infrastructure.publishing.models import PublicationMetadata


class TestExtractPublicationMetadata:
    def test_empty_list_returns_defaults(self):
        result = extract_publication_metadata([])
        assert isinstance(result, PublicationMetadata)
        assert result.title == "Research Project Template"

    def test_extracts_title_from_heading(self, tmp_path):
        f = tmp_path / "intro.md"
        f.write_text("# My Research Study\n\nThis is the content.")
        result = extract_publication_metadata([f])
        assert result.title == "My Research Study"

    def test_missing_file_falls_back_to_defaults(self, tmp_path):
        missing = tmp_path / "nonexistent.md"
        result = extract_publication_metadata([missing])
        assert isinstance(result, PublicationMetadata)
        assert result.title  # Some default title

    def test_returns_publication_metadata_instance(self, tmp_path):
        f = tmp_path / "paper.md"
        f.write_text("# Paper Title\n\nContent here.")
        result = extract_publication_metadata([f])
        assert isinstance(result, PublicationMetadata)

    def test_template_content_skipped(self, tmp_path):
        f = tmp_path / "template.md"
        f.write_text("# Research Project Template\n\nBoilerplate content.")
        result = extract_publication_metadata([f])
        # Template content is skipped; default title remains
        assert result.title == "Research Project Template"
