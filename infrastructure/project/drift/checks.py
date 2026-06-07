"""Template drift check implementations for canonical exemplar projects."""

from __future__ import annotations

import json
import re

try:
    import tomllib
except ImportError:  # Python <3.11 — use backport
    import tomli as tomllib  # type: ignore[no-redef]
from pathlib import Path

import yaml

from infrastructure.project.drift.models import Report
from infrastructure.project.drift.orchestrator import (
    check_repo_scripts,
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _rel(p: Path, repo_root: Path) -> str:
    """Best-effort relative path against repo_root.

    Falls back to the absolute path when ``p`` is outside the repository
    (e.g., synthetic test fixtures under ``tmp_path``). Production calls
    always pass repo-internal paths and stay short; tests call against
    a temp tree and get the absolute path. Keeps the detectors testable.
    """
    try:
        return str(p.relative_to(repo_root))
    except ValueError:
        return str(p)


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


# Dense active-inference sheaf-domain modules carry a documented split-TODO and
# are exempt from the oversize warning, mirroring ``LINE_COUNT_ALLOWLIST`` in
# ``scripts/gates/module_line_count_check.py``. Keep the two allowlists in sync;
# remove an entry once the sheaf builders are extracted into sibling modules.
_OVERSIZE_SRC_ALLOWLIST: frozenset[str] = frozenset(
    {
        "src/roadmap_tracks/sheaf_tracks.py",
        "src/manuscript/sheaf/semantic.py",
    }
)


def check_no_oversize_src_files(project_root: Path, report: Report, project: str) -> None:
    """``src/**/*.py`` files should not exceed 1500 lines (modularity smell).

    Catches the analysis.py-was-1719-lines smell; the template should not
    ship single source files that exceed thinkable refactor budget. Dense
    sheaf-domain modules in ``_OVERSIZE_SRC_ALLOWLIST`` are exempt (documented
    split-TODO; kept in sync with the module-line-count gate's allowlist).
    """
    src_dir = project_root / "src"
    if not src_dir.is_dir():
        return
    for py in src_dir.rglob("*.py"):
        if _rel(py, project_root) in _OVERSIZE_SRC_ALLOWLIST:
            continue
        line_count = sum(1 for _ in py.open("r", encoding="utf-8"))
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
    """No `unittest.mock`/`MagicMock`/`@patch`/`create_autospec` anywhere under `tests/`.

    Mirrors the repo-level no-mocks rule for the exemplars.
    """
    tests_dir = project_root / "tests"
    if not tests_dir.is_dir():
        return
    pat = re.compile(r"unittest\.mock|MagicMock|@patch|create_autospec")
    for py in tests_dir.rglob("*.py"):
        for m in pat.finditer(_read(py)):
            report.add(
                "ERROR",
                project,
                "mock_in_tests",
                f"{_rel(py, project_root)}: mock primitive `{m.group(0)}` found near offset {m.start()}",
            )


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


def _load_yaml_mapping(path: Path) -> dict:
    if not path.is_file():
        return {}
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


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
                (
                    f"CITATION.cff version {cff_version!r} disagrees with "
                    f".zenodo.json version {zenodo_version!r}"
                ),
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


def check_required_files_exist(project_root: Path, report: Report, project: str) -> None:
    """Exemplar must ship the canonical layout.

    Catches accidental deletion of files the README/AGENTS/docs assume exist.
    """
    must_exist = [
        "README.md",
        "AGENTS.md",
        "pyproject.toml",
        ".gitignore",
        "src/__init__.py",
        "tests/__init__.py",
        "tests/conftest.py",
        "manuscript/config.yaml",
        "manuscript/references.bib",
        "manuscript/preamble.md",
        "docs/AGENTS.md",
    ]
    for rel in must_exist:
        if not (project_root / rel).exists():
            report.add(
                "ERROR",
                project,
                "missing_canonical_file",
                f"{project}/{rel} is missing — exemplar contract broken",
            )


def check_repo_docs_hardcoded_counts(repo_root: Path, report: Report) -> None:
    """Catch hardcoded test counts / coverage percentages in repo-level `docs/`.

    Catches the round-4 finding class: `docs/operational/build/build-system.md`
    hardcoded "1796 infrastructure tests, 320 project tests" verbatim, and
    six docs hardcoded "83.33%" / "100% coverage" — both classes drift the
    moment the live numbers change. The rule is: counts and percentages
    live in `docs/_generated/canonical_facts.md` and other docs link there.

    Skipped: `_generated/*` (the canonical source of truth itself),
    `audit/archived/*` (intentional point-in-time snapshots), fenced
    code blocks (illustrative literal output is fine).
    """
    docs_dir = repo_root / "docs"
    if not docs_dir.is_dir():
        return
    # Patterns we care about — broad enough to catch real drift, narrow
    # enough not to flag every "1234" in unrelated prose.
    test_count_pat = re.compile(r"\b(\d{3,5})\s+(?:infrastructure|project|infra)\s+tests?\b", re.IGNORECASE)
    coverage_pat = re.compile(r"\b(\d{1,3}(?:\.\d+)?)\s*%\s*coverage\b", re.IGNORECASE)
    skip_dirs = {"_generated", "archived"}
    for md in docs_dir.rglob("*.md"):
        if any(part in skip_dirs for part in md.parts):
            continue
        text = _strip_code_fences(_read(md))
        for m in test_count_pat.finditer(text):
            rel_md = _rel(md, repo_root)
            report.add(
                "WARNING",
                "repo",
                "repo_docs_hardcoded_test_count",
                (
                    f"{rel_md}: hardcoded '{m.group(0)}' near offset {m.start()} "
                    "— link to docs/_generated/canonical_facts.md instead"
                ),
            )
        for m in coverage_pat.finditer(text):
            # Exempt the 90% / 60% gate floors (those ARE policy, not live numbers).
            value = float(m.group(1))
            if value in {60.0, 90.0}:
                continue
            rel_md = _rel(md, repo_root)
            report.add(
                "WARNING",
                "repo",
                "repo_docs_hardcoded_coverage_pct",
                (
                    f"{rel_md}: hardcoded '{m.group(0)}' near offset {m.start()} "
                    "— link to docs/_generated/canonical_facts.md instead"
                ),
            )


def check_project(repo_root: Path, project: str, report: Report) -> None:
    from infrastructure.project.drift.registry import run_project_checks

    project_root = repo_root / "projects" / project
    if not project_root.is_dir():
        report.add("WARNING", project, "project_missing", f"{project_root} does not exist; skipping")
        return
    run_project_checks(project_root, repo_root, report, project)


def check_repo_thin_orchestrator_scripts(repo_root: Path, report: Report) -> None:
    check_repo_scripts(repo_root, report)
