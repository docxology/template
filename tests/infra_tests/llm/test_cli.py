"""Tests for infrastructure.llm.cli module.

Tests CLI functionality using real data (No Mocks Policy):
- Pure logic tests for argument parsing and setup
- Integration tests marked with @pytest.mark.requires_ollama for network calls
"""

import argparse
import logging
import sys

import pytest

from infrastructure.llm.cli.main import (
    CLIError,
    check_command,
    create_parser,
    main,
    models_command,
    query_command,
    template_command,
)


class TestCLIArgumentParsing:
    """Test CLI argument parsing (pure logic)."""

    def test_main_no_args_exits(self, capsys, monkeypatch):
        """Test main with no arguments prints help and exits."""
        monkeypatch.setattr(sys, "argv", ["cli"])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    def test_query_command_parsing(self, monkeypatch):
        """Test query command argument parsing using the real parser."""
        parser = create_parser()

        # Test basic query
        args = parser.parse_args(["query", "test prompt"])
        assert args.prompt == "test prompt"
        assert args.short is False
        assert args.long is False

        # Test short mode
        args = parser.parse_args(["query", "--short", "test"])
        assert args.short is True

        # Test long mode
        args = parser.parse_args(["query", "--long", "test"])
        assert args.long is True

        # Test stream mode
        args = parser.parse_args(["query", "--stream", "test"])
        assert args.stream is True

        # Test with options
        args = parser.parse_args(["query", "--temperature", "0.5", "--seed", "42", "test"])
        assert args.temperature == 0.5
        assert args.seed == 42

    def test_check_command_parsing(self):
        """Test check command exists in the real parser."""
        parser = create_parser()
        args = parser.parse_args(["check"])
        assert args.command == "check"

    def test_models_command_parsing(self):
        """Test models command exists in the real parser."""
        parser = create_parser()
        args = parser.parse_args(["models"])
        assert args.command == "models"

    def test_template_command_parsing(self):
        """Test template command parsing using the real parser."""
        parser = create_parser()

        # List templates
        args = parser.parse_args(["template", "--list"])
        assert args.list is True

        # Apply template
        args = parser.parse_args(["template", "summarize_abstract", "--input", "text"])
        assert args.name == "summarize_abstract"
        assert args.input == "text"


class TestCLICheckCommand:
    """Test check command functionality."""

    def test_check_command_no_connection(self, caplog):
        """Test check command when Ollama not available."""
        # Create args namespace
        args = argparse.Namespace()

        # Override config to use unavailable port
        import os

        old_host = os.environ.get("OLLAMA_HOST")
        os.environ["OLLAMA_HOST"] = "http://localhost:99999"

        try:
            with caplog.at_level(logging.ERROR):
                with pytest.raises((CLIError, SystemExit)):
                    check_command(args)
        finally:
            if old_host:
                os.environ["OLLAMA_HOST"] = old_host
            else:
                os.environ.pop("OLLAMA_HOST", None)


class TestCLITemplateCommand:
    """Test template command functionality."""

    def test_template_list(self, capsys):
        """Test template --list command."""
        args = argparse.Namespace(list=True, name=None, input=None)

        template_command(args)

        captured = capsys.readouterr()
        assert "Available templates" in captured.out
        assert "summarize_abstract" in captured.out

    def test_template_no_name_no_list(self, caplog):
        """Test template command without name or list."""
        args = argparse.Namespace(list=False, name=None, input=None)

        with pytest.raises((CLIError, SystemExit)):
            template_command(args)


class TestCLIModelsCommand:
    """Test models command functionality."""

    def test_models_command_no_connection(self, capsys):
        """Test models command when Ollama not available."""
        args = argparse.Namespace()

        import os

        old_host = os.environ.get("OLLAMA_HOST")
        os.environ["OLLAMA_HOST"] = "http://localhost:99999"

        try:
            with pytest.raises((CLIError, SystemExit)):
                models_command(args)
        finally:
            if old_host:
                os.environ["OLLAMA_HOST"] = old_host
            else:
                os.environ.pop("OLLAMA_HOST", None)


class TestCLIQueryCommand:
    """Test query command functionality."""

    def test_query_command_no_connection(self, caplog):
        """Test query command when Ollama not available."""
        args = argparse.Namespace(
            prompt="test",
            short=False,
            long=False,
            stream=False,
            model=None,
            temperature=None,
            max_tokens=None,
            seed=None,
        )

        import os

        old_host = os.environ.get("OLLAMA_HOST")
        os.environ["OLLAMA_HOST"] = "http://localhost:99999"

        try:
            with pytest.raises((CLIError, SystemExit)):
                query_command(args)
        finally:
            if old_host:
                os.environ["OLLAMA_HOST"] = old_host
            else:
                os.environ.pop("OLLAMA_HOST", None)


# =============================================================================
# INTEGRATION TESTS (Require Ollama)
# =============================================================================


@pytest.mark.requires_ollama
@pytest.mark.timeout(120)  # LLM queries may take longer than default 10s timeout
class TestCLIWithOllama:
    """Integration tests requiring running Ollama server.

    Run with: pytest -m requires_ollama
    Skip with: pytest -m "not requires_ollama"
    """

    @pytest.fixture(autouse=True)
    def check_ollama(self, ensure_ollama_for_tests):
        """Ensure Ollama is running and functional for tests."""
        # Fixture dependency ensures Ollama is ready
        # If Ollama can't be started, ensure_ollama_for_tests will fail loudly
        pass

    def test_check_command_success(self, capsys):
        """Test check command with Ollama running."""
        args = argparse.Namespace()

        with pytest.raises(SystemExit) as exc_info:
            check_command(args)

        # Should exit 0 (success)
        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "running" in captured.out.lower()

    def test_models_command_success(self, capsys):
        """Test models command with Ollama running."""
        args = argparse.Namespace()

        models_command(args)

        captured = capsys.readouterr()
        # Should show available models or "No models found"
        assert "models" in captured.out.lower() or "model" in captured.out.lower()

    def test_query_command_basic(self, capsys):
        """Test basic query command."""
        args = argparse.Namespace(
            prompt="Say 'test' and nothing else",
            short=True,
            long=False,
            stream=False,
            model="smollm2:135m-instruct-q4_K_S",  # Use fast model for tests
            temperature=0.0,
            max_tokens=50,
            seed=42,
        )

        query_command(args)

        captured = capsys.readouterr()
        assert len(captured.out) > 0
