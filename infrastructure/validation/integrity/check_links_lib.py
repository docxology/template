#!/usr/bin/env python3
"""Library helpers for documentation link and path validation.

Used by :mod:`check_links` (CLI) and :mod:`audit_orchestrator`. The CLI entry
point and :func:`main` live in ``check_links.py``.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any, Set, TypedDict, Union, cast

from infrastructure.core.logging.utils import get_logger
from infrastructure.validation.docs.accuracy import extract_headings

logger = get_logger(__name__)

class LinkCheckResult(TypedDict):
    """Represents a single link check result from the link checker."""
    file: str
    line: int
    target: str
    text: str
    issue: str
    type: str


def find_all_markdown_files(repo_root: Union[str, Path]) -> list[Path]:
    """Find all markdown files in the repository."""
    repo_path = Path(repo_root)
    md_files = []
    exclude_dirs = {
        "output",
        "htmlcov",
        "projects_archive",
        ".venv",
        "venv",
        "site-packages",
        "__pycache__",
        ".pytest_cache",
        ".git",
        "node_modules",
    }
    for md_file in repo_path.rglob("*.md"):
        # Skip output, htmlcov, archived projects, virtual environments, and build artifacts
        if any(excluded in md_file.parts for excluded in exclude_dirs):
            continue
        md_files.append(md_file)
    return sorted(md_files)


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

    path_ref = match.group(0).strip()
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

    if ('"' in context_before or "'" in context_before) and (
        '"' in context_after or "'" in context_after
    ):
        return None

    if is_valid_directory_reference(path_ref) or not _should_validate_path(path_ref):
        return None

    resolved_path = _resolve_template_path(path_ref, repo_root)
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


def validate_file_paths_in_code(
    content: str, file_path: Path, repo_root: Path
) -> list[dict[str, Any]]:
    """Validate file path references within code blocks.

    Improved to avoid catching formatting artifacts and better handle multi-line paths.
    """
    issues = []
    code_blocks = extract_code_blocks(content, file_path)

    path_patterns = [
        r'projects/\{[^}]+\}/[^\'"\s\n\|`\)\]\}]*',
        r'output/\{[^}]+\}/[^\'"\s\n\|`\)\]\}]*',
        r'infrastructure/[^\'"\s\n\|`\)\]\}]+',
        r'scripts/[^\'"\s\n\|`\)\]\}]+',
        r'projects/[a-zA-Z_][a-zA-Z0-9_]*/[^\'"\s\n\|`\)\]\}]+',
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


# Consolidated path exclusion patterns — single source of truth for all
# skip/example paths. Avoids hardcoding in function body; extend by adding here.
_PATH_SKIP_SUBSTRINGS: frozenset[str] = frozenset(
    {
        # Template/placeholder paths
        "projects/{name}/",
        "projects/{project_name}",
        "{name}/manuscript/config.yaml.example",
        "your_project_name",
        "path/to/",
        "example.com",
        "your-domain.com",
        # Generic/example infrastructure paths
        "infrastructure/<module>",
        "infrastructure/example",
        "infrastructure/test_<module>",
        "infrastructure/example_module",
        "infrastructure/module/",
        "infrastructure/new_module/",
        "infrastructure/my_module/",
        "infrastructure/utils/",
        "infrastructure/helpers/",
        "infrastructure/common/",
        "infrastructure/shared/",
        "infrastructure/core.py",
        "infrastructure/test_core/",
        "infrastructure/test_specific.py",
        # Malformed markdown artifacts
        "infrastructure/AGENTS.md)",
        "infrastructure/AGENTS.md](../",
        "scripts/)",
        "scripts/`",
        # Example scripts/docs/tests
        "scripts/custom_check.py",
        "scripts/extra_checks.py",
        "scripts/my_script.py",
        "scripts/process_data.py",
        "scripts/optimization_analysis.py",
        "projects/my_project/",
        "projects/new_project/",
        "docs/my_guide.md",
        "docs/new_feature.md",
        "tests/test_my_feature.py",
        "tests/test_new_function.py",
        # Template examples in code blocks
        "project/tests/",
        "project/manuscript/",
        "project/src/",
    }
)

_PATH_SKIP_KEYWORDS: frozenset[str] = frozenset(
    {
        "placeholder",
        "template",
        "example",
        "your_",
        "sample",
        "my_",
        "myproject",
        "myresearch",
        "new_",
        "test_new_",
        "test_example",
        "test_my",
        "analysis.py",
        "analyze",
        "pipeline",
        "generate_",
        "custom_",
        "train_models",
        "evaluate_models",
        "external_simulation",
        "auto_document",
        "literature_",
        "statistics_",
        "correlation_",
        "batch_",
        "optimizer_",
        "capture_",
        "assess_",
        "scientific_",
        "mymodule",
        "*[module",
        "output/pdf/*",
        "test.sh",
        "view_results.sh",
        "setup.sh",
        "run_",
        "clean.sh",
        "docs_build.sh",
        "biology_analysis.py",
        "_quality_report.py",
        "scripts/*",
        "00_*",
        "01_*",
        "07_*",
        "ml_build.sh",
        "scripts/│",
        "scripts/tests",
        "projects/code_project/:",
        "scripts/03_render_pdf.py;",
        "data_quality",
        "infrastructure/[module_name",
        "06_fulltext_assessment",
        "serve_app.py",
        "projects/cognitive_case_diagrams/:",
        "sync_docs_notebooks.sh",
        "docs_serve.sh",
        "docs_sync_and_serve.sh",
        "module_name.py",
        "module.py",
        "bash_utils.sh.",
    }
)


def _should_validate_path(path_ref: str) -> bool:
    """Determine if a path reference should be validated.

    Uses module-level frozensets for skip patterns so additions are centralized
    and the function body stays focused on structural checks.
    """
    # Quick substring match against consolidated exclusion list
    if any(pattern in path_ref for pattern in _PATH_SKIP_SUBSTRINGS):
        return False

    # Template variables or angle-bracket placeholders
    if ("{" in path_ref and "}" in path_ref) or ("<" in path_ref and ">" in path_ref):
        return False

    # URLs and email addresses
    if "://" in path_ref or "@" in path_ref:
        return False

    # Documentation placeholder keywords
    path_lower = path_ref.lower()
    if any(kw in path_lower for kw in _PATH_SKIP_KEYWORDS):
        return False

    # Malformed paths containing formatting artifacts
    if any(char in path_ref for char in ("`", ")", "]", "}", "|", "\n", "\r")):
        path_stripped = path_ref.rstrip()
        if (
            path_stripped.endswith((")", "]", "}", "`", "|", "\\n"))
            or "\n" in path_ref
            or "\r" in path_ref
        ):
            return False
        if re.search(r"/\s*\n\s*[A-Z]", path_ref):
            return False

    return True


def _resolve_template_path(path_ref: str, repo_root: Path) -> Path | None:
    """Resolve template paths like projects/{name}/ to actual paths."""
    try:
        # Handle common template patterns
        if path_ref.startswith("projects/project/"):
            # Try actual project names first (discovered dynamically)
            project_names = _get_actual_project_names(repo_root)
            for project_name in project_names:
                actual_path = path_ref.replace("projects/project/", f"projects/{project_name}/")
                full_path = repo_root / actual_path
                if full_path.exists():
                    return full_path
            # If no actual project found, return None (path doesn't exist)
            return None
        elif path_ref.startswith("projects/{name}/"):
            # Can't resolve template, skip
            return None
        elif path_ref.startswith("infrastructure/"):
            return repo_root / path_ref
        elif path_ref.startswith("scripts/"):
            return repo_root / path_ref
        elif path_ref.startswith("output/project/"):
            # Try actual project names (discovered dynamically)
            project_names = _get_actual_project_names(repo_root)
            for project_name in project_names:
                actual_path = path_ref.replace("output/project/", f"output/{project_name}/")
                full_path = repo_root / actual_path
                if full_path.exists():
                    return full_path
            # If no actual project found, return None
            return None
        else:
            return repo_root / path_ref
    except OSError:
        return None

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
                    issues.append({
                        "file": str(file_path),
                        "line": line_num,
                        "target": item_name,
                        "issue": f"Directory tree references '{item_name}' which does not exist",
                        "type": "missing_tree_item",
                    })

    return issues


def _is_real_path_item(item_name: str) -> bool:
    """Check if a directory tree item looks like a real file/directory."""
    # Skip obvious placeholders or comments
    if any(skip in item_name.lower() for skip in ["...", "etc", "files", "more"]):
        return False

    # Skip if it contains template variables
    if "{" in item_name and "}" in item_name:
        return False

    return True


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
                                issues.extend(
                                    _validate_import_path(module_name, block, file_path, repo_root)
                                )
                        elif isinstance(node, ast.ImportFrom):
                            module_name: str | None = node.module
                            if module_name is not None:
                                issues.extend(
                                    _validate_import_path(module_name, block, file_path, repo_root)
                                )
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
        file_path_guess = (
            module_name.replace("infrastructure.", "infrastructure/").replace(".", "/") + ".py"
        )
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
                    parent_module.replace("infrastructure.", "infrastructure/").replace(".", "/")
                    + "/__init__.py"
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
                module_name.replace(
                    "projects.project.src.", f"projects/{project_name}/src/"
                ).replace(".", "/")
                + ".py"
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


def validate_placeholder_consistency(
    content: str, file_path: Path, repo_root: Path
) -> list[dict[str, Any]]:
    """Validate consistency of {name} placeholders vs actual project names."""
    issues: list[dict[str, Any]] = []

    # Find all placeholder usage
    placeholder_pattern = re.compile(r"\{([^}]+)\}")
    placeholder_pattern.findall(content)

    # Skip validation for certain file types that naturally use templates
    file_path_str = str(file_path)
    skip_files = [
        ".cursorrules/",  # Development rules naturally use templates
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

            has_specific_indicator = any(
                indicator in context.lower() for indicator in specific_project_indicators
            )
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


def _get_actual_project_names(repo_root: Path) -> list[str]:
    """Get list of actual project names from projects/ directory."""
    projects_dir = repo_root / "projects"
    if not projects_dir.exists():
        return []

    project_names = []
    for item in projects_dir.iterdir():
        if item.is_dir() and item.name not in ["__pycache__", ".pytest_cache"]:
            project_names.append(item.name)

    return project_names


def check_file_reference(target: str, source_file: Path, repo_root: Path) -> tuple[bool, str]:
    """Check if a file reference resolves correctly."""
    # Handle relative paths
    if target.startswith("../"):
        # Count how many levels up
        levels_up = target.count("../")
        target_path = source_file.parent
        for _ in range(levels_up):
            target_path = target_path.parent
        target_path = target_path / target.replace("../", "").replace("./", "")
    elif target.startswith("./"):
        target_path = source_file.parent / target[2:]
    else:
        # Relative to source file directory
        target_path = source_file.parent / target

    # Normalize path
    try:
        target_path = target_path.resolve()
        repo_root_resolved = repo_root.resolve()

        # Check if it's within repo first
        try:
            target_path.relative_to(repo_root_resolved)
        except ValueError:
            return False, f"Path outside repository: {target_path}"

        # Check if file or directory exists
        if target_path.exists():
            if target_path.is_file():
                return True, str(target_path.relative_to(repo_root_resolved))
            elif target_path.is_dir():
                # Directory references are valid (e.g., [src/](src/))
                return True, str(target_path.relative_to(repo_root_resolved))
            else:
                return (
                    False,
                    f"Path exists but is not a file or directory: {target_path}",
                )
        else:
            # Check if it's a markdown file without extension
            md_path = target_path.with_suffix(".md")
            if md_path.exists() and md_path.is_file():
                return True, str(md_path.relative_to(repo_root_resolved))
            return False, f"File or directory does not exist: {target_path}"
    except (OSError, ValueError) as e:
        return False, f"Error resolving path: {e}"

def generate_comprehensive_report(issues: dict[str, list[LinkCheckResult]], total_files: int) -> int:
    """Generate a comprehensive validation report."""
    total_issues = sum(len(issue_list) for issue_list in issues.values())

    logger.info("=" * 80)
    logger.info("COMPREHENSIVE FILEPATH AND REFERENCE AUDIT REPORT")
    logger.info("=" * 80)
    logger.info(f"Files scanned: {total_files}")
    logger.info(f"Total issues found: {total_issues}")

    # Report each category
    categories = [
        (
            "broken_anchor_links",
            "Broken Anchor Links",
            "Anchor links that don't resolve to headings",
        ),
        (
            "broken_file_refs",
            "Broken File References",
            "File references that don't exist",
        ),
        (
            "code_block_paths",
            "Invalid Code Block Paths",
            "File paths in code blocks that don't exist",
        ),
        (
            "directory_structures",
            "Directory Structure Issues",
            "Directory trees that don't match filesystem",
        ),
        (
            "python_imports",
            "Invalid Python Imports",
            "Import statements that reference non-existent modules",
        ),
        (
            "placeholder_consistency",
            "Placeholder Inconsistencies",
            "Inconsistent use of {name} vs actual project names",
        ),
    ]

    has_issues = False
    for category_key, title, description in categories:
        issue_list = issues[category_key]
        if issue_list:
            has_issues = True
            logger.warning(f"🚨 {title} ({len(issue_list)} issues)")
            logger.warning(f"   {description}")

            # Show first 5 issues per category
            for i, issue in enumerate(issue_list[:5]):
                logger.warning(f"   {i + 1}. {issue['file']}:{issue['line']}")
                logger.warning(f"      Target: {issue['target']}")
                logger.warning(f"      Issue: {issue['issue']}")
                if "text" in issue:
                    logger.warning(f"      Text: {issue['text']}")

            if len(issue_list) > 5:
                logger.warning(f"   ... and {len(issue_list) - 5} more issues in this category")
            logger.info("-" * 60)

    if not has_issues:
        logger.info("✅ ALL VALIDATIONS PASSED!")
        logger.info("No broken links, missing files, or reference issues found.")
        return 0

    logger.info("\n📋 SUMMARY BY CATEGORY:")
    for category_key, title, _ in categories:
        count = len(issues[category_key])
        if count > 0:
            logger.info(f"   • {title}: {count} issues")

    logger.info("\n🔧 Next steps: Run the audit script to generate detailed fix recommendations:")
    logger.info("   python scripts/audit_filepaths.py")

    return 1
def run_link_audit(repo_root: Path) -> int:
    """Run the comprehensive link and reference audit for ``repo_root``."""
    md_files = find_all_markdown_files(str(repo_root))

    logger.info(f"Found {len(md_files)} markdown files")
    logger.info("Running comprehensive filepath and reference audit")

    all_headings: dict[str, Set[str]] = {}
    # Accumulator uses list[Any] because the validate_* helpers return list[dict[str,Any]];
    # generate_comprehensive_report receives a cast to the narrower LinkCheckResult type.
    issues: dict[str, list[Any]] = {
        "broken_anchor_links": [],
        "broken_file_refs": [],
        "code_block_paths": [],
        "directory_structures": [],
        "python_imports": [],
        "placeholder_consistency": [],
    }

    # First pass: collect all headings
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
            all_headings[str(md_file.relative_to(repo_root))] = extract_headings(content)
        except (OSError, UnicodeDecodeError) as e:
            logger.error(f"Error reading {md_file}: {e}")

    # Second pass: comprehensive validation
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
            internal_links, external_links, file_refs = extract_links(content, md_file)

            # Check internal links (anchors)
            file_key = str(md_file.relative_to(repo_root))
            for link in internal_links:
                target = link["target"].lstrip("#")

                # Skip anchor link validation for manuscript files as they use cross-references
                # that are resolved during rendering, not same-file headings
                if "manuscript" in file_key:
                    continue

                # Skip cross-references that are meant to be resolved by the rendering pipeline
                # These include: fig:, sec:, eq:, table: prefixes, or standard section references
                cross_ref_prefixes = ["fig:", "sec:", "eq:", "table:", "tab:"]
                if any(target.startswith(prefix) for prefix in cross_ref_prefixes):
                    continue

                # Skip common manuscript section references
                common_sections = [
                    "methodology",
                    "experimental_results",
                    "discussion",
                    "conclusion",
                    "results",
                ]
                if target in common_sections or any(
                    sec in target.lower() for sec in common_sections
                ):
                    continue

                # Only check for actual heading anchors within the same file
                if file_key in all_headings and target not in all_headings[file_key]:
                    issues["broken_anchor_links"].append(
                        {
                            "file": file_key,
                            "line": link["line"],
                            "target": link["target"],
                            "text": link["text"],
                            "issue": "Anchor not found",
                            "type": "broken_anchor",
                        }
                    )

            # Check file references
            for ref in file_refs:
                target = ref["target"]
                if "#" in target:
                    target = target.split("#")[0]

                # Skip references to generated files in output directories
                if "output/" in target or "/output/" in target:
                    continue

                if target:
                    exists, msg = check_file_reference(target, md_file, repo_root)
                    if not exists:
                        issues["broken_file_refs"].append(
                            {
                                "file": str(md_file.relative_to(repo_root)),
                                "line": ref["line"],
                                "target": ref["target"],
                                "text": ref["text"],
                                "issue": msg,
                                "type": "broken_file_ref",
                            }
                        )

            # Additional validations
            code_block_issues = validate_file_paths_in_code(content, md_file, repo_root)
            issues["code_block_paths"].extend(code_block_issues)

            dir_structure_issues = validate_directory_structures(content, md_file, repo_root)
            issues["directory_structures"].extend(dir_structure_issues)

            import_issues = validate_python_imports(content, md_file, repo_root)
            issues["python_imports"].extend(import_issues)

            placeholder_issues = validate_placeholder_consistency(content, md_file, repo_root)
            issues["placeholder_consistency"].extend(placeholder_issues)

        except (OSError, UnicodeDecodeError) as e:
            logger.error(f"Error processing {md_file}: {e}")

    # Generate comprehensive report
    return generate_comprehensive_report(cast(dict[str, list[LinkCheckResult]], issues), len(md_files))

