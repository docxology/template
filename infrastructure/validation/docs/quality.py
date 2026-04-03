"""Phase 4: Quality Assessment for documentation scanning."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from infrastructure.core.logging.utils import get_logger
from infrastructure.validation.docs.models import QualityIssue

logger = get_logger(__name__)


def assess_clarity(
    content: str, md_file: Path, lines: list[str], repo_root: Path
) -> list[QualityIssue]:
    """Assess clarity and readability of a markdown document.

    Flags lines that exceed 120 characters, which may harm readability in
    narrow viewports or code-review diffs.

    Args:
        content: Full file content as a string.
        md_file: Absolute path to the markdown file being assessed.
        lines: File content split into individual lines.
        repo_root: Repository root used to compute relative file paths in issues.

    Returns:
        List of QualityIssue instances describing readability problems found.
    """
    issues = []
    file_key = str(md_file.relative_to(repo_root))

    # Check for very long lines
    for i, line in enumerate(lines, 1):
        if len(line) > 120 and not line.startswith("```"):
            issues.append(
                QualityIssue(
                    file=file_key,
                    line=i,
                    issue_type="clarity",
                    issue_message="Line exceeds 120 characters - may affect readability",
                    severity="info",
                )
            )

    return issues


_IMPERATIVE_VERBS: frozenset[str] = frozenset([
    "run", "execute", "install", "use", "configure", "create", "set",
    "add", "remove", "check", "verify", "update", "open", "close",
    "edit", "delete", "build", "deploy", "test", "start", "stop",
    "copy", "move", "rename", "make", "write", "read", "load", "save",
    "enable", "disable", "restart", "connect", "specify", "define",
    "provide", "pass", "import", "export", "generate", "select",
    "ensure", "include", "exclude", "replace", "modify", "review",
])


def assess_actionability(
    content: str, md_file: Path, lines: list[str], repo_root: Path
) -> list[QualityIssue]:
    """Assess whether list-item instructions in the document are actionable.

    Scans bulleted and numbered list items outside code blocks and checks
    whether each item begins with an imperative verb.  Items that start with
    a non-imperative word (e.g. passive constructs like "The user should …")
    are flagged as potentially non-actionable.

    Args:
        content: Full file content as a string.
        md_file: Absolute path to the markdown file being assessed.
        lines: File content split into individual lines.
        repo_root: Repository root used to compute relative file paths in issues.

    Returns:
        List of QualityIssue instances describing non-actionable list items.
    """
    issues: list[QualityIssue] = []
    file_key = str(md_file.relative_to(repo_root))
    in_code_block = False

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        # Match bulleted or numbered list items
        is_bullet = stripped.startswith(("- ", "* ", "+ "))
        is_numbered = (
            len(stripped) > 2
            and stripped[0].isdigit()
            and len(stripped) > 1
            and stripped[1] in ".)"
        )
        if not (is_bullet or is_numbered):
            continue

        # Extract text after the list marker
        if is_bullet:
            item_text = stripped[2:].strip()
        else:
            item_text = stripped[stripped.index(stripped[1]) + 1:].strip()

        if not item_text or item_text.startswith("`"):
            # Inline code command — always actionable
            continue

        first_word = item_text.split()[0].lower().rstrip(".,:")
        if first_word not in _IMPERATIVE_VERBS:
            issues.append(
                QualityIssue(
                    file=file_key,
                    line=i,
                    issue_type="actionability",
                    issue_message=(
                        f"List item may lack an imperative directive "
                        f"(starts with '{first_word}')"
                    ),
                    severity="info",
                )
            )

    return issues


def assess_maintainability(
    content: str, md_file: Path, lines: list[str], repo_root: Path
) -> list[QualityIssue]:
    """Assess maintainability of the document by detecting duplicate lines.

    Flags non-blank, non-heading lines that appear three or more times in the
    same file.  Repeated lines suggest copy-pasted content that should be
    consolidated or extracted to a shared reference.

    Args:
        content: Full file content as a string.
        md_file: Absolute path to the markdown file being assessed.
        lines: File content split into individual lines.
        repo_root: Repository root used to compute relative file paths in issues.

    Returns:
        List of QualityIssue instances describing repeated lines.
    """
    issues: list[QualityIssue] = []
    file_key = str(md_file.relative_to(repo_root))

    first_occurrence: dict[str, int] = {}
    line_counts: dict[str, int] = {}
    in_code_block = False

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block or not stripped or stripped.startswith("#"):
            continue

        if stripped not in first_occurrence:
            first_occurrence[stripped] = i
        line_counts[stripped] = line_counts.get(stripped, 0) + 1

    for line_text, count in line_counts.items():
        if count >= 3:
            preview = line_text[:60] + ("…" if len(line_text) > 60 else "")
            issues.append(
                QualityIssue(
                    file=file_key,
                    line=first_occurrence[line_text],
                    issue_type="maintainability",
                    issue_message=(
                        f"Line repeated {count} times — consider consolidating: '{preview}'"
                    ),
                    severity="info",
                )
            )

    return issues


def check_formatting(
    content: str, md_file: Path, lines: list[str], repo_root: Path
) -> list[QualityIssue]:
    """Check markdown formatting consistency.

    Validates heading hierarchy (no skipped levels) and other structural
    formatting rules that affect rendered output and readability.

    Args:
        content: Full file content as a string.
        md_file: Absolute path to the markdown file being assessed.
        lines: File content split into individual lines.
        repo_root: Repository root used to compute relative file paths in issues.

    Returns:
        List of QualityIssue instances describing formatting problems found.
    """
    issues = []
    file_key = str(md_file.relative_to(repo_root))

    # Check heading hierarchy
    prev_level = 0
    for i, line in enumerate(lines, 1):
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            if level > prev_level + 1:
                issues.append(
                    QualityIssue(
                        file=file_key,
                        line=i,
                        issue_type="formatting",
                        issue_message=f"Heading level jumps from {prev_level} to {level}",
                        severity="info",
                    )
                )
            prev_level = level

    return issues


def group_quality_by_type(issues: list[QualityIssue]) -> dict[str, int]:
    """Group quality issues by type."""
    types: dict[str, int] = defaultdict(int)
    for issue in issues:
        types[issue.issue_type] += 1
    return dict(types)


def group_quality_by_severity(issues: list[QualityIssue]) -> dict[str, int]:
    """Group quality issues by severity."""
    severities: dict[str, int] = defaultdict(int)
    for issue in issues:
        severities[issue.severity] += 1
    return dict(severities)


def run_quality_phase(
    md_files: list[Path], repo_root: Path
) -> tuple[dict[str, Any], list[QualityIssue]]:
    """Run Phase 4: Quality Assessment.

    Args:
        md_files: List of markdown files to assess
        repo_root: Root path of the repository

    Returns:
        Tuple of (quality_report, quality_issues)
    """
    logger.info("Phase 4: Quality Assessment...")

    quality_issues = []

    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
            lines = content.split("\n")

            # Check clarity and readability
            clarity_issues = assess_clarity(content, md_file, lines, repo_root)
            quality_issues.extend(clarity_issues)

            # Check actionability
            actionability_issues = assess_actionability(content, md_file, lines, repo_root)
            quality_issues.extend(actionability_issues)

            # Check maintainability
            maintainability_issues = assess_maintainability(content, md_file, lines, repo_root)
            quality_issues.extend(maintainability_issues)

            # Check formatting
            formatting_issues = check_formatting(content, md_file, lines, repo_root)
            quality_issues.extend(formatting_issues)

        except Exception as e:  # noqa: BLE001
            logger.warning(f"Error assessing {md_file}: {e}")

    quality_report = {
        "total_issues": len(quality_issues),
        "by_type": group_quality_by_type(quality_issues),
        "severity_breakdown": group_quality_by_severity(quality_issues),
    }

    logger.info(f"Found {len(quality_issues)} quality issues")
    return quality_report, quality_issues
