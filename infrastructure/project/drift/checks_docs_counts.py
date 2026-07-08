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


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _strip_code_fences(text: str) -> str:
    return re.sub(r"```[\s\S]*?```", "", text)


def _scan_hardcoded_counts_in_text(
    text: str,
    rel_md: str,
    report: Report,
    *,
    rule_prefix: str,
) -> None:
    test_count_pat = re.compile(r"\b(\d{3,5})\s+(?:infrastructure|project|infra)\s+tests?\b", re.IGNORECASE)
    coverage_pat = re.compile(r"\b(\d{1,3}(?:\.\d+)?)\s*%\s*coverage\b", re.IGNORECASE)
    for match in test_count_pat.finditer(text):
        report.add(
            "WARNING",
            "repo",
            f"{rule_prefix}_hardcoded_test_count",
            (
                f"{rel_md}: hardcoded '{match.group(0)}' near offset {match.start()} "
                "— link to docs/_generated/COUNTS.md instead"
            ),
        )
    for match in coverage_pat.finditer(text):
        value = float(match.group(1))
        if value in {60.0, 90.0}:
            continue
        report.add(
            "WARNING",
            "repo",
            f"{rule_prefix}_hardcoded_coverage_pct",
            (
                f"{rel_md}: hardcoded '{match.group(0)}' near offset {match.start()} "
                "— link to docs/_generated/COUNTS.md instead"
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
