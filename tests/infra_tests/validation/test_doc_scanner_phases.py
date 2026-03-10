"""Phase tests for infrastructure/validation/doc_scanner.py.

Tests documentation scanner phase functionality using real implementations.
Follows No Mocks Policy - all tests use real data and real execution.
"""

from infrastructure.validation.doc_scanner import DocumentationScanner


class TestDocScannerPhase5:
    """Test phase 5 improvements."""

    def test_phase5_improvements(self, tmp_path):
        """Test phase 5 improvements returns a dict with expected keys."""
        (tmp_path / "README.md").write_text("# README\n\nContent")

        scanner = DocumentationScanner(tmp_path)
        scanner.phase1_discovery()

        result = scanner.phase5_improvements()
        assert isinstance(result, dict)
        assert "total_improvements" in result


class TestDocScannerStatistics:
    """Test statistics generation."""

    def test_statistics_populated(self, tmp_path):
        """Test that statistics are populated after scans."""
        (tmp_path / "README.md").write_text("# README")

        scanner = DocumentationScanner(tmp_path)
        scanner.phase1_discovery()
        scanner.phase2_accuracy()
        scanner.phase3_completeness()
        scanner.phase4_quality()

        assert "phase1" in scanner.results.statistics
        assert "phase2" in scanner.results.statistics
        assert "phase3" in scanner.results.statistics
        assert "phase4" in scanner.results.statistics
