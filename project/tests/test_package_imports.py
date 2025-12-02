"""Test package-level imports and API exposure for Boundary Logic layer.

This module ensures that package-level imports from project.src are properly
exposed through the __init__.py file and that package metadata is correct.
"""
from __future__ import annotations

import pytest


class TestPackageLevelImports:
    """Test package-level API exposure through __init__.py."""

    def test_core_form_imports(self) -> None:
        """Test that core Form functions are accessible from package level."""
        # Import from package level (tests __init__.py)
        from src import (
            Form,
            make_void,
            make_mark,
            enclose,
            juxtapose,
        )
        
        # Verify basic form operations
        void = make_void()
        mark = make_mark()
        assert void.is_void()
        assert not mark.is_void()
        
        # Test form creation
        enclosed = enclose(mark)
        assert enclosed is not None

    def test_reduction_imports(self) -> None:
        """Test that reduction functions are accessible from package level."""
        from src import (
            reduce_form,
            forms_equivalent,
            canonical_form,
            make_mark,
            enclose,
        )
        
        # Verify reduction works
        form = enclose(enclose(make_mark()))  # ⟨⟨⟨ ⟩⟩⟩
        result = reduce_form(form)
        assert result is not None

    def test_algebra_imports(self) -> None:
        """Test that Boolean algebra functions are accessible from package level."""
        from src import (
            is_tautology,
            is_contradiction,
            is_satisfiable,
            make_mark,
            make_void,
        )
        
        # Verify algebra operations exist
        mark = make_mark()
        void = make_void()
        
        # Basic checks
        assert callable(is_tautology)
        assert callable(is_contradiction)
        assert callable(is_satisfiable)

    def test_visualization_imports(self) -> None:
        """Test that visualization classes are accessible from package level."""
        from src import (
            VisualizationEngine,
            create_multi_panel_figure,
            visualize_form,
        )
        
        # Verify classes and functions exist
        assert VisualizationEngine is not None
        assert callable(create_multi_panel_figure)
        assert callable(visualize_form)
        
        # Verify VisualizationEngine can be created
        engine = VisualizationEngine(output_dir=".")
        assert engine is not None

    def test_package_metadata(self) -> None:
        """Test that package metadata is properly defined."""
        import src as pkg
        
        # Test version
        assert hasattr(pkg, '__version__')
        assert pkg.__version__ == "1.0.0"
        
        # Test author
        assert hasattr(pkg, '__author__')
        assert pkg.__author__ == "Project Author"
        
        # Test description
        assert hasattr(pkg, '__description__')
        assert "Containment Theory" in pkg.__description__

    def test_package_all_exports(self) -> None:
        """Test that __all__ is properly defined and includes expected exports."""
        import src as pkg
        
        # Verify __all__ exists
        assert hasattr(pkg, '__all__')
        assert isinstance(pkg.__all__, list)
        
        # Verify expected core exports are in __all__
        expected_exports = [
            # Forms
            "Form",
            "make_void",
            "make_mark",
            "enclose",
            "juxtapose",
            # Reduction
            "reduce_form",
            "forms_equivalent",
            # Algebra
            "is_tautology",
            "is_contradiction",
            # Visualization
            "visualize_form",
            "VisualizationEngine",
            "create_multi_panel_figure",
        ]
        
        for export in expected_exports:
            assert export in pkg.__all__, f"Export '{export}' not in __all__"

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
        # The docstring describes Containment Theory/Boundary Logic
        assert "containment" in pkg.__doc__.lower() or "boundary" in pkg.__doc__.lower()
        assert "form" in pkg.__doc__.lower()

    def test_expression_parsing_imports(self) -> None:
        """Test that expression parsing is accessible."""
        from src import (
            parse,
            parse_expression,
            format_form,
        )
        
        assert callable(parse)
        assert callable(parse_expression)
        assert callable(format_form)

    def test_theorem_imports(self) -> None:
        """Test that theorem functions are accessible."""
        from src import (
            axiom_calling,
            axiom_crossing,
            get_all_theorems,
            verify_all_theorems,
        )
        
        # Test axiom functions return theorems
        j1 = axiom_calling()
        j2 = axiom_crossing()
        
        assert j1 is not None
        assert j2 is not None
        assert hasattr(j1, 'name')
        assert hasattr(j2, 'name')

    def test_verification_imports(self) -> None:
        """Test that verification functions are accessible."""
        from src import (
            verify_axioms,
            verify_consistency,
            verify_semantics,
            full_verification,
        )
        
        assert callable(verify_axioms)
        assert callable(verify_consistency)
        assert callable(verify_semantics)
        assert callable(full_verification)

