"""Live GitHub and Zenodo refresh for publication records."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from infrastructure.documentation._publication_records_load import _section_mapping
from infrastructure.documentation._publication_records_types import (
    PublicationRecord,
    _USER_AGENT,
    _record_id_from_doi,
    _record_url_from_doi,
)


def _fetch_json(url: str, timeout: float) -> tuple[str, dict[str, Any]]:
    headers = {"User-Agent": _USER_AGENT}
    if url.startswith("https://api.github.com/") and (token := os.getenv("GITHUB_TOKEN")):
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310  # nosec B310
            payload = json.loads(response.read().decode("utf-8"))
            return str(response.status), payload if isinstance(payload, dict) else {}
    except urllib.error.HTTPError as exc:
        return str(exc.code), {}
    except (OSError, TimeoutError, json.JSONDecodeError) as exc:
        return f"error: {exc.__class__.__name__}", {}


def refresh_external_records(records: list[PublicationRecord], *, timeout: float = 20.0) -> None:
    """Populate records with live GitHub and Zenodo API observations."""
    for record in records:
        findings: list[str] = []

        repo_slug = record.github_repo_slug
        if record.is_monorepo_publication_path:
            record.github_repo_status = "monorepo path"
            record.github_release_status = "covered by root release"
            if record.monorepo_slug:
                record.github_latest_release_tag = "root release"
                record.github_latest_release_url = f"https://github.com/{record.monorepo_slug}/releases/latest"
        elif repo_slug:
            repo_status, _ = _fetch_json(f"https://api.github.com/repos/{repo_slug}", timeout)
            release_status, release_payload = _fetch_json(
                f"https://api.github.com/repos/{repo_slug}/releases/latest",
                timeout,
            )
            record.github_repo_status = repo_status
            record.github_release_status = release_status
            record.github_latest_release_tag = str(release_payload.get("tag_name") or "")
            record.github_latest_release_url = str(release_payload.get("html_url") or "")
            record.github_latest_release_published_at = str(release_payload.get("published_at") or "")

            expected_tag = f"v{record.paper_version}" if record.paper_version else ""
            if expected_tag and record.github_latest_release_tag and record.github_latest_release_tag != expected_tag:
                findings.append(f"GitHub latest {record.github_latest_release_tag} != config {expected_tag}")
        else:
            record.github_repo_status = "missing repository"
            record.github_release_status = "missing repository"
            findings.append("missing github_repository")

        record_id = _record_id_from_doi(record.version_doi)
        if record_id:
            zenodo_status, zenodo_payload = _fetch_json(f"https://zenodo.org/api/records/{record_id}", timeout)
            metadata = _section_mapping(zenodo_payload, "metadata")
            links = _section_mapping(zenodo_payload, "links")
            record.zenodo_status = zenodo_status
            record.zenodo_record_url = str(links.get("html") or _record_url_from_doi(record.version_doi))
            record.zenodo_record_version = str(metadata.get("version") or "")
            record.zenodo_record_title = str(metadata.get("title") or "")
            record.zenodo_record_concept_doi = str(zenodo_payload.get("conceptdoi") or "")
            record.zenodo_record_doi = str(zenodo_payload.get("doi") or "")

            if record.concept_doi and record.zenodo_record_concept_doi:
                if record.concept_doi != record.zenodo_record_concept_doi:
                    findings.append(f"Zenodo concept {record.zenodo_record_concept_doi} != config {record.concept_doi}")
            if record.version_doi and record.zenodo_record_doi:
                if record.version_doi != record.zenodo_record_doi:
                    findings.append(f"Zenodo DOI {record.zenodo_record_doi} != config {record.version_doi}")
            if record.paper_version and record.zenodo_record_version:
                if record.paper_version != record.zenodo_record_version:
                    findings.append(f"Zenodo version {record.zenodo_record_version} != config {record.paper_version}")
        elif record.version_doi:
            record.zenodo_status = "invalid version DOI"
            findings.append("invalid version_doi")
        elif record.concept_doi:
            record.zenodo_status = "missing version DOI"
            findings.append("missing version_doi")
        elif record.is_monorepo_publication_path:
            record.zenodo_status = "not published separately"
        else:
            record.zenodo_status = "missing version DOI"
            findings.append("missing version_doi")

        record.external_findings = tuple(findings)
