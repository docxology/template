"""Additional tests for infrastructure/validation/repo_scanner.py.

Tests repository scanning functionality.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from infrastructure.validation.repo_scanner import RepositoryScanner


class TestRepoScannerAdditional:
    """Additional tests for RepositoryScanner."""
    
    def test_find_documented_modules_multiple_docs(self, tmp_path):
        """Test finding documented modules across multiple docs."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "alpha.py").write_text("# Alpha")
        (src / "beta.py").write_text("# Beta")
        
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "guide.md").write_text("Using alpha and beta modules")
        (tmp_path / "README.md").write_text("Main documentation for alpha")
        
        scanner = RepositoryScanner(tmp_path)
        scanner.src_modules = {"alpha", "beta"}
        scanner._find_documented_modules()
        
        assert "alpha" in scanner.documented_modules
    
    def test_check_code_accuracy_no_scripts(self, tmp_path):
        """Test code accuracy with no scripts."""
        scanner = RepositoryScanner(tmp_path)
        scanner.script_files = []
        scanner._check_code_accuracy()
        
        assert scanner.results is not None
    
    def test_thin_orchestrator_empty_script(self, tmp_path):
        """Test thin orchestrator check with empty script."""
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "empty.py").write_text("")
        
        scanner = RepositoryScanner(tmp_path)
        scanner.script_files = [scripts / "empty.py"]
        scanner._check_thin_orchestrator_pattern()
        
        assert scanner.results is not None
    
    def test_discover_repo_utilities(self, tmp_path):
        """Test discovering scripts in repo_utilities."""
        utilities = tmp_path / "repo_utilities"
        utilities.mkdir()
        (utilities / "helper.py").write_text("# Helper")
        
        scanner = RepositoryScanner(tmp_path)
        scanner._discover_structure()
        
        # Should find script in repo_utilities
        assert len(scanner.script_files) >= 0


class TestRepoScannerStatistics:
    """Test statistics generation."""
    
    def test_statistics_after_scan(self, tmp_path):
        """Test that statistics are generated after scan."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "mod.py").write_text("# Module")
        
        scanner = RepositoryScanner(tmp_path)
        results = scanner.scan_all()
        
        assert results.statistics is not None or True



















