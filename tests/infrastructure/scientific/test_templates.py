"""Test suite for infrastructure.scientific.templates module.

Tests scientific code template generation including:
- Module templates with best practices
- Test suite templates
- Workflow templates for reproducible research

All tests verify template structure and content.
"""

import ast
import re

import pytest

from infrastructure.scientific.templates import (
    create_scientific_module_template,
    create_scientific_test_suite,
    create_scientific_workflow_template,
)


class TestCreateScientificModuleTemplate:
    """Test create_scientific_module_template function."""

    def test_template_includes_module_name(self):
        """Test template includes the module name."""
        template = create_scientific_module_template("optimization")

        assert "optimization" in template
        assert '"""Scientific module: optimization' in template

    def test_template_has_future_annotations(self):
        """Test template includes future annotations import."""
        template = create_scientific_module_template("test_module")

        assert "from __future__ import annotations" in template

    def test_template_has_numpy_import(self):
        """Test template includes numpy import."""
        template = create_scientific_module_template("test_module")

        assert "import numpy as np" in template

    def test_template_has_typing_imports(self):
        """Test template includes typing imports."""
        template = create_scientific_module_template("test_module")

        assert "from typing import" in template
        assert "List" in template
        assert "Tuple" in template
        assert "Optional" in template

    def test_template_has_function1(self):
        """Test template includes function1."""
        template = create_scientific_module_template("test_module")

        assert "def function1" in template
        assert "param1: float" in template
        assert "param2: int" in template

    def test_template_has_function2(self):
        """Test template includes function2."""
        template = create_scientific_module_template("test_module")

        assert "def function2" in template
        assert "data: List[float]" in template
        assert "threshold: float" in template

    def test_template_has_docstrings(self):
        """Test template includes docstrings for functions."""
        template = create_scientific_module_template("test_module")

        # Count docstring markers
        docstring_count = template.count('"""')
        assert docstring_count >= 6  # At least module + 2 functions

    def test_template_has_input_validation(self):
        """Test template includes input validation."""
        template = create_scientific_module_template("test_module")

        assert "Input validation" in template
        assert "isinstance" in template
        assert "TypeError" in template

    def test_template_has_error_handling(self):
        """Test template includes error handling."""
        template = create_scientific_module_template("test_module")

        assert "try:" in template
        assert "except" in template
        assert "raise ValueError" in template or "ValueError" in template

    def test_template_has_examples(self):
        """Test template includes usage examples in docstrings."""
        template = create_scientific_module_template("test_module")

        assert "Examples:" in template
        assert ">>>" in template

    def test_template_has_raises_documentation(self):
        """Test template includes Raises section in docstrings."""
        template = create_scientific_module_template("test_module")

        assert "Raises:" in template
        assert "ValueError" in template

    def test_template_is_valid_python(self):
        """Test template is syntactically valid Python."""
        template = create_scientific_module_template("valid_module")

        # Should not raise SyntaxError
        ast.parse(template)

    def test_template_different_module_names(self):
        """Test template works with different module names."""
        names = ["analysis", "statistics", "ml_model", "data_processor"]

        for name in names:
            template = create_scientific_module_template(name)
            assert name in template
            # Should still be valid Python
            ast.parse(template)

    def test_template_has_return_types(self):
        """Test template includes return type annotations."""
        template = create_scientific_module_template("test_module")

        assert "-> float" in template
        assert "-> Tuple[" in template


