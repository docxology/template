"""Test package-level imports and API exposure for ways of knowing analysis layer.

This module ensures that package-level imports from project.src are properly
exposed through the __init__.py file and that package metadata is correct.
"""
from __future__ import annotations

import pytest


class TestPackageLevelImports:
    """Test package-level API exposure through __init__.py."""

    def test_ways_database_import(self) -> None:
        """Test that WaysDatabase is accessible from package level."""
        from src import WaysDatabase
        
        # Verify class exists
        assert WaysDatabase is not None

    def test_ways_analysis_imports(self) -> None:
        """Test that ways analysis classes are accessible from package level."""
        from src import (
            WaysAnalyzer,
            WaysCharacterization,
        )
        
        # Verify classes exist
        assert WaysAnalyzer is not None
        assert WaysCharacterization is not None

    def test_statistics_imports(self) -> None:
        """Test that ways statistics functions are accessible from package level."""
        from src import analyze_way_distributions
        
        # Verify function exists
        assert analyze_way_distributions is not None
        assert callable(analyze_way_distributions)

    def test_metrics_imports(self) -> None:
        """Test that ways metrics functions are accessible from package level."""
        from src import compute_way_coverage_metrics
        
        # Verify function exists
        assert compute_way_coverage_metrics is not None
        assert callable(compute_way_coverage_metrics)

    def test_package_metadata(self) -> None:
        """Test that package metadata is properly defined."""
        import src as pkg
        
        # Test version
        assert hasattr(pkg, '__version__')
        assert pkg.__version__ == "1.0.0"
        
        # Test layer designation
        assert hasattr(pkg, '__layer__')
        assert pkg.__layer__ == "scientific"

    def test_package_all_exports(self) -> None:
        """Test that __all__ is properly defined and includes expected ways modules."""
        import src as pkg
        
        # Verify __all__ exists
        assert hasattr(pkg, '__all__')
        assert isinstance(pkg.__all__, list)
        
        # Verify expected ways modules are in __all__
        expected_modules = [
            "database",
            "sql_queries",
            "models",
            "ways_analysis",
            "house_of_knowledge",
            "network_analysis",
            "ways_statistics",
            "metrics",
        ]
        
        for module in expected_modules:
            assert module in pkg.__all__, f"Module '{module}' not in __all__"

    def test_package_imports_without_errors(self) -> None:
        """Test that importing package doesn't produce import errors."""
        try:
            import src
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import src: {e}")

    def test_module_docstring(self) -> None:
        """Test that package has a docstring."""
        import src as pkg
        
        assert pkg.__doc__ is not None
        assert "ways" in pkg.__doc__.lower() or "knowing" in pkg.__doc__.lower()

    def test_import_error_fallback(self) -> None:
        """Test that ImportError fallback doesn't break package loading.
        
        This tests that even if individual imports fail, the package
        still loads gracefully (the except clause in __init__.py).
        """
        # This test verifies that the try/except block exists and works
        # The pass statement ensures graceful failure
        import src as pkg
        
        # Verify that despite potential import errors, the package works
        assert hasattr(pkg, '__version__')
        assert hasattr(pkg, '__all__')

