"""Publication-metadata drift checks for canonical exemplars."""

from __future__ import annotations

import json
import re
from pathlib import Path

try:
    import tomllib
except ImportError:  # Python <3.11 — use backport
    import tomli as tomllib  # type: ignore[no-redef]

import yaml

from infrastructure.core.files.serialization import load_yaml_mapping as _load_yaml_mapping
from infrastructure.core.files.serialization import relative_or_self as _rel
from infrastructure.project.drift.checks_publication_validators import (
    _PLACEHOLDER_AUTHOR_NAMES,
    _ZENODO_DOI_RE,
    _as_mapping,
    _author_rows,
    _cff_author_names,
    _fold_name,
    _is_canonical_template,
    _is_http_url,
    _normalize_doi,
    _read,
    _version_key,
    _zenodo_concept_identifier,
    check_config_author_placeholders,
    check_publishing_status_block_current,
)
from infrastructure.project.drift.models import Report

__all__ = (
    "check_config_author_placeholders",
    "check_license_file_present_and_consistent",
    "check_metadata_export_current",
    "check_publication_index_completeness",
    "check_publication_metadata_consistency",
    "check_publishing_status_block_current",
    "check_pyproject_publication_consistency",
    "check_repository_url_consistent",
)


def check_publication_index_completeness(project_root: Path, report: Report, project: str) -> None:
    """Require complete publication identity for every canonical public template.

    Additional publication locations remain optional, but declarations must be
    named HTTP(S) URLs supported by the publishing registry.
    """
    if not _is_canonical_template(project):
        return

    config_path = project_root / "manuscript" / "config.yaml"
    config: dict[str, object] = {}
    if config_path.is_file():
        try:
            config = _load_yaml_mapping(config_path)
        except yaml.YAMLError:
            pass
    publication = _as_mapping(config.get("publication"))
    publication_status = str(publication.get("status") or "published").strip().lower()
    is_draft = publication_status in {"draft", "unpublished"}

    required_files: tuple[str, ...] = ("STANDALONE.md",)
    if not is_draft:
        required_files += ("CITATION.cff", ".zenodo.json", "codemeta.json")
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

    if not config_path.is_file():
        return
    if not config:
        return
    paper = _as_mapping(config.get("paper"))
    book = _as_mapping(config.get("book"))

    if is_draft:
        github_repository = str(publication.get("github_repository") or "").strip()
        repository_url = str(publication.get("repository_url") or "").strip()
        if not github_repository and not repository_url.startswith(("https://github.com/", "http://github.com/")):
            report.add(
                "ERROR",
                project,
                "publication_index_github_missing",
                f"{_rel(config_path, project_root)} draft must declare its intended GitHub repository",
            )
        return

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


