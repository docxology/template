"""Project-level template drift checks for canonical exemplars."""

from __future__ import annotations

import json
import re

try:
    import tomllib
except ImportError:  # Python <3.11 — use backport
    import tomli as tomllib  # type: ignore[no-redef]
from pathlib import Path

import yaml

from infrastructure.core.files.serialization import load_yaml_mapping as _load_yaml_mapping
from infrastructure.core.files.serialization import relative_or_self as _rel
from infrastructure.project.drift.models import Report
from infrastructure.validation.output.no_mock_enforcer import validate_no_mocks


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _find_check_function_names(pipeline_py: Path) -> set[str]:
    """Return the actual `_check_*` function names declared in a pipeline module."""
    pat = re.compile(r"^def (_check_[A-Za-z0-9_]+)\s*\(", re.MULTILINE)
    return set(pat.findall(_read(pipeline_py)))


def _doc_check_function_refs(docs_dir: Path) -> dict[str, list[Path]]:
    """Return `{func_name: [doc paths that mention it]}` for every `_check_*` ref in docs."""
    refs: dict[str, list[Path]] = {}
    if not docs_dir.is_dir():
        return refs
    pat = re.compile(r"`(_check_[A-Za-z0-9_]+)`")
    for md in docs_dir.rglob("*.md"):
        for name in pat.findall(_read(md)):
            refs.setdefault(name, []).append(md)
    return refs


def check_function_name_drift(project_root: Path, report: Report, project: str) -> None:
    """Every `_check_<name>` referenced in docs must exist in the pipeline checks source.

    Catches: 4-doc drift in template_prose_project where docs referenced
    `_check_headings` / `_check_bibliography_consistency` — neither function
    exists in the pipeline checks source.
    """
    candidates = (
        project_root / "src" / "pipeline" / "checks.py",
        project_root / "src" / "pipeline.py",
    )
    pipeline = next((candidate for candidate in candidates if candidate.exists()), None)
    if pipeline is None:
        return  # e.g. template_code_project has no configured prose-check pipeline — N/A
    real_names = _find_check_function_names(pipeline)
    doc_refs = _doc_check_function_refs(project_root / "docs")
    for name, paths in doc_refs.items():
        if name not in real_names:
            for p in paths:
                report.add(
                    "ERROR",
                    project,
                    "function_name_drift",
                    (
                        f"docs reference `{name}` but {_rel(pipeline, project_root)} "
                        f"has {sorted(real_names)}; in {_rel(p, project_root)}"
                    ),
                )


def check_coverage_floor_consistency(project_root: Path, report: Report, project: str) -> None:
    """All docs referencing a `fail_under = N` value must match pyproject.toml.

    Catches: template_prose_project had `fail_under = 70` claimed in 2 docs
    while the actual pyproject.toml was `fail_under = 90`.
    """
    pyproject = project_root / "pyproject.toml"
    if not pyproject.exists():
        return
    data = tomllib.loads(_read(pyproject))
    actual = data.get("tool", {}).get("coverage", {}).get("report", {}).get("fail_under")
    if actual is None:
        return
    pat = re.compile(r"fail_under\s*=\s*([0-9]+)")
    for md in (project_root / "docs").rglob("*.md") if (project_root / "docs").is_dir() else []:
        for m in pat.finditer(_read(md)):
            stated = int(m.group(1))
            if stated != actual:
                report.add(
                    "ERROR",
                    project,
                    "coverage_floor_drift",
                    f"{_rel(md, project_root)} claims fail_under = {stated}; pyproject.toml has {actual}",
                )


def _strip_code_fences(text: str) -> str:
    """Remove fenced code blocks (```…```) so link/identifier scanning skips them.

    Dead-link false positives come from illustrative examples inside fenced
    code blocks (e.g., a syntax_guide.md template showing how to reference a
    hypothetical `new_figure.png` inside ``` ```). We intentionally do NOT
    strip inline code spans (`...`) because that is exactly where the
    drift detectors expect to find real identifier references — e.g.
    ``the class `TestRunProsePipeline` covers …`` — and stripping them
    would silently defeat `check_test_class_drift` and similar detectors.
    """
    return re.sub(r"```[\s\S]*?```", "", text)


def _is_example_filename(target: str) -> bool:
    """Heuristic: a path containing `<...>`, or a filename starting with
    `new_` / `my_` / `your_` / `example_`, is an illustrative example
    rather than a concrete reference."""
    if "<" in target and ">" in target:
        return True
    name = Path(target).name.lower()
    return any(name.startswith(prefix) for prefix in ("new_", "my_", "your_", "example_"))


