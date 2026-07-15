"""Zenodo API data models."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _zenodo_concept_doi_from_record_id(
    reserved_doi: str | None,
    concept_record_id: str | None,
) -> str | None:
    if not reserved_doi or not concept_record_id:
        return None
    match = re.fullmatch(r"(10\.5281/zenodo\.)\d+", reserved_doi.strip())
    if not match:
        return None
    return f"{match.group(1)}{concept_record_id}"


@dataclass(frozen=True)
class DepositionResult:
    """Result of creating a Zenodo deposition."""

    deposition_id: str
    bucket_url: str
    reserved_doi: str | None = None
    concept_doi: str | None = None
    concept_record_id: str | None = None

    @classmethod
    def from_zenodo_body(cls, body: dict[str, Any]) -> DepositionResult:
        """Parse a Zenodo deposition JSON body into a :class:`DepositionResult`."""
        raw_metadata = body.get("metadata")
        metadata: dict[str, Any] = raw_metadata if isinstance(raw_metadata, dict) else {}
        prereserve = (
            metadata.get("prereserve_doi")
            if isinstance(metadata.get("prereserve_doi"), dict)
            else body.get("prereserve_doi")
        )
        prereserve_map = prereserve if isinstance(prereserve, dict) else {}
        reserved_doi = (
            _string_or_none(prereserve_map.get("doi"))
            or _string_or_none(body.get("doi"))
            or _string_or_none(metadata.get("doi"))
        )
        concept_record_id = _string_or_none(body.get("conceptrecid")) or _string_or_none(metadata.get("conceptrecid"))
        concept_doi = (
            _string_or_none(body.get("conceptdoi"))
            or _string_or_none(metadata.get("conceptdoi"))
            or _zenodo_concept_doi_from_record_id(reserved_doi, concept_record_id)
        )
        return cls(
            deposition_id=str(body["id"]),
            bucket_url=str(body["links"]["bucket"]).rstrip("/"),
            reserved_doi=reserved_doi,
            concept_doi=concept_doi,
            concept_record_id=concept_record_id,
        )


@dataclass(frozen=True)
class PublishResult:
    """Result of publishing a deposition to Zenodo."""

    doi: str
    deposition_id: str
    concept_doi: str | None = None