def check_pyproject_publication_consistency(project_root: Path, report: Report, project: str) -> None:
    """`[project] version` / `[project] authors` in pyproject.toml must match CITATION.cff.

    Catches: on 2026-07-27 template_autopoiesis shipped `version = "0.1.0"` in
    pyproject.toml while CITATION.cff, codemeta.json, .zenodo.json and
    manuscript/config.yaml all declared 1.0.1 (the version actually deposited as
    10.5281/zenodo.21229620). It survived because the publication cross-checks
    bound config.yaml <-> CITATION.cff <-> .zenodo.json <-> codemeta.json and
    nothing in the drift package ever read pyproject.toml — yet pyproject's
    version and authors are the sole inputs to `uv build`, so the shipped wheel
    METADATA is stamped from the one file no gate was reading.

    Versions are compared as PEP 440 release tuples, so `0.1` (CITATION.cff) and
    `0.1.0` (pyproject) are equal rather than a false positive. A missing
    `[project] version`/`authors` key, or a `dynamic` declaration, is skipped:
    absence is not drift, and the placeholder-author check for absent metadata
    already lives in check_config_author_placeholders.
    """
    pyproject_path = project_root / "pyproject.toml"
    cff_path = project_root / "CITATION.cff"
    if not pyproject_path.is_file() or not cff_path.is_file():
        return

    try:
        pyproject = tomllib.loads(_read(pyproject_path))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        report.add(
            "ERROR",
            project,
            "publication_pyproject_unparseable",
            f"{_rel(pyproject_path, project_root)} is not valid TOML: {exc}",
        )
        return

    table = pyproject.get("project")
    if not isinstance(table, dict):
        return
    dynamic = table.get("dynamic")
    dynamic_fields = {str(field) for field in dynamic} if isinstance(dynamic, list) else set()

    try:
        cff = _load_yaml_mapping(cff_path)
    except (OSError, yaml.YAMLError):
        return

    cff_version = str(cff.get("version", "")).strip().strip("'\"")
    py_version = str(table.get("version", "")).strip()
    if py_version and cff_version and "version" not in dynamic_fields:
        if _version_key(py_version) != _version_key(cff_version):
            report.add(
                "ERROR",
                project,
                "publication_pyproject_version_drift",
                (
                    f"{_rel(pyproject_path, project_root)} [project] version {py_version!r} disagrees "
                    f"with CITATION.cff version {cff_version!r} — pyproject is the sole input to "
                    "`uv build`, so the published distribution would be stamped with the wrong release"
                ),
            )

    raw_authors = table.get("authors")
    if not isinstance(raw_authors, list) or "authors" in dynamic_fields:
        return
    py_names = [str(entry.get("name") or "").strip() for entry in raw_authors if isinstance(entry, dict)]
    py_names = [name for name in py_names if name]
    if not py_names:
        return

    for idx, name in enumerate(py_names):
        if _fold_name(name) in _PLACEHOLDER_AUTHOR_NAMES:
            report.add(
                "ERROR",
                project,
                "publication_pyproject_author_placeholder",
                (
                    f"{_rel(pyproject_path, project_root)} [project] authors[{idx}].name is the "
                    f"scaffold placeholder {name!r} — it rides into the built wheel's "
                    "`Author-email` metadata; replace with the real author"
                ),
            )

    cff_names = _cff_author_names(cff)
    if not cff_names:
        return
    known = {_fold_name(name) for name in cff_names}
    unknown = [name for name in py_names if _fold_name(name) not in known]
    if unknown:
        report.add(
            "ERROR",
            project,
            "publication_pyproject_author_drift",
            (
                f"{_rel(pyproject_path, project_root)} [project] authors {unknown!r} are not credited "
                f"in CITATION.cff (authors: {cff_names!r}) — the DOI record and the built distribution "
                "would attribute the same release to different people"
            ),
        )


def check_license_file_present_and_consistent(project_root: Path, report: Report, project: str) -> None:
    """Every exemplar must ship a LICENSE whose license matches its declared metadata.

    Catches: on 2026-07-27, 23 of 24 exemplars declared a license in CITATION.cff
    (and, for most, nowhere else) while shipping no LICENSE file at all. A fork
    extracted via STANDALONE.md therefore arrived with a README asserting terms
    that no file in the tree granted. `[project] license` was also absent from 21
    pyprojects, so the built wheel carried no license metadata either.

    The declared license in CITATION.cff is authoritative here: it is the surface
    the Zenodo deposits were made from, so LICENSE and pyproject are checked
    against it rather than the other way round.
    """
    cff_path = project_root / "CITATION.cff"
    if not cff_path.is_file():
        return
    try:
        cff = _load_yaml_mapping(cff_path)
    except (OSError, yaml.YAMLError):
        return
    declared = str(cff.get("license", "")).strip().strip("'\"")
    if not declared:
        return

    license_path = project_root / "LICENSE"
    if not license_path.is_file():
        report.add(
            "ERROR",
            project,
            "publication_license_file_missing",
            (
                f"CITATION.cff declares license {declared!r} but no LICENSE file exists — "
                "a standalone fork would ship terms it never grants"
            ),
        )
        return

    # Identify the shipped license by its distinctive header, not by full text.
    body = _read(license_path)
    head = "\n".join(body.splitlines()[:6]).lower()
    identifiers = {
        "MIT": "mit license",
        "Apache-2.0": "apache license",
        "CC-BY-4.0": "creative commons attribution 4.0",
    }
    marker = identifiers.get(declared)
    if marker and marker not in head:
        # Dual-licensed layout: code under one license in LICENSE, content under
        # the declared license in a LICENSE-<scope> sibling (template_textbook
        # ships Apache-2.0 code alongside CC-BY-4.0 manuscript content). Accept
        # it only when a sibling actually carries the declared license.
        siblings = sorted(project_root.glob("LICENSE-*"))
        covered = any(marker in _read(path).lower() for path in siblings if path.is_file())
        if not covered:
            report.add(
                "ERROR",
                project,
                "publication_license_file_drift",
                (
                    f"LICENSE does not look like {declared!r} (declared in CITATION.cff) and no "
                    f"LICENSE-* sibling carries it either; LICENSE opens with "
                    f"{head.splitlines()[0].strip()!r}"
                ),
            )

    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.is_file():
        return
    try:
        table = tomllib.loads(_read(pyproject_path)).get("project")
    except (OSError, tomllib.TOMLDecodeError):
        return
    if not isinstance(table, dict):
        return
    raw = table.get("license")
    declared_py = raw.get("text", "") if isinstance(raw, dict) else (raw or "")
    declared_py = str(declared_py).strip()
    if declared_py and declared_py != declared:
        report.add(
            "ERROR",
            project,
            "publication_license_metadata_drift",
            (
                f"pyproject [project] license {declared_py!r} disagrees with CITATION.cff "
                f"license {declared!r} — the wheel and the DOI record would state different terms"
            ),
        )