def check_referenced_files_exist(project_root: Path, report: Report, project: str) -> None:
    """Markdown links to local files must resolve.

    Catches the prior `output/AGENTS.md` drift (referenced in 3 docs; did not
    exist) and any future stale `[...](path.md)` links inside the project.
    Scope: top-level `*.md` (AGENTS.md, README.md, ...) plus everything under
    `docs/`, `manuscript/`, and `src/`. `output/` is excluded (disposable,
    regenerated). Broadened after the projects/templates/ move regressed
    relative links in AGENTS.md/manuscript/src that the docs-only scan missed.
    Skips: links inside fenced/inline code blocks, links containing `<...>`
    placeholders, and filenames starting with `new_`/`my_`/`your_`/`example_`
    (illustrative templates, not real references).
    """
    pat = re.compile(r"\[(?P<text>[^\]]+)\]\((?P<target>[^)#\s]+(?:#[^)\s]*)?)\)")
    md_files = sorted(project_root.glob("*.md"))
    for _sub in ("docs", "manuscript", "src"):
        _sub_dir = project_root / _sub
        if _sub_dir.is_dir():
            md_files.extend(sorted(_sub_dir.rglob("*.md")))
    for md in md_files:
        text = _strip_code_fences(_read(md))
        for m in pat.finditer(text):
            target = m.group("target").split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            if _is_example_filename(target):
                continue
            # `output/` is disposable and regenerated by the pipeline (and is
            # gitignored), so manuscript figure embeds such as
            # ``![...](../output/figures/x.png)`` point at artifacts that only
            # exist after a run. On a fresh checkout (CI strict drift gate) they
            # would otherwise read as dead links. The docstring contract already
            # excludes `output/`; enforce it for link TARGETS, not just for the
            # set of scanned source files. Missing rendered figures are caught at
            # render/manuscript-validation time, not by this stale-link gate.
            if "output" in target.replace("\\", "/").split("/"):
                continue
            candidate = (md.parent / target).resolve()
            if not candidate.exists():
                report.add(
                    "WARNING",
                    project,
                    "dead_link",
                    f"{_rel(md, project_root)} → {target!r} does not resolve (looked at {candidate})",
                )


def check_no_oversize_src_files(project_root: Path, report: Report, project: str) -> None:
    """``src/**/*.py`` files should not exceed 1500 lines (modularity smell).

    Catches the analysis.py-was-1719-lines smell; the template should not
    ship single source files that exceed thinkable refactor budget.
    """
    src_dir = project_root / "src"
    if not src_dir.is_dir():
        return
    for py in src_dir.rglob("*.py"):
        with py.open("r", encoding="utf-8") as handle:
            line_count = sum(1 for _ in handle)
        if line_count > 1500:
            report.add(
                "WARNING",
                project,
                "oversize_src_file",
                f"{_rel(py, project_root)} is {line_count} lines (> 1500 — consider splitting)",
            )


def check_no_blanket_except_in_src(project_root: Path, report: Report, project: str) -> None:
    """``except Exception:`` in ``src/**/*.py`` should be rare and explicitly justified.

    Catches the CLAUDE.md-forbidden pattern of swallowing errors.
    """
    src_dir = project_root / "src"
    if not src_dir.is_dir():
        return
    pat = re.compile(r"except\s+Exception\b")
    for py in src_dir.rglob("*.py"):
        text = _read(py)
        for m in pat.finditer(text):
            # Allow if the next 200 chars contain a noqa comment OR an `(ImportError`/specific filter.
            window = text[m.start() : m.start() + 200]
            if "# noqa: BLE001" in window or "(ImportError" in window or 'Exception("' in window:
                # If the surrounding comment marks this as an intentional
                # top-level / safety-net handler, suppress the warning entirely
                # — narrowing such handlers replaces honest breadth with silent
                # gaps. Otherwise emit a "consider narrowing" hint.
                if any(
                    marker in window
                    for marker in (
                        "TOP-LEVEL MAIN SAFETY NET",
                        "safety net",
                        "final handler",
                        "top-level main",
                    )
                ):
                    continue
                rel_path = _rel(py, project_root)
                report.add(
                    "WARNING",
                    project,
                    "blanket_except_with_noqa",
                    (f"{rel_path}: `except Exception` with noqa near offset {m.start()} — narrow if possible"),
                )
            else:
                report.add(
                    "ERROR",
                    project,
                    "blanket_except",
                    f"{_rel(py, project_root)}: `except Exception` near offset {m.start()} without noqa justification",
                )


