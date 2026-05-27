"""Zenodo API data models."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DepositionResult:
    """Result of creating a Zenodo deposition."""

    deposition_id: str
    bucket_url: str


@dataclass(frozen=True)
class PublishResult:
    """Result of publishing a deposition to Zenodo."""

    doi: str
    deposition_id: str
