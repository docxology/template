"""Integration and workflow tests for infrastructure.validation.repo.scanner."""

import pytest

from infrastructure.validation.repo import scanner as repo_scanner
from infrastructure.validation.repo.scanner import RepositoryScanner, RepoScanResults

ScanResults = RepoScanResults


class TestRepositoryScannerIntegration:
    """Integration tests for RepositoryScanner."""

    def test_scan_all(self, tmp_path):
        """Test complete scan workflow."""
        # Create minimal repo structure
        src = tmp_path / "src"
        src.mkdir()
        (src / "__init__.py").write_text("")
        (src / "example.py").write_text("def func(): return 42")

        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "run.py").write_text("from src.example import func")

        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "test_example.py").write_text("def test_example(): pass")

        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'")
        (tmp_path / "README.md").write_text("# Test\n\nUsing example module...")

        scanner = RepositoryScanner(tmp_path)
        results = scanner.scan_all()

        assert isinstance(results, RepoScanResults)
        assert results.statistics["repo_modules"] == 1
        assert results.statistics["script_files"] == 1
        assert results.statistics["test_files"] == 1

    def test_scan_with_repo_utilities(self, tmp_path):
        """Test scanning with repo_utilities directory."""
        repo_utils = tmp_path / "repo_utilities"
        repo_utils.mkdir()
        (repo_utils / "helper.py").write_text("def help(): pass")

        scanner = RepositoryScanner(tmp_path)
        scanner._discover_structure()

        assert scanner.script_files == [repo_utils / "helper.py"]

    def test_scan_with_docs_directory(self, tmp_path):
        """Test scanning with docs directory."""
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "guide.md").write_text("# Guide")
        (docs / "api.md").write_text("# API Reference")

        src = tmp_path / "src"
        src.mkdir()
        (src / "module.py").write_text("# Module")

        (tmp_path / "README.md").write_text("See [guide](docs/guide.md)")

        scanner = RepositoryScanner(tmp_path)
        scanner.src_modules = {"module"}
        scanner._find_documented_modules()
        scanner._check_documented_commands()

        assert scanner.results.accuracy_issues == []


class TestRepositoryScannerMethods:
    """Test RepositoryScanner methods."""

    def test_extract_imports(self, tmp_path):
        """Test extracting imports from Python files."""
        script = tmp_path / "script.py"
        script.write_text(
            """
import os
from pathlib import Path
from src.module import func
import numpy as np
"""
        )

        scanner = RepositoryScanner(tmp_path)
        imports = scanner._extract_imports(script)

        assert "os" in imports

    def test_extract_imports_empty_file(self, tmp_path):
        """Test extracting imports from empty file."""
        script = tmp_path / "empty.py"
        script.write_text("")

        scanner = RepositoryScanner(tmp_path)
        imports = scanner._extract_imports(script)

        assert len(imports) == 0

    def test_extract_imports_syntax_error(self, tmp_path):
        """Test extracting imports from file with syntax error."""
        script = tmp_path / "bad.py"
        script.write_text("def broken(")

        scanner = RepositoryScanner(tmp_path)
        imports = scanner._extract_imports(script)

        assert imports == {}


