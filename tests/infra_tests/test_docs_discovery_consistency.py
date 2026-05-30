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


def test_publication_records_doc_matches_public_scope() -> None:
    """docs/_generated/publication_records.md must cover every public exemplar."""
    root = _repo_root()
    doc_path = root / "docs" / "_generated" / "publication_records.md"
    assert doc_path.is_file(), (
        "Missing publication records doc; run "
        "uv run python scripts/generate_publication_records_doc.py --refresh-external"
    )

    text = doc_path.read_text(encoding="utf-8")
    discovered = set(public_project_names(root))
    documented = set(re.findall(r"\| `([^`]+)` \|", text))

    assert documented == discovered, (
        "publication_records.md drifted from public project scope; "
        "run uv run python scripts/generate_publication_records_doc.py --refresh-external\n"
        f"missing={sorted(discovered - documented)} extra={sorted(documented - discovered)}"
    )


def test_github_readme_publication_block_matches_public_scope() -> None:
    """The GitHub README publication table is generated from public scope."""
    root = _repo_root()
    text = (root / ".github" / "README.md").read_text(encoding="utf-8")
    match = re.search(
        r"<!-- BEGIN:PUBLICATION_RECORDS -->(?P<block>.*?)<!-- END:PUBLICATION_RECORDS -->",
        text,
        flags=re.DOTALL,
    )
    assert match, ".github/README.md must contain the generated publication records block"

    discovered = set(public_project_names(root))
    documented = set(re.findall(r"\.\./projects/([a-z0-9_]+/[a-z0-9_]+)/", match.group("block")))
    assert documented == discovered, (
        ".github/README.md publication table drifted from public project scope; "
        "run uv run python scripts/generate_publication_records_doc.py --refresh-external\n"
        f"missing={sorted(discovered - documented)} extra={sorted(documented - discovered)}"
    )


def test_top_level_docs_do_not_claim_four_public_exemplars() -> None:
    """The public exemplar set currently has five entries, not four."""
    root = _repo_root()
    docs_to_check = [
        root / "AGENTS.md",
        root / "README.md",
        root / "CLAUDE.md",
        root / ".cursorrules",
        root / ".github" / "README.md",
        root / ".github" / "AGENTS.md",
        root / "projects" / "AGENTS.md",
        root / "projects" / "README.md",
        root / "docs" / "guides" / "manuscript-semantics.md",
    ]
    forbidden = (
        "four projects under `projects/` are permanent canonical exemplars",
        "four public template exemplars",
        "four permanent canonical exemplars",
    )
    for doc_path in docs_to_check:
        text = doc_path.read_text(encoding="utf-8").lower()
        for phrase in forbidden:
            assert phrase not in text, doc_path


def test_docs_markdown_no_broken_projects_paths() -> None:
    """Links under docs/ must not point at projects/NAME/ unless NAME exists.

    ``valid`` is seeded with the declared lifecycle subfolder names so the
    check is clone-stable. On a fresh CI checkout ``projects/`` only tracks
    ``templates/`` and the root *.md files; ``working/``, ``archive/``,
    ``published/``, ``other/``, and ``active/`` are local-only lifecycle
    mirrors and must not be treated as broken links just because they aren't
    tracked directories on the CI worker.
    """
    from infrastructure.project.discovery import NON_RENDERED_SUBDIRS

    root = _repo_root()
    # Lifecycle dirs are valid project prefixes by declaration, not by presence.
    lifecycle_dirs = NON_RENDERED_SUBDIRS | {"active", "templates"}
    valid = lifecycle_dirs | {
        p.name for p in (root / "projects").iterdir() if p.is_dir() and not p.name.startswith(".")
    }
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


def test_generated_docs_use_skills_index_command() -> None:
    """Generated-doc hubs must point at the command that writes skills_index.md."""
    root = _repo_root()
    for rel_path in ("docs/_generated/README.md", "docs/_generated/AGENTS.md"):
        text = (root / rel_path).read_text(encoding="utf-8")
        assert "uv run python -m infrastructure.skills write-index" in text, rel_path
        assert not re.search(
            r"skills_index\.md.*uv run python -m infrastructure\.skills write(?!-index)",
            text,
            flags=re.DOTALL,
        ), rel_path


def test_root_agents_is_public_repo_contract_not_personal_memory() -> None:
    """Public AGENTS.md must not carry local learned-preference memory blocks."""
    root = _repo_root()
    text = (root / "AGENTS.md").read_text(encoding="utf-8")
    forbidden = (
        "## Learned User Preferences",
        "## Learned Workspace Facts",
        "thermo-nuclear-code-quality-review",
    )
    for phrase in forbidden:
        assert phrase not in text


def test_continual_learning_local_state_gitignored() -> None:
    """Continual-learning runtime files must stay out of version control."""
    root = _repo_root()
    gitignore = (root / ".gitignore").read_text(encoding="utf-8")
    for pattern in (
        ".cursor/hooks/state/continual-learning-memory.json",
        ".cursor/hooks/state/continual-learning-index.json",
    ):
        assert pattern in gitignore, f".gitignore must ignore {pattern}"


def test_continual_learning_index_not_tracked() -> None:
    """Transcript index is machine-local and must not be git-tracked."""
    import subprocess

    root = _repo_root()
    result = subprocess.run(
        ["git", "ls-files", ".cursor/hooks/state/continual-learning-index.json"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == ""


def test_publishing_cli_docs_do_not_advertise_apa_mla_formats() -> None:
    """The CLI supports BibTeX only; APA/MLA are programmatic helpers."""
    root = _repo_root()
    docs_to_check = [
        root / "infrastructure" / "publishing" / "README.md",
        root / "docs" / "guides" / "publishing-guide.md",
        root / "docs" / "modules" / "guides" / "publishing-module.md",
        root / "infrastructure" / "publishing" / "AGENTS.md",
    ]
    for doc_path in docs_to_check:
        text = doc_path.read_text(encoding="utf-8")
        assert not re.search(r"generate-citation[^\n`]*--format\s+(apa|mla)\b", text, re.IGNORECASE), doc_path
        assert "`--format`,\n        choices=[\"bibtex\"]" not in text, doc_path


def test_api_reference_publish_to_zenodo_return_type() -> None:
    """Generated API docs must show the current PublishResult return contract."""
    root = _repo_root()
    text = (root / "docs" / "reference" / "api-reference.md").read_text(encoding="utf-8")
    match = re.search(r"### `publish_to_zenodo`.*?```python\n(?P<sig>.*?)\n```", text, re.DOTALL)
    assert match, "publish_to_zenodo section missing from generated API reference"
    assert "-> PublishResult" in match.group("sig")


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
