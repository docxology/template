"""Link extraction and validation helpers for markdown audits."""

import ast
import re
from pathlib import Path
from typing import Any, TypedDict

from infrastructure.core.logging.utils import get_logger
from infrastructure.validation.integrity._link_normalize import (
    _get_actual_project_names,
    _is_real_path_item,
    _resolve_template_path,
)
from infrastructure.validation.integrity.link_skip_policy import should_validate_path as _should_validate_path

logger = get_logger(__name__)


class LinkCheckResult(TypedDict):
    """Represents a single link check result from the link checker."""

    file: str
    line: int
    target: str
    text: str
    issue: str
    type: str


def extract_links(
    content: str, file_path: Path
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Extract internal links, external links, and file references from markdown."""
    internal_links = []
    external_links = []
    file_refs = []

    # Remove code blocks to avoid false positives
    # Pattern for code blocks: ```...``` or `...`
    code_block_pattern = re.compile(r"```[\s\S]*?```|`[^`]+`")
    content_without_code = code_block_pattern.sub("", content)

    # Pattern for markdown links: [text](path)
    link_pattern = re.compile(r"\[([^\]]+)\]\(([^\)]+)\)")

    for match in link_pattern.finditer(content_without_code):
        link_text = match.group(1)
        link_target = match.group(2)

        # Skip if it's an anchor link only
        if link_target.startswith("#"):
            internal_links.append(
                {
                    "text": link_text,
                    "target": link_target,
                    "line": content[: match.start()].count("\n") + 1,
                    "file": str(file_path),
                }
            )
        # Check if it's an external link (including URLs with paths)
        elif (
            link_target.startswith("http://")
            or link_target.startswith("https://")
            or "://" in link_target
            or link_target.startswith("mailto:")
        ):
            external_links.append(
                {
                    "text": link_text,
                    "target": link_target,
                    "line": content[: match.start()].count("\n") + 1,
                    "file": str(file_path),
                }
            )
        # Internal file reference
        else:
            file_refs.append(
                {
                    "text": link_text,
                    "target": link_target,
                    "line": content[: match.start()].count("\n") + 1,
                    "file": str(file_path),
                }
            )

    return internal_links, external_links, file_refs


def extract_code_blocks(content: str, file_path: Path) -> list[dict[str, Any]]:
    """Extract code blocks from markdown content for validation.

    Improved to handle multi-line code blocks and filter out formatting artifacts.
    """
    code_blocks = []

    # Pattern for code blocks: ```language\ncode\n``` (handles multi-line)
    # Use non-greedy matching to avoid capturing too much
    code_block_pattern = re.compile(r"```(\w+)?\n(.*?)```", re.DOTALL)

    for match in code_block_pattern.finditer(content):
        language = match.group(1) or ""
        code_content = match.group(2)
        line_number = content[: match.start()].count("\n") + 1

        # Skip empty code blocks
        if not code_content.strip():
            continue

        code_blocks.append(
            {
                "language": language,
                "content": code_content,
                "line": line_number,
                "file": str(file_path),
            }
        )

    return code_blocks


def _check_code_path_match(
    match: re.Match[str], block: dict[str, Any], content: str, file_path: Path, repo_root: Path
) -> dict[str, Any] | None:
    """Validate a single path match in a code block."""
    from infrastructure.validation.repo.known_exceptions import (
        is_code_block_artifact,
        is_mermaid_artifact,
        is_valid_directory_reference,
    )

    path_ref = match.group(0).strip().rstrip(":")
    if len(path_ref) < 3:
        return None

    if is_code_block_artifact(path_ref) or is_mermaid_artifact(path_ref):
        return None

    lines = path_ref.split("\n")
    if any(line.strip().startswith("#") for line in lines if line.strip()):
        return None

    match_start = match.start()
    match_end = match.end()
    context_before = block["content"][max(0, match_start - 10) : match_start]
    context_after = block["content"][match_end : min(len(block["content"]), match_end + 10)]

    if ('"' in context_before or "'" in context_before) and ('"' in context_after or "'" in context_after):
        return None

    if is_valid_directory_reference(path_ref) or not _should_validate_path(path_ref):
        return None

    resolved_path = _resolve_template_path(path_ref, repo_root, file_path)
    if not resolved_path:
        return None
    try:
        if resolved_path.exists():
            return None
    except ValueError as e:
        # Path objects can throw ValueError for invalid paths (e.g., embedded NUL).
        return {
            "file": str(file_path),
            "line": block.get("line", 0) + content[:match_start].count("\n"),
            "target": path_ref,
            "issue": f"Invalid file path in code block: {path_ref} ({e})",
            "type": "code_block_path",
        }

    if resolved_path.suffix or not path_ref.endswith("/"):
        return {
            "file": str(file_path),
            "line": block.get("line", 0) + content[:match_start].count("\n"),
            "target": path_ref,
            "issue": f"File path in code block does not exist: {path_ref}",
            "type": "code_block_path",
        }
    return None


def validate_file_paths_in_code(content: str, file_path: Path, repo_root: Path) -> list[dict[str, Any]]:
    """Validate file path references within code blocks.

    Improved to avoid catching formatting artifacts and better handle multi-line paths.
    """
    issues = []
    code_blocks = extract_code_blocks(content, file_path)

    path_patterns = [
        r'(?<![\w./-])projects/\{[^}]+\}/[^\'"\s\n\|`\)\]\}]*',
        r'(?<![\w./-])output/\{[^}]+\}/[^\'"\s\n\|`\)\]\}]*',
        r'(?<![\w./-])infrastructure/[^\'"\s\n\|`\)\]\}]+',
        r'(?<![\w./-])scripts/[^\'"\s\n\|`\)\]\}]+',
        r'(?<![\w./-])projects/[a-zA-Z_][a-zA-Z0-9_]*/[^\'"\s\n\|`\)\]\}]+',
    ]

    for block in code_blocks:
        if block.get("language") in ["mermaid", "graph", "flowchart"]:
            continue

        for pattern in path_patterns:
            for match in re.finditer(pattern, block.get("content", "")):
                issue = _check_code_path_match(match, block, content, file_path, repo_root)
                if issue:
                    issues.append(issue)

    return issues


def validate_directory_structures(content: str, file_path: Path, repo_root: Path) -> list[dict[str, Any]]:
    """Validate directory structure examples in markdown against actual filesystem.

    Scans code blocks for tree diagrams (├── / └── patterns) and checks that
    referenced files and directories actually exist relative to repo_root.
    """
    issues: list[dict[str, Any]] = []

    tree_patterns = [
        r"```\n([^`]*?)```",
        r"```\w+\n([^`]*?)```",
    ]

    for pattern in tree_patterns:
        for match in re.finditer(pattern, content, re.DOTALL):
            tree_content = match.group(1)
            for line in tree_content.split("\n"):
                dir_match = re.search(r"[├└]──\s*([^\s]+)", line.strip())
                if not dir_match:
                    continue
                item_name = dir_match.group(1)
                if not _is_real_path_item(item_name):
                    continue
                # Documentation files reference illustrative paths — skip
                if file_path.parent.name in ("docs", "infrastructure", "scripts"):
                    continue
                # Check existence relative to repo root
                candidate = repo_root / item_name.rstrip("/")
                if not candidate.exists():
                    line_num = content[: match.start()].count("\n") + 1
                    issues.append(
                        {
                            "file": str(file_path),
                            "line": line_num,
                            "target": item_name,
                            "issue": f"Directory tree references '{item_name}' which does not exist",
                            "type": "missing_tree_item",
                        }
                    )

    return issues


def validate_python_imports(content: str, file_path: Path, repo_root: Path) -> list[dict[str, Any]]:
    """Validate Python import statements in code blocks."""
    issues = []
    code_blocks = extract_code_blocks(content, file_path)

    for block in code_blocks:
        if block["language"].lower() in ["python", "py"]:
            # Parse Python code to find imports
            try:
                import warnings

                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", SyntaxWarning)
                    tree = ast.parse(block["content"])
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                module_name = alias.name
                                issues.extend(_validate_import_path(module_name, block, file_path, repo_root))
                        elif isinstance(node, ast.ImportFrom):
                            module_name: str | None = node.module
                            if module_name is not None:
                                issues.extend(_validate_import_path(module_name, block, file_path, repo_root))
            except SyntaxError as e:
                # Skip malformed Python code
                logger.debug(f"Syntax error extracting imports from {file_path.name}: {e}")
                continue

    return issues


def _validate_import_path(
    module_name: str, block: dict[str, Any], file_path: Path, repo_root: Path
) -> list[dict[str, Any]]:
    """Validate a single import path."""
    issues: list[dict[str, str]] = []

    # Convert module path to file path
    if module_name.startswith("infrastructure."):
        # First check if it's a direct module import (e.g., infrastructure.core.performance)
        file_path_guess = module_name.replace("infrastructure.", "infrastructure/").replace(".", "/") + ".py"
        full_path = repo_root / file_path_guess
        if full_path.exists():
            # File exists, import should be valid
            return issues

        # Check if it's a submodule that should be imported from __init__.py
        # For example: infrastructure.core.performance might be imported via infrastructure.core.__init__.py  # noqa: E501
        path_parts = module_name.split(".")
        if len(path_parts) >= 2:
            # Check parent __init__.py files
            for i in range(len(path_parts) - 1, 0, -1):
                parent_module = ".".join(path_parts[:i])
                init_path_guess = (
                    parent_module.replace("infrastructure.", "infrastructure/").replace(".", "/") + "/__init__.py"
                )
                init_full_path = repo_root / init_path_guess
                if init_full_path.exists():
                    # Parent __init__.py exists, assume the import is valid
                    # We could check the __init__.py content, but that's complex and slow
                    return issues

        # If we get here, neither the direct file nor parent __init__.py exists
        issues.append(
            {
                "file": str(file_path),
                "line": block["line"],
                "target": module_name,
                "issue": f"Python import not found: {module_name}",
                "type": "python_import",
            }
        )

    elif module_name.startswith("projects.project.src."):
        # Try actual project names (discovered dynamically)
        found = False
        project_names = _get_actual_project_names(repo_root)
        for project_name in project_names:
            file_path_guess = (
                module_name.replace("projects.project.src.", f"projects/{project_name}/src/").replace(".", "/") + ".py"
            )
            full_path = repo_root / file_path_guess
            if full_path.exists():
                found = True
                break
            # Check for __init__.py in parent
            init_path = full_path.parent / "__init__.py"
            if init_path.exists():
                found = True
                break

        if not found:
            issues.append(
                {
                    "file": str(file_path),
                    "line": block["line"],
                    "target": module_name,
                    "issue": f"Python import not found: {module_name}",
                    "type": "python_import",
                }
            )

    return issues


def validate_placeholder_consistency(content: str, file_path: Path, repo_root: Path) -> list[dict[str, Any]]:
    """Validate consistency of {name} placeholders vs actual project names."""
    issues: list[dict[str, Any]] = []

    # Find all placeholder usage
    placeholder_pattern = re.compile(r"\{([^}]+)\}")
    placeholder_pattern.findall(content)

    # Skip validation for certain file types that naturally use templates
    file_path_str = str(file_path)
    skip_files = [
        "docs/rules/",  # Standards corpus uses `{name}` placeholders in examples
        "docs/architecture/",  # Architecture docs explain templates
        "docs/core/",  # Core docs explain system structure
        "infrastructure/AGENTS.md",  # Infrastructure docs use templates
        "AGENTS.md",  # Root docs explain templates
    ]

    if any(skip_path in file_path_str for skip_path in skip_files):
        return issues

    # Check for inconsistent usage of {name} vs actual project names
    project_names = _get_actual_project_names(repo_root)

    for match in placeholder_pattern.finditer(content):
        placeholder = match.group(1)
        if placeholder == "name":
            # Get context around the placeholder
            context = content[max(0, match.start() - 100) : match.end() + 100]

            # Skip if this is in documentation explaining the template system
            skip_contexts = [
                "projects/{name}",
                "template structure",
                "multi-project",
                "placeholder",
                "example project",
                "generic project",
                "any project",
                "research project",
                "your project",
                "new project",
            ]

            if any(skip_ctx in context.lower() for skip_ctx in skip_contexts):
                continue

            # Check if this should be a real project name
            # Only flag if we're clearly talking about an actual project, not a template
            specific_project_indicators = [
                "run the",
                "execute",
                "build",
                "generate",
                "compile",
                "test the project",
                "this project",
            ]

            has_specific_indicator = any(indicator in context.lower() for indicator in specific_project_indicators)
            mentions_specific_project = any(proj in context for proj in project_names)

            if has_specific_indicator and mentions_specific_project:
                # This might be inconsistent - using {name} when specific project exists
                issues.append(
                    {
                        "file": str(file_path),
                        "line": content[: match.start()].count("\n") + 1,
                        "target": match.group(0),
                        "issue": f"Using placeholder {{name}} when specific project names exist: {project_names}",  # noqa: E501
                        "type": "placeholder_inconsistency",
                    }
                )

    return issues


def check_file_reference(target: str, source_file: Path, repo_root: Path) -> tuple[bool, str]:
    """Check if a file reference resolves correctly."""
    from infrastructure.validation.paths import resolve_markdown_target

    resolved = resolve_markdown_target(target, source_file, repo_root)
    if resolved.exists:
        if resolved.resolved is not None:
            try:
                return True, str(resolved.resolved.relative_to(repo_root.resolve()))
            except ValueError:
                pass
        return True, resolved.message
    return False, resolved.message
