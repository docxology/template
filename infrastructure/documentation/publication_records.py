"""Generate source-bound publication record documentation for public exemplars."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from infrastructure.core.files.serialization import load_yaml_mapping as _load_yaml_mapping
from infrastructure.documentation.publication_standalone import (
    extract_standalone_publication_block,
    render_standalone_publication_block,
    replace_standalone_publication_block,
)
from infrastructure.project.public_scope import public_project_names
from infrastructure.publishing.repository_metadata import normalized_repository_url

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


def _published_artifacts(publication: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    """Return sorted, non-empty platform/URL pairs from source-owned config."""
    raw = publication.get("published_artifacts")
    if not isinstance(raw, dict):
        return ()
    return tuple(
        sorted(
            (str(platform).strip(), str(url).strip())
            for platform, url in raw.items()
            if str(platform).strip() and str(url).strip()
        )
    )


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


def _published_artifact_links(record: PublicationRecord) -> str:
    """Render config-declared noncanonical publication locations compactly."""
    if not record.published_artifacts:
        return "n/a"
    return "<br>".join(_markdown_link(platform, url) for platform, url in record.published_artifacts)


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
    codemeta: dict[str, Any],
    standalone_exists: bool,
) -> tuple[str, ...]:
    findings: list[str] = []
    cff_version = str(citation.get("version", "")).strip().strip("'\"")
    cff_doi = str(citation.get("doi", "")).strip()
    zenodo_version = str(zenodo_json.get("version", "")).strip()
    codemeta_version = str(codemeta.get("version", "")).strip()
    codemeta_doi = str(codemeta.get("identifier", "")).strip()

    if not standalone_exists:
        findings.append("missing STANDALONE.md")

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

    if not codemeta:
        findings.append("missing codemeta.json")
    elif paper_version and codemeta_version != paper_version:
        findings.append(f"codemeta version {codemeta_version or 'empty'} != config {paper_version}")
    if codemeta and concept_doi and codemeta_doi != concept_doi:
        findings.append(f"codemeta DOI {codemeta_doi or 'empty'} != concept {concept_doi}")

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
        repository_url = normalized_repository_url(publication) or ""

        standalone_path = project_root / "STANDALONE.md"
        citation_path = project_root / "CITATION.cff"
        zenodo_json_path = project_root / ".zenodo.json"
        codemeta_path = project_root / "codemeta.json"
        citation = _load_yaml_mapping(citation_path)
        zenodo_json = _load_json_mapping(zenodo_json_path)
        codemeta = _load_json_mapping(codemeta_path)

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
                published_artifacts=_published_artifacts(publication),
                standalone_path=standalone_path,
                config_path=config_path,
                citation_path=citation_path,
                zenodo_json_path=zenodo_json_path,
                codemeta_path=codemeta_path,
                citation_version=str(citation.get("version", "")).strip().strip("'\""),
                citation_doi=str(citation.get("doi", "")).strip(),
                zenodo_json_version=str(zenodo_json.get("version", "")).strip(),
                sidecar_findings=_sidecar_findings(
                    paper_version=paper_version,
                    concept_doi=concept_doi,
                    citation=citation,
                    zenodo_json=zenodo_json,
                    codemeta=codemeta,
                    standalone_exists=standalone_path.is_file(),
                ),
            )
        )
    return records


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
    record_count = len(records)
    standalone_count = sum(record.standalone_path.is_file() for record in records)
    github_count = sum(bool(record.github_display_url) for record in records)
    doi_pair_count = sum(bool(record.concept_doi and record.version_doi) for record in records)
    additional_location_count = sum(len(record.published_artifacts) for record in records)
    multi_location_project_count = sum(bool(record.published_artifacts) for record in records)

    lines = [
        "# Publication Records",
        "",
        "This file is **generated**. Do not edit by hand.",
        "",
        "Local source fields come from `infrastructure.project.public_scope`, each public exemplar's "
        "`manuscript/config.yaml`, `CITATION.cff`, and `.zenodo.json`. GitHub and Zenodo columns are "
        f"from public APIs when the generator runs with `--refresh-external` ({external_text}).",
        "Additional publication locations are source-owned declarations from "
        "`publication.published_artifacts`; they are indexed here but are not independently live-checked.",
        "",
        "Regenerate:",
        "",
        "```bash",
        "uv run python scripts/docgen/publication_records.py --refresh-external",
        "```",
        "",
        "## Coverage Summary",
        "",
        f"- Public exemplars indexed: **{record_count}**.",
        f"- Standalone guides present: **{standalone_count}/{record_count}**.",
        f"- Standalone GitHub repositories declared: **{github_count}/{record_count}**.",
        f"- Concept and version DOI pairs declared: **{doi_pair_count}/{record_count}**.",
        f"- Additional publication locations declared: **{additional_location_count}** across "
        f"**{multi_location_project_count}** exemplars.",
        "",
        "## Public Exemplar Publication Matrix",
        "",
        "| Project | Config version | Standalone guide | GitHub repo | Latest GitHub release | "
        "Concept DOI | Latest version DOI | Other locations | Zenodo version | Status |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for record in records:
        project_label = f"`{record.project_name}`"
        standalone = _markdown_link(
            "`STANDALONE.md`" if record.standalone_path.is_file() else "missing",
            _relative_link(record.standalone_path, repo_root, repo_root / "docs" / "_generated")
            if record.standalone_path.is_file()
            else "",
        )
        github = _markdown_link(record.github_display_label, record.github_display_url)
        release_label = record.github_latest_release_tag or record.github_release_status
        release = _markdown_link(release_label, record.github_latest_release_url)
        concept = _markdown_link(record.concept_doi, _doi_url(record.concept_doi))
        version = _markdown_link(record.version_doi, _doi_url(record.version_doi))
        other_locations = _published_artifact_links(record)
        status = f"{record.sidecar_status}; {record.external_status}"
        lines.append(
            "| "
            + " | ".join(
                [
                    project_label,
                    record.paper_version or "n/a",
                    standalone,
                    github,
                    release,
                    concept,
                    version,
                    other_locations,
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
            "| Project | Standalone guide | Config | Citation | Zenodo metadata | CodeMeta |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for record in records:
        standalone_link = _markdown_link(
            "`STANDALONE.md`" if record.standalone_path.is_file() else "missing",
            _relative_link(record.standalone_path, repo_root, repo_root / "docs" / "_generated")
            if record.standalone_path.is_file()
            else "",
        )
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
        codemeta_link = _markdown_link(
            "`codemeta.json`" if record.codemeta_path.is_file() else "missing",
            _relative_link(record.codemeta_path, repo_root, repo_root / "docs" / "_generated")
            if record.codemeta_path.is_file()
            else "",
        )
        lines.append(
            f"| `{record.project_name}` | {standalone_link} | {config_link} | "
            f"{citation_link} | {zenodo_link} | {codemeta_link} |"
        )

    lines.extend(
        [
            "",
            "## DOI Roles",
            "",
            "- `publication.doi` is the stable Zenodo concept DOI used for citations and PDF cover pages.",
            "- `publication.version_doi` is the latest immutable Zenodo deposit DOI.",
            "- `publication.version_record` points at the latest immutable Zenodo record page.",
            "- `publication.github_repository` is the standalone public GitHub repository for the exemplar.",
            "- `STANDALONE.md` documents what works outside the monorepo and what still requires "
            "shared infrastructure.",
            "- `publication.published_artifacts` records additional durable locations such as OSF, Software Heritage, "
            "Hugging Face, IPFS, package indexes, and static sites; an absent entry is not treated as published.",
            "",
        ]
    )
    return "\n".join(lines)


def render_github_readme_publication_block(records: list[PublicationRecord]) -> str:
    """Render the generated publication table block for ``.github/README.md``."""
    lines = [
        README_BLOCK_BEGIN,
        "<!-- This block is generated by scripts/docgen/publication_records.py. Do not hand-edit. -->",
        "",
        "| Exemplar | Config version | Standalone guide | GitHub | Latest release | "
        "Zenodo concept DOI | Latest version DOI | Other locations |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for record in records:
        project = _markdown_link(f"`{record.project_name}`", f"../projects/{record.project_name}/")
        standalone = _markdown_link(
            "guide" if record.standalone_path.is_file() else "missing",
            f"../projects/{record.project_name}/STANDALONE.md" if record.standalone_path.is_file() else "",
        )
        github = _markdown_link(record.github_display_label, record.github_display_url)
        release_label = record.github_latest_release_tag or record.github_release_status
        release = _markdown_link(release_label, record.github_latest_release_url)
        concept = _markdown_link(record.concept_doi, _doi_url(record.concept_doi))
        version = _markdown_link(record.version_doi, _doi_url(record.version_doi))
        other_locations = _published_artifact_links(record)
        lines.append(
            f"| {project} | {record.paper_version or 'n/a'} | {standalone} | {github} | {release} | "
            f"{concept} | {version} | {other_locations} |"
        )
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


def _markdown_table_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        if not line.startswith("| "):
            continue
        columns = [column.strip() for column in line.strip().strip("|").split("|")]
        if not columns or all(set(column) <= {"-", " "} for column in columns):
            continue
        rows.append(columns)
    return rows


def _project_label_from_cell(cell: str) -> str:
    match = re.search(r"`([^`]+)`", cell)
    return match.group(1) if match else cell.strip()


def _publication_matrix_source_rows(text: str) -> dict[str, tuple[str, str, str, str, str, str]]:
    rows: dict[str, tuple[str, str, str, str, str, str]] = {}
    for columns in _markdown_table_rows(text):
        if len(columns) < 10:
            continue
        project_name = _project_label_from_cell(columns[0])
        if not project_name.startswith("templates/"):
            continue
        rows[project_name] = (columns[1], columns[2], columns[3], columns[5], columns[6], columns[7])
    return rows


def _local_source_path_rows(text: str) -> dict[str, tuple[str, str, str, str, str]]:
    rows: dict[str, tuple[str, str, str, str, str]] = {}
    for columns in _markdown_table_rows(text):
        if len(columns) != 6:
            continue
        project_name = _project_label_from_cell(columns[0])
        if not project_name.startswith("templates/") or "manuscript/config.yaml" not in columns[2]:
            continue
        rows[project_name] = (columns[1], columns[2], columns[3], columns[4], columns[5])
    return rows


def _github_readme_source_rows(text: str) -> dict[str, tuple[str, str, str, str, str, str]]:
    rows: dict[str, tuple[str, str, str, str, str, str]] = {}
    match = re.search(
        re.escape(README_BLOCK_BEGIN) + r"(?P<block>.*?)" + re.escape(README_BLOCK_END),
        text,
        flags=re.DOTALL,
    )
    if not match:
        return rows
    for columns in _markdown_table_rows(match.group("block")):
        if len(columns) < 8:
            continue
        project_name = _project_label_from_cell(columns[0])
        if not project_name.startswith("templates/"):
            continue
        rows[project_name] = (columns[1], columns[2], columns[3], columns[5], columns[6], columns[7])
    return rows


def _row_map_differences(
    label: str,
    current: Mapping[str, tuple[str, ...]],
    expected: Mapping[str, tuple[str, ...]],
) -> list[str]:
    differences: list[str] = []
    if current == expected:
        return differences
    missing = sorted(set(expected) - set(current))
    extra = sorted(set(current) - set(expected))
    changed = sorted(name for name in set(current) & set(expected) if current[name] != expected[name])
    details = []
    if missing:
        details.append(f"missing={missing}")
    if extra:
        details.append(f"extra={extra}")
    if changed:
        details.append(f"changed={changed}")
    differences.append(f"{label} drifted: {' '.join(details)}")
    return differences


def check_publication_records_doc(
    repo_root: Path,
    *,
    refresh_external: bool = False,
    update_github_readme: bool = True,
) -> list[str]:
    """Check publication records doc."""
    repo_root = Path(repo_root).resolve()
    records = load_publication_records(repo_root)
    if refresh_external:
        refresh_external_records(records)

    expected_doc = render_publication_records_doc(repo_root, records, refreshed_external=refresh_external)
    doc_path = repo_root / "docs" / "_generated" / "publication_records.md"
    if not doc_path.is_file():
        return [f"missing {doc_path.relative_to(repo_root)}"]

    differences: list[str] = []
    current_doc = doc_path.read_text(encoding="utf-8")
    differences.extend(
        _row_map_differences(
            "publication_records.md source-owned matrix columns",
            _publication_matrix_source_rows(current_doc),
            _publication_matrix_source_rows(expected_doc),
        )
    )
    differences.extend(
        _row_map_differences(
            "publication_records.md local source paths",
            _local_source_path_rows(current_doc),
            _local_source_path_rows(expected_doc),
        )
    )

    if update_github_readme:
        readme_path = repo_root / ".github" / "README.md"
        if not readme_path.is_file():
            differences.append(f"missing {readme_path.relative_to(repo_root)}")
        else:
            expected_readme = replace_github_readme_publication_block(
                readme_path.read_text(encoding="utf-8"),
                render_github_readme_publication_block(records),
            )
            differences.extend(
                _row_map_differences(
                    ".github/README.md publication block source-owned columns",
                    _github_readme_source_rows(readme_path.read_text(encoding="utf-8")),
                    _github_readme_source_rows(expected_readme),
                )
            )
    stale_standalone = [
        record.project_name
        for record in records
        if not record.standalone_path.is_file()
        or extract_standalone_publication_block(record.standalone_path.read_text(encoding="utf-8"))
        != render_standalone_publication_block(record)
    ]
    if stale_standalone:
        differences.append(f"standalone publication identity blocks drifted: {stale_standalone}")
    return differences


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

    for record in records:
        if not record.standalone_path.is_file():
            continue
        current = record.standalone_path.read_text(encoding="utf-8")
        record.standalone_path.write_text(
            replace_standalone_publication_block(current, render_standalone_publication_block(record)),
            encoding="utf-8",
        )

    return out_path, readme_path
