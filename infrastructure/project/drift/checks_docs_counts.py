"""Repo-wide drift checks for hardcoded counts in long-lived documentation."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from infrastructure.core.files.serialization import relative_or_self as _rel
from infrastructure.project.drift.models import Report


def _tracked_paths(repo_root: Path) -> set[Path] | None:
    """Resolved paths of every git-tracked file, or ``None`` if git is unavailable.

    Filesystem-walking checks intersect their candidates with this set so that
    untracked, git-ignored sibling directories (local-only projects, nested
    worktree checkouts) cannot redden the gate on a maintainer's machine while
    passing on CI, which runs against a fresh clone that never contains them.
    Returning ``None`` (no ``.git``, git binary missing, exported tarball) keeps
    the previous name-based skip behavior so the check still runs offline.
    """
    try:
        proc = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=repo_root,
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return {(repo_root / rel).resolve() for rel in proc.stdout.decode("utf-8").split("\0") if rel}


SHARED_TEMPLATE_DESIGN_REQUIRED_SECTIONS: tuple[str, ...] = (
    "## 1. Atmosphere & Identity",
    "## 2. Color",
    "## 3. Typography",
    "## 4. Spacing & Layout",
    "## 5. Components",
    "## 6. Motion & Interaction",
    "## 7. Depth & Surface",
    "## Browser QA Expectations",
    "## Template-Specific Boundaries",
)

_PUBLIC_ROSTER_LITERAL_RE = re.compile(
    r"\b(?:eighteen|nineteen|twenty(?:-three)?|\d+)\s+"
    r"(?:public\s+)?(?:canonical\s+)?(?:template[_*]*\s+)?(?:projects|exemplars)\b",
    re.IGNORECASE,
)
_OUTPUT_POLICY_CONTRADICTION_RE = re.compile(
    r"(?:never\s+commit\s+generated\s+outputs|"
    r"(?:generated\s+)?output\s+trees?.{0,40}must\s+not\s+be\s+tracked|"
    r"generated\s+outputs?.{0,40}must\s+not\s+be\s+tracked)",
    re.IGNORECASE,
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _strip_code_fences(text: str) -> str:
    return re.sub(r"```[\s\S]*?```", "", text)


# A bare collected-test total ("279 tests", "1,204 passed"). The original pattern
# required the words infrastructure/project/infra between the number and "tests",
# so the highest-churn form — a plain per-exemplar total in a README — was never
# caught. Two digits minimum: single-digit counts are almost always prose.
#
# Plural only. The singular form is almost never a count in this repo — it is a
# stage identifier ("Stage 01 test runner") or a noun phrase ("50 test images per
# class") — so matching `tests?` produced pure false positives.
# At most ONE qualifier word between the number and the noun, so both the original
# "1234 infrastructure tests" and the bare "279 tests" are caught. Allowing two
# words matched "max_tokens=500 for fallback tests", where 500 is a token limit.
_TEST_COUNT_RE = re.compile(
    r"\b(\d{2,3}(?:,\d{3})*|\d{2,5})\s+(?:[A-Za-z][A-Za-z-]*\s+)?(?:tests|passed)\b",
    re.IGNORECASE,
)
# "Stage 12 tests" is a pipeline stage, not a measured total.
_STAGE_PREFIX_RE = re.compile(r"stage[-\s]$", re.IGNORECASE)
# Both orders: "95.91% coverage" and "coverage: 95.91%" / "coverage of 95.91 %".
_COVERAGE_RE = re.compile(
    r"\b(?:(?P<pre>\d{1,3}(?:\.\d+)?)\s*%\s*(?:source\s+|line\+branch\s+)?coverage"
    r"|coverage(?:\s+of)?\s*[:=]?\s*(?P<post>\d{1,3}(?:\.\d+)?)\s*%)",
    re.IGNORECASE,
)
# Policy floors, not measurements — these are contract values and belong in prose.
_POLICY_COVERAGE_VALUES = {60.0, 75.0, 89.0, 90.0}
_COUNT_NOQA_RE = re.compile(r"<!--\s*noqa:\s*(?:docs-lint|drift-counts)", re.IGNORECASE)

# This file is an immutable audit trail, not current guidance.  Its measured
# totals are intentionally preserved so reviewers can reconstruct what a
# historical release actually claimed; applying the live-count rule to it
# would either erase that evidence or require one-line escape hatches on
# every record.  Keep this list explicit and narrow so ordinary archival
# prose remains subject to drift review.
HISTORICAL_EVIDENCE_RELATIVE_PATHS = frozenset({"docs/maintenance/exemplar-backlog-history.md"})


def _scan_hardcoded_counts_in_text(
    text: str,
    rel_md: str,
    report: Report,
    *,
    rule_prefix: str,
) -> None:
    """Flag hardcoded test totals / coverage percentages outside the generated doc.

    Line-based so a finding can cite a line number and so a dated historical note
    can opt out with an inline ``<!-- noqa: drift-counts -->``. Measured values
    belong in ``docs/_generated/COUNTS.md``, which is regenerated from the live
    tree; a copy pasted into prose silently rots (2026-07-27: adding one test to
    ``template_formal`` required editing nine separate hardcoded totals).
    """
    for lineno, line in enumerate(text.splitlines(), 1):
        if _COUNT_NOQA_RE.search(line):
            continue
        for match in _TEST_COUNT_RE.finditer(line):
            if _STAGE_PREFIX_RE.search(line[max(0, match.start() - 8) : match.start()]):
                continue
            report.add(
                "WARNING",
                "repo",
                f"{rule_prefix}_hardcoded_test_count",
                (
                    f"{rel_md}:{lineno}: hardcoded {match.group(0)!r} — link to "
                    "docs/_generated/COUNTS.md, or mark a dated historical note with "
                    "`<!-- noqa: drift-counts -->`"
                ),
            )
        for match in _COVERAGE_RE.finditer(line):
            raw = match.group("pre") or match.group("post")
            if raw is None or float(raw) in _POLICY_COVERAGE_VALUES:
                continue
            report.add(
                "WARNING",
                "repo",
                f"{rule_prefix}_hardcoded_coverage_pct",
                (
                    f"{rel_md}:{lineno}: hardcoded {match.group(0)!r} — link to "
                    "docs/_generated/COUNTS.md, or mark a dated historical note with "
                    "`<!-- noqa: drift-counts -->`"
                ),
            )


def check_docs_hardcoded_counts(repo_root: Path, report: Report) -> None:
    """Catch hardcoded test counts / coverage percentages in long-lived docs."""
    # `.claude` and `.git` are gitignored agent/VCS dirs that can hold nested
    # worktree checkouts of this very repo; scanning them double-counts repo docs
    # and surfaces drift for files that are not part of the tracked tree.
    skip_dir_names = {
        "_generated",
        "archived",
        "node_modules",
        ".venv",
        "__pycache__",
        ".claude",
        ".git",
    }
    scanned: set[Path] = set()
    tracked = _tracked_paths(repo_root)

    def _include(md: Path) -> bool:
        if any(part in skip_dir_names for part in md.parts):
            return False
        try:
            relative = md.resolve().relative_to(repo_root.resolve()).as_posix()
        except ValueError:
            relative = ""
        if relative in HISTORICAL_EVIDENCE_RELATIVE_PATHS:
            return False
        # When git is available, only scan tracked files so untracked local-only
        # dirs (e.g. a sibling private project) cannot redden the gate off-CI.
        return tracked is None or md.resolve() in tracked

    docs_dir = repo_root / "docs"
    if docs_dir.is_dir():
        for md in docs_dir.rglob("*.md"):
            if _include(md):
                scanned.add(md.resolve())

    for name in ("README.md", "AGENTS.md"):
        for md in repo_root.rglob(name):
            if _include(md):
                scanned.add(md.resolve())

    # Root agent-instruction files. These are the documents agents are told to
    # trust for copy-paste commands, so a stale count here propagates furthest.
    # STATUS.md and TO-DO.md are deliberately excluded: they are dated
    # verification ledgers whose entries describe past runs by design, so every
    # line would need an opt-out annotation.
    for name in ("CLAUDE.md", "START_HERE.md", "CONTRIBUTING.md", "MAINTAINERS.md"):
        md = repo_root / name
        if md.is_file() and _include(md):
            scanned.add(md.resolve())

    for md in sorted(scanned):
        text = _strip_code_fences(_read(md))
        _scan_hardcoded_counts_in_text(text, _rel(md, repo_root), report, rule_prefix="repo_docs")


def check_shared_template_design_contract(repo_root: Path, report: Report) -> None:
    """Check shared template design contract."""
    design_path = repo_root / "projects" / "templates" / "DESIGN.md"
    agents_path = repo_root / "projects" / "templates" / "AGENTS.md"

    if not design_path.is_file():
        report.add(
            "ERROR",
            "repo",
            "shared_template_design_missing",
            "projects/templates/DESIGN.md is missing - public templates need a shared design/browser-QA contract",
        )
        return

    design_text = _read(design_path)
    for section in SHARED_TEMPLATE_DESIGN_REQUIRED_SECTIONS:
        if section not in design_text:
            report.add(
                "ERROR",
                "repo",
                "shared_template_design_section_missing",
                f"{_rel(design_path, repo_root)} lacks required section {section!r}",
            )

    if not agents_path.is_file():
        report.add(
            "ERROR",
            "repo",
            "shared_template_design_signpost_missing",
            "projects/templates/AGENTS.md is missing, so the shared design contract is not discoverable",
        )
        return

    agents_text = _read(agents_path)
    if "DESIGN.md" not in agents_text or "browser-QA" not in agents_text:
        report.add(
            "ERROR",
            "repo",
            "shared_template_design_signpost_missing",
            "projects/templates/AGENTS.md must signpost DESIGN.md and browser-QA expectations",
        )


def check_shared_template_truth_contract(repo_root: Path, report: Report) -> None:
    """Prevent shared docs from duplicating roster counts or denying tracked public outputs."""
    for path in (
        repo_root / "projects" / "templates" / "AGENTS.md",
        repo_root / "projects" / "templates" / "DESIGN.md",
    ):
        if not path.is_file():
            continue
        text = _strip_code_fences(_read(path))
        if _PUBLIC_ROSTER_LITERAL_RE.search(text):
            report.add(
                "ERROR",
                "repo",
                "shared_template_roster_literal",
                f"{_rel(path, repo_root)} hard-codes the public exemplar count",
            )
        if "docs/_generated/active_projects.md" not in text:
            report.add(
                "ERROR",
                "repo",
                "shared_template_roster_pointer_missing",
                f"{_rel(path, repo_root)} must link docs/_generated/active_projects.md",
            )

    for path in (
        repo_root / "CLAUDE.md",
        repo_root / "infrastructure" / "AGENTS.md",
        repo_root / "projects" / "AGENTS.md",
        repo_root / "projects" / "templates" / "AGENTS.md",
    ):
        if not path.is_file():
            continue
        text = _strip_code_fences(_read(path))
        if _OUTPUT_POLICY_CONTRADICTION_RE.search(text):
            report.add(
                "ERROR",
                "repo",
                "public_output_policy_contradiction",
                f"{_rel(path, repo_root)} contradicts the canonical public-output allowlist",
            )
