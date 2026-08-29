"""Publication-record types and DOI/GitHub URL helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

README_BLOCK_BEGIN = "<!-- BEGIN:PUBLICATION_RECORDS -->"
README_BLOCK_END = "<!-- END:PUBLICATION_RECORDS -->"

_USER_AGENT = "docxology-template-publication-records/1.0"
_ZENODO_DOI_RE = re.compile(r"10\.5281/zenodo\.(?P<record>\d+)")


@dataclass(slots=True)
class PublicationRecord:
    """Local and optionally refreshed external metadata for one public project."""

    project_name: str
    title: str
    paper_version: str
    authors: tuple[str, ...]
    concept_doi: str
    version_doi: str
    version_record: str
    github_repository: str
    repository_url: str
    published_artifacts: tuple[tuple[str, str], ...]
    standalone_path: Path
    config_path: Path
    citation_path: Path
    zenodo_json_path: Path
    codemeta_path: Path
    citation_version: str = ""
    citation_doi: str = ""
    zenodo_json_version: str = ""
    sidecar_findings: tuple[str, ...] = ()
    github_repo_status: str = "not checked"
    github_release_status: str = "not checked"
    github_latest_release_tag: str = ""
    github_latest_release_url: str = ""
    github_latest_release_published_at: str = ""
    zenodo_status: str = "not checked"
    zenodo_record_url: str = ""
    zenodo_record_version: str = ""
    zenodo_record_title: str = ""
    zenodo_record_concept_doi: str = ""
    zenodo_record_doi: str = ""
    external_findings: tuple[str, ...] = ()

    @property
    def github_repo_slug(self) -> str:
        """Return ``owner/repo``, falling back to a github.com ``repository_url``.

        Book-schema exemplars declare ``publication.repository_url`` instead of
        ``publication.github_repository``; both should surface a GitHub link.
        """
        if self.github_repository:
            return self.github_repository
        path = self.github_url_path
        if path and "/tree/" not in path and "/blob/" not in path:
            parts = path.split("/")
            if len(parts) >= 2:
                return "/".join(parts[:2])
        return ""

    @property
    def github_url_path(self) -> str:
        """Return the GitHub url path."""
        url = self.repository_url
        if url and "github.com/" in url:
            return url.split("github.com/", 1)[1].strip("/")
        return ""

    @property
    def is_monorepo_publication_path(self) -> bool:
        """Check whether monorepo publication path."""
        path = self.github_url_path
        return not self.github_repository and ("/tree/" in path or "/blob/" in path)

    @property
    def monorepo_slug(self) -> str:
        """Return the monorepo slug."""
        if not self.is_monorepo_publication_path:
            return ""
        parts = self.github_url_path.split("/")
        if len(parts) >= 2:
            return "/".join(parts[:2])
        return ""

    @property
    def github_display_label(self) -> str:
        """Return the GitHub display label."""
        if self.github_repo_slug:
            return self.github_repo_slug
        if self.is_monorepo_publication_path and self.monorepo_slug:
            return f"{self.monorepo_slug} path"
        return ""

    @property
    def github_display_url(self) -> str:
        """Return the GitHub display url."""
        if self.github_repo_slug:
            return _github_repo_url(self.github_repo_slug)
        if self.is_monorepo_publication_path:
            return self.repository_url
        return ""

    @property
    def sidecar_status(self) -> str:
        """Return a compact sidecar consistency status."""
        return "ok" if not self.sidecar_findings else "; ".join(self.sidecar_findings)

    @property
    def external_status(self) -> str:
        """Return a compact external verification status."""
        raw_statuses = (self.github_repo_status, self.github_release_status, self.zenodo_status)
        accepted = (
            {"200", "monorepo path"},
            {"200", "covered by root release"},
            {"200", "not published separately"},
        )
        if any(status == "not checked" or status.startswith("error:") for status in raw_statuses):
            verification = "unverified"
        elif not self.external_findings and all(status in allowed for status, allowed in zip(raw_statuses, accepted)):
            verification = "verified"
        else:
            verification = "incomplete"
        statuses = [
            f"GitHub repo {self.github_repo_status}",
            f"GitHub release {self.github_release_status}",
            f"Zenodo {self.zenodo_status}",
        ]
        if self.external_findings:
            statuses.extend(self.external_findings)
        return f"{verification}; " + "; ".join(statuses)

    @property
    def declared_location_count(self) -> int:
        """Count canonical GitHub/Zenodo locations plus extra declared artifacts."""
        canonical = int(bool(self.github_display_url)) + int(bool(self.concept_doi))
        return canonical + len(self.published_artifacts)


def _doi_url(doi: str) -> str:
    return f"https://doi.org/{doi}" if doi else ""


def _github_repo_url(repo: str) -> str:
    return f"https://github.com/{repo}" if repo else ""


def _record_id_from_doi(doi: str) -> str:
    match = _ZENODO_DOI_RE.search(doi)
    return match.group("record") if match else ""


def _record_url_from_doi(doi: str) -> str:
    record_id = _record_id_from_doi(doi)
    return f"https://zenodo.org/records/{record_id}" if record_id else ""
