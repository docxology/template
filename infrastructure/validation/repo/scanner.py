#!/usr/bin/env python3
"""Repository-wide accuracy and completeness scan.

This script performs comprehensive checks for:
- Code accuracy (scripts match documentation, imports work)
- Completeness (all modules documented, all features covered)
- Test coverage (all src/ modules have tests)
- Configuration accuracy (dependencies, configs match reality)
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

from infrastructure.core.logging.utils import get_logger
from infrastructure.validation.docs.models import CompletenessGap, ScanAccuracyIssue
from infrastructure.validation.repo._repo_ast import extract_imports, verify_import
from infrastructure.validation.repo._repo_documented_commands import check_documented_commands
from infrastructure.validation.repo._repo_scan_report import build_repo_scan_report
from infrastructure.validation.repo.models import RepoScanResults

logger = get_logger(__name__)


def _find_repo_root_for_main() -> Path:
    """Walk parents from this file until a directory containing pyproject.toml."""
    here = Path(__file__).resolve().parent
    for p in [here, *here.parents]:
        if (p / "pyproject.toml").exists():
            return p
    return here.parents[3]


class RepositoryScanner:
    """Comprehensive repository scanner."""

    def __init__(self, repo_root: Path):
        """Initialize repository scanner with root path."""
        self.repo_root = repo_root.resolve()
        self.results = RepoScanResults()
        self.src_modules: set[str] = set()
        self.script_files: list[Path] = []
        self.test_files: list[Path] = []
        self.documented_modules: set[str] = set()

    def scan_all(self) -> RepoScanResults:
        """Execute all 6 phases of the repository scan.

        Performs comprehensive repository analysis in sequential phases:
        1. Structure discovery (src modules, scripts, tests, documentation)
        2. Code accuracy (import verification, command existence)
        3. Completeness (documentation coverage, test coverage)
        4. Test coverage (pytest execution and results)
        5. Configuration (pyproject.toml, config.yaml validation)
        6. Thin orchestrator pattern compliance

        Returns:
            RepoScanResults: Container with accuracy_issues list, completeness_gaps
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

    def _discover_structure(self) -> None:
        """Discover repository structure."""
        src_dir = self.repo_root / "src"
        if src_dir.exists():
            for py_file in src_dir.glob("*.py"):
                if py_file.name != "__init__.py":
                    self.src_modules.add(py_file.stem)

        for script_dir in [
            self.repo_root / "scripts",
            self.repo_root / "repo_utilities",
        ]:
            if script_dir.exists():
                for py_file in script_dir.glob("*.py"):
                    if py_file.name != "__init__.py":
                        self.script_files.append(py_file)

        tests_dir = self.repo_root / "tests"
        if tests_dir.exists():
            for test_file in tests_dir.glob("test_*.py"):
                self.test_files.append(test_file)

        self._find_documented_modules()

        logger.info(f"Found {len(self.src_modules)} src/ modules")
        logger.info(f"Found {len(self.script_files)} script files")
        logger.info(f"Found {len(self.test_files)} test files")
        logger.info(f"Found {len(self.documented_modules)} documented modules")

    def _find_documented_modules(self) -> None:
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
                    for module in self.src_modules:
                        if module in content:
                            self.documented_modules.add(module)
                except (OSError, UnicodeDecodeError) as e:
                    logger.debug(f"Failed to scan {md_file} for module references: {e}")

    def _check_code_accuracy(self) -> None:
        """Check code accuracy."""
        issues: list[ScanAccuracyIssue] = []

        for script in self.script_files:
            try:
                imports = extract_imports(script)
                for imp in imports:
                    if imp.startswith("src.") or imp in self.src_modules:
                        module_name = imp.replace("src.", "")
                        if module_name in self.src_modules:
                            if not self._verify_import(script, module_name, imports[imp]):
                                issues.append(
                                    ScanAccuracyIssue(
                                        category="import",
                                        severity="error",
                                        file=str(script.relative_to(self.repo_root)),
                                        message=f"Import verification failed for {imp}",
                                        details=f"Functions/classes: {imports[imp]}",
                                    )
                                )
            except (OSError, UnicodeDecodeError, SyntaxError) as e:
                issues.append(
                    ScanAccuracyIssue(
                        category="import",
                        severity="warning",
                        file=str(script.relative_to(self.repo_root)),
                        message=f"Could not parse imports: {e}",
                    )
                )

        self._check_documented_commands_into(issues)

        self.results.accuracy_issues.extend(issues)
        logger.info(f"Found {len(issues)} code accuracy issues")

    def _extract_imports(self, file_path: Path) -> dict[str, list[str]]:
        """Extract imports from a Python file (delegates to shared AST helper)."""
        return extract_imports(file_path)

    def _verify_import(self, script_path: Path, module_name: str, items: list[str]) -> bool:
        """Verify imported symbols exist in src (script_path reserved for API stability)."""
        _ = script_path
        return verify_import(self.repo_root, module_name, items)

    def _check_documented_commands(self) -> None:
        """Append documented-command issues to ``results`` (tests and scan phase 2)."""
        self.results.accuracy_issues.extend(
            check_documented_commands(self.repo_root, self.src_modules)
        )

    def _check_documented_commands_into(self, issues: list[ScanAccuracyIssue]) -> None:
        """Merge documented-command findings into a local issues list (phase 2)."""
        issues.extend(check_documented_commands(self.repo_root, self.src_modules))

    def _check_completeness(self) -> None:
        """Check completeness."""
        gaps = []

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

        documented_scripts = set()
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
                except (OSError, UnicodeDecodeError) as e:
                    logger.debug(f"Failed to check script documentation in {md_file}: {e}")

        for script in self.script_files:
            if script.name not in documented_scripts and not script.name.startswith("_"):
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

    def _check_test_coverage(self) -> None:
        """Check test coverage."""
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
                if "FAILED" in result.stdout or "ERROR" in result.stdout:
                    self.results.accuracy_issues.append(
                        ScanAccuracyIssue(
                            category="testing",
                            severity="error",
                            file="tests/",
                            message="Test suite has failures",
                            details=(
                                result.stdout[-500:] if result.stdout else result.stderr[-500:]
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
        except (subprocess.SubprocessError, OSError) as e:
            logger.warning(f"Could not run tests: {e}")

    def _check_configuration(self) -> None:
        """Check configuration accuracy."""
        issues = []

        config_path = self.repo_root / "project" / "manuscript" / "config.yaml"
        example_path = self.repo_root / "project" / "manuscript" / "config.yaml.example"

        if config_path.exists() and example_path.exists():
            try:
                with open(config_path, encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                with open(example_path, encoding="utf-8") as f:
                    example = yaml.safe_load(f)

                if not self._configs_match(config, example):
                    issues.append(
                        ScanAccuracyIssue(
                            category="configuration",
                            severity="warning",
                            file="project/manuscript/config.yaml",
                            message="Config structure may not match example",
                        )
                    )
            except (OSError, yaml.YAMLError, ValueError) as e:
                issues.append(
                    ScanAccuracyIssue(
                        category="configuration",
                        severity="warning",
                        file="project/manuscript/config.yaml",
                        message=f"Could not parse config: {e}",
                    )
                )

        self.results.accuracy_issues.extend(issues)
        logger.info(f"Found {len(issues)} configuration issues")

    def _configs_match(self, config: dict[str, Any], example: dict[str, Any]) -> bool:
        """Check if config structures match."""
        if not config or not example:
            return False

        config_keys = set(config.keys())
        example_keys = set(example.keys())

        return config_keys.issubset(example_keys) or config_keys == example_keys

    def _check_thin_orchestrator_pattern(self) -> None:
        """Check thin orchestrator pattern compliance."""
        issues = []

        for script in self.script_files:
            if script.name.startswith("_"):
                continue

            try:
                content = script.read_text(encoding="utf-8")
                imports = extract_imports(script)

                has_src_import = False
                for imp in imports:
                    if imp in self.src_modules or "src" in imp.lower():
                        has_src_import = True
                        break

                business_logic_patterns = [
                    r'def\s+\w+\([^)]*\):\s*\n\s*"""[^"]*algorithm',
                    r"def\s+\w+\([^)]*\):\s*\n\s*#\s*[Cc]ompute",
                ]

                for pattern in business_logic_patterns:
                    if re.search(pattern, content, re.MULTILINE):
                        break

                if not has_src_import and script.parent.name == "scripts":
                    issues.append(
                        ScanAccuracyIssue(
                            category="architecture",
                            severity="warning",
                            file=str(script.relative_to(self.repo_root)),
                            message="Script may not follow thin orchestrator pattern (no src/ imports)",  # noqa: E501
                        )
                    )
            except (OSError, UnicodeDecodeError, SyntaxError) as e:
                issues.append(
                    ScanAccuracyIssue(
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
        return build_repo_scan_report(self.results)


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
    repo_root = _find_repo_root_for_main()
    scanner = RepositoryScanner(repo_root)

    results = scanner.scan_all()

    report = scanner.generate_report()
    report_path = repo_root / "docs" / "REPO_ACCURACY_COMPLETENESS_REPORT.md"
    _tmp = report_path.with_suffix(report_path.suffix + ".tmp")
    try:
        _tmp.write_text(report, encoding="utf-8")
        _tmp.replace(report_path)
    except OSError:
        _tmp.unlink(missing_ok=True)
        raise

    logger.info("\n" + "=" * 70)
    logger.info("SCAN COMPLETE")
    logger.info("=" * 70)
    logger.info(f"\nReport saved to: {report_path}")
    logger.info("\nSummary:")
    logger.info(f"  Accuracy Issues: {len(results.accuracy_issues)}")
    logger.info(f"  Completeness Gaps: {len(results.completeness_gaps)}")

    error_count = sum(1 for i in results.accuracy_issues if i.severity == "error")
    warning_count = sum(1 for i in results.accuracy_issues if i.severity == "warning")

    logger.info(f"\n  Errors: {error_count}")
    logger.info(f"  Warnings: {warning_count}")

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
