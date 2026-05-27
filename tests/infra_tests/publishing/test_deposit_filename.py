"""Tests for metadata-driven deposit upload filenames."""

from __future__ import annotations

from infrastructure.publishing.deposit_filename import (
    DepositPublishContext,
    author_segment,
    build_deposit_filename,
    legacy_deposit_filename,
    topic_segment,
    year_segment,
)
from infrastructure.publishing.models import AuthorRecord, PublicationMetadata


def _template_code_metadata() -> PublicationMetadata:
    return PublicationMetadata(
        title="Convergence Analysis of Gradient Descent Optimization",
        authors=["Research Template Author", "Co-Author"],
        abstract="Test abstract.",
        keywords=["optimization"],
        publication_date="2026",
        author_records=[
            AuthorRecord(name="Research Template Author"),
            AuthorRecord(name="Co-Author"),
        ],
        paper_version="2.0",
    )


class TestDepositFilename:
    def test_template_code_project_default_pattern(self) -> None:
        metadata = _template_code_metadata()
        authors_config = [
            {"name": "Research Template Author", "corresponding": True},
            {"name": "Co-Author", "corresponding": False},
        ]
        context = DepositPublishContext(
            deposit_filename_config={},
            authors_config=authors_config,
        )
        name = build_deposit_filename(
            metadata=metadata,
            pdf_sha256="b591a0ced6221697b6ac478a62ee80d71f65a1e72c6873d73f54ef423cddb59c",
            project_name="template_code_project",
            release_tag="v2.0.0",
            publish_context=context,
        )
        assert name == "Author_2026_Convergence_b591a0ce.pdf"

    def test_corresponding_author_preferred(self) -> None:
        metadata = PublicationMetadata(
            title="Release Test Paper",
            authors=["Co-Author", "Lead Author"],
            abstract="Test.",
            keywords=[],
            author_records=[
                AuthorRecord(name="Co-Author"),
                AuthorRecord(name="Lead Author"),
            ],
        )
        authors_config = [
            {"name": "Co-Author", "corresponding": False},
            {"name": "Lead Author", "corresponding": True},
        ]
        assert author_segment(metadata, authors_config=authors_config) == "Author"

    def test_year_fallback_from_release_tag(self) -> None:
        metadata = PublicationMetadata(
            title="Untitled",
            authors=["Test Author"],
            abstract="Test.",
            keywords=[],
        )
        assert year_segment(metadata, "release-2025-smoke") == "2025"

    def test_topic_override_via_config(self) -> None:
        metadata = _template_code_metadata()
        name = build_deposit_filename(
            metadata=metadata,
            pdf_sha256="abc123def456",
            project_name="template_code_project",
            release_tag="v2.0.0",
            publish_context=DepositPublishContext(
                deposit_filename_config={"enabled": True, "topic": "GradientDescent"},
                authors_config=[],
            ),
        )
        assert name == "Author_2026_Gradientdescent_abc123de.pdf"

    def test_disabled_returns_legacy_name(self) -> None:
        metadata = _template_code_metadata()
        name = build_deposit_filename(
            metadata=metadata,
            pdf_sha256="b591a0ced6221697b6ac478a62ee80d71f65a1e72c6873d73f54ef423cddb59c",
            project_name="template_code_project",
            release_tag="v2.0.0",
            publish_context=DepositPublishContext(
                deposit_filename_config={"enabled": False},
                authors_config=[],
            ),
        )
        assert name == legacy_deposit_filename("template_code_project")

    def test_unicode_author_and_title_folding(self) -> None:
        metadata = PublicationMetadata(
            title="Méthode générale d'optimisation",
            authors=["Cauchy, Augustin-Louis"],
            abstract="Test.",
            keywords=[],
            publication_date="1847",
            author_records=[AuthorRecord(name="Cauchy, Augustin-Louis")],
        )
        name = build_deposit_filename(
            metadata=metadata,
            pdf_sha256="deadbeef" * 8,
            project_name="demo",
            release_tag="v1.0.0",
        )
        assert name.startswith("Cauchy_1847_Methode_")
        assert name.endswith(".pdf")

    def test_empty_topic_falls_back_to_legacy(self) -> None:
        metadata = PublicationMetadata(
            title="A An The",
            authors=["Test Author"],
            abstract="Test.",
            keywords=[],
            publication_date="2026",
        )
        name = build_deposit_filename(
            metadata=metadata,
            pdf_sha256="abc123" * 10,
            project_name="demo_project",
            release_tag="v1.0.0",
        )
        assert name == "demo_project_combined.pdf"

    def test_topic_segment_truncates_long_override(self) -> None:
        metadata = _template_code_metadata()
        long_topic = "X" * 40
        segment = topic_segment(metadata, topic_override=long_topic)
        assert len(segment) == 24