def check_publication_metadata_consistency(project_root: Path, report: Report, project: str) -> None:
    """Cross-check publication.doi, version_doi, pyproject.toml, CITATION.cff, and .zenodo.json."""
    # Runs first and unconditionally: pyproject.toml <-> CITATION.cff drift is
    # real for draft exemplars too, and this function returns early for a draft
    # publication status and for a project with no manuscript/config.yaml.
    check_pyproject_publication_consistency(project_root, report, project)

    config_path = project_root / "manuscript" / "config.yaml"
    if not config_path.is_file():
        return

    config = _load_yaml_mapping(config_path)
    paper = _as_mapping(config.get("paper"))
    publication = _as_mapping(config.get("publication"))
    if str(publication.get("status") or "published").strip().lower() in {
        "draft",
        "unpublished",
    }:
        return
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


def check_repository_url_consistent(project_root: Path, report: Report, project: str) -> None:
    """Tracked sidecars must name the exemplar's own standalone repository.

    Catches: on 2026-07-27 ``template_advanced_literature_review`` shipped
    ``repository-code: https://github.com/docxology/template`` — the MONOREPO —
    in its tracked ``CITATION.cff`` and ``codemeta.json``, while its own
    ``config.yaml`` correctly named ``docxology/template_advanced_literature_review``
    in four places. GitHub renders CITATION.cff live and Zenodo ingests this
    metadata, so the published citation pointed readers at the wrong repository.

    ``check_metadata_export_current`` did not catch it because that check
    deliberately projects only authorship and concept-DOI fields, leaving the
    repository URL unbound to its source.
    """
    config_path = project_root / "manuscript" / "config.yaml"
    if not config_path.is_file():
        return
    try:
        config = _load_yaml_mapping(config_path, strict=True)
    except (OSError, yaml.YAMLError):
        return

    from infrastructure.publishing.repository_metadata import normalized_repository_url

    publication = config.get("publication")
    expected = normalized_repository_url(publication if isinstance(publication, dict) else None)
    if not expected:
        return
    expected = expected.rstrip("/")

    cff_path = project_root / "CITATION.cff"
    if cff_path.is_file():
        try:
            cff = _load_yaml_mapping(cff_path)
        except (OSError, yaml.YAMLError):
            cff = {}
        actual = str(cff.get("repository-code", "")).strip().rstrip("/")
        if actual and actual != expected:
            report.add(
                "ERROR",
                project,
                "publication_repository_url_drift",
                (
                    f"CITATION.cff repository-code {actual!r} does not match the repository declared "
                    f"in manuscript/config.yaml ({expected!r}) — GitHub renders this file as the "
                    "citation, so readers would be sent to the wrong repository"
                ),
            )

    codemeta_path = project_root / "codemeta.json"
    if codemeta_path.is_file():
        try:
            codemeta = json.loads(_read(codemeta_path))
        except (OSError, json.JSONDecodeError):
            codemeta = {}
        actual = str(codemeta.get("codeRepository", "")).strip().rstrip("/") if isinstance(codemeta, dict) else ""
        if actual and actual != expected:
            report.add(
                "ERROR",
                project,
                "publication_repository_url_drift",
                (
                    f"codemeta.json codeRepository {actual!r} does not match the repository declared "
                    f"in manuscript/config.yaml ({expected!r})"
                ),
            )


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
        config = _load_yaml_mapping(config_path, strict=True)
    except (OSError, yaml.YAMLError) as exc:
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
                _load_yaml_mapping(path, strict=True)
                if rel_name == "CITATION.cff"
                else json.loads(path.read_text(encoding="utf-8"))
            )
        except (OSError, yaml.YAMLError, json.JSONDecodeError) as exc:
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
