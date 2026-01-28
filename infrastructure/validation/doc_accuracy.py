"""Phase 2: Accuracy Verification for documentation scanning."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import yaml

from infrastructure.core.logging_utils import get_logger
from infrastructure.validation.doc_models import AccuracyIssue, LinkIssue

logger = get_logger(__name__)


def extract_headings(content: str) -> Set[str]:
    """Extract all heading anchors from markdown."""
    headings = set()

    # Pattern for headings with explicit anchors
    anchor_pattern = re.compile(r"^#+\s+.*\{#([^}]+)\}", re.MULTILINE)
    for match in anchor_pattern.finditer(content):
        headings.add(match.group(1))

    # Pattern for regular headings (convert to anchor format)
    heading_pattern = re.compile(r"^(#+)\s+(.+)$", re.MULTILINE)
    for match in heading_pattern.finditer(content):
        heading_text = match.group(2).strip()
        # Convert to anchor format
        anchor = re.sub(r"[^\w\s-]", "", heading_text.lower())
        anchor = re.sub(r"[-\s]+", "-", anchor)
        anchor = anchor.strip("-")
        if anchor:
            headings.add(anchor)

    return headings


def resolve_file_path(
    target: str, source_file: Path, repo_root: Path
) -> Tuple[bool, str, str]:
    """Resolve a file path relative to source file.

    Returns:
        Tuple of (exists: bool, message: str, path_type: str)
        path_type is 'file', 'directory', or 'unknown'
    """
    # Check if target is a directory reference (ends with /)
    is_directory_ref = target.endswith("/")

    if target.startswith("../"):
        levels_up = target.count("../")
        target_path = source_file.parent
        for _ in range(levels_up):
            target_path = target_path.parent
        target_path = target_path / target.replace("../", "").replace("./", "")
    elif target.startswith("./"):
        target_path = source_file.parent / target[2:]
    else:
        target_path = source_file.parent / target

    try:
        target_path = target_path.resolve()
        repo_root_resolved = repo_root.resolve()

        # Check if path is within repository
        try:
            target_path.relative_to(repo_root_resolved)
        except ValueError:
            return False, f"Path outside repository: {target_path}", "unknown"

        # Check if it exists
        if target_path.exists():
            if target_path.is_file():
                return True, "", "file"
            elif target_path.is_dir():
                # If it's a directory and target ends with /, it's valid
                if is_directory_ref:
                    return True, "", "directory"
                # If it's a directory but target doesn't end with /, might be intentional
                # Check if there's a file with same name (without extension)
                return True, "", "directory"
            else:
                return (
                    False,
                    f"Path exists but is not a file or directory: {target_path}",
                    "unknown",
                )
        else:
            # Path doesn't exist
            if is_directory_ref:
                return False, f"Directory does not exist: {target_path}", "directory"
            else:
                # Check if it might be a file
                # Remove file extension and check if directory exists
                if target_path.suffix:
                    dir_path = target_path.parent
                    if dir_path.exists() and dir_path.is_dir():
                        return False, f"File does not exist: {target_path}", "file"
                return False, f"File does not exist: {target_path}", "file"
    except Exception as e:
        return False, f"Error resolving path: {e}", "unknown"


def check_links(
    md_files: List[Path], repo_root: Path, all_headings: Dict[str, Set[str]]
) -> List[LinkIssue]:
    """Check all links in markdown files.

    Improved to skip links inside code blocks.
    """
    issues = []
    link_pattern = re.compile(r"\[([^\]]+)\]\(([^\)]+)\)")

    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
            file_key = str(md_file.relative_to(repo_root))

            # Remove code blocks to avoid false positives
            code_block_pattern = re.compile(r"```[\s\S]*?```", re.MULTILINE)
            code_block_ranges = []
            for cb_match in code_block_pattern.finditer(content):
                code_block_ranges.append((cb_match.start(), cb_match.end()))

            for match in link_pattern.finditer(content):
                # Skip if link is inside a code block
                link_start = match.start()
                link_end = match.end()
                in_code_block = any(
                    start <= link_start < end for start, end in code_block_ranges
                )
                if in_code_block:
                    continue

                link_text = match.group(1)
                target = match.group(2)
                line_num = content[: match.start()].count("\n") + 1

                # Check anchor links
                if target.startswith("#"):
                    anchor = target.lstrip("#")
                    if file_key in all_headings:
                        if anchor not in all_headings[file_key]:
                            issues.append(
                                LinkIssue(
                                    file=file_key,
                                    line=line_num,
                                    link_text=link_text,
                                    target=target,
                                    issue_type="broken_anchor",
                                    issue_message=f"Anchor '{anchor}' not found in file",
                                )
                            )

                # Check file references
                elif not target.startswith("http"):
                    file_part = target.split("#")[0] if "#" in target else target
                    if file_part:
                        resolved = resolve_file_path(file_part, md_file, repo_root)
                        exists, message, path_type = resolved
                        if not exists:
                            # Only flag as error if it's clearly a file reference
                            # Directory references are often valid (especially if they end with /)
                            if path_type == "file" or (
                                path_type == "directory" and not file_part.endswith("/")
                            ):
                                # Determine severity based on path type
                                if path_type == "file":
                                    issue_type = "broken_file"
                                    severity = "error"
                                elif path_type == "directory":
                                    issue_type = "broken_directory"
                                    severity = (
                                        "warning"  # Directory might be intentional
                                    )
                                else:
                                    issue_type = "broken_path"
                                    severity = "warning"

                                issues.append(
                                    LinkIssue(
                                        file=file_key,
                                        line=line_num,
                                        link_text=link_text,
                                        target=target,
                                        issue_type=issue_type,
                                        issue_message=message,
                                        severity=severity,
                                    )
                                )
        except Exception as e:
            logger.warning("Error checking links in %s: %s", md_file, e)

    return issues


def extract_script_name(command: str) -> Optional[str]:
    """Extract script name from command."""
    # Look for ./script.sh or python script.py patterns
    match = re.search(r"\./([\w/]+\.(?:sh|py))", command)
    if match:
        return match.group(1)
    match = re.search(r"python.*?([\w/]+\.py)", command)
    if match:
        return match.group(1)
    return None


def verify_commands(md_files: List[Path], repo_root: Path) -> List[AccuracyIssue]:
    """Verify commands in documentation match actual implementations."""
    issues = []
    command_pattern = re.compile(r"```(?:bash|sh|shell)?\n(.*?)\n```", re.DOTALL)

    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
            file_key = str(md_file.relative_to(repo_root))

            for match in command_pattern.finditer(content):
                command_block = match.group(1)
                line_num = content[: match.start()].count("\n") + 1

                # Check for common script references
                for line in command_block.split("\n"):
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Check if script exists
                        if "./" in line or line.startswith("python"):
                            script_name = extract_script_name(line)
                            if script_name:
                                script_path = repo_root / script_name
                                if not script_path.exists():
                                    issues.append(
                                        AccuracyIssue(
                                            file=file_key,
                                            line=line_num,
                                            issue_type="command",
                                            issue_message=f"Referenced script '{script_name}' does not exist",
                                            severity="error",
                                        )
                                    )
        except Exception:
            pass

    return issues


def check_file_paths(md_files: List[Path], repo_root: Path) -> List[AccuracyIssue]:
    """Check file paths mentioned in documentation."""
    issues = []
    path_pattern = re.compile(r"`([\w/\.\-]+)`")

    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
            file_key = str(md_file.relative_to(repo_root))

            for match in path_pattern.finditer(content):
                path_str = match.group(1)
                line_num = content[: match.start()].count("\n") + 1

                # Check if it looks like a file path
                if "/" in path_str or path_str.endswith(
                    (".md", ".py", ".sh", ".yaml", ".toml")
                ):
                    resolved = resolve_file_path(path_str, md_file, repo_root)
                    exists, message, path_type = resolved
                    if not exists and "output" not in path_str:
                        # Only flag file references, not directory references
                        if path_type == "file" or (
                            path_type == "directory" and not path_str.endswith("/")
                        ):
                            issues.append(
                                AccuracyIssue(
                                    file=file_key,
                                    line=line_num,
                                    issue_type="path",
                                    issue_message=f"Referenced path '{path_str}' may not exist: {message}",
                                    severity=(
                                        "warning"
                                        if path_type == "directory"
                                        else "error"
                                    ),
                                )
                            )
        except Exception:
            pass

    return issues


def validate_config_options(
    md_files: List[Path], config_files: Dict[str, Path]
) -> List[AccuracyIssue]:
    """Validate configuration options mentioned in docs."""
    issues = []

    # Load actual config files
    config_data = {}
    if "config.yaml" in config_files:
        try:
            with open(config_files["config.yaml"], "r") as f:
                config_data["yaml"] = yaml.safe_load(f) or {}
        except Exception:
            pass

    # Check documentation for config references
    # This is a simplified check - could be enhanced to actually validate against config schema

    return issues


def check_terminology(md_files: List[Path]) -> List[AccuracyIssue]:
    """Check terminology consistency across documentation."""
    issues = []
    # This would check for inconsistent terminology
    # For now, return empty - could be enhanced with a terminology dictionary
    return issues


def run_accuracy_phase(
    md_files: List[Path], repo_root: Path, config_files: Dict[str, Path]
) -> Tuple[Dict, List[LinkIssue], List[AccuracyIssue], Dict[str, Set[str]]]:
    """Run Phase 2: Accuracy Verification.

    Args:
        md_files: List of markdown files to check
        repo_root: Root path of the repository
        config_files: Dictionary of config file paths

    Returns:
        Tuple of (accuracy_report, link_issues, accuracy_issues, all_headings)
    """
    logger.info("Phase 2: Accuracy Verification...")

    # Collect headings for anchor validation
    all_headings: Dict[str, Set[str]] = {}
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
            all_headings[str(md_file.relative_to(repo_root))] = extract_headings(
                content
            )
        except Exception as e:
            logger.warning("Error reading %s: %s", md_file, e)

    # Check links
    link_issues = check_links(md_files, repo_root, all_headings)
    logger.info("Found %d link issues", len(link_issues))

    # Verify commands
    command_issues = verify_commands(md_files, repo_root)
    logger.info("Found %d command accuracy issues", len(command_issues))

    # Check file paths
    path_issues = check_file_paths(md_files, repo_root)
    logger.info("Found %d file path issues", len(path_issues))

    # Validate configuration options
    config_issues = validate_config_options(md_files, config_files)
    logger.info("Found %d configuration issues", len(config_issues))

    # Check terminology consistency
    terminology_issues = check_terminology(md_files)
    logger.info("Found %d terminology issues", len(terminology_issues))

    # Combine all accuracy issues
    accuracy_issues = command_issues + path_issues + config_issues + terminology_issues

    accuracy_report = {
        "link_issues": len(link_issues),
        "command_issues": len(command_issues),
        "path_issues": len(path_issues),
        "config_issues": len(config_issues),
        "terminology_issues": len(terminology_issues),
        "total_issues": len(link_issues) + len(accuracy_issues),
    }

    return accuracy_report, link_issues, accuracy_issues, all_headings
