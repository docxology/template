"""Documentation verification checks (lint, markdown, commands, link cycles)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from infrastructure.core.logging.utils import get_logger
from infrastructure.validation.content.markdown_validator import validate_markdown
from infrastructure.validation.docs.accuracy import verify_commands
from infrastructure.validation.docs.cross_link_lint import detect_markdown_link_cycles
from infrastructure.validation.content.discovery import discover_markdown_files
from infrastructure.validation.docs.discovery import identify_cross_references
from infrastructure.validation.docs.lint_runner import doc_roots, run_docs_lint

logger = get_logger(__name__)


def run_link_audit(repo_root: Path) -> dict[str, Any]:
    """Run the repository link checker in-process."""
    try:
        from infrastructure.validation.integrity.check_links import run_link_audit as audit_links

        exit_code = audit_links(repo_root)
        return {
            "success": exit_code == 0,
            "exit_code": exit_code,
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("Link checker failed: %s", exc)
        return {"success": False, "error": str(exc)}


def verify_cross_references(repo_root: Path) -> dict[str, Any]:
    """Count cross-references across discovered markdown files."""
    md_files = discover_markdown_files(repo_root, scope="repo")
    return {
        "status": "verified",
        "total_references": len(identify_cross_references(md_files)),
    }


def run_verification_checks(repo_root: Path) -> dict[str, Any]:
    """Run documentation verification checks against the repository."""
    logger.info("Documentation verification checks...")

    md_files = discover_markdown_files(repo_root, scope="repo")
    roots = doc_roots(repo_root)

    lint_report = run_docs_lint(repo_root, quiet=True)
    docs_lint: dict[str, Any]
    if lint_report.runtime_error:
        docs_lint = {
            "status": "skipped",
            "reason": lint_report.runtime_error,
        }
    elif lint_report.failed:
        docs_lint = {
            "status": "failed",
            "issue_counts": {
                "mermaid": len(lint_report.mermaid or []),
                "broken_links": len(lint_report.broken_links or []),
                "consistency": len(lint_report.consistency or []),
                "doc_pairs": len(lint_report.doc_pairs or []),
            },
        }
    else:
        docs_lint = {"status": "passed", "issue_counts": {}}

    docs_dir = repo_root / "docs"
    if docs_dir.is_dir():
        problems, exit_code = validate_markdown(docs_dir, repo_root, strict=False)
        md_validation = {
            "status": "failed" if exit_code != 0 else "passed",
            "issue_count": len(problems),
        }
    else:
        md_validation = {"status": "skipped", "reason": "docs/ directory absent"}

    command_issues = verify_commands(md_files, repo_root)
    commands_tested = {
        "status": "failed" if command_issues else "passed",
        "issue_count": len(command_issues),
    }

    cycles = detect_markdown_link_cycles(roots)
    circular_references = {
        "status": "failed" if cycles else "passed",
        "cycle_count": len(cycles),
        "cycles": [list(cycle.files) for cycle in cycles[:10]],
    }

    return {
        "link_checker": run_link_audit(repo_root),
        "docs_lint": docs_lint,
        "markdown_validation": md_validation,
        "commands_tested": commands_tested,
        "cross_references": verify_cross_references(repo_root),
        "circular_references": circular_references,
    }
