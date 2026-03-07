"""Coverage tests for infrastructure/validation/doc_scanner.py.

Tests documentation scanning functionality using real implementations.
Follows No Mocks Policy - all tests use real data and real execution.
"""

from infrastructure.validation import doc_scanner
from infrastructure.validation.doc_scanner import DocumentationScanner


class TestDocScannerCore:
    """Test core doc scanner module."""

    def test_module_imports(self):
        """Test that module imports correctly."""
        assert doc_scanner is not None

    def test_scanner_class_exists(self):
        """Test that DocumentationScanner class is importable."""
        assert DocumentationScanner is not None

    def test_main_function_exists(self):
        """Test that main() entry point exists."""
        assert hasattr(doc_scanner, "main")
        assert callable(doc_scanner.main)


class TestDocScannerIntegration:
    """Integration tests for doc scanner."""

    def test_full_scan_workflow(self, tmp_path):
        """Test that run_full_scan returns results and a report string."""
        (tmp_path / "README.md").write_text("# README\n\nContent.")

        scanner = DocumentationScanner(tmp_path)
        results, report = scanner.run_full_scan()

        assert results is not None
        assert isinstance(report, str)
        assert len(report) > 0

    def test_phase6_verification_structure(self, tmp_path):
        """Test that phase6_verification returns expected keys."""
        scanner = DocumentationScanner(tmp_path)

        result = scanner.phase6_verification()

        assert "link_checker" in result
        assert "markdown_syntax" in result
        assert "commands_tested" in result
        assert "cross_references" in result
        assert "circular_references" in result
