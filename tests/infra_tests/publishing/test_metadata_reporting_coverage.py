"""Tests for infrastructure.publishing._metadata_reporting — expanded coverage."""

import json

from infrastructure.publishing._metadata_reporting import (
    _classify_publication_type,
    generate_publication_summary,
    create_academic_profile_data,
    generate_publication_metrics,
    calculate_metadata_complexity_score,
    calculate_complexity_score,
    create_repository_metadata,
)
from infrastructure.publishing.models import PublicationMetadata


def _make_metadata(**overrides):
    defaults = dict(
        title="A Research Paper on Template Systems",
        authors=["Alice Smith", "Bob Jones", "Carol Lee"],
        abstract="This paper explores advanced template systems for scientific publishing. " * 10,
        keywords=["templates", "publishing", "science", "automation", "research"],
        doi="10.5281/zenodo.12345678",
        license="MIT",
        repository_url="https://github.com/example/repo",
        publication_date="2025-01-15",
        journal="Journal of Template Science",
        conference=None,
        publisher="Template Press",
    )
    defaults.update(overrides)
    return PublicationMetadata(**defaults)


class TestClassifyPublicationType:
    def test_software(self):
        meta = _make_metadata(title="Research Template Framework")
        assert _classify_publication_type(meta) == "software"

    def test_article(self):
        meta = _make_metadata(title="Neural Networks for Vision")
        assert _classify_publication_type(meta) == "article"


class TestGeneratePublicationSummary:
    def test_basic(self):
        meta = _make_metadata()
        summary = generate_publication_summary(meta)
        assert "Publication Information" in summary
        assert meta.title in summary
        assert "Alice Smith" in summary

    def test_with_doi(self):
        meta = _make_metadata(doi="10.5281/zenodo.12345678")
        summary = generate_publication_summary(meta)
        assert "DOI" in summary
        assert "10.5281/zenodo.12345678" in summary

    def test_without_doi(self):
        meta = _make_metadata(doi=None)
        summary = generate_publication_summary(meta)
        assert "DOI" not in summary

    def test_with_journal(self):
        meta = _make_metadata(journal="Nature")
        summary = generate_publication_summary(meta)
        assert "Nature" in summary

    def test_without_journal(self):
        meta = _make_metadata(journal=None)
        summary = generate_publication_summary(meta)
        assert "Journal" not in summary

    def test_with_conference(self):
        meta = _make_metadata(conference="NeurIPS 2025", journal=None)
        summary = generate_publication_summary(meta)
        assert "NeurIPS 2025" in summary


class TestCreateAcademicProfileData:
    def test_with_doi(self):
        meta = _make_metadata()
        profile = create_academic_profile_data(meta)
        assert profile["title"] == meta.title
        assert "identifiers" in profile
        assert profile["identifiers"][0]["type"] == "doi"

    def test_without_doi(self):
        meta = _make_metadata(doi=None)
        profile = create_academic_profile_data(meta)
        assert "identifiers" not in profile


class TestCalculateMetadataComplexityScore:
    def test_minimal(self):
        meta = _make_metadata(
            title="Short",
            abstract="Brief.",
            authors=["One"],
            keywords=["k"],
            doi=None,
            journal=None,
            publisher=None,
            publication_date=None,
        )
        score = calculate_metadata_complexity_score(meta)
        assert 0 <= score <= 100

    def test_high_complexity(self):
        meta = _make_metadata(
            title="A Very Long and Detailed Research Paper Title for Evaluation",
            abstract="word " * 350,
            authors=["A", "B", "C", "D", "E", "F"],
            keywords=["a", "b", "c", "d", "e", "f", "g", "h", "i"],
            doi="10.1234/test",
            journal="Nature",
            publisher="Springer",
            publication_date="2025-01-01",
        )
        score = calculate_metadata_complexity_score(meta)
        assert score >= 80

    def test_medium_title(self):
        """Title with 7-9 words."""
        meta = _make_metadata(title="Research on Neural Network Image Processing Tasks")
        score = calculate_metadata_complexity_score(meta)
        assert score > 0

    def test_short_title(self):
        """Title with 5-6 words."""
        meta = _make_metadata(title="Neural Networks Image Processing")
        score = calculate_metadata_complexity_score(meta)
        assert score > 0

    def test_abstract_200_words(self):
        meta = _make_metadata(abstract="word " * 220)
        score = calculate_metadata_complexity_score(meta)
        assert score > 0

    def test_abstract_100_words(self):
        meta = _make_metadata(abstract="word " * 120)
        score = calculate_metadata_complexity_score(meta)
        assert score > 0

    def test_abstract_50_words(self):
        meta = _make_metadata(abstract="word " * 60)
        score = calculate_metadata_complexity_score(meta)
        assert score > 0

    def test_four_authors(self):
        meta = _make_metadata(authors=["A", "B", "C", "D"])
        score = calculate_metadata_complexity_score(meta)
        assert score > 0

    def test_two_authors(self):
        meta = _make_metadata(authors=["A", "B"])
        score = calculate_metadata_complexity_score(meta)
        assert score > 0

    def test_five_keywords(self):
        meta = _make_metadata(keywords=["a", "b", "c", "d", "e"])
        score = calculate_metadata_complexity_score(meta)
        assert score > 0

    def test_three_keywords(self):
        meta = _make_metadata(keywords=["a", "b", "c"])
        score = calculate_metadata_complexity_score(meta)
        assert score > 0

    def test_conference_no_journal(self):
        meta = _make_metadata(journal=None, conference="ICML 2025")
        score = calculate_metadata_complexity_score(meta)
        assert score > 0


class TestCalculateComplexityScore:
    def test_alias(self):
        meta = _make_metadata()
        assert calculate_complexity_score(meta) == calculate_metadata_complexity_score(meta)


class TestGeneratePublicationMetrics:
    def test_basic(self):
        meta = _make_metadata()
        metrics = generate_publication_metrics(meta)
        assert "title_length" in metrics
        assert "abstract_length" in metrics
        assert "author_count" in metrics
        assert metrics["has_doi"] is True
        assert metrics["complexity_score"] > 0

    def test_no_doi(self):
        meta = _make_metadata(doi=None)
        metrics = generate_publication_metrics(meta)
        assert metrics["has_doi"] is False


class TestCreateRepositoryMetadata:
    def test_with_url_and_doi(self):
        meta = _make_metadata()
        json_str = create_repository_metadata(meta)
        data = json.loads(json_str)
        assert data["@type"] == "SoftwareSourceCode"
        assert data["name"] == meta.title
        assert "url" in data
        assert "identifier" in data

    def test_without_url_and_doi(self):
        meta = _make_metadata(repository_url=None, doi=None)
        json_str = create_repository_metadata(meta)
        data = json.loads(json_str)
        assert "url" not in data
        assert "identifier" not in data
