#!/usr/bin/env python3
"""Comprehensive tests for infrastructure/exceptions.py.

Tests the custom exception hierarchy with real usage patterns.
No mocks - tests actual exception behavior and context.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add infrastructure to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infrastructure.core.exceptions import (
    TemplateError,
    ConfigurationError,
    MissingConfigurationError,
    InvalidConfigurationError,
    ValidationError,
    MarkdownValidationError,
    PDFValidationError,
    DataValidationError,
    BuildError,
    CompilationError,
    ScriptExecutionError,
    PipelineError,
    FileOperationError,
    FileNotFoundError,
    InvalidFileFormatError,
    DependencyError,
    MissingDependencyError,
    VersionMismatchError,
    TestError as TemplateTestError,  # Renamed to avoid pytest collection conflict
    InsufficientCoverageError,
    IntegrationError,
    raise_with_context,
    format_file_context,
    chain_exceptions,
)


class TestBaseTemplateError:
    """Test base TemplateError class."""
    
    def test_basic_error(self):
        """Test basic error creation."""
        error = TemplateError("Something went wrong")
        assert error.message == "Something went wrong"
        assert error.context == {}
        assert str(error) == "Something went wrong"
    
    def test_error_with_context(self):
        """Test error with context."""
        context = {"file": "data.csv", "line": 10}
        error = TemplateError("Parse error", context=context)
        assert error.message == "Parse error"
        assert error.context == context
        assert "file=data.csv" in str(error)
        assert "line=10" in str(error)
    
    def test_error_inheritance(self):
        """Test all exceptions inherit from TemplateError."""
        exceptions = [
            ConfigurationError,
            ValidationError,
            BuildError,
            FileOperationError,
            DependencyError,
            TemplateTestError,
            IntegrationError,
        ]
        
        for exc_class in exceptions:
            error = exc_class("Test error")
            assert isinstance(error, TemplateError)
            assert isinstance(error, Exception)


class TestConfigurationErrors:
    """Test configuration-related exceptions."""
    
    def test_configuration_error(self):
        """Test ConfigurationError."""
        error = ConfigurationError("Invalid config")
        assert isinstance(error, TemplateError)
        assert error.message == "Invalid config"
    
    def test_missing_configuration_error(self):
        """Test MissingConfigurationError."""
        error = MissingConfigurationError(
            "Required key missing",
            context={"key": "author", "file": "config.yaml"}
        )
        assert isinstance(error, ConfigurationError)
        assert error.context["key"] == "author"
    
    def test_invalid_configuration_error(self):
        """Test InvalidConfigurationError."""
        error = InvalidConfigurationError(
            "Invalid email format",
            context={"field": "email", "value": "invalid"}
        )
        assert isinstance(error, ConfigurationError)
        assert "email" in str(error)


class TestValidationErrors:
    """Test validation-related exceptions."""
    
    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError("Validation failed")
        assert isinstance(error, TemplateError)
    
    def test_markdown_validation_error(self):
        """Test MarkdownValidationError."""
        error = MarkdownValidationError(
            "Image not found",
            context={"image": "figure.png", "file": "intro.md", "line": 42}
        )
        assert isinstance(error, ValidationError)
        assert error.context["image"] == "figure.png"
        assert error.context["line"] == 42
    
    def test_pdf_validation_error(self):
        """Test PDFValidationError."""
        error = PDFValidationError(
            "Unresolved references",
            context={"pdf": "manuscript.pdf", "count": 3}
        )
        assert isinstance(error, ValidationError)
        assert "manuscript.pdf" in str(error)
    
    def test_data_validation_error(self):
        """Test DataValidationError."""
        error = DataValidationError(
            "NaN values found",
            context={"column": "temperature", "count": 5}
        )
        assert isinstance(error, ValidationError)
        assert error.context["column"] == "temperature"


class TestBuildErrors:
    """Test build-related exceptions."""
    
    def test_build_error(self):
        """Test BuildError."""
        error = BuildError("Build failed")
        assert isinstance(error, TemplateError)
    
    def test_compilation_error(self):
        """Test CompilationError."""
        error = CompilationError(
            "LaTeX compilation failed",
            context={"file": "manuscript.tex", "exit_code": 1}
        )
        assert isinstance(error, BuildError)
        assert error.context["exit_code"] == 1
    
    def test_script_execution_error(self):
        """Test ScriptExecutionError."""
        error = ScriptExecutionError(
            "Script failed",
            context={"script": "analysis.py", "exit_code": 1}
        )
        assert isinstance(error, BuildError)
        assert "analysis.py" in str(error)
    
    def test_pipeline_error(self):
        """Test PipelineError."""
        error = PipelineError(
            "Stage failed",
            context={"stage": "02_run_analysis", "failed_scripts": ["script1.py"]}
        )
        assert isinstance(error, BuildError)
        assert error.context["stage"] == "02_run_analysis"


class TestFileOperationErrors:
    """Test file operation exceptions."""
    
    def test_file_operation_error(self):
        """Test FileOperationError."""
        error = FileOperationError("Operation failed")
        assert isinstance(error, TemplateError)
    
    def test_file_not_found_error(self):
        """Test FileNotFoundError."""
        error = FileNotFoundError(
            "File not found",
            context={"file": "data.csv", "searched_in": "/path/to/project"}
        )
        assert isinstance(error, FileOperationError)
        assert "data.csv" in str(error)
    
    def test_invalid_file_format_error(self):
        """Test InvalidFileFormatError."""
        error = InvalidFileFormatError(
            "Invalid format",
            context={"file": "output.pdf", "detected_type": "text/plain"}
        )
        assert isinstance(error, FileOperationError)
        assert error.context["detected_type"] == "text/plain"


class TestDependencyErrors:
    """Test dependency-related exceptions."""
    
    def test_dependency_error(self):
        """Test DependencyError."""
        error = DependencyError("Dependency missing")
        assert isinstance(error, TemplateError)
    
    def test_missing_dependency_error(self):
        """Test MissingDependencyError."""
        error = MissingDependencyError(
            "Tool not found",
            context={"tool": "pandoc", "install_cmd": "apt-get install pandoc"}
        )
        assert isinstance(error, DependencyError)
        assert "pandoc" in str(error)
    
    def test_version_mismatch_error(self):
        """Test VersionMismatchError."""
        error = VersionMismatchError(
            "Version too old",
            context={"tool": "pandoc", "found": "2.5", "required": ">=3.1.9"}
        )
        assert isinstance(error, DependencyError)
        assert error.context["found"] == "2.5"
        assert error.context["required"] == ">=3.1.9"


class TestTestErrors:
    """Test test-related exceptions."""
    
    def test_test_error(self):
        """Test TestError."""
        error = TemplateTestError("Test failed")
        assert isinstance(error, TemplateError)
    
    def test_insufficient_coverage_error(self):
        """Test InsufficientCoverageError."""
        error = InsufficientCoverageError(
            "Coverage below threshold",
            context={"actual": 85.5, "required": 100.0, "missing_lines": [10, 15, 20]}
        )
        assert isinstance(error, TemplateTestError)
        assert error.context["actual"] == 85.5
        assert error.context["required"] == 100.0
        assert len(error.context["missing_lines"]) == 3


class TestIntegrationError:
    """Test integration-related exceptions."""
    
    def test_integration_error(self):
        """Test IntegrationError."""
        error = IntegrationError(
            "Integration failed",
            context={"module1": "data_generator", "module2": "analysis"}
        )
        assert isinstance(error, TemplateError)
        assert "data_generator" in str(error)


class TestUtilityFunctions:
    """Test exception utility functions."""
    
    def test_raise_with_context(self):
        """Test raise_with_context utility."""
        with pytest.raises(ValidationError) as exc_info:
            raise_with_context(
                ValidationError,
                "Validation failed",
                file="data.csv",
                line=10,
                column="temperature"
            )
        
        error = exc_info.value
        assert error.message == "Validation failed"
        assert error.context["file"] == "data.csv"
        assert error.context["line"] == 10
        assert error.context["column"] == "temperature"
    
    def test_format_file_context(self):
        """Test format_file_context utility."""
        context = format_file_context("data.csv", line=10)
        assert context["file"] == "data.csv"
        assert context["line"] == 10
    
    def test_format_file_context_no_line(self):
        """Test format_file_context without line number."""
        context = format_file_context("data.csv")
        assert context["file"] == "data.csv"
        assert "line" not in context
    
    def test_format_file_context_with_path(self):
        """Test format_file_context with Path object."""
        path = Path("project/data.csv")
        context = format_file_context(path, line=42)
        assert "data.csv" in context["file"]
        assert context["line"] == 42
    
    def test_chain_exceptions(self):
        """Test chain_exceptions utility."""
        original = ValueError("Original error")
        
        try:
            raise original
        except ValueError as e:
            new_error = ValidationError("Wrapped error")
            chained = chain_exceptions(new_error, e)
        
        assert chained.context["original_error"] == "Original error"
        assert chained.context["original_type"] == "ValueError"
        assert chained.__cause__ is original


class TestExceptionCatching:
    """Test exception catching patterns."""
    
    def test_catch_all_template_errors(self):
        """Test catching all template errors with base class."""
        exceptions_to_test = [
            ConfigurationError("Config error"),
            ValidationError("Validation error"),
            BuildError("Build error"),
            FileOperationError("File error"),
            DependencyError("Dependency error"),
            TemplateTestError("Test error"),
            IntegrationError("Integration error"),
        ]
        
        for exc in exceptions_to_test:
            try:
                raise exc
            except TemplateError as e:
                assert isinstance(e, TemplateError)
                assert e.message in str(e)
    
    def test_catch_specific_exception_type(self):
        """Test catching specific exception types."""
        try:
            raise PDFValidationError("PDF error", context={"pdf": "test.pdf"})
        except PDFValidationError as e:
            assert isinstance(e, PDFValidationError)
            assert isinstance(e, ValidationError)
            assert isinstance(e, TemplateError)
            assert e.context["pdf"] == "test.pdf"
    
    def test_catch_hierarchy(self):
        """Test exception hierarchy catching."""
        # Catch more specific first
        try:
            raise MissingConfigurationError("Key missing")
        except MissingConfigurationError as e:
            assert isinstance(e, ConfigurationError)
            assert isinstance(e, TemplateError)
        
        # Catch less specific
        try:
            raise MissingConfigurationError("Key missing")
        except ConfigurationError as e:
            assert isinstance(e, TemplateError)
        
        # Catch base class
        try:
            raise MissingConfigurationError("Key missing")
        except TemplateError as e:
            assert isinstance(e, Exception)


class TestContextPreservation:
    """Test context preservation across exception chain."""
    
    def test_context_preserved_in_str(self):
        """Test context is preserved in string representation."""
        error = ValidationError(
            "Validation failed",
            context={
                "file": "data.csv",
                "line": 42,
                "column": "temperature",
                "value": "invalid"
            }
        )
        
        error_str = str(error)
        assert "file=data.csv" in error_str
        assert "line=42" in error_str
        assert "column=temperature" in error_str
        assert "value=invalid" in error_str
    
    def test_chained_context_accessible(self):
        """Test chained exception context is accessible."""
        try:
            try:
                raise ValueError("Original problem")
            except ValueError as e:
                new_error = BuildError("Build failed")
                raise chain_exceptions(new_error, e)
        except BuildError as e:
            assert "Original problem" in e.context["original_error"]
            assert e.context["original_type"] == "ValueError"
            assert isinstance(e.__cause__, ValueError)


class TestRealWorldUsagePatterns:
    """Test real-world usage patterns."""
    
    def test_config_loading_error_pattern(self):
        """Test typical config loading error pattern."""
        def load_config(path: str):
            if not Path(path).exists():
                raise_with_context(
                    FileNotFoundError,
                    "Config file not found",
                    file=path,
                    searched_in=str(Path.cwd())
                )
        
        with pytest.raises(FileNotFoundError) as exc_info:
            load_config("nonexistent.yaml")
        
        error = exc_info.value
        assert "nonexistent.yaml" in str(error)
        assert "searched_in" in error.context
    
    def test_validation_error_pattern(self):
        """Test typical validation error pattern."""
        def validate_data(data: dict):
            if "required_field" not in data:
                raise_with_context(
                    DataValidationError,
                    "Required field missing",
                    field="required_field",
                    available_fields=list(data.keys())
                )
        
        with pytest.raises(DataValidationError) as exc_info:
            validate_data({"other_field": "value"})
        
        error = exc_info.value
        assert error.context["field"] == "required_field"
        assert "other_field" in error.context["available_fields"]
    
    def test_build_error_pattern(self):
        """Test typical build error pattern."""
        def run_build(cmd: list[str]):
            import subprocess
            result = subprocess.run(cmd, capture_output=True)
            if result.returncode != 0:
                raise_with_context(
                    CompilationError,
                    "Compilation failed",
                    command=" ".join(cmd),
                    exit_code=result.returncode,
                    stderr=result.stderr.decode()
                )
        
        with pytest.raises(CompilationError) as exc_info:
            run_build(["false"])  # Command that always fails
        
        error = exc_info.value
        assert error.context["exit_code"] != 0
        assert "command" in error.context



