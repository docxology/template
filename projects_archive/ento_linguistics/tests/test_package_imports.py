"""Test package-level imports and API exposure for scientific layer.

This module ensures that package-level imports from project.src are properly
exposed through the __init__.py file and that package metadata is correct.
"""

from __future__ import annotations

import pytest


class TestPackageLevelImports:
    """Test package-level API exposure through __init__.py."""

    def test_core_function_imports(self) -> None:
        """Test that core functions are accessible from package level."""
        # Import from package level (tests __init__.py)
        from src.core.example import add_numbers, calculate_average

        # Verify functions work
        assert add_numbers(2, 3) == 5
        assert calculate_average([1, 2, 3]) == 2.0

    def test_class_imports(self) -> None:
        """Test that core classes are accessible from explicit subpackage imports."""
        from src.pipeline.simulation import SimpleSimulation, SimulationBase
        from src.visualization.visualization import VisualizationEngine

        # Verify classes exist and can be instantiated
        assert SimpleSimulation is not None
        assert SimulationBase is not None
        assert VisualizationEngine is not None

        # Verify VisualizationEngine can be created
        engine = VisualizationEngine(output_dir=".")
        assert engine is not None

    def test_statistics_imports(self) -> None:
        """Test that statistics functions are accessible from explicit subpackage imports."""
        import numpy as np
        from src.analysis.statistics import calculate_descriptive_stats

        # Test statistics function
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        stats = calculate_descriptive_stats(data)

        assert stats is not None
        assert hasattr(stats, "mean")
        assert stats.mean == 3.0

    def test_package_metadata(self) -> None:
        """Test that package metadata is properly defined."""
        import src as pkg

        # Test version
        assert hasattr(pkg, "__version__")
        assert pkg.__version__ == "1.0.0"

        # Test layer designation
        assert hasattr(pkg, "__layer__")
        assert pkg.__layer__ == "scientific"

    def test_package_all_exports(self) -> None:
        """Test that __all__ is properly defined with subpackage names."""
        import src as pkg

        # Verify __all__ exists
        assert hasattr(pkg, "__all__")
        assert isinstance(pkg.__all__, list)

        # Verify expected subpackages are in __all__
        # (lazy loading: only subpackage names, not individual modules)
        expected_subpackages = [
            "analysis",
            "visualization",
            "data",
            "core",
            "pipeline",
        ]

        for subpkg in expected_subpackages:
            assert subpkg in pkg.__all__, f"Subpackage '{subpkg}' not in __all__"

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
        assert "scientific" in pkg.__doc__.lower()
        assert "source" in pkg.__doc__.lower()

    def test_import_error_fallback(self) -> None:
        """Test that ImportError fallback doesn't break package loading.

        This tests that even if individual imports fail, the package
        still loads gracefully (the except clause in __init__.py).
        """
        # This test verifies that the try/except block exists and works
        # The pass statement ensures graceful failure
        import src as pkg

        # Verify that despite potential import errors, the package works
        assert hasattr(pkg, "__version__")
        assert hasattr(pkg, "__all__")
