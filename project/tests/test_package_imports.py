"""Test package-level imports and API exposure for tree grafting toolkit.

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
        from src import (
            check_cambium_alignment,
            calculate_graft_angle,
            estimate_callus_formation_time,
        )
        
        # Verify functions work
        is_compat, ratio = check_cambium_alignment(15.0, 15.0)
        assert is_compat is True
        assert ratio == pytest.approx(1.0)
        
        angle = calculate_graft_angle(15.0, 15.0, "whip")
        assert angle == 35.0

    def test_class_imports(self) -> None:
        """Test that core classes are accessible from package level."""
        from src import (
            CambiumIntegrationSimulation,
            GraftSimulationBase,
            GraftVisualizationEngine,
        )
        
        # Verify classes exist and can be instantiated
        assert CambiumIntegrationSimulation is not None
        assert GraftSimulationBase is not None
        assert GraftVisualizationEngine is not None
        
        # Verify GraftVisualizationEngine can be created
        engine = GraftVisualizationEngine(output_dir=".")
        assert engine is not None

    def test_statistics_imports(self) -> None:
        """Test that statistics functions are accessible from package level."""
        from src import calculate_graft_statistics
        
        import numpy as np
        
        # Test statistics function
        success = np.array([1, 1, 0, 1, 0])
        stats = calculate_graft_statistics(success)
        
        assert stats is not None
        assert "success" in stats
        assert stats["success"].success_rate == 0.6

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
        """Test that __all__ is properly defined and includes expected modules."""
        import src as pkg
        
        # Verify __all__ exists
        assert hasattr(pkg, '__all__')
        assert isinstance(pkg.__all__, list)
        
        # Verify expected modules are in __all__
        expected_modules = [
            "graft_basics",
            "biological_simulation",
            "graft_statistics",
            "graft_data_generator",
            "graft_data_processing",
            "graft_metrics",
            "graft_parameters",
            "graft_analysis",
            "graft_plots",
            "graft_reporting",
            "graft_validation",
            "graft_visualization",
            "compatibility_prediction",
            "species_database",
            "technique_library",
            "rootstock_analysis",
            "seasonal_planning",
            "economic_analysis",
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
        assert "grafting" in pkg.__doc__.lower() or "tree" in pkg.__doc__.lower()
