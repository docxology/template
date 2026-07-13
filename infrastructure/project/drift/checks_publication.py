"""Publication-metadata drift checks for canonical exemplars."""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

import yaml

from infrastructure.core.files.serialization import load_yaml_mapping as _load_yaml_mapping
from infrastructure.core.files.serialization import relative_or_self as _rel
from infrastructure.project.drift.models import Report


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


_ZENODO_DOI_RE = re.compile(r"^10\.5281/zenodo\.\d+$")


def _is_canonical_template(project: str) -> bool:
    return project.startswith("templates/template_") and "/" not in project.removeprefix("templates/")


def _is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def check_publication_index_completeness(project_root: Path, report: Report, project: str) -> None:
    """Require complete publication identity for every canonical public template.

    Additional publication locations remain optional, but declarations must be
    named HTTP(S) URLs supported by the publishing registry.
    """
    if not _is_canonical_template(project):
        return

    required_files = ("STANDALONE.md", "CITATION.cff", ".zenodo.json", "codemeta.json")
    for rel_name in required_files:
        if not (project_root / rel_name).is_file():
            report.add(
                "ERROR",
                project,
                "publication_index_file_missing",
                f"{project}/{rel_name} is required for the public exemplar publication index",
            )

    standalone_path = project_root / "STANDALONE.md"
    if standalone_path.is_file():
        from infrastructure.documentation.publication_standalone import (
            STANDALONE_BLOCK_BEGIN,
            STANDALONE_BLOCK_END,
        )

        standalone = _read(standalone_path)
        if STANDALONE_BLOCK_BEGIN not in standalone or STANDALONE_BLOCK_END not in standalone:
            report.add(
                "ERROR",
                project,
                "publication_index_block_missing",
                (
                    f"{project}/STANDALONE.md lacks the generated publication identity block — "
                    "run `uv run python scripts/docgen/publication_records.py`"
                ),
            )

    config_path = project_root / "manuscript" / "config.yaml"
    if not config_path.is_file():
        return
    try:
        config = _load_yaml_mapping(config_path)
    except yaml.YAMLError:
        return
    publication = config.get("publication", {}) if isinstance(config.get("publication"), dict) else {}
    paper = config.get("paper", {}) if isinstance(config.get("paper"), dict) else {}
    book = config.get("book", {}) if isinstance(config.get("book"), dict) else {}

    required_values = {
        "publication.doi": _normalize_doi(publication.get("doi")),
        "publication.version_doi": _normalize_doi(publication.get("version_doi")),
        "publication.version_record": str(publication.get("version_record") or "").strip(),
        "work version": str(paper.get("version") or book.get("version") or "").strip(),
    }
    for field, value in required_values.items():
        if not value:
            report.add(
                "ERROR",
                project,
                "publication_index_value_missing",
                f"{_rel(config_path, project_root)} must declare {field} for a canonical public exemplar",
            )

    version_record = required_values["publication.version_record"]
    if version_record and not _is_http_url(version_record):
        report.add(
            "ERROR",
            project,
            "publication_index_url_invalid",
            f"{_rel(config_path, project_root)} publication.version_record is not an HTTP(S) URL: {version_record!r}",
        )

    github_repository = str(publication.get("github_repository") or "").strip()
    repository_url = str(publication.get("repository_url") or "").strip()
    github_url = repository_url.startswith(("https://github.com/", "http://github.com/"))
    if not github_repository and not github_url:
        report.add(
            "ERROR",
            project,
            "publication_index_github_missing",
            (
                f"{_rel(config_path, project_root)} must declare publication.github_repository "
                "or a github.com publication.repository_url"
            ),
        )
    elif github_repository and not re.fullmatch(r"[^/\s]+/[^/\s]+", github_repository):
        report.add(
            "ERROR",
            project,
            "publication_index_github_invalid",
            f"publication.github_repository must use owner/repository form, got {github_repository!r}",
        )

    artifacts = publication.get("published_artifacts")
    if artifacts is None:
        return
    if not isinstance(artifacts, dict):
        report.add(
            "ERROR",
            project,
            "publication_index_artifacts_invalid",
            "publication.published_artifacts must be a platform-to-URL mapping",
        )
        return

    from infrastructure.publishing.registry import PLATFORM_REGISTRY

    known_platforms = {entry.name for entry in PLATFORM_REGISTRY}
    for platform, raw_url in artifacts.items():
        platform_name = str(platform).strip()
        url = str(raw_url or "").strip()
        if platform_name not in known_platforms:
            report.add(
                "ERROR",
                project,
                "publication_index_platform_unknown",
                f"publication.published_artifacts uses unknown platform {platform_name!r}",
            )
        if not _is_http_url(url):
            report.add(
                "ERROR",
                project,
                "publication_index_url_invalid",
                f"publication.published_artifacts.{platform_name} is not an HTTP(S) URL: {url!r}",
            )


