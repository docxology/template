"""Phase 1: Discovery and Inventory for documentation scanning."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

from infrastructure.core.logging_utils import get_logger
from infrastructure.project.discovery import ProjectInfo, discover_projects
from infrastructure.validation.doc_models import DocumentationFile

logger = get_logger(__name__)


def find_markdown_files(repo_root: Path) -> List[Path]:
    """Find all markdown files excluding output/htmlcov and virtual environments."""
    exclude_dirs = {
        "output",
        "htmlcov",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        ".git",
        "node_modules",
        ".tox",
        "dist",
        "build",
        ".mypy_cache",
        "projects_archive",
    }
    md_files = []
    for md_file in repo_root.rglob("*.md"):
        # Skip if any part of the path is in exclude list
        if not any(excluded in md_file.parts for excluded in exclude_dirs):
            md_files.append(md_file)
    return sorted(md_files)


def catalog_agents_readme(md_files: List[Path], repo_root: Path) -> List[str]:
    """Catalog all AGENTS.md and README.md files."""
    agents_readme = []
    for md_file in md_files:
        if md_file.name in ("AGENTS.md", "README.md"):
            agents_readme.append(str(md_file.relative_to(repo_root)))
    return sorted(agents_readme)


def find_config_files(repo_root: Path) -> Dict[str, Path]:
    """Find configuration files."""
    exclude_dirs = {
        "output",
        "htmlcov",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        ".git",
        "node_modules",
        ".tox",
        "dist",
        "build",
        ".mypy_cache",
    }
    config_patterns = ["pyproject.toml", "config.yaml", "*.toml", "*.yaml", "*.yml"]
    configs = {}

    for pattern in config_patterns:
        for config_file in repo_root.rglob(pattern):
            # Skip if any part of the path is in exclude list
            if not any(excluded in config_file.parts for excluded in exclude_dirs):
                if config_file.name not in configs:
                    configs[config_file.name] = config_file

    return configs


def find_script_files(repo_root: Path) -> List[Path]:
    """Find all script files (Python and shell) excluding virtual environments."""
    exclude_dirs = {
        "output",
        "htmlcov",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        ".git",
        "node_modules",
        ".tox",
        "dist",
        "build",
        ".mypy_cache",
        "tests",
    }
    scripts = []
    for ext in ["*.py", "*.sh"]:
        for script in repo_root.rglob(ext):
            # Skip if any part of the path is in exclude list
            if not any(excluded in script.parts for excluded in exclude_dirs):
                # Only include scripts in specific directories
                if any(
                    part in script.parts
                    for part in ["scripts", "repo_utilities", "src"]
                ):
                    scripts.append(script)

    return sorted(scripts)


def create_hierarchy(md_files: List[Path], repo_root: Path) -> Dict[str, List[str]]:
    """Create documentation hierarchy map."""
    hierarchy = defaultdict(list)
    for md_file in md_files:
        rel_path = str(md_file.relative_to(repo_root))
        directory = str(md_file.parent.relative_to(repo_root))
        if directory == ".":
            directory = "root"
        hierarchy[directory].append(rel_path)
    return dict(hierarchy)


def identify_cross_references(md_files: List[Path]) -> Set[str]:
    """Identify cross-reference patterns."""
    cross_refs = set()
    link_pattern = re.compile(r"\[([^\]]+)\]\(([^\)]+)\)")

    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
            for match in link_pattern.finditer(content):
                target = match.group(2)
                if not target.startswith("http") and not target.startswith("#"):
                    cross_refs.add(target)
        except Exception:
            pass

    return cross_refs


def categorize_documentation(
    md_files: List[Path], repo_root: Path
) -> Dict[str, List[str]]:
    """Categorize documentation files."""
    categories = defaultdict(list)

    # Get project information for better categorization
    projects = discover_projects(repo_root)
    project_names = {p.name for p in projects}

    for md_file in md_files:
        rel_path = str(md_file.relative_to(repo_root))

        # Check if this file belongs to a specific project
        project_category = _get_project_category(rel_path, project_names)
        if project_category:
            categories[project_category].append(rel_path)
            continue

        if "docs/" in rel_path:
            if "AGENTS" in md_file.name or "README" in md_file.name:
                categories["directory_docs"].append(rel_path)
            elif "HOW_TO" in md_file.name or "GETTING_STARTED" in md_file.name:
                categories["user_guides"].append(rel_path)
            elif "ARCHITECTURE" in md_file.name or "WORKFLOW" in md_file.name:
                categories["architecture"].append(rel_path)
            elif "API" in md_file.name or "REFERENCE" in md_file.name:
                categories["api_docs"].append(rel_path)
            else:
                categories["general_docs"].append(rel_path)
        elif "manuscript/" in rel_path:
            categories["manuscript"].append(rel_path)
        elif md_file.name in ("AGENTS.md", "README.md"):
            categories["directory_docs"].append(rel_path)
        else:
            categories["other"].append(rel_path)

    return dict(categories)


def _get_project_category(rel_path: str, project_names: set) -> str | None:
    """Determine if a file belongs to a specific project and return category."""
    # Check if path contains projects/{name}/
    if rel_path.startswith("projects/"):
        parts = rel_path.split("/")
        if len(parts) >= 2 and parts[1] in project_names:
            project_name = parts[1]
            # Determine sub-category within project
            if "manuscript/" in rel_path:
                return f"project_manuscript_{project_name}"
            elif "scripts/" in rel_path:
                return f"project_scripts_{project_name}"
            elif "tests/" in rel_path:
                return f"project_tests_{project_name}"
            elif "src/" in rel_path:
                return f"project_src_{project_name}"
            else:
                return f"project_{project_name}"

    return None


def analyze_documentation_file(md_file: Path, repo_root: Path) -> DocumentationFile:
    """Analyze a documentation file and extract metadata."""
    try:
        content = md_file.read_text(encoding="utf-8")
        rel_path = str(md_file.relative_to(repo_root))
        directory = str(md_file.parent.relative_to(repo_root))

        # Determine category
        category = "other"
        if "docs/" in rel_path:
            category = "documentation"
        elif "manuscript/" in rel_path:
            category = "manuscript"
        elif md_file.name in ("AGENTS.md", "README.md"):
            category = "directory_doc"

        # Count words and lines
        words = len(content.split())
        lines = len(content.split("\n"))

        # Check for links and code blocks
        has_links = bool(re.search(r"\[.*?\]\(.*?\)", content))
        has_code_blocks = bool(re.search(r"```", content))

        # Get modification time
        mtime = datetime.fromtimestamp(md_file.stat().st_mtime).isoformat()

        return DocumentationFile(
            path=str(md_file),
            relative_path=rel_path,
            directory=directory,
            name=md_file.name,
            category=category,
            word_count=words,
            line_count=lines,
            has_links=has_links,
            has_code_blocks=has_code_blocks,
            last_modified=mtime,
        )
    except Exception as e:
        logger.error("Error analyzing %s: %s", md_file, e)
        return DocumentationFile(
            path=str(md_file),
            relative_path=str(md_file.relative_to(repo_root)),
            directory=str(md_file.parent.relative_to(repo_root)),
            name=md_file.name,
        )


def run_discovery_phase(repo_root: Path) -> Dict:
    """Run Phase 1: Discovery and Inventory.

    Args:
        repo_root: Root path of the repository

    Returns:
        Dictionary with discovery results
    """
    logger.info("Phase 1: Discovery and Inventory...")

    # Find all markdown files
    md_files = find_markdown_files(repo_root)
    logger.info("Found %d markdown files", len(md_files))

    # Catalog AGENTS.md and README.md files
    agents_readme = catalog_agents_readme(md_files, repo_root)
    logger.info("Found %d AGENTS.md/README.md files", len(agents_readme))

    # Identify configuration files
    config_files = find_config_files(repo_root)
    logger.info("Found %d configuration files", len(config_files))

    # Map script files
    script_files = find_script_files(repo_root)
    logger.info("Found %d script files", len(script_files))

    # Create documentation hierarchy
    hierarchy = create_hierarchy(md_files, repo_root)

    # Identify cross-reference patterns
    cross_refs = identify_cross_references(md_files)

    # Categorize documentation
    categories = categorize_documentation(md_files, repo_root)

    # Build documentation file metadata
    documentation_files = []
    for md_file in md_files:
        doc_file = analyze_documentation_file(md_file, repo_root)
        documentation_files.append(doc_file)

    inventory = {
        "markdown_files": len(md_files),
        "agents_readme_files": len(agents_readme),
        "config_files": len(config_files),
        "script_files": len(script_files),
        "hierarchy": hierarchy,
        "cross_references": len(cross_refs),
        "categories": categories,
        "agents_readme_list": agents_readme,
        "config_files_list": list(config_files.keys()),
        "script_files_list": [str(s.relative_to(repo_root)) for s in script_files],
        "documentation_files": documentation_files,
    }

    return inventory


def discover_project_documentation(repo_root: Path) -> Dict[str, Dict]:
    """Discover documentation organized by project.

    Args:
        repo_root: Repository root directory

    Returns:
        Dictionary mapping project names to their documentation metadata
    """
    projects = discover_projects(repo_root)
    md_files = find_markdown_files(repo_root)

    project_docs = {}

    for project in projects:
        project_docs[project.name] = {
            "project_info": {
                "name": project.name,
                "path": str(project.path),
                "has_src": project.has_src,
                "has_tests": project.has_tests,
                "has_scripts": project.has_scripts,
                "has_manuscript": project.has_manuscript,
                "is_valid": project.is_valid,
                "metadata": project.metadata,
            },
            "documentation_files": [],
            "manuscript_files": [],
            "script_docs": [],
            "test_docs": [],
            "statistics": {},
        }

        # Find files belonging to this project
        project_prefix = f"projects/{project.name}/"
        for md_file in md_files:
            rel_path = str(md_file.relative_to(repo_root))
            if rel_path.startswith(project_prefix):
                doc_info = analyze_documentation_file(md_file, repo_root)
                project_docs[project.name]["documentation_files"].append(doc_info)

                # Categorize within project
                if "manuscript/" in rel_path:
                    project_docs[project.name]["manuscript_files"].append(doc_info)
                elif "scripts/" in rel_path:
                    project_docs[project.name]["script_docs"].append(doc_info)
                elif "tests/" in rel_path:
                    project_docs[project.name]["test_docs"].append(doc_info)

        # Calculate statistics
        project_docs[project.name]["statistics"] = _calculate_project_stats(
            project_docs[project.name]
        )

    return project_docs


def _calculate_project_stats(project_data: Dict) -> Dict[str, int]:
    """Calculate documentation statistics for a project."""
    all_docs = (
        project_data["documentation_files"]
        + project_data["manuscript_files"]
        + project_data["script_docs"]
        + project_data["test_docs"]
    )

    total_words = sum(doc.word_count for doc in all_docs if hasattr(doc, "word_count"))
    total_lines = sum(doc.line_count for doc in all_docs if hasattr(doc, "line_count"))
    has_links = sum(
        1 for doc in all_docs if hasattr(doc, "has_links") and doc.has_links
    )
    has_code_blocks = sum(
        1 for doc in all_docs if hasattr(doc, "has_code_blocks") and doc.has_code_blocks
    )

    return {
        "total_files": len(all_docs),
        "manuscript_files": len(project_data["manuscript_files"]),
        "script_docs": len(project_data["script_docs"]),
        "test_docs": len(project_data["test_docs"]),
        "total_words": total_words,
        "total_lines": total_lines,
        "files_with_links": has_links,
        "files_with_code": has_code_blocks,
    }


def validate_project_documentation_integrity(repo_root: Path) -> Dict[str, List[str]]:
    """Validate documentation integrity across projects.

    Args:
        repo_root: Repository root directory

    Returns:
        Dictionary mapping project names to lists of integrity issues
    """
    projects = discover_projects(repo_root)
    issues = {}

    for project in projects:
        project_issues = []

        # Check for required documentation
        if project.has_manuscript and not project.has_manuscript:
            project_issues.append("Project has manuscript directory but no AGENTS.md")

        if project.has_scripts and not any((project.path / "scripts").glob("*.md")):
            project_issues.append("Project has scripts directory but no documentation")

        # Check for README files in key directories
        required_readmes = ["README.md"]
        if project.has_src:
            required_readmes.append("src/README.md")
        if project.has_tests:
            required_readmes.append("tests/README.md")

        for readme_path in required_readmes:
            if not (project.path / readme_path).exists():
                project_issues.append(f"Missing required documentation: {readme_path}")

        issues[project.name] = project_issues

    return issues


def get_audit_context(repo_root: Path) -> Dict:
    """Get comprehensive context for audit operations.

    Args:
        repo_root: Repository root directory

    Returns:
        Dictionary with audit context including projects, configs, and hierarchy
    """
    projects = discover_projects(repo_root)
    md_files = find_markdown_files(repo_root)
    config_files = find_config_files(repo_root)
    hierarchy = create_hierarchy(md_files, repo_root)
    categories = categorize_documentation(md_files, repo_root)
    project_docs = discover_project_documentation(repo_root)

    return {
        "projects": [
            {"name": p.name, "path": str(p.path), "metadata": p.metadata}
            for p in projects
        ],
        "total_projects": len(projects),
        "total_markdown_files": len(md_files),
        "config_files": list(config_files.keys()),
        "documentation_hierarchy": hierarchy,
        "documentation_categories": categories,
        "project_documentation": project_docs,
        "cross_references": list(identify_cross_references(md_files)),
        "directory_docs": catalog_agents_readme(md_files, repo_root),
    }