class TestRepositoryScannerCheckCode:
    """Test code accuracy checking."""

    def test_check_code_accuracy_with_imports(self, tmp_path):
        """Test code accuracy checking with imports."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "__init__.py").write_text("")
        (src / "example.py").write_text("def func(): pass")

        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "run.py").write_text("from src.example import func")

        scanner = RepositoryScanner(tmp_path)
        scanner._discover_structure()
        scanner._check_code_accuracy()

        assert scanner.results.accuracy_issues == []

    def test_check_code_accuracy_with_project_imports(self, tmp_path):
        """Test code accuracy checking with project-local imports."""
        project_src = tmp_path / "projects" / "example_project" / "src"
        project_src.mkdir(parents=True)
        (project_src / "optimizer.py").write_text("def optimize():\n    return 1\n")

        project_scripts = tmp_path / "projects" / "example_project" / "scripts"
        project_scripts.mkdir(parents=True)
        (project_scripts / "run.py").write_text(
            "from projects.example_project.src.optimizer import optimize\nprint(optimize())"
        )

        scanner = RepositoryScanner(tmp_path)
        scanner._discover_structure()
        scanner._check_code_accuracy()

        import_issues = [i for i in scanner.results.accuracy_issues if i.category == "import"]
        assert import_issues == []


class TestRepositoryScannerCompleteness:
    """Test completeness checking."""

    def test_check_completeness_all_documented(self, tmp_path):
        """Test completeness with all modules documented."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "example.py").write_text("# Example module")

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "guide.md").write_text("# Guide\n\nThe example module...")

        scanner = RepositoryScanner(tmp_path)
        scanner.repo_modules = {"src.example"}
        scanner.documented_modules = {"example"}
        scanner.test_files = [tmp_path / "tests" / "test_example.py"]
        scanner._check_completeness()

        assert scanner.results.completeness_gaps == []

    def test_check_completeness_undocumented(self, tmp_path):
        """Test completeness with undocumented modules."""
        scanner = RepositoryScanner(tmp_path)
        scanner.repo_modules = {"src.module_a", "src.module_b"}
        scanner.documented_modules = {"module_a"}
        tests = tmp_path / "tests"
        tests.mkdir()
        test_module_a = tests / "test_module_a.py"
        test_module_b = tests / "test_module_b.py"
        test_module_a.write_text("def test_module_a(): pass")
        test_module_b.write_text("def test_module_b(): pass")
        scanner.test_files = [test_module_a, test_module_b]
        scanner._check_completeness()

        module_b_gaps = [g for g in scanner.results.completeness_gaps if g.item.endswith(".module_b")]
        assert len(module_b_gaps) == 1
        assert module_b_gaps[0].category == "documentation"


class TestRepositoryScannerTestCoverage:
    """Test test coverage checking."""

    def test_check_test_coverage_full(self, tmp_path):
        """Test coverage checking with full coverage."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "example.py").write_text("# Example")

        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "test_example.py").write_text("def test_example(): pass")

        scanner = RepositoryScanner(tmp_path)
        scanner.src_modules = {"example"}
        scanner.test_files = [tests / "test_example.py"]
        scanner._check_test_coverage()

        assert scanner.results.accuracy_issues == []

    def test_check_completeness_missing_test(self, tmp_path):
        """Missing dedicated tests are reported as a testing gap."""
        scanner = RepositoryScanner(tmp_path)
        scanner.repo_modules = {"src.module_without_test"}
        scanner.test_files = []
        scanner._check_completeness()

        testing_gaps = [g for g in scanner.results.completeness_gaps if g.category == "testing"]
        assert len(testing_gaps) == 1
        assert testing_gaps[0].item.endswith("module_without_test")


class TestRepositoryScannerConfiguration:
    """Test configuration checking."""

    def test_check_configuration_valid(self, tmp_path):
        """Test valid configuration."""
        (tmp_path / "pyproject.toml").write_text(
            """
[project]
name = "test"
dependencies = ["pytest"]
"""
        )

        scanner = RepositoryScanner(tmp_path)
        scanner._check_configuration()

        assert scanner.results.accuracy_issues == []

    def test_check_configuration_missing(self, tmp_path):
        """Test missing configuration files."""
        scanner = RepositoryScanner(tmp_path)
        scanner._check_configuration()

        assert scanner.results.accuracy_issues == []


class TestRepositoryScannerThinOrchestrator:
    """Test thin orchestrator pattern checking."""

    def test_check_thin_orchestrator_compliant(self, tmp_path):
        """Test checking compliant script."""
        scripts = tmp_path / "scripts"
        scripts.mkdir()

        (scripts / "good.py").write_text(
            """
