"""Repo-wide drift checks for hardcoded counts in long-lived documentation."""

from __future__ import annotations

import re
from pathlib import Path

from infrastructure.project.drift.models import Report


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _rel(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


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
    skip_dir_names = {"_generated", "archived", "node_modules", ".venv", "__pycache__"}
    scanned: set[Path] = set()

    docs_dir = repo_root / "docs"
    if docs_dir.is_dir():
        for md in docs_dir.rglob("*.md"):
            if any(part in skip_dir_names for part in md.parts):
                continue
            scanned.add(md.resolve())

    for name in ("README.md", "AGENTS.md"):
        for md in repo_root.rglob(name):
            if any(part in skip_dir_names for part in md.parts):
                continue
            scanned.add(md.resolve())

    for md in sorted(scanned):
        text = _strip_code_fences(_read(md))
        _scan_hardcoded_counts_in_text(text, _rel(md, repo_root), report, rule_prefix="repo_docs")