def check_mocks_absent_from_tests(project_root: Path, report: Report, project: str) -> None:
    """No mock frameworks anywhere under an exemplar's `tests/`.

    Delegates to :func:`infrastructure.validation.output.no_mock_enforcer.validate_no_mocks`
    — the same AST + comment/string-stripped scanner the repo-level
    ``verify_no_mocks`` gate uses — so the exemplar rule and the repo rule can
    never diverge. (Previously this maintained its own weaker regex that both
    missed ``from unittest import mock`` and false-positived on docstrings that
    merely mention the policy.)
    """
    tests_dir = project_root / "tests"
    if not tests_dir.is_dir():
        return
    for violation in validate_no_mocks(tests_dir, project_root):
        report.add("ERROR", project, "mock_in_tests", violation)


def _find_test_class_names(tests_dir: Path) -> set[str]:
    """Return every `class TestXxx` declared anywhere under `tests/`."""
    if not tests_dir.is_dir():
        return set()
    pat = re.compile(r"^class (Test[A-Za-z0-9_]*)\b", re.MULTILINE)
    names: set[str] = set()
    for py in tests_dir.rglob("*.py"):
        names.update(pat.findall(_read(py)))
    return names


def check_test_class_drift(project_root: Path, report: Report, project: str) -> None:
    """Every `TestXxx` named in a doc must exist under `tests/`.

    Catches the May 2026 v2-audit finding: a sibling-parity `PATTERNS.md`
    file inventoried `TestCheckGradeLevel`, `TestBibliographyConsistency`,
    `TestCheckHeadings` — none of which exist in the actual test suite.
    """
    docs_dir = project_root / "docs"
    if not docs_dir.is_dir():
        return
    # Also scan tests/PATTERNS.md and tests/AGENTS.md, which conventionally
    # inventory test classes.
    extra = [
        project_root / "tests" / "PATTERNS.md",
        project_root / "tests" / "AGENTS.md",
    ]
    real_classes = _find_test_class_names(project_root / "tests")
    pat = re.compile(r"`(Test[A-Z][A-Za-z0-9_]*)`")
    for md in list(docs_dir.rglob("*.md")) + [p for p in extra if p.is_file()]:
        text = _strip_code_fences(_read(md))
        for name in set(pat.findall(text)):
            if name not in real_classes:
                report.add(
                    "ERROR",
                    project,
                    "test_class_drift",
                    (
                        f"{_rel(md, project_root)} references `{name}` but tests/ has no "
                        f"such class. Real classes: {sorted(real_classes)}"
                    ),
                )


def _parse_all_block(text: str) -> set[str] | None:
    """Parse a single `__all__ = [...]` block. Returns the set of string entries.

    Robust to multi-line block and either single or double quotes around
    each entry. Returns None if no `__all__` block is present.
    """
    m = re.search(r"__all__\s*=\s*\[(.*?)\]", text, re.DOTALL)
    if not m:
        return None
    body = m.group(1)
    return set(re.findall(r"[\"']([A-Za-z_][A-Za-z0-9_]*)[\"']", body))


def check_all_export_drift(project_root: Path, report: Report, project: str) -> None:
    """Every `__all__ = [...]` block in a doc/STYLE/AGENTS file must match `src/__init__.py`.

    Catches the May 2026 v2-audit finding: prose `src/STYLE.md` documented
    an `__all__` list that didn't match `src/__init__.py` — claimed
    `CheckResult` and `write_resolved_manuscript_tree` exported (false),
    missed `ManuscriptVariables`, `plot_*`, `substitute_in_text` (true).
    """
    init_py = project_root / "src" / "__init__.py"
    if not init_py.is_file():
        return
    actual = _parse_all_block(_read(init_py))
    if actual is None:
        return
    # Scan files where __all__ is conventionally documented.
    candidates = [
        project_root / "src" / "STYLE.md",
        project_root / "src" / "AGENTS.md",
        project_root / "docs" / "style_guide.md",
        project_root / "docs" / "AGENTS.md",
    ]
    for md in candidates:
        if not md.is_file():
            continue
        text = _read(md)
        claimed = _parse_all_block(text)
        if claimed is None:
            continue
        missing_from_doc = sorted(actual - claimed)
        invented_in_doc = sorted(claimed - actual)
        if missing_from_doc or invented_in_doc:
            report.add(
                "ERROR",
                project,
                "__all___doc_drift",
                (
                    f"{_rel(md, project_root)} __all__ block disagrees with src/__init__.py "
                    f"— invented: {invented_in_doc}; missing: {missing_from_doc}"
                ),
            )


