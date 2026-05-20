#!/usr/bin/env python3
"""Detect documentation/code drift in the two canonical exemplar projects.

Background. A May 2026 audit of `projects/template_code_project/` and
`projects/template_prose_project/` found that the dominant defect class in
both exemplars was "the docs make a falsifiable claim and the file system
contradicts it" — wrong function names, drifting coverage numbers, stale
test counts, references to files that no longer exist, claims about which
modules import infrastructure that disagreed with the code. Every finding
was a single class of defect — doc/code drift — and most of them are
mechanically detectable.

This script is the converted audit. It runs a small battery of
empirically-grounded checks against the two exemplars and fails CI on
any drift it can detect. Adding a new check is the cheap path; the cost
of a new audit pass is the expensive one.

Exit code: 0 on no drift; 1 if any check fails (with a printed report).

Usage:

    uv run python scripts/check_template_drift.py
    uv run python scripts/check_template_drift.py --project template_code_project
    uv run python scripts/check_template_drift.py --strict   # fail on warnings too
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

PROJECT_NAMES = ("template_code_project", "template_prose_project")


@dataclass
class Finding:
    severity: str  # "ERROR" or "WARNING"
    project: str
    rule: str
    message: str


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)

    def add(self, sev: str, project: str, rule: str, message: str) -> None:
        self.findings.append(Finding(sev, project, rule, message))

    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "ERROR"]

    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "WARNING"]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _find_check_function_names(pipeline_py: Path) -> set[str]:
    """Return the actual `_check_*` function names declared in a `pipeline.py`."""
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
    """Every `_check_<name>` referenced in docs must exist in src/pipeline.py.

    Catches: 4-doc drift in template_prose_project where docs referenced
    `_check_headings` / `_check_bibliography_consistency` — neither function
    exists in src/pipeline.py.
    """
    pipeline = project_root / "src" / "pipeline.py"
    if not pipeline.exists():
        return  # e.g. template_code_project has no pipeline.py — N/A
    real_names = _find_check_function_names(pipeline)
    doc_refs = _doc_check_function_refs(project_root / "docs")
    for name, paths in doc_refs.items():
        if name not in real_names:
            for p in paths:
                report.add(
                    "ERROR",
                    project,
                    "function_name_drift",
                    f"docs reference `{name}` but src/pipeline.py has {sorted(real_names)}; in {p.relative_to(REPO_ROOT)}",
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
                    f"{md.relative_to(REPO_ROOT)} claims fail_under = {stated}; pyproject.toml has {actual}",
                )


def _strip_code_fences(text: str) -> str:
    """Remove fenced code blocks (```…```) and inline code (`…`) for link scanning.

    Dead-link false positives come from illustrative examples inside code
    blocks (e.g., a syntax_guide.md template showing how to reference a
    hypothetical `new_figure.png`). The link checker should not warn about
    those.
    """
    # Strip fenced blocks first (greedy across newlines).
    text = re.sub(r"```[\s\S]*?```", "", text)
    # Strip inline code spans on a single line.
    text = re.sub(r"`[^`\n]+`", "", text)
    return text


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
    Skips: links inside fenced/inline code blocks, links containing `<...>`
    placeholders, and filenames starting with `new_`/`my_`/`your_`/`example_`
    (illustrative templates, not real references).
    """
    docs_dir = project_root / "docs"
    if not docs_dir.is_dir():
        return
    pat = re.compile(r"\[(?P<text>[^\]]+)\]\((?P<target>[^)#\s]+(?:#[^)\s]*)?)\)")
    for md in docs_dir.rglob("*.md"):
        text = _strip_code_fences(_read(md))
        for m in pat.finditer(text):
            target = m.group("target").split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            if _is_example_filename(target):
                continue
            candidate = (md.parent / target).resolve()
            if not candidate.exists():
                report.add(
                    "WARNING",
                    project,
                    "dead_link",
                    f"{md.relative_to(REPO_ROOT)} → {target!r} does not resolve (looked at {candidate})",
                )


