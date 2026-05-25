"""Docs alignment with project discovery and markdown links under docs/."""

from __future__ import annotations

import re
from pathlib import Path

from infrastructure.project.public_scope import public_project_names


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_active_projects_doc_matches_discovery() -> None:
    """docs/_generated/active_projects.md exactly matches public project scope."""
    root = _repo_root()
    doc_path = root / "docs" / "_generated" / "active_projects.md"
    assert doc_path.is_file(), f"Missing {doc_path}; run scripts/generate_active_projects_doc.py"

    text = doc_path.read_text(encoding="utf-8")
    discovered = set(public_project_names(root))
    current_match = re.search(r"Current entries:\n\n(?P<entries>(?:- `[^`]+`\n)+)", text)
    assert current_match, "active_projects.md must contain a generated Current entries block"
    documented = set(re.findall(r"- `([^`]+)`", current_match.group("entries")))

    assert documented == discovered, (
        "active_projects.md drifted from public project scope; "
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


def test_canonical_facts_infrastructure_python_count_matches_tree() -> None:
    """The generated factsheet must not carry a stale infrastructure .py count."""
    root = _repo_root()
    doc_path = root / "docs" / "_generated" / "canonical_facts.md"
    text = doc_path.read_text(encoding="utf-8")

    count_match = re.search(r"Last refreshed count: \*\*(?P<count>\d+)\*\*", text)
    assert count_match, "canonical_facts.md must include the refreshed infrastructure Python-file count"

    documented = int(count_match.group("count"))
    actual = sum(1 for path in (root / "infrastructure").rglob("*.py") if path.is_file())
    assert documented == actual, (
        "canonical_facts.md drifted from the live infrastructure Python-file count; "
        f"documented={documented} actual={actual}"
    )


def test_pipeline_control_docs_describe_file_backed_hitl_boundary() -> None:
    """Agent/HITL docs must not imply an autonomous approval service exists."""
    root = _repo_root()
    text = (root / "docs" / "operational" / "pipeline-control.md").read_text(encoding="utf-8")

    for expected in (
        "output/hitl/agent_context.json",
        "output/hitl/agent_response.schema.json",
        "There is no WebSocket server, MCP server, or autonomous approval loop.",
    ):
        assert expected in text


def test_literature_search_docs_match_paperclip_mcp_contract() -> None:
    """Paperclip docs must match the implemented MCP-style auth and endpoint."""
    root = _repo_root()
    text = (root / "docs" / "best-practices" / "literature-search-best-practices.md").read_text(encoding="utf-8")

    assert "`X-API-Key`" in text
    assert "MCP-style JSON-RPC to `/mcp`" in text
    assert "`Authorization: Bearer`" not in text
