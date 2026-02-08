#!/usr/bin/env python3
"""Display detailed project information.

This script shows comprehensive project details including:
- Manuscript configuration and content
- Source code structure
- Output files and deliverables
- Test coverage information
"""

import sys
from pathlib import Path
from typing import Dict, Any

# Add repo root to Python path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from infrastructure.core.logging_utils import get_logger
from infrastructure.project.discovery import discover_projects, ProjectInfo

logger = get_logger(__name__)


def get_project_info(project_name: str, repo_root: Path) -> Dict[str, Any]:
    """Get comprehensive project information.

    Args:
        project_name: Name of the project
        repo_root: Repository root path

    Returns:
        Dictionary with project information
    """
    project_dir = repo_root / "projects" / project_name

    if not project_dir.exists():
        raise FileNotFoundError(f"Project directory not found: {project_dir}")

    info = {
        "name": project_name,
        "directory": str(project_dir),
        "manuscript": {},
        "source": {},
        "output": {},
        "tests": {}
    }

    # Manuscript info
    manuscript_dir = project_dir / "manuscript"
    if manuscript_dir.exists():
        info["manuscript"]["location"] = str(manuscript_dir)
        info["manuscript"]["md_files"] = len(list(manuscript_dir.glob("*.md")))

        config_file = manuscript_dir / "config.yaml"
        info["manuscript"]["has_config"] = config_file.exists()

        if config_file.exists():
            import yaml
            with open(config_file) as f:
                config = yaml.safe_load(f)
                info["manuscript"]["title"] = config.get("paper", {}).get("title", "")
                info["manuscript"]["authors"] = config.get("authors", [])

    # Source code info
    src_dir = project_dir / "src"
    if src_dir.exists():
        info["source"]["location"] = str(src_dir)
        info["source"]["py_files"] = len(list(src_dir.rglob("*.py")))

    # Output info
    output_dir = project_dir / "output"
    if output_dir.exists():
        info["output"]["location"] = str(output_dir)
        if (output_dir / "pdf").exists():
            info["output"]["pdf_count"] = len(list((output_dir / "pdf").glob("*.pdf")))
        if (output_dir / "figures").exists():
            info["output"]["figure_count"] = len(list((output_dir / "figures").glob("*.png")))

    # Tests info
    tests_dir = project_dir / "tests"
    if tests_dir.exists():
        info["tests"]["location"] = str(tests_dir)
        info["tests"]["test_files"] = len(list(tests_dir.glob("test_*.py")))

    return info


def display_project_info(info: Dict[str, Any]) -> None:
    """Display project information in formatted output."""
    print(f"\n{'='*60}")
    print(f"  PROJECT INFORMATION: {info['name']}")
    print(f"{'='*60}\n")

    print(f"Project Directory: {info['directory']}\n")

    # Manuscript
    if info["manuscript"]:
        print("Manuscript:")
        print(f"  Location: {info['manuscript'].get('location', 'N/A')}")
        print(f"  Markdown files: {info['manuscript'].get('md_files', 0)}")
        if info['manuscript'].get('has_config'):
            print("  Config: ✓ (config.yaml found)")
            if info['manuscript'].get('title'):
                print(f"  Title: {info['manuscript']['title']}")
        else:
            print("  Config: ✗ (config.yaml not found)")
        print()

    # Source code
    if info["source"]:
        print("Source Code:")
        print(f"  Location: {info['source'].get('location', 'N/A')}")
        print(f"  Python files: {info['source'].get('py_files', 0)}")
        print()

    # Output
    if info["output"]:
        print("Output:")
        print(f"  Location: {info['output'].get('location', 'N/A')}")
        if "pdf_count" in info["output"]:
            print(f"  PDFs: {info['output']['pdf_count']}")
        if "figure_count" in info["output"]:
            print(f"  Figures: {info['output']['figure_count']}")
        print()

    # Tests
    if info["tests"]:
        print("Tests:")
        print(f"  Location: {info['tests'].get('location', 'N/A')}")
        print(f"  Test files: {info['tests'].get('test_files', 0)}")
        print()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Display project information")
    parser.add_argument("--project", default="project", help="Project name")

    args = parser.parse_args()

    try:
        info = get_project_info(args.project, repo_root)
        display_project_info(info)
        return 0
    except Exception as e:
        logger.error(f"Failed to get project info: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())