class TestCreateScientificTestSuite:
    """Test create_scientific_test_suite function."""

    def test_test_suite_includes_module_name(self):
        """Test test suite includes module name."""
        test_suite = create_scientific_test_suite("optimization")

        assert "optimization" in test_suite
        assert 'Test suite for optimization module' in test_suite

    def test_test_suite_has_pytest_import(self):
        """Test test suite imports pytest."""
        test_suite = create_scientific_test_suite("test_module")

        assert "import pytest" in test_suite

    def test_test_suite_has_numpy_import(self):
        """Test test suite imports numpy."""
        test_suite = create_scientific_test_suite("test_module")

        assert "import numpy as np" in test_suite

    def test_test_suite_has_stability_tests(self):
        """Test test suite includes stability test class."""
        test_suite = create_scientific_test_suite("test_module")

        assert "class TestNumericalStability" in test_suite
        assert "test_function_stability_across_range" in test_suite

    def test_test_suite_has_performance_tests(self):
        """Test test suite includes performance test class."""
        test_suite = create_scientific_test_suite("test_module")

        assert "class TestPerformance" in test_suite
        assert "test_function_performance" in test_suite

    def test_test_suite_has_correctness_tests(self):
        """Test test suite includes correctness test class."""
        test_suite = create_scientific_test_suite("test_module")

        assert "class TestCorrectness" in test_suite
        assert "test_basic_functionality" in test_suite

    def test_test_suite_has_edge_case_tests(self):
        """Test test suite includes edge case test class."""
        test_suite = create_scientific_test_suite("test_module")

        assert "class TestEdgeCases" in test_suite
        assert "test_zero_inputs" in test_suite
        assert "test_large_inputs" in test_suite

    def test_test_suite_has_main_block(self):
        """Test test suite includes main execution block."""
        test_suite = create_scientific_test_suite("test_module")

        assert 'if __name__ == "__main__"' in test_suite
        assert "pytest.main" in test_suite

    def test_test_suite_has_path_setup(self):
        """Test test suite includes path setup for imports."""
        test_suite = create_scientific_test_suite("test_module")

        assert "sys.path" in test_suite
        assert "Path(__file__)" in test_suite

    def test_test_suite_has_assertions(self):
        """Test test suite includes assertions."""
        test_suite = create_scientific_test_suite("test_module")

        assert "assert" in test_suite

    def test_test_suite_different_module_names(self):
        """Test test suite works with different module names."""
        names = ["analysis", "statistics", "ml_model"]

        for name in names:
            test_suite = create_scientific_test_suite(name)
            assert name in test_suite
            assert f"import {name}" in test_suite


class TestCreateScientificWorkflowTemplate:
    """Test create_scientific_workflow_template function."""

    def test_workflow_includes_name(self):
        """Test workflow template includes workflow name."""
        template = create_scientific_workflow_template("ml_training")

        assert "ml_training" in template
        assert "Scientific research workflow: ml_training" in template

    def test_workflow_has_shebang(self):
        """Test workflow template includes shebang line."""
        template = create_scientific_workflow_template("workflow")

        assert "#!/usr/bin/env python3" in template

    def test_workflow_has_future_annotations(self):
        """Test workflow has future annotations import."""
        template = create_scientific_workflow_template("workflow")

        assert "from __future__ import annotations" in template

    def test_workflow_has_standard_imports(self):
        """Test workflow has standard library imports."""
        template = create_scientific_workflow_template("workflow")

        assert "import os" in template
        assert "import sys" in template
        assert "import json" in template
        assert "from pathlib import Path" in template
        assert "from datetime import datetime" in template

    def test_workflow_has_scientific_imports(self):
        """Test workflow has scientific computing imports."""
        template = create_scientific_workflow_template("workflow")

        assert "import numpy as np" in template
        assert "import matplotlib.pyplot as plt" in template

    def test_workflow_has_setup_function(self):
        """Test workflow has setup environment function."""
        template = create_scientific_workflow_template("workflow")

        assert "def setup_workflow_environment" in template
        assert "np.random.seed(42)" in template

    def test_workflow_has_data_processing_function(self):
        """Test workflow has data processing function."""
        template = create_scientific_workflow_template("workflow")

        assert "def run_data_processing" in template
        assert "Dict[str, Any]" in template

    def test_workflow_has_validation_function(self):
        """Test workflow has validation function."""
        template = create_scientific_workflow_template("workflow")

        assert "def validate_workflow_results" in template
        assert "-> bool" in template

    def test_workflow_has_report_generation(self):
        """Test workflow has report generation function."""
        template = create_scientific_workflow_template("workflow")

        assert "def generate_workflow_report" in template
        assert "# Scientific Workflow Report" in template

    def test_workflow_has_main_function(self):
        """Test workflow has main function."""
        template = create_scientific_workflow_template("workflow")

        assert "def main():" in template
        assert 'if __name__ == "__main__"' in template
        assert "main()" in template

    def test_workflow_has_logging(self):
        """Test workflow has logging setup."""
        template = create_scientific_workflow_template("workflow")

        assert "logger" in template
        assert "get_logger" in template
        assert "logger.info" in template

    def test_workflow_has_output_directories(self):
        """Test workflow creates output directories."""
        template = create_scientific_workflow_template("workflow")

        assert "output_dirs" in template
        assert "mkdir" in template

    def test_workflow_has_reproducibility(self):
        """Test workflow includes reproducibility features."""
        template = create_scientific_workflow_template("workflow")

        assert "reproducibility" in template
        assert "generate_reproducibility_report" in template
        assert "save_reproducibility_report" in template

    def test_workflow_has_error_handling(self):
        """Test workflow includes error handling."""
        template = create_scientific_workflow_template("workflow")

        assert "sys.exit(1)" in template
        assert "logger.error" in template

    def test_workflow_different_names(self):
        """Test workflow works with different names."""
        names = ["data_analysis", "model_training", "result_validation"]

        for name in names:
            template = create_scientific_workflow_template(name)
            assert name in template
            assert "def main():" in template


