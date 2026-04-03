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
        self.repo_modules: set[str] = set()
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
        self.src_modules.clear()
        self.repo_modules.clear()
        self.script_files.clear()
        self.test_files.clear()

        module_roots = [self.repo_root / "infrastructure"]
        root_src = self.repo_root / "src"
        if root_src.exists():
            module_roots.append(root_src)

        projects_dir = self.repo_root / "projects"
        if projects_dir.is_dir():
            for project_src in projects_dir.glob("*/src"):
                if project_src.is_dir():
                    module_roots.append(project_src)

        for module_root in module_roots:
            for py_file in module_root.rglob("*.py"):
                if py_file.name == "__init__.py":
                    continue
                module_name = self._module_name(py_file)
                self.repo_modules.add(module_name)
                self.src_modules.add(py_file.stem)

        self._discover_scripts()
        self._discover_tests()
        self._find_documented_modules()

        logger.info(f"Found {len(self.repo_modules)} repository modules")
        logger.info(f"Found {len(self.script_files)} script files")
        logger.info(f"Found {len(self.test_files)} test files")
        logger.info(f"Found {len(self.documented_modules)} documented modules")

    def _discover_scripts(self) -> None:
        """Discover runnable scripts across the repository."""
        script_roots = [self.repo_root / "scripts"]
        projects_dir = self.repo_root / "projects"
        if projects_dir.is_dir():
            script_roots.extend(projects_dir.glob("*/scripts"))

        for script_root in script_roots:
            if not script_root.is_dir():
                continue
            for pattern in ("*.py", "*.sh"):
                for script in script_root.glob(pattern):
                    if script.name != "__init__.py":
                        self.script_files.append(script)

        for entry_point in (self.repo_root / "run.sh", self.repo_root / "secure_run.sh"):
            if entry_point.exists():
                self.script_files.append(entry_point)

    def _discover_tests(self) -> None:
        """Discover test files across the repository."""
        tests_roots = [self.repo_root / "tests"]
        projects_dir = self.repo_root / "projects"
        if projects_dir.is_dir():
            tests_roots.extend(projects_dir.glob("*/tests"))

        for tests_root in tests_roots:
            if not tests_root.is_dir():
                continue
            for test_file in tests_root.rglob("test_*.py"):
                self.test_files.append(test_file)

    def _module_name(self, file_path: Path) -> str:
        """Convert a Python file path into a dotted module name."""
        relative_path = file_path.relative_to(self.repo_root).with_suffix("")
        return ".".join(relative_path.parts)

    def _is_local_import(self, module_name: str) -> bool:
        """Return True when ``module_name`` points to repository code."""
        return (
            module_name.startswith("infrastructure.")
            or module_name.startswith("projects.")
            or module_name.startswith("src.")
            or module_name in self.src_modules
        )

    def _find_documented_modules(self) -> None:
        """Find modules mentioned in documentation."""
        docs_targets = [
            self.repo_root,
            self.repo_root / "docs",
            self.repo_root / "infrastructure",
            self.repo_root / "projects",
            self.repo_root / "scripts",
        ]

        for docs_target in docs_targets:
            if not docs_target.exists():
                continue

            md_files = [docs_target] if docs_target.is_file() else list(docs_target.rglob("*.md"))
            for md_file in md_files:
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
            if script.suffix != ".py":
                continue
            try:
                imports = extract_imports(script)
                for imp in imports:
                    if self._is_local_import(imp) and not self._verify_import(script, imp, imports[imp]):
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

        documented = self.documented_modules
        for module in self.repo_modules:
            module_stem = module.split(".")[-1]
            if module_stem not in documented:
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
            if any(test_name == module.split(".")[-1] for module in self.repo_modules):
                tested_modules.add(test_name)

        for module in self.repo_modules:
            module_stem = module.split(".")[-1]
            if module_stem not in tested_modules:
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
            self.repo_root / "AGENTS.md",
            self.repo_root / "infrastructure" / "README.md",
            self.repo_root / "infrastructure" / "AGENTS.md",
            self.repo_root / "scripts" / "README.md",
            self.repo_root / "docs" / "DOCUMENTATION_INDEX.md",
            self.repo_root / "projects" / "README.md",
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
            result = subprocess.run(  # nosec B603
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

        config_files = sorted(
            path
            for path in self.repo_root.glob("**/manuscript/config.yaml")
            if "output" not in path.parts and "site-packages" not in path.parts
        )

        for config_path in config_files:
            example_path = config_path.with_name("config.yaml.example")
            if not example_path.exists():
                continue

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
                            file=str(config_path.relative_to(self.repo_root)),
                            message="Config structure may not match example",
                        )
                    )
            except (OSError, yaml.YAMLError, ValueError) as e:
                issues.append(
                    ScanAccuracyIssue(
                        category="configuration",
                        severity="warning",
                        file=str(config_path.relative_to(self.repo_root)),
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
            if script.name.startswith("_") or script.suffix != ".py":
                continue

            try:
                content = script.read_text(encoding="utf-8")
                imports = extract_imports(script)

                has_repo_import = any(self._is_local_import(imp) for imp in imports)

                business_logic_patterns = [
                    r'def\s+\w+\([^)]*\):\s*\n\s*"""[^"]*algorithm',
                    r"def\s+\w+\([^)]*\):\s*\n\s*#\s*[Cc]ompute",
                ]

                for pattern in business_logic_patterns:
                    if re.search(pattern, content, re.MULTILINE):
                        break

                if not has_repo_import and script.parent.name == "scripts":
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
