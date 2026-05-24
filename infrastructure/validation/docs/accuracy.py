"""Accuracy verification for documentation scanning."""

import re
from pathlib import Path
from typing import Any

import yaml

from infrastructure.core.logging.utils import get_logger
from infrastructure.validation.docs.consistency_lint import is_placeholder_name
from infrastructure.validation.docs.models import LinkIssue, ScanAccuracyIssue

logger = get_logger(__name__)

_CONFIG_REF_RE = re.compile(
    r"`([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+)`",
    re.IGNORECASE,
)

_TERMINOLOGY_RULES: tuple[tuple[re.Pattern[str], str, str], ...] = (
    (
        re.compile(r"\bzero\s+mock(?:s|ed|ing)?\b", re.IGNORECASE),
        "no mocks",
        "Repository policy uses 'no mocks' (see tests/AGENTS.md).",
    ),
    (
        re.compile(r"\b8\s+stage(?:s)?\b(?![^\n]{0,40}(?:core-only|excluding|exclude))", re.IGNORECASE),
        "stage-count phrasing",
        "Default full pipeline is 10 core+LLM stages; 8 applies only with --core-only.",
    ),
)


def extract_headings(content: str) -> set[str]:
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


def resolve_file_path(target: str, source_file: Path, repo_root: Path) -> tuple[bool, str, str]:
    """Resolve a file path relative to source file.

    Returns:
        Tuple of (exists: bool, message: str, path_type: str)
        path_type is 'file', 'directory', or 'unknown'
    """
    from infrastructure.validation.paths import resolve_markdown_target

    resolved = resolve_markdown_target(target, source_file, repo_root)
    path_type = (
        resolved.path_type if resolved.path_type != "unknown" else ("directory" if target.endswith("/") else "file")
    )
    return resolved.exists, resolved.message, path_type


def check_links(md_files: list[Path], repo_root: Path, all_headings: dict[str, set[str]]) -> list[LinkIssue]:
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
                match.end()
                in_code_block = any(start <= link_start < end for start, end in code_block_ranges)
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
                            if path_type == "file" or (path_type == "directory" and not file_part.endswith("/")):
                                # Determine severity based on path type
                                if path_type == "file":
                                    issue_type = "broken_file"
                                    severity = "error"
                                elif path_type == "directory":
                                    issue_type = "broken_directory"
                                    severity = "warning"  # Directory might be intentional
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
        except (OSError, UnicodeDecodeError) as e:
            logger.warning(f"Error checking links in {md_file}: {e}")

    return issues


def extract_script_name(command: str) -> str | None:
    """Extract script name from command."""
    # Look for ./script.sh or python script.py patterns
    match = re.search(r"\./([\w/]+\.(?:sh|py))", command)
    if match:
        return match.group(1)
    match = re.search(r"python.*?([\w/]+\.py)", command)
    if match:
        return match.group(1)
    return None


def verify_commands(md_files: list[Path], repo_root: Path) -> list[ScanAccuracyIssue]:
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
                                        ScanAccuracyIssue(
                                            category="command",
                                            severity="error",
                                            file=file_key,
                                            line=line_num,
                                            message=f"Referenced script '{script_name}' does not exist",  # noqa: E501
                                        )
                                    )
        except (OSError, UnicodeDecodeError) as e:
            logger.warning(f"Failed to check command references in {md_file}: {e}")

    return issues


def check_file_paths(md_files: list[Path], repo_root: Path) -> list[ScanAccuracyIssue]:
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
                if "/" in path_str or path_str.endswith((".md", ".py", ".sh", ".yaml", ".toml")):
                    resolved = resolve_file_path(path_str, md_file, repo_root)
                    exists, message, path_type = resolved
                    if not exists and "output" not in path_str:
                        # Only flag file references, not directory references
                        if path_type == "file" or (path_type == "directory" and not path_str.endswith("/")):
                            issues.append(
                                ScanAccuracyIssue(
                                    category="path",
                                    severity=("warning" if path_type == "directory" else "error"),
                                    file=file_key,
                                    line=line_num,
                                    message=f"Referenced path '{path_str}' may not exist: {message}",  # noqa: E501
                                )
                            )
        except (OSError, UnicodeDecodeError) as e:
            logger.warning(f"Failed to check file paths in {md_file}: {e}")

    return issues


