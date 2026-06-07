"""Generate source-bound publication record documentation for public exemplars."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from infrastructure.project.public_scope import public_project_names

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
    config_path: Path
    citation_path: Path
    zenodo_json_path: Path
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
        url = self.repository_url
        if url and "github.com/" in url:
            return url.split("github.com/", 1)[1].strip("/")
        return ""

    @property
    def sidecar_status(self) -> str:
        """Return a compact sidecar consistency status."""
        return "ok" if not self.sidecar_findings else "; ".join(self.sidecar_findings)

    @property
    def external_status(self) -> str:
        """Return a compact external verification status."""
        statuses = [
            f"GitHub repo {self.github_repo_status}",
            f"GitHub release {self.github_release_status}",
            f"Zenodo {self.zenodo_status}",
        ]
        if self.external_findings:
            statuses.extend(self.external_findings)
        return "; ".join(statuses)


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def _load_json_mapping(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    loaded = json.loads(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def _section_mapping(container: dict[str, Any], key: str) -> dict[str, Any]:
    value = container.get(key)
    return value if isinstance(value, dict) else {}


def _authors_from_config(config: dict[str, Any]) -> tuple[str, ...]:
    raw_authors = config.get("authors")
    if not isinstance(raw_authors, list):
        return ()
    names: list[str] = []
    for author in raw_authors:
        if isinstance(author, dict) and author.get("name"):
            names.append(str(author["name"]).strip())
    return tuple(name for name in names if name)


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


def _markdown_link(label: str, url: str) -> str:
    if not label:
        return "n/a"
    return f"[{label}]({url})" if url else label


def _relative_link(path: Path, repo_root: Path, from_dir: Path) -> str:
    rel = path.relative_to(repo_root)
    target = Path("..") / ".." / rel if from_dir.name == "_generated" else rel
    return target.as_posix()


def _sidecar_findings(
    *,
    paper_version: str,
    concept_doi: str,
    citation: dict[str, Any],
    zenodo_json: dict[str, Any],
) -> tuple[str, ...]:
    findings: list[str] = []
    cff_version = str(citation.get("version", "")).strip().strip("'\"")
    cff_doi = str(citation.get("doi", "")).strip()
    zenodo_version = str(zenodo_json.get("version", "")).strip()

    if not citation:
        findings.append("missing CITATION.cff")
    elif paper_version and cff_version != paper_version:
        findings.append(f"CITATION version {cff_version or 'empty'} != config {paper_version}")
    if citation and concept_doi and cff_doi != concept_doi:
        findings.append(f"CITATION DOI {cff_doi or 'empty'} != concept {concept_doi}")

    if not zenodo_json:
        findings.append("missing .zenodo.json")
    elif paper_version and zenodo_version != paper_version:
        findings.append(f".zenodo version {zenodo_version or 'empty'} != config {paper_version}")

    return tuple(findings)


def load_publication_records(repo_root: Path) -> list[PublicationRecord]:
    """Load publication records from public project configs and sidecars."""
    repo_root = Path(repo_root).resolve()
    records: list[PublicationRecord] = []
    for project_name in public_project_names(repo_root):
        project_root = repo_root / "projects" / project_name
        config_path = project_root / "manuscript" / "config.yaml"
        config = _load_yaml_mapping(config_path)
        paper = _section_mapping(config, "paper")
        book = _section_mapping(config, "book")
        publication = _section_mapping(config, "publication")

        # Prose/code exemplars use `paper:`; book-length exemplars use `book:`.
        title = str(paper.get("title") or book.get("title") or project_name)
        paper_version = str(paper.get("version") or book.get("version") or "").strip()
        concept_doi = str(publication.get("doi") or "").strip()
        version_doi = str(publication.get("version_doi") or "").strip()
        version_record = str(publication.get("version_record") or "").strip()
        github_repository = str(publication.get("github_repository") or "").strip()
        repository_url = str(publication.get("repository_url") or "").strip() or _github_repo_url(github_repository)

        citation_path = project_root / "CITATION.cff"
        zenodo_json_path = project_root / ".zenodo.json"
        citation = _load_yaml_mapping(citation_path)
        zenodo_json = _load_json_mapping(zenodo_json_path)

        records.append(
            PublicationRecord(
                project_name=project_name,
                title=title,
                paper_version=paper_version,
                authors=_authors_from_config(config),
                concept_doi=concept_doi,
                version_doi=version_doi,
                version_record=version_record,
                github_repository=github_repository,
                repository_url=repository_url,
                config_path=config_path,
                citation_path=citation_path,
                zenodo_json_path=zenodo_json_path,
                citation_version=str(citation.get("version", "")).strip().strip("'\""),
                citation_doi=str(citation.get("doi", "")).strip(),
                zenodo_json_version=str(zenodo_json.get("version", "")).strip(),
                sidecar_findings=_sidecar_findings(
                    paper_version=paper_version,
                    concept_doi=concept_doi,
                    citation=citation,
                    zenodo_json=zenodo_json,
                ),
            )
        )
    return records


def _fetch_json(url: str, timeout: float) -> tuple[str, dict[str, Any]]:
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310  # nosec B310 - fixed public api.github.com and zenodo.org URLs only; scheme is locked by caller
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
        if repo_slug:
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
        else:
            record.zenodo_status = "missing version DOI"
            findings.append("missing version_doi")

        record.external_findings = tuple(findings)


def render_publication_records_doc(
    repo_root: Path,
    records: list[PublicationRecord],
    *,
    generated_at: datetime | None = None,
    refreshed_external: bool = False,
) -> str:
    """Render ``docs/_generated/publication_records.md``."""
    repo_root = Path(repo_root).resolve()
    generated_at = generated_at or datetime.now(timezone.utc)
    generated_text = generated_at.isoformat(timespec="seconds")
    external_text = f"refreshed at `{generated_text}`" if refreshed_external else "not refreshed in this run"

    lines = [
        "# Publication Records",
        "",
        "This file is **generated**. Do not edit by hand.",
        "",
        "Local source fields come from `infrastructure.project.public_scope`, each public exemplar's "
        "`manuscript/config.yaml`, `CITATION.cff`, and `.zenodo.json`. GitHub and Zenodo columns are "
        f"from public APIs when the generator runs with `--refresh-external` ({external_text}).",
        "",
        "Regenerate:",
        "",
        "```bash",
        "uv run python scripts/generate_publication_records_doc.py --refresh-external",
        "```",
        "",
        "## Public Exemplar Publication Matrix",
        "",
        "| Project | Config version | GitHub repo | Latest GitHub release | "
        "Concept DOI | Latest version DOI | Zenodo version | Status |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for record in records:
        project_label = f"`{record.project_name}`"
        github = _markdown_link(record.github_repo_slug, _github_repo_url(record.github_repo_slug))
        release_label = record.github_latest_release_tag or record.github_release_status
        release = _markdown_link(release_label, record.github_latest_release_url)
        concept = _markdown_link(record.concept_doi, _doi_url(record.concept_doi))
        version = _markdown_link(record.version_doi, _doi_url(record.version_doi))
        status = f"{record.sidecar_status}; {record.external_status}"
        lines.append(
            "| "
            + " | ".join(
                [
                    project_label,
                    record.paper_version or "n/a",
                    github,
                    release,
                    concept,
                    version,
                    record.zenodo_record_version or "not checked",
                    status,
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Local Source Paths",
            "",
            "| Project | Config | Citation | Zenodo metadata |",
            "| --- | --- | --- | --- |",
        ]
    )
    for record in records:
        config_link = _markdown_link(
            "`manuscript/config.yaml`",
            _relative_link(record.config_path, repo_root, repo_root / "docs" / "_generated"),
        )
        citation_link = _markdown_link(
            "`CITATION.cff`",
            _relative_link(record.citation_path, repo_root, repo_root / "docs" / "_generated"),
        )
        zenodo_link = _markdown_link(
            "`.zenodo.json`",
            _relative_link(record.zenodo_json_path, repo_root, repo_root / "docs" / "_generated"),
        )
        lines.append(f"| `{record.project_name}` | {config_link} | {citation_link} | {zenodo_link} |")

    lines.extend(
        [
            "",
            "## DOI Roles",
            "",
            "- `publication.doi` is the stable Zenodo concept DOI used for citations and PDF cover pages.",
            "- `publication.version_doi` is the latest immutable Zenodo deposit DOI.",
            "- `publication.version_record` points at the latest immutable Zenodo record page.",
            "- `publication.github_repository` is the standalone public GitHub repository for the exemplar.",
            "",
        ]
    )
    return "\n".join(lines)


def render_github_readme_publication_block(records: list[PublicationRecord]) -> str:
    """Render the generated publication table block for ``.github/README.md``."""
    lines = [
        README_BLOCK_BEGIN,
        "<!-- This block is generated by scripts/generate_publication_records_doc.py. Do not hand-edit. -->",
        "",
        "| Exemplar | Config version | GitHub | Latest release | Zenodo concept DOI | Latest version DOI |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for record in records:
        project = _markdown_link(f"`{record.project_name}`", f"../projects/{record.project_name}/")
        github = _markdown_link(record.github_repo_slug, _github_repo_url(record.github_repo_slug))
        release_label = record.github_latest_release_tag or record.github_release_status
        release = _markdown_link(release_label, record.github_latest_release_url)
        concept = _markdown_link(record.concept_doi, _doi_url(record.concept_doi))
        version = _markdown_link(record.version_doi, _doi_url(record.version_doi))
        lines.append(f"| {project} | {record.paper_version or 'n/a'} | {github} | {release} | {concept} | {version} |")
    lines.extend(
        [
            "",
            "Full generated matrix: "
            "[`docs/_generated/publication_records.md`](../docs/_generated/publication_records.md).",
            "",
            README_BLOCK_END,
        ]
    )
    return "\n".join(lines)


def replace_github_readme_publication_block(readme_text: str, block: str) -> str:
    """Replace the generated publication block in ``.github/README.md``."""
    pattern = re.compile(
        re.escape(README_BLOCK_BEGIN) + r".*?" + re.escape(README_BLOCK_END),
        flags=re.DOTALL,
    )
    if not pattern.search(readme_text):
        raise ValueError("Missing publication records markers in .github/README.md")
    return pattern.sub(block, readme_text)


def write_publication_records_doc(
    repo_root: Path,
    *,
    refresh_external: bool = False,
    update_github_readme: bool = True,
) -> tuple[Path, Path | None]:
    """Write generated publication docs and optionally sync ``.github/README.md``."""
    repo_root = Path(repo_root).resolve()
    records = load_publication_records(repo_root)
    if refresh_external:
        refresh_external_records(records)

    out_dir = repo_root / "docs" / "_generated"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "publication_records.md"
    out_path.write_text(
        render_publication_records_doc(repo_root, records, refreshed_external=refresh_external),
        encoding="utf-8",
    )

    readme_path: Path | None = None
    if update_github_readme:
        readme_path = repo_root / ".github" / "README.md"
        block = render_github_readme_publication_block(records)
        readme_path.write_text(
            replace_github_readme_publication_block(readme_path.read_text(encoding="utf-8"), block),
            encoding="utf-8",
        )

    return out_path, readme_path