def _normalize_doi(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower().startswith("https://doi.org/"):
        return text[len("https://doi.org/") :]
    return text


def check_publication_metadata_consistency(project_root: Path, report: Report, project: str) -> None:
    """Cross-check publication.doi, version_doi, CITATION.cff, and .zenodo.json."""
    config_path = project_root / "manuscript" / "config.yaml"
    if not config_path.is_file():
        return

    config = _load_yaml_mapping(config_path)
    paper = config.get("paper", {}) if isinstance(config.get("paper"), dict) else {}
    publication = config.get("publication", {}) if isinstance(config.get("publication"), dict) else {}
    paper_version = str(paper.get("version", "")).strip()

    concept_doi = _normalize_doi(publication.get("doi", ""))
    version_doi = _normalize_doi(publication.get("version_doi", ""))
    version_record = str(publication.get("version_record", "")).strip()

    if concept_doi and not _ZENODO_DOI_RE.match(concept_doi):
        report.add(
            "WARNING",
            project,
            "publication_doi_format",
            f"{_rel(config_path, project_root)} publication.doi is not a Zenodo DOI: {concept_doi!r}",
        )

    if version_doi:
        if not _ZENODO_DOI_RE.match(version_doi):
            report.add(
                "WARNING",
                project,
                "publication_version_doi_format",
                f"{_rel(config_path, project_root)} publication.version_doi is not a Zenodo DOI: {version_doi!r}",
            )
        if concept_doi and concept_doi == version_doi:
            report.add(
                "ERROR",
                project,
                "publication_split_doi_collision",
                (
                    f"{_rel(config_path, project_root)} publication.doi equals publication.version_doi "
                    "— use concept DOI in doi and latest deposit in version_doi"
                ),
            )
        if not version_record:
            report.add(
                "WARNING",
                project,
                "publication_version_record_missing",
                f"{_rel(config_path, project_root)} has version_doi but no version_record URL",
            )
    elif concept_doi:
        report.add(
            "WARNING",
            project,
            "publication_split_doi_missing",
            (
                f"{_rel(config_path, project_root)} has publication.doi but no version_doi — "
                "adopt split layout per docs/guides/zenodo-doi-strategy.md"
            ),
        )

    cff_path = project_root / "CITATION.cff"
    cff_version = ""
    if cff_path.is_file():
        cff = _load_yaml_mapping(cff_path)
        cff_version = str(cff.get("version", "")).strip().strip("'\"")
        cff_doi = _normalize_doi(cff.get("doi", ""))
        if paper_version and cff_version and paper_version != cff_version:
            report.add(
                "ERROR",
                project,
                "publication_cff_version_drift",
                (f"paper.version {paper_version!r} in config.yaml disagrees with CITATION.cff version {cff_version!r}"),
            )
        if concept_doi and cff_doi and concept_doi != cff_doi:
            report.add(
                "ERROR",
                project,
                "publication_cff_doi_drift",
                f"CITATION.cff doi {cff_doi!r} must match publication.doi concept {concept_doi!r}",
            )

    zenodo_path = project_root / ".zenodo.json"
    if zenodo_path.is_file():
        try:
            zenodo = json.loads(zenodo_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            report.add(
                "ERROR",
                project,
                "publication_zenodo_json_invalid",
                f"{_rel(zenodo_path, project_root)} is not valid JSON",
            )
            return
        zenodo_version = str(zenodo.get("version", "")).strip()
        if zenodo_version and paper_version and zenodo_version != paper_version:
            report.add(
                "ERROR",
                project,
                "publication_zenodo_version_drift",
                (f"paper.version {paper_version!r} disagrees with .zenodo.json version {zenodo_version!r}"),
            )
        # Schema-agnostic: CITATION.cff and .zenodo.json must agree on version
        # (catches book-schema exemplars where paper.version is absent).
        if cff_version and zenodo_version and cff_version != zenodo_version:
            report.add(
                "ERROR",
                project,
                "publication_cff_zenodo_version_drift",
                (f"CITATION.cff version {cff_version!r} disagrees with .zenodo.json version {zenodo_version!r}"),
            )
        # Comprehensive DOI cross-referencing: when a concept DOI is declared,
        # .zenodo.json must point back to it via related_identifiers isVersionOf.
        if concept_doi:
            related = zenodo.get("related_identifiers")
            related = related if isinstance(related, list) else []
            has_concept_xlink = any(
                isinstance(entry, dict)
                and str(entry.get("relation", "")).strip() == "isVersionOf"
                and _normalize_doi(entry.get("identifier")) == concept_doi
                for entry in related
            )
            if not has_concept_xlink:
                report.add(
                    "ERROR",
                    project,
                    "publication_zenodo_missing_concept_xlink",
                    (
                        f"{_rel(zenodo_path, project_root)} lacks a related_identifiers "
                        f"isVersionOf entry for concept DOI {concept_doi!r} — Zenodo deposit "
                        "must cross-reference the concept DOI (see docs/guides/zenodo-doi-strategy.md)"
                    ),
                )


def _normalize_orcid(value: object) -> str:
    """Strip an orcid.org URL prefix so bare and URL ORCID forms compare equal.

    CFF files historically carry `https://orcid.org/0000-...` while the current
    generator emits the bare identifier; both name the same person and must not
    read as authorship drift. Handles http/https schemes, an optional `www.`
    host prefix, and a trailing slash.
    """
    original = str(value or "").strip()
    text = original.rstrip("/")
    lowered = text.lower()
    for prefix in ("https://", "http://"):
        if lowered.startswith(prefix):
            text = text[len(prefix) :]
            lowered = lowered[len(prefix) :]
            break
    for host in ("www.orcid.org/", "orcid.org/"):
        if lowered.startswith(host):
            return text[len(host) :]
    return original


def _author_rows(entries: object, keys: tuple[str, ...]) -> list[tuple[str, ...]]:
    """Project an authors/creators list onto stripped, ORCID-normalized string tuples."""
    rows: list[tuple[str, ...]] = []
    if not isinstance(entries, list):
        return rows
    for entry in entries:
        if isinstance(entry, dict):
            rows.append(tuple(_normalize_orcid(str(entry.get(key) or "").strip()) for key in keys))
    return rows


def _zenodo_concept_identifier(payload: object) -> str:
    """Return the normalized isVersionOf DOI from a .zenodo.json-shaped mapping."""
    related = payload.get("related_identifiers") if isinstance(payload, dict) else None
    if not isinstance(related, list):
        return ""
    for entry in related:
        if isinstance(entry, dict) and str(entry.get("relation", "")).strip() == "isVersionOf":
            return _normalize_doi(entry.get("identifier"))
    return ""


def check_metadata_export_current(project_root: Path, report: Report, project: str) -> None:
    """Tracked CITATION.cff / .zenodo.json / codemeta.json must agree with
    manuscript/config.yaml on authorship (names, ORCIDs) and concept DOI.

    Catches: on 2026-07-10 five exemplars shipped the scaffold
    "Research Template Author" (one with a fabricated ORCID) in these
    config-DERIVED files after config.yaml itself had been corrected —
    GitHub renders CITATION.cff live and Zenodo ingests .zenodo.json, and
    no gate bound the derived files back to their source (a cross-vendor
    audit caught it, not the gate suite). Expected values are re-derived
    with the generator itself (infrastructure.publishing.metadata_export),
    projecting only authorship and concept-DOI fields so version/date
    churn — covered by check_publication_metadata_consistency — never
    false-fires here.
    """
    config_path = project_root / "manuscript" / "config.yaml"
    targets = ("CITATION.cff", ".zenodo.json", "codemeta.json")
    if not config_path.is_file() or not any((project_root / name).is_file() for name in targets):
        return

    from infrastructure.publishing.metadata_export import (
        build_citation_cff,
        build_codemeta,
        build_zenodo,
    )

    regen_hint = (
        "regenerate with `uv run python -m infrastructure.publishing.metadata_export_cli "
        f"metadata-export --project {project}`"
    )

    try:
        config = _load_yaml_mapping(config_path)
    except yaml.YAMLError as exc:
        report.add(
            "ERROR",
            project,
            "metadata_export_config_unparseable",
            f"{_rel(config_path, project_root)} is not valid YAML — cannot derive expected metadata: {exc}",
        )
        return

    specs: tuple[tuple[str, dict[str, object], str, tuple[str, ...], str | None], ...] = (
        (
            "CITATION.cff",
            yaml.safe_load(build_citation_cff(config)) or {},
            "authors",
            ("family-names", "given-names", "orcid"),
            "doi",
        ),
        (".zenodo.json", build_zenodo(config), "creators", ("name", "orcid"), None),
        ("codemeta.json", build_codemeta(config), "author", ("familyName", "givenName", "@id"), "identifier"),
    )
    for rel_name, expected, authors_key, author_keys, doi_key in specs:
        path = project_root / rel_name
        if not path.is_file():
            continue
        try:
            loaded: object = (
                _load_yaml_mapping(path) if rel_name == "CITATION.cff" else json.loads(path.read_text(encoding="utf-8"))
            )
        except (yaml.YAMLError, json.JSONDecodeError) as exc:
            report.add(
                "ERROR",
                project,
                "metadata_export_unparseable",
                f"{rel_name} cannot be parsed ({exc}) — {regen_hint}",
            )
            continue
        actual: dict[str, object] = loaded if isinstance(loaded, dict) else {}

        expected_authors = _author_rows(expected.get(authors_key), author_keys)
        actual_authors = _author_rows(actual.get(authors_key), author_keys)
        if expected_authors != actual_authors:
            report.add(
                "ERROR",
                project,
                "metadata_export_author_drift",
                (
                    f"{rel_name} {authors_key} {actual_authors} disagree with manuscript/config.yaml "
                    f"authorship {expected_authors} — {regen_hint}"
                ),
            )

        if doi_key is None:
            expected_doi = _zenodo_concept_identifier(expected)
            actual_doi = _zenodo_concept_identifier(actual)
        else:
            expected_doi = _normalize_doi(expected.get(doi_key, ""))
            actual_doi = _normalize_doi(actual.get(doi_key, ""))
        if expected_doi != actual_doi:
            report.add(
                "ERROR",
                project,
                "metadata_export_doi_drift",
                (
                    f"{rel_name} concept DOI {actual_doi!r} disagrees with manuscript/config.yaml "
                    f"concept DOI {expected_doi!r} — {regen_hint}"
                ),
            )


_PLACEHOLDER_AUTHOR_NAMES = frozenset({"research template author", "project author", "your name"})
_PLACEHOLDER_ORCIDS = frozenset({"0000-0000-0000-0000", "0000-0000-0000-1234"})
_KNOWN_AUTHOR_KEYS = frozenset({"name", "orcid", "email", "affiliation", "corresponding"})


def check_config_author_placeholders(project_root: Path, report: Report, project: str) -> None:
    """Scaffold authorship in manuscript/config.yaml must not ride into derived metadata.

    The export-consistency checks bind derived CITATION.cff/.zenodo.json/codemeta.json
    back to config.yaml, so a placeholder author in config.yaml ITSELF passes them
    green — the derived files faithfully agree with the bad source. This check
    inspects the source of truth directly. Scoped to manuscript/config.yaml only;
    config.yaml.example is expected to hold placeholders and is never scanned.
    """
    config_path = project_root / "manuscript" / "config.yaml"
    if not config_path.is_file():
        return
    config = _load_yaml_mapping(config_path)
    raw_authors = config.get("authors")
    authors = [entry for entry in raw_authors if isinstance(entry, dict)] if isinstance(raw_authors, list) else []

    if not authors:
        publication = config.get("publication", {}) if isinstance(config.get("publication"), dict) else {}
        if _normalize_doi(publication.get("doi", "")):
            report.add(
                "WARNING",
                project,
                "config_authors_missing_with_doi",
                (
                    f"{_rel(config_path, project_root)} declares publication.doi but has no authors block — "
                    "metadata export falls back to the 'Project Author' placeholder, which would ride "
                    "into a real Zenodo deposit"
                ),
            )
        return

    for idx, author in enumerate(authors):
        name = str(author.get("name", "")).strip()
        if " ".join(name.lower().split()) in _PLACEHOLDER_AUTHOR_NAMES:
            report.add(
                "ERROR",
                project,
                "config_author_placeholder_name",
                (
                    f"{_rel(config_path, project_root)} authors[{idx}].name is the scaffold "
                    f"placeholder {name!r} — replace with a real author before publication"
                ),
            )
        orcid = _normalize_orcid(author.get("orcid"))
        if orcid in _PLACEHOLDER_ORCIDS:
            report.add(
                "ERROR",
                project,
                "config_author_placeholder_orcid",
                (
                    f"{_rel(config_path, project_root)} authors[{idx}].orcid is the example "
                    f"value {orcid!r} — replace with the author's real ORCID or remove the key"
                ),
            )
        unknown_keys = sorted(str(key) for key in author if str(key) not in _KNOWN_AUTHOR_KEYS)
        if unknown_keys:
            report.add(
                "ERROR",
                project,
                "config_author_unknown_keys",
                (
                    f"{_rel(config_path, project_root)} authors[{idx}] has unrecognized key(s) "
                    f"{unknown_keys} — the metadata generator silently ignores keys outside "
                    f"{sorted(_KNOWN_AUTHOR_KEYS)} (a plural 'affiliations:' once dropped an "
                    "affiliation from public metadata)"
                ),
            )


def check_publishing_status_block_current(project_root: Path, report: Report, project: str) -> None:
    """README's generated `PUBLISHING-STATUS` block must exist and be in sync.

    `infrastructure.publishing.status_report` compiles `manuscript/config.yaml`
    + the platform registry into a marker-delimited block; this check is the
    enforcement that makes that surfacing durable rather than a one-time edit
    that silently drifts the next time `config.yaml` changes.
    """
    config_path = project_root / "manuscript" / "config.yaml"
    if not config_path.is_file():
        return
    readme_path = project_root / "README.md"
    if not readme_path.is_file():
        return

    from infrastructure.publishing.status_report import (
        BLOCK_START,
        compile_publishing_status,
        status_report_is_current,
    )

    readme_text = _read(readme_path)
    if BLOCK_START not in readme_text:
        report.add(
            "WARNING",
            project,
            "publishing_status_block_missing",
            (
                f"{project}/README.md has no PUBLISHING-STATUS block — run "
                "`uv run python -m infrastructure.publishing.status_report "
                f"--project projects/{project} --write "
                '--init-after "## Publication and rendering"` to surface the '
                "cross-platform publishing surface (see docs/guides/publishing-guide.md)."
            ),
        )
        return

    try:
        compiled = compile_publishing_status(project_root)
    except yaml.YAMLError as exc:
        report.add(
            "ERROR",
            project,
            "publishing_status_config_unparseable",
            f"{_rel(config_path, project_root)} is not valid YAML — cannot compile publishing status: {exc}",
        )
        return

    if not status_report_is_current(readme_text, compiled):
        report.add(
            "WARNING",
            project,
            "publishing_status_block_stale",
            (
                f"{project}/README.md PUBLISHING-STATUS block is out of sync with manuscript/config.yaml — "
                "regenerate with `uv run python -m infrastructure.publishing.status_report "
                f"--project projects/{project} --write`."
            ),
        )
