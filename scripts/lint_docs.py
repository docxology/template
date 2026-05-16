#!/usr/bin/env python3
"""Thin orchestrator: run all documentation linters in sequence.

Invokes:
    1. infrastructure.validation.docs.mermaid_lint    — fenced ```mermaid blocks
    2. infrastructure.validation.docs.cross_link_lint — relative Markdown links
    3. infrastructure.validation.docs.consistency_lint — module-count + ghost-project
    4. infrastructure.validation.docs.doc_pair_lint   — folder-level doc pairs

Exits non-zero if any linter reports a failure. Designed for CI integration.

Usage:
    uv run python scripts/lint_docs.py [--mermaid-only|--links-only|--consistency-only|--doc-pairs-only]
                                      [--quiet] [--json]

Examples:
    uv run python scripts/lint_docs.py                # run everything
    uv run python scripts/lint_docs.py --mermaid-only # mermaid blocks only
    uv run python scripts/lint_docs.py --json         # machine-readable report
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

# Bootstrap: add repo root so the centralized helper itself is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

from infrastructure.core.logging.utils import (  # noqa: E402
    get_logger,
    log_header,
    log_success,
)
from infrastructure.validation.docs.consistency_lint import (  # noqa: E402
    Inconsistency,
    check_canonical_count_singularity,
    check_command_conventions,
    check_doc_imports_resolve,
    check_module_count_claims,
    check_no_ghost_projects,
    check_readme_files_list,
)
from infrastructure.validation.docs.cross_link_lint import (  # noqa: E402
    BrokenLink,
    find_broken_links,
)
from infrastructure.validation.docs.doc_pair_lint import (  # noqa: E402
    DocPairIssue,
    find_doc_pair_issues,
)
from infrastructure.validation.docs.mermaid_lint import (  # noqa: E402
    ValidationFailure,
    find_mermaid_blocks,
    mmdc_available,
    validate_blocks,
)

logger = get_logger(__name__)


def _doc_roots(repo_root: Path) -> list[Path]:
    """Default sweep roots: docs/, infrastructure/, .github/, plus root .md files."""
    roots: list[Path] = []
    for sub in ("docs", "infrastructure", ".github", "scripts"):
        candidate = repo_root / sub
        if candidate.is_dir():
            roots.append(candidate)
    for md in repo_root.glob("*.md"):
        roots.append(md)
    # also sweep projects/*/manuscript and projects/*/README only — not full src trees
    for project_md in (repo_root / "projects").glob("*/*.md"):
        roots.append(project_md)
    return roots


def _run_mermaid(repo_root: Path, *, quiet: bool) -> list[ValidationFailure]:
    blocks = find_mermaid_blocks(_doc_roots(repo_root))
    if not quiet:
        logger.info("mermaid: discovered %d blocks", len(blocks))
    if not mmdc_available():
        # Fail loudly — CI must install mmdc; locally surface the requirement.
        raise RuntimeError(
            "mmdc (mermaid-cli) not on PATH. Install with "
            "`npm install -g @mermaid-js/mermaid-cli` and provide a Chrome binary "
            "(set CHROME_EXECUTABLE_PATH or run "
            "`npx puppeteer browsers install chrome-headless-shell`)."
        )
    failures = validate_blocks(blocks)
    return failures


def _run_links(repo_root: Path, *, quiet: bool) -> list[BrokenLink]:
    broken = find_broken_links(_doc_roots(repo_root))
    if not quiet:
        logger.info("cross-links: %d broken", len(broken))
    return broken


def _run_consistency(repo_root: Path, *, quiet: bool) -> list[Inconsistency]:
    issues: list[Inconsistency] = []
    issues.extend(check_module_count_claims(repo_root))
    issues.extend(check_no_ghost_projects(repo_root))
    issues.extend(check_command_conventions(repo_root))
    issues.extend(check_doc_imports_resolve(repo_root))
    issues.extend(check_readme_files_list(repo_root))
    issues.extend(check_canonical_count_singularity(repo_root))
    if not quiet:
        logger.info("consistency: %d issues", len(issues))
    return issues


def _run_doc_pairs(repo_root: Path, *, quiet: bool) -> list[DocPairIssue]:
    issues = find_doc_pair_issues(repo_root)
    if not quiet:
        logger.info("doc-pairs: %d issues", len(issues))
    return issues


def _emit_text(
    *,
    mermaid: list[ValidationFailure] | None,
    links: list[BrokenLink] | None,
    consistency: list[Inconsistency] | None,
    doc_pairs: list[DocPairIssue] | None,
) -> None:
    if mermaid:
        log_header("MERMAID FAILURES", logger)
        for f in mermaid:
            logger.error(f.format())
    if links:
        log_header("BROKEN LINKS", logger)
        for ln in links:
            logger.error(ln.format())
    if consistency:
        log_header("CONSISTENCY ISSUES", logger)
        for ic in consistency:
            logger.error(ic.format())
    if doc_pairs:
        log_header("DOC-PAIR ISSUES", logger)
        for issue in doc_pairs:
            logger.error(issue.format())


def _emit_json(
    *,
    mermaid: list[ValidationFailure] | None,
    links: list[BrokenLink] | None,
    consistency: list[Inconsistency] | None,
    doc_pairs: list[DocPairIssue] | None,
    repo_root: Path,
) -> None:
    payload: dict[str, Any] = {
        "mermaid": [
            {
                "file": str(f.block.file.relative_to(repo_root))
                if _is_rel(f.block.file, repo_root)
                else str(f.block.file),
                "line": f.block.line,
                "kind": f.block.kind,
                "returncode": f.returncode,
                "stderr": f.stderr,
            }
            for f in (mermaid or [])
        ],
        "broken_links": [
            {
                "file": str(b.file.relative_to(repo_root))
                if _is_rel(b.file, repo_root)
                else str(b.file),
                "line": b.line,
                "text": b.text,
                "target": b.target,
                "reason": b.reason,
            }
            for b in (links or [])
        ],
        "consistency": [
            {
                "file": str(i.file.relative_to(repo_root))
                if _is_rel(i.file, repo_root)
                else str(i.file),
                "line": i.line,
                "category": i.category,
                "detail": i.detail,
            }
            for i in (consistency or [])
        ],
        "doc_pairs": [
            {
                "path": str(issue.path),
                "missing_readme": issue.missing_readme,
                "missing_agents": issue.missing_agents,
            }
            for issue in (doc_pairs or [])
        ],
    }
    sys.stdout.write(json.dumps(payload, indent=2) + "\n")


def _is_rel(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run mermaid + cross-link + consistency linters across the repo.",
    )
    parser.add_argument("--mermaid-only", action="store_true")
    parser.add_argument("--links-only", action="store_true")
    parser.add_argument("--consistency-only", action="store_true")
    parser.add_argument("--doc-pairs-only", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--strict-mermaid",
        action="store_true",
        help=(
            "Treat a missing mmdc binary as a hard failure (exit 2). Default: a "
            "missing mmdc is a graceful skip locally, but is auto-strict under CI "
            "(the `CI` env var) so the gate stays enforced where it matters."
        ),
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root (defaults to script's parent dir).",
    )
    args = parser.parse_args(argv)

    only_flags = sum(
        1
        for f in (
            args.mermaid_only,
            args.links_only,
            args.consistency_only,
            args.doc_pairs_only,
        )
        if f
    )
    if only_flags > 1:
        parser.error(
            "pass at most one of --mermaid-only, --links-only, "
            "--consistency-only, --doc-pairs-only"
        )

    run_mermaid = not (args.links_only or args.consistency_only or args.doc_pairs_only)
    run_links = not (args.mermaid_only or args.consistency_only or args.doc_pairs_only)
    run_consistency = not (args.mermaid_only or args.links_only or args.doc_pairs_only)
    run_doc_pairs = not (args.mermaid_only or args.links_only or args.consistency_only)

    repo_root = args.repo_root.resolve()

    mermaid_failures: list[ValidationFailure] | None = None
    broken_links: list[BrokenLink] | None = None
    consistency: list[Inconsistency] | None = None
    doc_pairs: list[DocPairIssue] | None = None
    runtime_error: str | None = None

    # mmdc is an optional local tool: missing it must not make the whole harness
    # unrunnable pre-push (that just gets the harness skipped, and rot creeps in
    # between CI runs). Default = graceful skip + warning. Strict (hard exit 2)
    # iff --strict-mermaid OR running under CI (`CI` env), so the gate stays
    # enforced exactly where mmdc is provisioned (see .github/workflows/ci.yml).
    mermaid_strict = bool(args.strict_mermaid or os.environ.get("CI"))
    if run_mermaid:
        try:
            mermaid_failures = _run_mermaid(repo_root, quiet=args.quiet)
        except RuntimeError as e:
            mermaid_failures = []
            if mermaid_strict:
                runtime_error = str(e)
                if not args.quiet:
                    logger.error("mermaid lint cannot run (strict): %s", e)
            elif not args.quiet:
                logger.warning(
                    "mermaid lint SKIPPED (mmdc unavailable): %s — "
                    "not failing locally; CI enforces it strictly.",
                    e,
                )
    if run_links:
        broken_links = _run_links(repo_root, quiet=args.quiet)
    if run_consistency:
        consistency = _run_consistency(repo_root, quiet=args.quiet)
    if run_doc_pairs:
        doc_pairs = _run_doc_pairs(repo_root, quiet=args.quiet)

    fail = bool(
        (mermaid_failures and len(mermaid_failures) > 0)
        or (broken_links and len(broken_links) > 0)
        or (consistency and len(consistency) > 0)
        or (doc_pairs and len(doc_pairs) > 0)
        or runtime_error
    )

    if args.json:
        _emit_json(
            mermaid=mermaid_failures,
            links=broken_links,
            consistency=consistency,
            doc_pairs=doc_pairs,
            repo_root=repo_root,
        )
    elif not args.quiet or fail:
        _emit_text(
            mermaid=mermaid_failures,
            links=broken_links,
            consistency=consistency,
            doc_pairs=doc_pairs,
        )
        if not fail:
            log_success("All documentation linters passed", logger)

    if runtime_error:
        return 2
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
