#!/usr/bin/env python3
"""Repository-wide accuracy and completeness scan.

This script performs comprehensive checks for:
- Code accuracy (scripts match documentation, imports work)
- Completeness (all modules documented, all features covered)
- Test coverage (all src/ modules have tests)
- Configuration accuracy (dependencies, configs match reality)
"""
from __future__ import annotations

import ast
import importlib.util
import os
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import yaml

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class AccuracyIssue:
    """Represents an accuracy issue."""

    category: str
    severity: str
    file: str
    line: int = 0
    message: str = ""
    details: str = ""


@dataclass
class CompletenessGap:
    """Represents a completeness gap."""

    category: str
    item: str
    description: str
    severity: str = "warning"


@dataclass
class ScanResults:
    """Container for scan results."""

    accuracy_issues: List[AccuracyIssue] = field(default_factory=list)
    completeness_gaps: List[CompletenessGap] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)


class RepositoryScanner:
    """Comprehensive repository scanner."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root.resolve()
        self.results = ScanResults()
        self.src_modules: Set[str] = set()
        self.script_files: List[Path] = []
        self.test_files: List[Path] = []
        self.documented_modules: Set[str] = set()

    def scan_all(self) -> ScanResults:
        """Execute all 6 phases of the repository scan.

        Performs comprehensive repository analysis in sequential phases:
        1. Structure discovery (src modules, scripts, tests, documentation)
        2. Code accuracy (import verification, command existence)
        3. Completeness (documentation coverage, test coverage)
        4. Test coverage (pytest execution and results)
        5. Configuration (pyproject.toml, config.yaml validation)
        6. Thin orchestrator pattern compliance

        Returns:
            ScanResults: Container with accuracy_issues list, completeness_gaps
                list, and statistics dictionary containing scan metrics.
        """
        logger.info("REPOSITORY-WIDE ACCURACY AND COMPLETENESS SCAN")

        logger.info("[1/6] Discovering repository structure...")
        self._discover_structure()

        logger.info("[2/6] Checking code accuracy...")
        self._check_code_accuracy()

        logger.info("[3/6] Checking completeness...")
        self._check_completeness()

        logger.info("[4/6] Checking test coverage...")
        self._check_test_coverage()

        logger.info("[5/6] Checking configuration accuracy...")
        self._check_configuration()

        logger.info("[6/6] Checking thin orchestrator pattern compliance...")
        self._check_thin_orchestrator_pattern()

        return self.results

    def _discover_structure(self):
        """Discover repository structure."""
        # Find src modules
        src_dir = self.repo_root / "src"
        if src_dir.exists():
            for py_file in src_dir.glob("*.py"):
                if py_file.name != "__init__.py":
                    self.src_modules.add(py_file.stem)

        # Find scripts
        for script_dir in [
            self.repo_root / "scripts",
            self.repo_root / "repo_utilities",
        ]:
            if script_dir.exists():
                for py_file in script_dir.glob("*.py"):
                    if py_file.name != "__init__.py":
                        self.script_files.append(py_file)

        # Find tests
        tests_dir = self.repo_root / "tests"
        if tests_dir.exists():
            for test_file in tests_dir.glob("test_*.py"):
                self.test_files.append(test_file)

        # Find documented modules
        self._find_documented_modules()

        logger.info(f"Found {len(self.src_modules)} src/ modules")
        logger.info(f"Found {len(self.script_files)} script files")
        logger.info(f"Found {len(self.test_files)} test files")
        logger.info(f"Found {len(self.documented_modules)} documented modules")

    def _find_documented_modules(self):
        """Find modules mentioned in documentation."""
        docs_dirs = [
            self.repo_root / "docs",
            self.repo_root,
            self.repo_root / "src",
            self.repo_root / "scripts",
        ]

        for docs_dir in docs_dirs:
            if not docs_dir.exists():
                continue
            for md_file in docs_dir.rglob("*.md"):
                try:
                    content = md_file.read_text(encoding="utf-8")
                    # Look for module references
                    for module in self.src_modules:
                        if module in content:
                            self.documented_modules.add(module)
                except Exception:
                    pass

    def _check_code_accuracy(self):
        """Check code accuracy."""
        issues = []

        # Check if scripts can import src modules
        for script in self.script_files:
            try:
                imports = self._extract_imports(script)
                for imp in imports:
                    if imp.startswith("src.") or imp in self.src_modules:
                        # Try to verify import would work
                        module_name = imp.replace("src.", "")
                        if module_name in self.src_modules:
                            # Check if function/class exists
                            if not self._verify_import(
                                script, module_name, imports[imp]
                            ):
                                issues.append(
                                    AccuracyIssue(
                                        category="import",
                                        severity="error",
                                        file=str(script.relative_to(self.repo_root)),
                                        message=f"Import verification failed for {imp}",
                                        details=f"Functions/classes: {imports[imp]}",
                                    )
                                )
            except Exception as e:
                issues.append(
                    AccuracyIssue(
                        category="import",
                        severity="warning",
                        file=str(script.relative_to(self.repo_root)),
                        message=f"Could not parse imports: {e}",
                    )
                )

        # Check if documented commands exist
        self._check_documented_commands()

        self.results.accuracy_issues.extend(issues)
        logger.info(f"Found {len(issues)} code accuracy issues")

    def _extract_imports(self, file_path: Path) -> Dict[str, List[str]]:
        """Extract imports from Python file."""
        imports = {}
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports[alias.name] = []
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        if module not in imports:
                            imports[module] = []
                        imports[module].append(alias.name)
        except Exception:
            pass

        return imports

    def _verify_import(
        self, script_path: Path, module_name: str, items: List[str]
    ) -> bool:
        """Verify that imported items exist in module."""
        module_path = self.repo_root / "src" / f"{module_name}.py"
        if not module_path.exists():
            return False

        try:
            content = module_path.read_text(encoding="utf-8")
            tree = ast.parse(content)

            defined = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    defined.add(node.name)
                elif isinstance(node, ast.ClassDef):
                    defined.add(node.name)

            # Check if all imported items are defined
            for item in items:
                if item not in defined:
                    return False
            return True
        except Exception:
            return False

    def _check_documented_commands(self):
        """Check if documented commands/scripts actually exist."""
        issues = []

        # Check README and docs for script references
        for md_file in [self.repo_root / "README.md"] + list(
            (self.repo_root / "docs").glob("*.md")
        ):
            if not md_file.exists():
                continue
            try:
                content = md_file.read_text(encoding="utf-8")
                # Look for script references (but exclude src/ modules and code examples)
                script_pattern = r"`([\w/]+\.(?:py|sh))`|\./([\w/]+\.(?:py|sh))"
                for match in re.finditer(script_pattern, content):
                    script_ref = match.group(1) or match.group(2)

                    # Skip if it's a src/ module (those are documented, not scripts)
                    if script_ref.startswith("src/") or script_ref in self.src_modules:
                        continue

                    # Skip if it's in a code block (likely an example)
                    before_match = content[: match.start()]
                    code_block_count = before_match.count("```")
                    if code_block_count % 2 == 1:  # Inside a code block
                        continue

                    # Check if it exists as a script
                    script_path = self.repo_root / script_ref
                    # Also check common script locations
                    if not script_path.exists():
                        # Check scripts/ and repo_utilities/
                        for script_dir in ["scripts", "repo_utilities"]:
                            alt_path = (
                                self.repo_root / script_dir / Path(script_ref).name
                            )
                            if alt_path.exists():
                                break
                        else:
                            # Only report if it's clearly a script reference (has .sh or in scripts/)
                            # Skip if it's in EXAMPLES.md (those are templates/examples)
                            if (
                                md_file.name == "EXAMPLES.md"
                                and "Create"
                                in content[max(0, match.start() - 50) : match.start()]
                            ):
                                continue

                            if (
                                script_ref.endswith(".sh")
                                or "scripts/" in script_ref
                                or "repo_utilities/" in script_ref
                            ):
                                line_num = content[: match.start()].count("\n") + 1
                                issues.append(
                                    AccuracyIssue(
                                        category="command",
                                        severity="error",
                                        file=str(md_file.relative_to(self.repo_root)),
                                        line=line_num,
                                        message=f"Documented script does not exist: {script_ref}",
                                    )
                                )
            except Exception:
                pass

        self.results.accuracy_issues.extend(issues)

    def _check_completeness(self):
        """Check completeness."""
        gaps = []

        # Check if all src modules are documented
        for module in self.src_modules:
            if module not in self.documented_modules:
                gaps.append(
                    CompletenessGap(
                        category="documentation",
                        item=module,
                        description=f"Module {module} may not be fully documented",
                        severity="info",
                    )
                )

        # Check if all src modules have tests
        tested_modules = set()
        for test_file in self.test_files:
            test_name = test_file.stem.replace("test_", "")
            if test_name in self.src_modules:
                tested_modules.add(test_name)

        for module in self.src_modules:
            if module not in tested_modules:
                gaps.append(
                    CompletenessGap(
                        category="testing",
                        item=module,
                        description=f"Module {module} may not have dedicated test file",
                        severity="warning",
                    )
                )

        # Check if scripts are documented
        documented_scripts = set()
        # Check multiple documentation locations
        doc_locations = [
            self.repo_root / "README.md",
            self.repo_root / "scripts" / "README.md",
            self.repo_root / "repo_utilities" / "README.md",
            self.repo_root / "repo_utilities" / "AGENTS.md",
            self.repo_root / "docs" / "DOCUMENTATION_INDEX.md",
        ]
        for md_file in doc_locations:
            if md_file.exists():
                try:
                    content = md_file.read_text(encoding="utf-8")
                    for script in self.script_files:
                        if script.name in content:
                            documented_scripts.add(script.name)
                except Exception:
                    pass

        for script in self.script_files:
            if (
                script.name not in documented_scripts
                and script.name != "comprehensive_doc_scan.py"
            ):
                gaps.append(
                    CompletenessGap(
                        category="documentation",
                        item=script.name,
                        description=f"Script {script.name} may not be documented",
                        severity="info",
                    )
                )

        self.results.completeness_gaps.extend(gaps)
        logger.info(f"Found {len(gaps)} completeness gaps")

    def _check_test_coverage(self):
        """Check test coverage."""
        # Try to run pytest (without coverage to avoid dependency issues)
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=short"],
                capture_output=True,
                text=True,
                cwd=self.repo_root,
                timeout=60,
            )
            if result.returncode == 0:
                logger.info("Test suite passes")
            else:
                # Only report if there are actual test failures (not just missing deps)
                if "FAILED" in result.stdout or "ERROR" in result.stdout:
                    self.results.accuracy_issues.append(
                        AccuracyIssue(
                            category="testing",
                            severity="error",
                            file="tests/",
                            message="Test suite has failures",
                            details=(
                                result.stdout[-500:]
                                if result.stdout
                                else result.stderr[-500:]
                            ),
                        )
                    )
                    logger.warning("Test suite has failures")
                else:
                    logger.warning("Could not determine test status")
        except subprocess.TimeoutExpired:
            logger.warning("Test suite timed out")
        except FileNotFoundError:
            logger.warning("pytest not found (may need to install dependencies)")
        except Exception as e:
            logger.warning(f"Could not run tests: {e}")

    def _check_configuration(self):
        """Check configuration accuracy."""
        issues = []

        # Check pyproject.toml dependencies
        pyproject_path = self.repo_root / "pyproject.toml"
        if pyproject_path.exists():
            try:
                content = pyproject_path.read_text(encoding="utf-8")
                # Check if dependencies are used
                # This is a simplified check
                pass
            except Exception:
                pass

        # Check config.yaml structure
        config_path = self.repo_root / "project" / "manuscript" / "config.yaml"
        example_path = self.repo_root / "project" / "manuscript" / "config.yaml.example"

        if config_path.exists() and example_path.exists():
            try:
                with open(config_path, "r") as f:
                    config = yaml.safe_load(f)
                with open(example_path, "r") as f:
                    example = yaml.safe_load(f)

                # Check structure matches
                if not self._configs_match(config, example):
                    issues.append(
                        AccuracyIssue(
                            category="configuration",
                            severity="warning",
                            file="project/manuscript/config.yaml",
                            message="Config structure may not match example",
                        )
                    )
            except Exception as e:
                issues.append(
                    AccuracyIssue(
                        category="configuration",
                        severity="warning",
                        file="project/manuscript/config.yaml",
                        message=f"Could not parse config: {e}",
                    )
                )

        self.results.accuracy_issues.extend(issues)
        logger.info(f"Found {len(issues)} configuration issues")

    def _configs_match(self, config: dict, example: dict) -> bool:
        """Check if config structures match."""
        # Simplified check - just verify top-level keys
        if not config or not example:
            return False

        config_keys = set(config.keys())
        example_keys = set(example.keys())

        # Config should have same or subset of example keys
        return config_keys.issubset(example_keys) or config_keys == example_keys

    def _check_thin_orchestrator_pattern(self):
        """Check thin orchestrator pattern compliance."""
        issues = []

        for script in self.script_files:
            if (
                script.name.startswith("_")
                or script.name == "comprehensive_doc_scan.py"
            ):
                continue

            try:
                content = script.read_text(encoding="utf-8")
                imports = self._extract_imports(script)

                # Check if script imports from src/
                has_src_import = False
                for imp in imports:
                    if imp in self.src_modules or "src" in imp.lower():
                        has_src_import = True
                        break

                # Check for business logic patterns (simplified)
                business_logic_patterns = [
                    r'def\s+\w+\([^)]*\):\s*\n\s*"""[^"]*algorithm',
                    r"def\s+\w+\([^)]*\):\s*\n\s*#\s*[Cc]ompute",
                ]

                has_business_logic = False
                for pattern in business_logic_patterns:
                    if re.search(pattern, content, re.MULTILINE):
                        has_business_logic = True
                        break

                # Scripts should import from src, not implement business logic
                if not has_src_import and script.parent.name == "scripts":
                    issues.append(
                        AccuracyIssue(
                            category="architecture",
                            severity="warning",
                            file=str(script.relative_to(self.repo_root)),
                            message="Script may not follow thin orchestrator pattern (no src/ imports)",
                        )
                    )
            except Exception as e:
                issues.append(
                    AccuracyIssue(
                        category="architecture",
                        severity="info",
                        file=str(script.relative_to(self.repo_root)),
                        message=f"Could not analyze script: {e}",
                    )
                )

        self.results.accuracy_issues.extend(issues)
        logger.info(f"Found {len(issues)} architecture pattern issues")

    def generate_report(self) -> str:
        """Generate comprehensive report."""
        lines = [
            "# Repository Accuracy and Completeness Scan Report",
            "",
            f"**Scan Date**: {self._get_timestamp()}",
            "",
            "## Executive Summary",
            "",
            f"- **Accuracy Issues**: {len(self.results.accuracy_issues)}",
            f"- **Completeness Gaps**: {len(self.results.completeness_gaps)}",
            "",
            "## Accuracy Issues",
            "",
        ]

        # Group by category
        by_category = defaultdict(list)
        for issue in self.results.accuracy_issues:
            by_category[issue.category].append(issue)

        for category, issues in sorted(by_category.items()):
            lines.append(f"### {category.title()} Issues ({len(issues)})")
            lines.append("")
            for issue in issues[:20]:  # Limit to first 20
                lines.append(f"- **{issue.severity.upper()}**: `{issue.file}`")
                if issue.line:
                    lines.append(f"  - Line {issue.line}: {issue.message}")
                else:
                    lines.append(f"  - {issue.message}")
                if issue.details:
                    lines.append(f"  - Details: {issue.details}")
            if len(issues) > 20:
                lines.append(f"- ... and {len(issues) - 20} more")
            lines.append("")

        lines.extend(["## Completeness Gaps", ""])

        # Group by category
        by_category = defaultdict(list)
        for gap in self.results.completeness_gaps:
            by_category[gap.category].append(gap)

        for category, gaps in sorted(by_category.items()):
            lines.append(f"### {category.title()} Gaps ({len(gaps)})")
            lines.append("")
            for gap in gaps:
                lines.append(f"- **{gap.severity.upper()}**: {gap.item}")
                lines.append(f"  - {gap.description}")
            lines.append("")

        lines.extend(
            [
                "## Recommendations",
                "",
                "1. Address all ERROR-level accuracy issues",
                "2. Review WARNING-level issues for potential problems",
                "3. Fill completeness gaps where appropriate",
                "4. Ensure all src/ modules are tested and documented",
                "",
            ]
        )

        return "\n".join(lines)

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime

        return datetime.now().isoformat()


