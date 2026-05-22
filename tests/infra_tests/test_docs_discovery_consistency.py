"""Docs alignment with project discovery and markdown links under docs/."""

from __future__ import annotations

import re
from pathlib import Path

from infrastructure.project.discovery import discover_projects


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_active_projects_doc_matches_discovery() -> None:
    """docs/_generated/active_projects.md exactly matches discovery."""
    root = _repo_root()
    doc_path = root / "docs" / "_generated" / "active_projects.md"
    assert doc_path.is_file(), f"Missing {doc_path}; run scripts/generate_active_projects_doc.py"

    text = doc_path.read_text(encoding="utf-8")
    discovered = {p.qualified_name for p in discover_projects(root)}
    current_match = re.search(r"Current entries:\n\n(?P<entries>(?:- `[^`]+`\n)+)", text)
    assert current_match, "active_projects.md must contain a generated Current entries block"
    documented = set(re.findall(r"- `([^`]+)`", current_match.group("entries")))

    assert documented == discovered, (
        "active_projects.md drifted from discover_projects(); "
        "run uv run python scripts/generate_active_projects_doc.py\n"
        f"missing={sorted(discovered - documented)} extra={sorted(documented - discovered)}"
    )


def test_docs_markdown_no_broken_projects_paths() -> None:
    """Links under docs/ must not point at projects/NAME/ unless NAME exists."""
    root = _repo_root()
    valid = {p.name for p in (root / "projects").iterdir() if p.is_dir() and not p.name.startswith(".")}
    link_target = re.compile(r"\]\(([^)]+)\)")
    projects_segment = re.compile(r"projects/([a-z0-9_]+)/")
    failures: list[str] = []

    for md_path in sorted((root / "docs").rglob("*.md")):
        content = md_path.read_text(encoding="utf-8", errors="replace")
        for m in link_target.finditer(content):
            target = m.group(1).strip().strip("<>").split("#", 1)[0].strip()
            if "projects_archive" in target or "projects_in_progress" in target:
                continue
            sm = projects_segment.search(target)
            if not sm:
                continue
            name = sm.group(1)
            if name not in valid:
                rel = md_path.relative_to(root)
                failures.append(f"{rel}: link target {target!r} references missing projects/{name}/")

    assert not failures, "Broken projects/ links in docs/:\n" + "\n".join(failures)