def _flatten_yaml_keys(data: Any, prefix: str = "") -> set[str]:
    """Return dotted paths for keys in a nested YAML mapping."""
    keys: set[str] = set()
    if isinstance(data, dict):
        for key, value in data.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            keys.add(path)
            keys.update(_flatten_yaml_keys(value, path))
    return keys


def _load_known_config_keys(config_files: dict[str, Path]) -> set[str]:
    known: set[str] = set()
    for name, path in config_files.items():
        if not name.endswith((".yaml", ".yml")) or not path.exists():
            continue
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError, ValueError) as exc:
            logger.debug("Failed to load %s for config validation: %s", name, exc)
            continue
        known.update(_flatten_yaml_keys(data))
    return known


def _config_ref_known(ref: str, known_keys: set[str]) -> bool:
    if ref in known_keys:
        return True
    return any(key.startswith(f"{ref}.") for key in known_keys)


def validate_config_options(
    md_files: list[Path],
    config_files: dict[str, Path],
    repo_root: Path,
) -> list[ScanAccuracyIssue]:
    """Validate configuration options mentioned in docs against loaded config files."""
    issues: list[ScanAccuracyIssue] = []
    known_keys = _load_known_config_keys(config_files)
    if not known_keys:
        return issues

    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
            file_key = str(md_file.relative_to(repo_root))
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            logger.warning("Failed to read %s for config validation: %s", md_file, exc)
            continue

        for match in _CONFIG_REF_RE.finditer(content):
            ref = match.group(1)
            if "/" in ref or ref.endswith((".md", ".py", ".yaml", ".yml", ".toml", ".sh")):
                continue
            if is_placeholder_name(ref.split(".")[0]):
                continue
            if _config_ref_known(ref, known_keys):
                continue
            line_num = content[: match.start()].count("\n") + 1
            issues.append(
                ScanAccuracyIssue(
                    category="config",
                    severity="warning",
                    file=file_key,
                    line=line_num,
                    message=f"Config reference `{ref}` not found in loaded config files",
                )
            )
    return issues


def check_terminology(md_files: list[Path], repo_root: Path) -> list[ScanAccuracyIssue]:
    """Check terminology consistency against curated repository conventions."""
    issues: list[ScanAccuracyIssue] = []
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
            file_key = str(md_file.relative_to(repo_root))
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            logger.warning("Failed to read %s for terminology check: %s", md_file, exc)
            continue

        for pattern, preferred, detail in _TERMINOLOGY_RULES:
            for match in pattern.finditer(content):
                line_num = content[: match.start()].count("\n") + 1
                issues.append(
                    ScanAccuracyIssue(
                        category="terminology",
                        severity="info",
                        file=file_key,
                        line=line_num,
                        message=f"Prefer '{preferred}': {detail}",
                        details=match.group(0),
                    )
                )
    return issues


def verify_documentation_accuracy(
    md_files: list[Path], repo_root: Path, config_files: dict[str, Path]
) -> tuple[dict[str, Any], list[LinkIssue], list[ScanAccuracyIssue], dict[str, set[str]]]:
    """Verify documentation accuracy (links, commands, paths, terminology).

    Args:
        md_files: List of markdown files to check
        repo_root: Root path of the repository
        config_files: Dictionary of config file paths

    Returns:
        Tuple of (accuracy_report, link_issues, accuracy_issues, all_headings)
    """
    logger.info("Accuracy verification...")

    # Collect headings for anchor validation
    all_headings: dict[str, set[str]] = {}
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
            all_headings[str(md_file.relative_to(repo_root))] = extract_headings(content)
        except (OSError, UnicodeDecodeError) as e:
            logger.warning(f"Error reading {md_file}: {e}")

    # Check links
    link_issues = check_links(md_files, repo_root, all_headings)
    logger.info(f"Found {len(link_issues)} link issues")

    # Verify commands
    command_issues = verify_commands(md_files, repo_root)
    logger.info(f"Found {len(command_issues)} command accuracy issues")

    # Check file paths
    path_issues = check_file_paths(md_files, repo_root)
    logger.info(f"Found {len(path_issues)} file path issues")

    # Validate configuration options
    config_issues = validate_config_options(md_files, config_files, repo_root)
    logger.info(f"Found {len(config_issues)} configuration issues")

    # Check terminology consistency
    terminology_issues = check_terminology(md_files, repo_root)
    logger.info(f"Found {len(terminology_issues)} terminology issues")

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
