"""Project-level template drift checks for canonical exemplars."""

from __future__ import annotations

import re

try:
    import tomllib
except ImportError:  # Python <3.11 — use backport
    import tomli as tomllib  # type: ignore[no-redef]
from pathlib import Path

from infrastructure.core.files.serialization import load_yaml_mapping as _load_yaml_mapping
from infrastructure.core.files.serialization import relative_or_self as _rel
from infrastructure.project.drift.models import Report
from infrastructure.project.drift.checks_publication import (
    check_config_author_placeholders,
    check_metadata_export_current,
    check_publication_index_completeness,
    check_publication_metadata_consistency,
    check_publishing_status_block_current,
)
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
    "check_publication_index_completeness",
    "check_publication_metadata_consistency",
    "check_publishing_status_block_current",
    "check_referenced_files_exist",
    "check_required_files_exist",
    "check_template_signpost_contract",
    "check_test_class_drift",
]