from src.module import func
result = func()
print(result)
"""
        )

        scanner = RepositoryScanner(tmp_path)
        scanner.script_files = [scripts / "good.py"]
        scanner._check_thin_orchestrator_pattern()

        assert scanner.results.accuracy_issues == []

    def test_check_thin_orchestrator_non_compliant(self, tmp_path):
        """Test checking non-compliant script."""
        scripts = tmp_path / "scripts"
        scripts.mkdir()

        # Script with business logic
        (scripts / "bad.py").write_text(
            """
def complex_calculation(x, y, z):
    result = 0
    for i in range(100):
        result += x * y - z / (i + 1)
    return result

data = complex_calculation(1, 2, 3)
"""
        )

        scanner = RepositoryScanner(tmp_path)
        scanner.script_files = [scripts / "bad.py"]
        scanner._check_thin_orchestrator_pattern()

        architecture_issues = [issue for issue in scanner.results.accuracy_issues if issue.category == "architecture"]
        assert len(architecture_issues) == 1
        assert "thin orchestrator" in architecture_issues[0].message


class TestRepositoryScannerFullScan:
    """Test full scan functionality."""

    def test_scan_all_complete(self, tmp_path):
        """Test complete scan with full repo structure."""
        # Create full repo structure
        src = tmp_path / "src"
        src.mkdir()
        (src / "__init__.py").write_text("")
        (src / "example.py").write_text("def func(): return 42")

        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "run.py").write_text("from src.example import func\nprint(func())")

        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "test_example.py").write_text("def test_example(): assert True")

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "guide.md").write_text("# Guide\n\nUsing example module...")

        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'")
        (tmp_path / "README.md").write_text("# Project")

        scanner = RepositoryScanner(tmp_path)
        results = scanner.scan_all()

        assert isinstance(results, ScanResults)
        assert results.statistics["repo_modules"] == 1
        assert results.statistics["script_files"] == 1
        assert results.statistics["test_files"] == 1


class TestRepositoryScannerEdgeCases:
    """Test edge cases."""

    def test_empty_repository(self, tmp_path):
        """Test scanning empty repository."""
        scanner = RepositoryScanner(tmp_path)
        scanner._discover_structure()

        assert len(scanner.src_modules) == 0
        assert len(scanner.script_files) == 0

    def test_non_python_files(self, tmp_path):
        """Test handling non-Python files."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "data.json").write_text('{"key": "value"}')
        (src / "config.yaml").write_text("key: value")

        scanner = RepositoryScanner(tmp_path)
        scanner._discover_structure()

        # Should not include non-Python files
        assert "data" not in scanner.src_modules


class TestRepoScannerCore:
    """Test core repo scanner functionality."""

    def test_module_imports(self):
        """Test that module imports correctly."""
        assert repo_scanner.__name__ == "infrastructure.validation.repo.scanner"
        assert callable(repo_scanner.main)

    def test_has_scanner_functionality(self):
        """Test that module has scanning functionality."""
        assert callable(repo_scanner.RepositoryScanner)
        assert callable(repo_scanner.main)


class TestRepoScannerIntegration:
    """Integration tests for repo scanner."""

    def test_full_scan_workflow(self, tmp_path):
        """Test complete repository scan workflow."""
        # Create complete repo structure
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()
        (tmp_path / "docs").mkdir()
        (tmp_path / "src" / "__init__.py").write_text("")
        (tmp_path / "src" / "example.py").write_text("def example(): return 1")
        (tmp_path / "tests" / "test_example.py").write_text("def test_example(): assert True")
        (tmp_path / "README.md").write_text("# Project")

        results = RepositoryScanner(tmp_path).scan_all()

        assert results.statistics["repo_modules"] == 1
        assert results.statistics["test_files"] == 1


if __name__ == "__main__":
    pytest.main([__file__])
