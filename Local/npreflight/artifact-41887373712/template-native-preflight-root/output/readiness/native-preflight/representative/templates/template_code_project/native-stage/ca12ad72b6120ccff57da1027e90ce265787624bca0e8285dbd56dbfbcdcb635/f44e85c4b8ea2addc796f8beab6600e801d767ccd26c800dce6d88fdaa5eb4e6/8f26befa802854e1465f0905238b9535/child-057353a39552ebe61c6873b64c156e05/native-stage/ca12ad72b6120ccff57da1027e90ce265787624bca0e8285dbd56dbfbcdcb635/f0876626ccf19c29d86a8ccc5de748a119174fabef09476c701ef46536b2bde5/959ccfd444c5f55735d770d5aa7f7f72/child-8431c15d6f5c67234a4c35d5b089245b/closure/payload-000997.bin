"""Dependency-light value models shared by transmission publishing modules."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TransmissionContext:
    """Inputs for rendering transmission bookends and integrity barcodes."""

    title: str
    version: str | None
    doi: str | None
    version_doi: str | None
    version_record: str | None
    github_release_url: str | None
    github_repository: str | None
    pdf_sha256: str | None
    pdf_sha512: str | None
    zenodo_record_url: str | None
    pairing_valid: bool
    pairing_checklist: str
    pairing_compact: str
    steganography_summary: str
    steganography_one_liner: str
    figure_markdown: str
    integrity_strip_markdown: str
    manifest_snippet: str
    manifest_path: str
    prior_releases_table: str
    prior_compact: str
    published: bool


__all__ = ["TransmissionContext"]
