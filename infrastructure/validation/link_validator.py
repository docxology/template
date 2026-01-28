"""Link validation utilities for documentation.

This module provides comprehensive validation of markdown links and file references
across the repository, ensuring all internal documentation links resolve correctly.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from urllib.parse import urlparse

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


class LinkValidator:
    """Validates markdown links and file references."""

    def __init__(self, repo_root: Path):
        """Initialize validator with repository root.

        Args:
            repo_root: Root directory of the repository
        """
        self.repo_root = repo_root
        self.all_files: Set[Path] = set()
        self.all_dirs: Set[Path] = set()
        self._scan_repository()

    def _scan_repository(self) -> None:
        """Scan repository for all files."""
        exclude_patterns = {
            "__pycache__",
            ".git",
            "htmlcov",
            ".pytest_cache",
            ".venv",
            "node_modules",
            ".cursor",
            "output",
            ".DS_Store",
        }

        for path in self.repo_root.rglob("*"):
            # Skip excluded directories - check if any path component exactly matches exclude pattern
            path_parts = path.parts
            should_exclude = False
            for part in path_parts:
                if part in exclude_patterns:
                    should_exclude = True
                    break
            if should_exclude:
                continue

            if path.is_file():
                self.all_files.add(path.relative_to(self.repo_root))
            elif path.is_dir():
                self.all_dirs.add(path.relative_to(self.repo_root))

    def extract_markdown_links(
        self, content: str, file_path: Path
    ) -> List[Tuple[str, str, int]]:
        """Extract all markdown links from content, skipping those inside code blocks.

        Args:
            content: Markdown content
            file_path: Path of the file being processed

        Returns:
            List of tuples (link_text, link_target, line_number)
        """
        links = []

        # Pattern for [text](target) links
        link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
        lines = content.split("\n")

        in_code_block = False
        in_inline_code = False

        for line_num, line in enumerate(lines, 1):
            # Track code block state (``` markers)
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue

            # Skip lines inside code blocks
            if in_code_block:
                continue

            # Find all links in this line
            matches = re.findall(link_pattern, line)
            for match in matches:
                link_text, link_target = match
                links.append((link_text, link_target, line_num))

        return links

    def resolve_link_target(
        self, link_target: str, source_file: Path
    ) -> Tuple[Path | None, bool]:
        """Resolve a link target to an absolute path.

        Args:
            link_target: The link target (relative or absolute path, may contain #anchor)
            source_file: Path of the file containing the link

        Returns:
            Tuple of (resolved_path, is_external)
        """
        # Check if it's an external URL
        if link_target.startswith(("http://", "https://", "mailto:", "ftp://")):
            return None, True

        # Split off anchor if present
        if "#" in link_target:
            file_part, anchor_part = link_target.split("#", 1)
            link_target = file_part  # Resolve just the file part

        # Handle anchor-only links (references within same file)
        if not link_target or link_target.startswith("#"):
            return source_file, False

        # Get absolute repo root
        repo_root_abs = self.repo_root.resolve()

        # Resolve relative paths
        if link_target.startswith("./") or link_target.startswith("../"):
            # Relative to the directory containing the source file
            source_dir = source_file.parent
            try:
                # Build the full path and resolve it step by step
                full_path = source_dir / link_target

                # Convert to parts and manually resolve .. components
                parts = list(full_path.parts)
                resolved_parts = []

                for part in parts:
                    if part == "..":
                        # Go up one directory if possible
                        if resolved_parts:
                            resolved_parts.pop()
                    elif part != ".":
                        resolved_parts.append(part)

                # Reconstruct the path
                resolved_path = Path(*resolved_parts)

                # Check if it exists and make relative to repo root
                resolved_abs = resolved_path.resolve()
                if resolved_abs.is_relative_to(repo_root_abs):
                    return resolved_abs.relative_to(repo_root_abs), False
                else:
                    return None, False
            except (ValueError, RuntimeError):
                return None, False
        elif link_target.endswith("/"):
            # Directory reference - check for common index files (AGENTS.md, README.md, index.md)
            index_files = ["AGENTS.md", "README.md", "index.md"]

            # Try relative to repo root first
            candidate_dir = (repo_root_abs / link_target).resolve()
            if candidate_dir.exists() and candidate_dir.is_relative_to(repo_root_abs):
                # Check for index files in this directory
                for index_file in index_files:
                    index_path = candidate_dir / index_file
                    if index_path.exists() and index_path.is_relative_to(repo_root_abs):
                        return index_path.relative_to(repo_root_abs), False
                # Directory exists but no index file found - return directory itself
                return candidate_dir.relative_to(repo_root_abs), False

            # Fallback: relative to source file directory
            source_dir = source_file.parent
            candidate_dir = (source_dir / link_target).resolve()
            if candidate_dir.exists() and candidate_dir.is_relative_to(repo_root_abs):
                # Check for index files in this directory
                for index_file in index_files:
                    index_path = candidate_dir / index_file
                    if index_path.exists() and index_path.is_relative_to(repo_root_abs):
                        return index_path.relative_to(repo_root_abs), False
                # Directory exists but no index file found - return directory itself
                return candidate_dir.relative_to(repo_root_abs), False

            return None, False
        else:
            # Assume relative to repo root or relative to source file
            # First try relative to source file directory
            source_dir = source_file.parent
            candidate1 = (source_dir / link_target).resolve()
            if candidate1.exists() and candidate1.is_relative_to(repo_root_abs):
                return candidate1.relative_to(repo_root_abs), False

            # Then try relative to repo root
            candidate2 = (repo_root_abs / link_target).resolve()
            if candidate2.exists() and candidate2.is_relative_to(repo_root_abs):
                return candidate2.relative_to(repo_root_abs), False

            return None, False

    def validate_file_links(self, file_path: Path) -> Dict[str, List[Dict[str, str]]]:
        """Validate all links in a markdown file.

        Args:
            file_path: Path to the markdown file

        Returns:
            Dictionary with 'valid' and 'broken' link lists
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, IOError) as e:
            logger.warning(f"Could not read {file_path}: {e}")
            return {"valid": [], "broken": []}

        links = self.extract_markdown_links(content, file_path)
        valid_links = []
        broken_links = []

        for link_text, link_target, line_num in links:
            resolved_path, is_external = self.resolve_link_target(
                link_target, file_path
            )

            if is_external:
                # External links are considered valid (we don't check them)
                valid_links.append(
                    {
                        "text": link_text,
                        "target": link_target,
                        "line": str(line_num),
                        "type": "external",
                    }
                )
            elif link_target.startswith("#"):
                # Anchor links within the same file are valid
                valid_links.append(
                    {
                        "text": link_text,
                        "target": link_target,
                        "line": str(line_num),
                        "type": "anchor",
                    }
                )
            elif "#" in link_target:
                # Links with anchors (file.md#anchor) - check if file exists
                if resolved_path and resolved_path in self.all_files:
                    valid_links.append(
                        {
                            "text": link_text,
                            "target": link_target,
                            "line": str(line_num),
                            "type": "internal_anchor",
                        }
                    )
                else:
                    broken_links.append(
                        {
                            "text": link_text,
                            "target": link_target,
                            "line": str(line_num),
                            "type": "broken",
                            "file": str(file_path),
                        }
                    )
            elif resolved_path:
                # Check if it's a directory reference (ends with /)
                # If resolved_path is a file (index file), treat it as valid
                if link_target.endswith("/"):
                    if resolved_path in self.all_files:
                        # Directory link resolved to an index file (AGENTS.md, README.md, etc.)
                        valid_links.append(
                            {
                                "text": link_text,
                                "target": link_target,
                                "line": str(line_num),
                                "type": "directory_index",
                            }
                        )
                    elif resolved_path in self.all_dirs:
                        # Directory exists but no index file found
                        valid_links.append(
                            {
                                "text": link_text,
                                "target": link_target,
                                "line": str(line_num),
                                "type": "directory",
                            }
                        )
                    else:
                        broken_links.append(
                            {
                                "text": link_text,
                                "target": link_target,
                                "line": str(line_num),
                                "type": "broken",
                                "file": str(file_path),
                            }
                        )
                elif resolved_path in self.all_files:
                    valid_links.append(
                        {
                            "text": link_text,
                            "target": str(resolved_path),
                            "line": str(line_num),
                            "type": "internal",
                        }
                    )
                else:
                    broken_links.append(
                        {
                            "text": link_text,
                            "target": link_target,
                            "line": str(line_num),
                            "type": "broken",
                            "file": str(file_path),
                        }
                    )
            else:
                broken_links.append(
                    {
                        "text": link_text,
                        "target": link_target,
                        "line": str(line_num),
                        "type": "broken",
                        "file": str(file_path),
                    }
                )

        return {"valid": valid_links, "broken": broken_links}

    def validate_all_markdown_files(self) -> Dict[str, Dict[str, List[Dict[str, str]]]]:
        """Validate links in all markdown files in the repository.

        Returns:
            Dictionary mapping file paths to their validation results
        """
        results = {}

        # Find all markdown files
        markdown_files = []
        for ext in ["*.md", "*.markdown"]:
            markdown_files.extend(self.repo_root.rglob(ext))

        for md_file in sorted(markdown_files):
            relative_path = md_file.relative_to(self.repo_root)
            logger.info(f"Validating links in {relative_path}")
            results[str(relative_path)] = self.validate_file_links(md_file)

        return results

    def generate_report(
        self, validation_results: Dict[str, Dict[str, List[Dict[str, str]]]]
    ) -> str:
        """Generate a comprehensive validation report.

        Args:
            validation_results: Results from validate_all_markdown_files

        Returns:
            Formatted report string
        """
        total_files = len(validation_results)
        total_valid_links = 0
        total_broken_links = 0
        broken_links_details = []

        for file_path, file_results in validation_results.items():
            valid_count = len(file_results["valid"])
            broken_count = len(file_results["broken"])

            total_valid_links += valid_count
            total_broken_links += broken_count

            if broken_count > 0:
                broken_links_details.extend(file_results["broken"])

        # Generate report
        report_lines = [
            "# Markdown Link Validation Report",
            "",
            f"## Summary",
            "",
            f"- **Files scanned**: {total_files}",
            f"- **Valid links**: {total_valid_links}",
            f"- **Broken links**: {total_broken_links}",
            "",
        ]

        if broken_links_details:
            report_lines.extend(
                [
                    "## Broken Links",
                    "",
                    "| File | Line | Link Text | Target |",
                    "|------|------|-----------|--------|",
                ]
            )

            for broken in broken_links_details:
                report_lines.append(
                    f"| {broken['file']} | {broken['line']} | {broken['text']} | {broken['target']} |"
                )

            report_lines.append("")
        else:
            report_lines.extend(
                [
                    "## ✅ All Links Valid",
                    "",
                    "No broken links found in the repository!",
                    "",
                ]
            )

        # File-by-file breakdown
        report_lines.extend(
            [
                "## File-by-File Results",
                "",
                "| File | Valid | Broken |",
                "|------|-------|--------|",
            ]
        )

        for file_path, file_results in validation_results.items():
            valid_count = len(file_results["valid"])
            broken_count = len(file_results["broken"])
            status = "✅" if broken_count == 0 else "❌"
            report_lines.append(f"| {file_path} | {valid_count} | {broken_count} |")

        return "\n".join(report_lines)


def main() -> int:
    """Main entry point for link validation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate markdown links in repository"
    )
    parser.add_argument("--output", type=str, help="Output file for validation report")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Setup logging
    if args.verbose:
        import logging

        logging.getLogger().setLevel(logging.INFO)

    # Run validation
    repo_root = Path.cwd()
    validator = LinkValidator(repo_root)

    logger.info("Starting markdown link validation...")
    results = validator.validate_all_markdown_files()

    # Generate report
    report = validator.generate_report(results)

    # Count broken links
    total_broken = sum(len(file_results["broken"]) for file_results in results.values())

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        logger.info(f"Report written to {args.output}")
    else:
        print(report)

    # Return exit code based on validation results
    return 0 if total_broken == 0 else 1


if __name__ == "__main__":
    exit(main())