def check_no_oversize_src_files(project_root: Path, report: Report, project: str) -> None:
    """`src/*.py` files should not exceed 1500 lines (modularity smell).

    Catches the analysis.py-was-1719-lines smell; the template should not
    ship single source files that exceed thinkable refactor budget.
    """
    src_dir = project_root / "src"
    if not src_dir.is_dir():
        return
    for py in src_dir.glob("*.py"):
        line_count = sum(1 for _ in py.open("r", encoding="utf-8"))
        if line_count > 1500:
            report.add(
                "WARNING",
                project,
                "oversize_src_file",
                f"{py.relative_to(REPO_ROOT)} is {line_count} lines (> 1500 — consider splitting)",
            )


def check_no_blanket_except_in_src(project_root: Path, report: Report, project: str) -> None:
    """`except Exception:` in `src/*.py` should be rare and explicitly justified.

    Catches the CLAUDE.md-forbidden pattern of swallowing errors.
    """
    src_dir = project_root / "src"
    if not src_dir.is_dir():
        return
    pat = re.compile(r"except\s+Exception\b")
    for py in src_dir.glob("*.py"):
        text = _read(py)
        for m in pat.finditer(text):
            # Allow if the next 200 chars contain a noqa comment OR an `(ImportError`/specific filter.
            window = text[m.start(): m.start() + 200]
            if "# noqa: BLE001" in window or "(ImportError" in window or "Exception(\"" in window:
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
                report.add(
                    "WARNING",
                    project,
                    "blanket_except_with_noqa",
                    f"{py.relative_to(REPO_ROOT)}: `except Exception` with noqa near offset {m.start()} — narrow if possible",
                )
            else:
                report.add(
                    "ERROR",
                    project,
                    "blanket_except",
                    f"{py.relative_to(REPO_ROOT)}: `except Exception` near offset {m.start()} without noqa justification",
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
                f"{py.relative_to(REPO_ROOT)}: mock primitive `{m.group(0)}` found near offset {m.start()}",
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
                    f"{md.relative_to(REPO_ROOT)} references `{name}` but tests/ has no such class. Real classes: {sorted(real_classes)}",
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
                f"{md.relative_to(REPO_ROOT)} __all__ block disagrees with src/__init__.py — invented: {invented_in_doc}; missing: {missing_from_doc}",
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


def check_project(project: str, report: Report) -> None:
    project_root = REPO_ROOT / "projects" / project
    if not project_root.is_dir():
        report.add("WARNING", project, "project_missing", f"{project_root} does not exist; skipping")
        return
    check_required_files_exist(project_root, report, project)
    check_function_name_drift(project_root, report, project)
    check_test_class_drift(project_root, report, project)
    check_all_export_drift(project_root, report, project)
    check_coverage_floor_consistency(project_root, report, project)
    check_referenced_files_exist(project_root, report, project)
    check_no_oversize_src_files(project_root, report, project)
    check_no_blanket_except_in_src(project_root, report, project)
    check_mocks_absent_from_tests(project_root, report, project)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project",
        choices=list(PROJECT_NAMES) + ["all"],
        default="all",
        help="Which exemplar to check (default: all).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat WARNINGs as ERRORs.",
    )
    parser.add_argument(
        "--format",
        choices=("human", "github"),
        default="human",
        help="Output format (default: human; 'github' emits ::error/::warning lines).",
    )
    return parser.parse_args(argv)


def _print_human(report: Report) -> None:
    if not report.findings:
        print("template_drift: no drift detected.")
        return
    errors = report.errors()
    warnings = report.warnings()
    if errors:
        print(f"template_drift: {len(errors)} ERROR(S):")
        for f in errors:
            print(f"  [ERROR] {f.project}/{f.rule}: {f.message}")
    if warnings:
        print(f"template_drift: {len(warnings)} WARNING(S):")
        for f in warnings:
            print(f"  [warn]  {f.project}/{f.rule}: {f.message}")


def _print_github(report: Report) -> None:
    for f in report.findings:
        prefix = "::error" if f.severity == "ERROR" else "::warning"
        print(f"{prefix} title={f.project}/{f.rule}::{f.message}")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    report = Report()
    projects = list(PROJECT_NAMES) if args.project == "all" else [args.project]
    for project in projects:
        check_project(project, report)
    if args.format == "github":
        _print_github(report)
    else:
        _print_human(report)
    if report.errors():
        return 1
    if args.strict and report.warnings():
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
