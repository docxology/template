"""Docs alignment with project discovery and markdown links under docs/."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from infrastructure.project.discovery import discover_projects
from infrastructure.project.public_scope import LOCAL_ONLY_TEMPLATE_NAMES, public_project_names
from infrastructure.validation.docs.consistency._shared import DEFAULT_LONG_LIVED_DOC_ROOTS


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _doc_chunks(text: str) -> list[str]:
    chunks = [line for line in text.splitlines() if line.strip()]
    chunks.extend(block for block in re.split(r"\n\s*\n", text) if block.strip())
    return chunks


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

    # NOTE: both `documented` (parsed from the generated doc) and `discovered`
    # (from public_project_names()) are derived from the same static registry, so
    # this assertion only detects doc/registry drift — not unregistered on-disk
    # template projects.  The second assertion below catches that gap.
    assert documented == discovered, (
        "active_projects.md drifted from public project scope; "
        "run uv run python scripts/generate_active_projects_doc.py\n"
        f"missing={sorted(discovered - documented)} extra={sorted(documented - discovered)}"
    )

    # Guard against on-disk template projects that exist under projects/templates/
    # but are not yet registered in public_project_names().  If this assertion
    # fails, add the new project to public_scope.py (or remove it from disk).
    on_disk_templates = {
        p.qualified_name for p in discover_projects(root) if p.path.is_relative_to(root / "projects" / "templates")
    }
    registered = set(public_project_names(root)) | set(LOCAL_ONLY_TEMPLATE_NAMES)
    unregistered = on_disk_templates - registered
    assert not unregistered, (
        "Template projects exist on disk but are not registered in public_project_names(); "
        "add them to infrastructure/project/public_scope.py or remove from projects/templates/: "
        f"{sorted(unregistered)}"
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


def test_top_level_docs_do_not_claim_stale_public_exemplar_counts() -> None:
    """Top-level docs must not claim outdated public exemplar counts (four or five)."""
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
        root / "MAINTAINERS.md",
    ]
    forbidden = (
        "four projects under `projects/` are permanent canonical exemplars",
        "four public template exemplars",
        "four permanent canonical exemplars",
        "five projects under `projects/templates/` are permanent canonical exemplars",
        "five public exemplars",
        "five permanent canonical exemplars",
    )
    for doc_path in docs_to_check:
        text = doc_path.read_text(encoding="utf-8").lower()
        for phrase in forbidden:
            assert phrase not in text, doc_path


def test_human_docs_do_not_carry_partial_public_exemplar_rosters() -> None:
    root = _repo_root()
    public_leaves = {name.split("/")[-1] for name in public_project_names(root)}
    docs_to_check = [
        root / "AGENTS.md",
        root / "README.md",
        root / "CLAUDE.md",
        root / ".cursorrules",
        root / ".github" / "README.md",
        root / ".github" / "AGENTS.md",
        root / "projects" / "AGENTS.md",
        root / "projects" / "README.md",
        root / "docs" / "documentation-index.md",
        root / "docs" / "guides" / "publishing-guide.md",
        root / "docs" / "guides" / "zenodo-doi-strategy.md",
    ]
    failures: list[str] = []
    for doc_path in docs_to_check:
        text = doc_path.read_text(encoding="utf-8", errors="replace")
        for index, chunk in enumerate(_doc_chunks(text), start=1):
            mentioned = {leaf for leaf in public_leaves if re.search(rf"\b{re.escape(leaf)}\b", chunk)}
            if len(mentioned) < 3 or mentioned == public_leaves:
                continue
            lower = chunk.lower()
            has_generated_roster = (
                "docs/_generated/active_projects.md" in chunk
                or "../docs/_generated/active_projects.md" in chunk
                or "_generated/active_projects.md" in chunk
            )
            allows_examples = any(phrase in lower for phrase in ("example", "starting point", "authoritative roster"))
            if has_generated_roster and allows_examples:
                continue
            failures.append(f"{doc_path.relative_to(root)} chunk {index}: {sorted(mentioned)}")

    assert not failures, "Partial public exemplar rosters must link the generated roster:\n" + "\n".join(failures)


def test_consistency_lint_roots_include_public_project_docs() -> None:
    """Consistency lint must scan every public project doc tree."""
    root = _repo_root()
    expected = {f"projects/{name}" for name in public_project_names(root)}
    configured = set(DEFAULT_LONG_LIVED_DOC_ROOTS)
    assert expected.issubset(configured), (
        f"documentation consistency roots must track public_project_names(); missing={sorted(expected - configured)}"
    )


def test_long_lived_docs_use_typed_public_project_paths() -> None:
    """Docs must use ``projects/templates/<name>/`` for public template exemplars."""
    root = _repo_root()
    public_leaves = {name.split("/")[-1] for name in public_project_names(root)}
    stale_path = re.compile(r"(?<![A-Za-z0-9_/])projects/(?P<name>template_[A-Za-z0-9_]+)/")
    scan_roots = [
        root / ".github",
        root / "docs",
        root / "infrastructure",
        root / "projects" / "templates",
    ]
    excluded_parts = {"archive", "audit", "output", "__pycache__", "_skill-eval"}
    failures: list[str] = []
    candidates = sorted(root.glob("*.md"))
    for scan_root in scan_roots:
        candidates.extend(sorted(scan_root.rglob("*.md")))

    for md_path in candidates:
        if any(part in excluded_parts for part in md_path.relative_to(root).parts):
            continue
        text = md_path.read_text(encoding="utf-8", errors="replace")
        for line_no, line in enumerate(text.splitlines(), start=1):
            for match in stale_path.finditer(line):
                if match.group("name") in public_leaves:
                    failures.append(f"{md_path.relative_to(root)}:{line_no}: {match.group(0)}")

    assert not failures, "Use projects/templates/<name>/ for public exemplar paths:\n" + "\n".join(failures)


def test_docs_do_not_advertise_sia_task_dir_flag() -> None:
    """SIA validate uses a positional task_dir, not a --task-dir option."""
    root = _repo_root()
    docs = [
        root / "infrastructure" / "sia" / "SKILL.md",
        *sorted((root / "docs").rglob("*.md")),
        *sorted((root / "projects" / "templates" / "template_sia").rglob("*.md")),
    ]
    failures: list[str] = []
    for doc_path in docs:
        if any(
            part in {"archive", "audit", "output", "__pycache__", "_skill-eval"}
            for part in doc_path.relative_to(root).parts
        ):
            continue
        text = doc_path.read_text(encoding="utf-8", errors="replace")
        if "validate --task-dir" in text:
            failures.append(str(doc_path.relative_to(root)))

    assert not failures, "SIA docs must use `validate TASK_DIR`, not `validate --task-dir`: " + ", ".join(failures)


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
    doc_path = root / "docs" / "_generated" / "COUNTS.md"
    text = doc_path.read_text(encoding="utf-8")

    count_match = re.search(r"Last refreshed count: \*\*(?P<count>\d+)\*\*", text)
    assert count_match, "COUNTS.md must include the refreshed infrastructure Python-file count"

    documented = int(count_match.group("count"))
    # Count git-tracked source files, not an on-disk rglob: build- or test-generated
    # .py files under infrastructure/ (e.g. a version stub written during `uv sync`
    # in CI) would otherwise inflate the count and flap this gate per-environment.
    # The factsheet documents the tracked source surface, which is what drift means.
    tracked = subprocess.run(
        ["git", "ls-files", "infrastructure"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    actual = sum(1 for path in tracked if path.endswith(".py"))
    assert documented == actual, (
        f"COUNTS.md drifted from the tracked infrastructure Python-file count; documented={documented} actual={actual}"
    )


def test_canonical_facts_test_collections_match_current_counts() -> None:
    """The generated factsheet must not carry stale infra test collection counts."""
    root = _repo_root()
    doc_path = root / "docs" / "_generated" / "COUNTS.md"
    text = doc_path.read_text(encoding="utf-8")
    match = re.search(
        r"Result: \*\*(?P<project>\d+)\*\* project-scope infrastructure tests collected "
        r"and \*\*(?P<publishing>\d+)\*\* publishing tests collected",
        text,
    )
    assert match, "COUNTS.md must include project and publishing collection counts"

    def collected_count(path: str) -> int:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", path, "--collect-only", "-q", "--no-cov"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
        # Match the collected-count summary regardless of pytest verbosity: at
        # normal verbosity it is decorated ("===== 214 tests collected ====="),
        # at quiet ("-q") it is bare ("214 tests collected in 0.13s"). Don't
        # require the "=" rule bars, which depend on the inherited addopts -v/-q.
        count_match = re.search(r"(?P<count>\d+) tests? collected", proc.stdout)
        assert count_match, proc.stdout
        return int(count_match.group("count"))

    documented_project = int(match.group("project"))
    documented_publishing = int(match.group("publishing"))
    actual_project = collected_count("tests/infra_tests/project/")
    actual_publishing = collected_count("tests/infra_tests/publishing/")
    assert documented_project == actual_project
    assert documented_publishing == actual_publishing


def test_canonical_facts_exemplar_table_matches_public_scope() -> None:
    """The exemplar collection table must include every public template project."""
    root = _repo_root()
    text = (root / "docs" / "_generated" / "COUNTS.md").read_text(encoding="utf-8")
    expected = {name.split("/")[-1] for name in public_project_names(root)}
    table_match = re.search(
        r"\| Project \| Tests collected \| `src/` line\+branch coverage \|\n"
        r"\|[-| ]+\|\n(?P<body>(?:\| `template_[^`]+` \|[^\n]+\n)+)",
        text,
    )
    assert table_match, "COUNTS.md must include the exemplar collection table"
    documented = set(re.findall(r"\| `([^`]+)` \|", table_match.group("body")))
    assert documented == expected, (
        "COUNTS.md exemplar table drifted from public scope; "
        f"missing={sorted(expected - documented)} extra={sorted(documented - expected)}"
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
        assert '`--format`,\n        choices=["bibtex"]' not in text, doc_path


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
