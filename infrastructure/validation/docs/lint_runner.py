"""Documentation lint orchestration across mermaid, links, consistency, and doc pairs."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infrastructure.core.logging.utils import get_logger, log_header, log_success
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.validation.docs.consistency_lint import (
    Inconsistency,
    check_canonical_count_singularity,
    check_command_conventions,
    check_doc_imports_resolve,
    check_memory_decision_rule_links,
    check_module_count_claims,
    check_no_ghost_projects,
    check_project_discovery_claims,
    check_readme_files_list,
    check_stale_shell_contracts,
)
from infrastructure.validation.docs.cross_link_lint import BrokenLink, find_broken_links
from infrastructure.validation.docs.doc_pair_lint import DocPairIssue, find_doc_pair_issues
from infrastructure.validation.docs.mermaid_lint import (
    ValidationFailure,
    find_mermaid_blocks,
    mmdc_available,
    validate_blocks,
)

logger = get_logger(__name__)


@dataclass
class DocsLintReport:
    """Data container for DocsLintReport."""

    mermaid: list[ValidationFailure] | None
    broken_links: list[BrokenLink] | None
    consistency: list[Inconsistency] | None
    doc_pairs: list[DocPairIssue] | None
    runtime_error: str | None = None

    @property
    def failed(self) -> bool:
        """Return True if the lint run failed."""
        return bool(
            (self.mermaid and len(self.mermaid) > 0)
            or (self.broken_links and len(self.broken_links) > 0)
            or (self.consistency and len(self.consistency) > 0)
            or (self.doc_pairs and len(self.doc_pairs) > 0)
            or self.runtime_error
        )

    @property
    def exit_code(self) -> int:
        """Return the exit code (0 for success, non-zero for failure)."""
        if self.runtime_error:
            return 2
        return 1 if self.failed else 0


def doc_roots(repo_root: Path) -> list[Path]:
    """Return the public template documentation roots for repo-wide linting."""
    roots: list[Path] = []
    for sub in ("docs", "infrastructure", ".github", "scripts", "tests"):
        candidate = repo_root / sub
        if candidate.is_dir():
            roots.append(candidate)
    for md in repo_root.glob("*.md"):
        roots.append(md)
    projects = repo_root / "projects"
    if projects.is_dir():
        for project_name in PUBLIC_PROJECT_NAMES:
            project = projects / project_name
            if project.is_dir():
                roots.append(project)
    return roots


def _is_rel(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def run_mermaid_lint(repo_root: Path, *, quiet: bool) -> list[ValidationFailure]:
    """Run mermaid lint."""
    blocks = find_mermaid_blocks(doc_roots(repo_root))
    if not quiet:
        logger.info("mermaid: discovered %d blocks", len(blocks))
    if not mmdc_available():
        raise RuntimeError(
            "mmdc (mermaid-cli) not on PATH. Install with "
            "`npm install -g @mermaid-js/mermaid-cli` and provide a Chrome binary "
            "(set CHROME_EXECUTABLE_PATH or run "
            "`npx puppeteer browsers install chrome-headless-shell`)."
        )
    return validate_blocks(blocks)


def run_links_lint(repo_root: Path, *, quiet: bool) -> list[BrokenLink]:
    """Run links lint."""
    broken = find_broken_links(doc_roots(repo_root))
    if not quiet:
        logger.info("cross-links: %d broken", len(broken))
    return broken


def run_consistency_lint(repo_root: Path, *, quiet: bool) -> list[Inconsistency]:
    """Run consistency lint."""
    issues: list[Inconsistency] = []
    issues.extend(check_module_count_claims(repo_root))
    issues.extend(check_no_ghost_projects(repo_root))
    issues.extend(check_command_conventions(repo_root))
    issues.extend(check_doc_imports_resolve(repo_root))
    issues.extend(check_readme_files_list(repo_root))
    issues.extend(check_project_discovery_claims(repo_root))
    issues.extend(check_canonical_count_singularity(repo_root))
    issues.extend(check_memory_decision_rule_links(repo_root))
    issues.extend(check_stale_shell_contracts(repo_root))
    if not quiet:
        logger.info("consistency: %d issues", len(issues))
    return issues


def run_doc_pairs_lint(repo_root: Path, *, quiet: bool) -> list[DocPairIssue]:
    """Run doc pairs lint."""
    issues = find_doc_pair_issues(repo_root)
    if not quiet:
        logger.info("doc-pairs: %d issues", len(issues))
    return issues


def emit_text_report(report: DocsLintReport) -> None:
    """Emit text report."""
    if report.mermaid:
        log_header("MERMAID FAILURES", logger)
        for failure in report.mermaid:
            logger.error(failure.format())
    if report.broken_links:
        log_header("BROKEN LINKS", logger)
        for link in report.broken_links:
            logger.error(link.format())
    if report.consistency:
        log_header("CONSISTENCY ISSUES", logger)
        for issue in report.consistency:
            logger.error(issue.format())
    if report.doc_pairs:
        log_header("DOC-PAIR ISSUES", logger)
        for pair_issue in report.doc_pairs:
            logger.error(pair_issue.format())


def emit_json_report(report: DocsLintReport, repo_root: Path) -> str:
    """Emit json report."""
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
            for f in (report.mermaid or [])
        ],
        "broken_links": [
            {
                "file": str(b.file.relative_to(repo_root)) if _is_rel(b.file, repo_root) else str(b.file),
                "line": b.line,
                "text": b.text,
                "target": b.target,
                "reason": b.reason,
            }
            for b in (report.broken_links or [])
        ],
        "consistency": [
            {
                "file": str(i.file.relative_to(repo_root)) if _is_rel(i.file, repo_root) else str(i.file),
                "line": i.line,
                "category": i.category,
                "detail": i.detail,
            }
            for i in (report.consistency or [])
        ],
        "doc_pairs": [
            {
                "path": str(issue.path),
                "missing_readme": issue.missing_readme,
                "missing_agents": issue.missing_agents,
            }
            for issue in (report.doc_pairs or [])
        ],
    }
    return json.dumps(payload, indent=2) + "\n"


def run_docs_lint(
    repo_root: Path,
    *,
    mermaid_only: bool = False,
    links_only: bool = False,
    consistency_only: bool = False,
    doc_pairs_only: bool = False,
    quiet: bool = False,
    strict_mermaid: bool = False,
) -> DocsLintReport:
    """Run docs lint."""
    only_flags = sum(1 for f in (mermaid_only, links_only, consistency_only, doc_pairs_only) if f)
    if only_flags > 1:
        raise ValueError("pass at most one of mermaid_only, links_only, consistency_only, doc_pairs_only")

    from infrastructure.validation.docs.scan_scope import iter_markdown_files

    if not iter_markdown_files([repo_root]):
        # Every linter below rides this discovery; a zero-file scan means the
        # scope itself is broken (it once silently excluded whole worktree
        # checkouts) and each linter would return a vacuous pass. Fail loud.
        raise ValueError(
            f"documentation lint discovered 0 markdown files under {repo_root} — "
            "scan scope is broken; refusing to report a vacuous pass"
        )

    run_mermaid = not (links_only or consistency_only or doc_pairs_only)
    run_links = not (mermaid_only or consistency_only or doc_pairs_only)
    run_consistency = not (mermaid_only or links_only or doc_pairs_only)
    run_doc_pairs = not (mermaid_only or links_only or consistency_only)

    mermaid_failures: list[ValidationFailure] | None = None
    broken_links: list[BrokenLink] | None = None
    consistency: list[Inconsistency] | None = None
    doc_pairs: list[DocPairIssue] | None = None
    runtime_error: str | None = None

    mermaid_strict = bool(strict_mermaid or os.environ.get("CI"))
    if run_mermaid:
        try:
            mermaid_failures = run_mermaid_lint(repo_root, quiet=quiet)
        except RuntimeError as exc:
            mermaid_failures = []
            if mermaid_strict:
                runtime_error = str(exc)
                if not quiet:
                    logger.error("mermaid lint cannot run (strict): %s", exc)
            elif not quiet:
                logger.warning(
                    "mermaid lint SKIPPED (mmdc unavailable): %s — not failing locally; CI enforces it strictly.",
                    exc,
                )
    if run_links:
        broken_links = run_links_lint(repo_root, quiet=quiet)
    if run_consistency:
        consistency = run_consistency_lint(repo_root, quiet=quiet)
    if run_doc_pairs:
        doc_pairs = run_doc_pairs_lint(repo_root, quiet=quiet)

    return DocsLintReport(
        mermaid=mermaid_failures,
        broken_links=broken_links,
        consistency=consistency,
        doc_pairs=doc_pairs,
        runtime_error=runtime_error,
    )


def format_docs_lint_report(
    report: DocsLintReport,
    repo_root: Path,
    *,
    as_json: bool = False,
    quiet: bool = False,
) -> str | None:
    """Format docs lint report."""
    if as_json:
        return emit_json_report(report, repo_root)
    if not quiet or report.failed:
        emit_text_report(report)
        if not report.failed:
            log_success("All documentation linters passed", logger)
    return None
