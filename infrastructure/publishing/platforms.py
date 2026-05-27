"""Backwards-compatible platform integration re-exports."""

from infrastructure.publishing.arxiv.submission import prepare_arxiv_submission
from infrastructure.publishing.github.release import create_github_release
from infrastructure.publishing.zenodo.publish import publish_to_zenodo

__all__ = [
    "create_github_release",
    "prepare_arxiv_submission",
    "publish_to_zenodo",
]