_ZENODO_DOI_RE = re.compile(r"^10\.5281/zenodo\.\d+$")


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

    specs: tuple[tuple[str, dict, str, tuple[str, ...], str | None], ...] = (
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
        actual: dict = loaded if isinstance(loaded, dict) else {}

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


def check_required_files_exist(project_root: Path, report: Report, project: str) -> None:
    """Exemplar must ship the minimum forkable project layout.

    Catches accidental deletion of core files that make a copied exemplar
    runnable. Fit-for-purpose docs are validated by link/drift checks, but the
    older 12-file docs hub is not a universal requirement for specialized
    exemplars.
    """
    must_exist = [
        "README.md",
        "AGENTS.md",
        "TODO.md",
        "pyproject.toml",
        ".gitignore",
        "scripts",
        "src/__init__.py",
        "tests",
        "tests/__init__.py",
        "manuscript/config.yaml",
        "manuscript/config.yaml.example",
        "manuscript/references.bib",
        "manuscript/preamble.md",
    ]
    for rel in must_exist:
        if not (project_root / rel).exists():
            report.add(
                "ERROR",
                project,
                "missing_canonical_file",
                f"{project}/{rel} is missing — exemplar contract broken",
            )


SignpostOption = str | tuple[str, ...]

_TEMPLATE_SIGNPOST_GROUPS: dict[str, dict[str, tuple[SignpostOption, ...]]] = {
    "README.md": {
        "monorepo run path": ("run via the template monorepo", "uv run python scripts/"),
        "when to use": ("when to use this template", "use this template"),
        "configuration entry points": (("config.yaml", "config.yaml.example"), "configuration"),
        "tests": ("pytest", "tests"),
        "outputs and validation": ("validate", "validation", "output", "stage 04"),
        "publication or boundaries": ("publication", "boundary", "boundaries", "doi", "zenodo", "claim"),
        "fork or template integrity": ("fork", "template integrity", "standalone"),
    },
    "AGENTS.md": {
        "source of truth or configuration": ("ground truth", "source of truth", "config.yaml", "configuration"),
        "commands or pipeline": ("uv run", "pipeline", "scripts/"),
        "contracts or boundaries": ("contract", "boundary", "do not", "publication", "todo"),
    },
    "TODO.md": {
        "current validation evidence": ("current validation evidence",),
        "integrity and template-status gaps": ("integrity and template-status gaps",),
        "configurable-surface gaps": ("configurable-surface gaps",),
        "documentation and signposting gaps": ("documentation and signposting gaps",),
        "test and validator gaps": ("test and validator gaps",),
        "ordered improvement ladder": ("ordered improvement ladder",),
    },
}


def _contains_signpost(text: str, options: tuple[SignpostOption, ...]) -> bool:
    lowered = text.lower()
    for option in options:
        if isinstance(option, tuple):
            if all(term in lowered for term in option):
                return True
        elif option in lowered:
            return True
    return False


def check_template_signpost_contract(project_root: Path, report: Report, project: str) -> None:
    """Check template signpost contract."""
    for rel, groups in _TEMPLATE_SIGNPOST_GROUPS.items():
        path = project_root / rel
        if not path.is_file():
            continue
        text = _read(path)
        for group, options in groups.items():
            if _contains_signpost(text, options):
                continue
            report.add(
                "ERROR",
                project,
                "missing_template_signpost",
                f"{project}/{rel} lacks {group} signpost; accepted terms: {options}",
            )


def check_config_example_parity(project_root: Path, report: Report, project: str) -> None:
    """Check config example parity."""
    config_path = project_root / "manuscript" / "config.yaml"
    example_path = project_root / "manuscript" / "config.yaml.example"
    if not config_path.is_file() or not example_path.is_file():
        return
    config = _load_yaml_mapping(config_path)
    example = _load_yaml_mapping(example_path)
    for section in sorted(set(config) - set(example)):
        report.add(
            "ERROR",
            project,
            "config_example_missing_section",
            f"{project}/manuscript/config.yaml.example lacks top-level section {section!r} from config.yaml",
        )


__all__ = [
    "check_all_export_drift",
    "check_config_author_placeholders",
    "check_config_example_parity",
    "check_coverage_floor_consistency",
    "check_function_name_drift",
    "check_metadata_export_current",
    "check_mocks_absent_from_tests",
    "check_no_blanket_except_in_src",
    "check_no_oversize_src_files",
    "check_publication_metadata_consistency",
    "check_publishing_status_block_current",
    "check_referenced_files_exist",
    "check_required_files_exist",
    "check_template_signpost_contract",
    "check_test_class_drift",
]
