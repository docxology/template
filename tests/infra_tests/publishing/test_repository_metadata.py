"""Repository metadata normalization tests."""

from infrastructure.publishing.repository_metadata import normalized_repository_url


def test_explicit_repository_url_wins() -> None:
    publication = {
        "repository_url": " https://example.org/source ",
        "github_repository": "owner/repo",
    }
    assert normalized_repository_url(publication) == "https://example.org/source"


def test_github_slug_is_normalized_to_url() -> None:
    assert normalized_repository_url({"github_repository": " owner/repo "}) == "https://github.com/owner/repo"


def test_missing_repository_metadata_returns_none() -> None:
    assert normalized_repository_url({}) is None
