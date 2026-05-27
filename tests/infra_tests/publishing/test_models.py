"""Tests for infrastructure.publishing.models."""

from __future__ import annotations

from infrastructure.publishing.models import CitationStyle, PublicationMetadata


class TestPublicationMetadata:
    def test_defaults(self) -> None:
        metadata = PublicationMetadata(
            title="Paper",
            authors=["Author"],
            abstract="Abstract.",
            keywords=["kw"],
        )
        assert metadata.license == "CC-BY-4.0"
        assert metadata.doi is None


class TestCitationStyle:
    def test_construction(self) -> None:
        style = CitationStyle(
            name="apa",
            format_string="{author} ({year}). {title}.",
            example="Smith (2024). Example.",
        )
        assert style.name == "apa"
        assert "{author}" in style.format_string
        assert style.example.startswith("Smith")
