"""Load publication records from public project configs and sidecars."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from infrastructure.core.files.serialization import load_yaml_mapping as _load_yaml_mapping
from infrastructure.documentation._publication_records_types import PublicationRecord
from infrastructure.project.public_scope import public_project_names
from infrastructure.publishing.repository_metadata import normalized_repository_url


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