class TestTemplateIntegration:
    """Integration tests for template generation."""

    def test_module_and_test_suite_compatibility(self):
        """Test generated module and test suite are compatible."""
        module_name = "integration_test"

        module_template = create_scientific_module_template(module_name)
        test_template = create_scientific_test_suite(module_name)

        # Both should reference the same module name
        assert module_name in module_template
        assert f"import {module_name}" in test_template

    def test_all_templates_have_docstrings(self):
        """Test all template types have module docstrings."""
        module = create_scientific_module_template("test")
        tests = create_scientific_test_suite("test")
        workflow = create_scientific_workflow_template("test")

        for template in [module, tests, workflow]:
            # Should start with docstring (after shebang if present)
            lines = template.strip().split("\n")
            # Find first non-shebang, non-empty line
            for line in lines:
                if line.strip() and not line.startswith("#!"):
                    assert line.strip().startswith('"""'), f"Template should start with docstring, got: {line[:50]}"
                    break

    def test_templates_follow_pep8_style(self):
        """Test templates generally follow PEP 8 style."""
        template = create_scientific_module_template("style_test")

        # Check for common PEP 8 patterns
        assert "def function" in template  # Function definitions
        assert "    " in template  # 4-space indentation
        assert "# " in template  # Comment with space

    def test_templates_are_complete(self):
        """Test templates are complete and not truncated."""
        module = create_scientific_module_template("complete")
        tests = create_scientific_test_suite("complete")
        workflow = create_scientific_workflow_template("complete")

        # All should have proper ending
        for template in [module, tests, workflow]:
            stripped = template.rstrip()
            # Should not end abruptly
            assert len(stripped) > 100
            # Should have balanced quotes
            triple_quote_count = template.count('"""')
            assert triple_quote_count % 2 == 0


class TestTemplateEdgeCases:
    """Test edge cases in template generation."""

    def test_module_name_with_underscores(self):
        """Test module name with underscores."""
        template = create_scientific_module_template("my_scientific_module")

        assert "my_scientific_module" in template

    def test_module_name_single_character(self):
        """Test single character module name."""
        template = create_scientific_module_template("x")

        assert "Scientific module: x" in template

    def test_module_name_with_numbers(self):
        """Test module name with numbers."""
        template = create_scientific_module_template("module_v2")

        assert "module_v2" in template

    def test_workflow_name_long(self):
        """Test long workflow name."""
        long_name = "very_long_workflow_name_for_testing_purposes"
        template = create_scientific_workflow_template(long_name)

        assert long_name in template


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