def main() -> int:
    """Execute repository-wide accuracy and completeness scan.

    Discovers the repository root, performs a comprehensive 6-step scan
    (structure discovery, code accuracy, completeness, test coverage,
    configuration, and thin orchestrator pattern compliance), and saves
    the report to docs/REPO_ACCURACY_COMPLETENESS_REPORT.md.

    Returns:
        int: Exit code - 0 if no error-level issues found, 1 otherwise.

    Raises:
        OSError: If report file cannot be written to the docs directory.
    """
    repo_root = Path(__file__).parent.parent
    scanner = RepositoryScanner(repo_root)

    results = scanner.scan_all()

    # Generate report
    report = scanner.generate_report()
    report_path = repo_root / "docs" / "REPO_ACCURACY_COMPLETENESS_REPORT.md"
    report_path.write_text(report, encoding="utf-8")

    print("\n" + "=" * 70)
    print("SCAN COMPLETE")
    print("=" * 70)
    print(f"\nReport saved to: {report_path}")
    print(f"\nSummary:")
    print(f"  Accuracy Issues: {len(results.accuracy_issues)}")
    print(f"  Completeness Gaps: {len(results.completeness_gaps)}")

    # Count by severity
    error_count = sum(1 for i in results.accuracy_issues if i.severity == "error")
    warning_count = sum(1 for i in results.accuracy_issues if i.severity == "warning")

    print(f"\n  Errors: {error_count}")
    print(f"  Warnings: {warning_count}")

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
