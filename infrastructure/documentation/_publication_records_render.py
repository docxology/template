"""Render generated publication-record documentation."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from infrastructure.documentation._publication_records_types import (
    PublicationRecord,
    README_BLOCK_BEGIN,
    README_BLOCK_END,
    _doi_url,
)


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
