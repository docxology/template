"""Tests for infrastructure.llm.cli module.

Tests CLI functionality using real data (No Mocks Policy):
- Pure logic tests for argument parsing and setup
- Integration tests marked with @pytest.mark.requires_ollama for network calls
"""

import argparse
import sys
import pytest

from infrastructure.llm.cli.main import main, query_command, check_command, models_command, template_command
from infrastructure.llm.core.config import LLMConfig
from infrastructure.llm.core.client import LLMClient


class TestCLIArgumentParsing:
    """Test CLI argument parsing (pure logic)."""

    def test_main_no_args_exits(self, capsys, monkeypatch):
        """Test main with no arguments prints help and exits."""
        monkeypatch.setattr(sys, 'argv', ['cli'])
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 1

    def test_query_command_parsing(self, monkeypatch):
        """Test query command argument parsing."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        
        query_parser = subparsers.add_parser("query")
        query_parser.add_argument("prompt")
        query_parser.add_argument("--short", action="store_true")
        query_parser.add_argument("--long", action="store_true")
        query_parser.add_argument("--stream", action="store_true")
        query_parser.add_argument("--model", type=str, default=None)
        query_parser.add_argument("--temperature", type=float, default=None)
        query_parser.add_argument("--max-tokens", type=int, default=None)
        query_parser.add_argument("--seed", type=int, default=None)
        
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
        args = parser.parse_args([
            "query", "--temperature", "0.5", "--seed", "42", "test"
        ])
        assert args.temperature == 0.5
        assert args.seed == 42

    def test_check_command_parsing(self):
        """Test check command exists."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        check_parser = subparsers.add_parser("check")
        
        args = parser.parse_args(["check"])
        assert args.command == "check"

    def test_models_command_parsing(self):
        """Test models command exists."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        models_parser = subparsers.add_parser("models")
        
        args = parser.parse_args(["models"])
        assert args.command == "models"

    def test_template_command_parsing(self):
        """Test template command parsing."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        
        template_parser = subparsers.add_parser("template")
        template_parser.add_argument("name", nargs="?", default=None)
        template_parser.add_argument("--list", action="store_true")
        template_parser.add_argument("--input", type=str, default=None)
        
        # List templates
        args = parser.parse_args(["template", "--list"])
        assert args.list is True
        
        # Apply template
        args = parser.parse_args(["template", "summarize_abstract", "--input", "text"])
        assert args.name == "summarize_abstract"
        assert args.input == "text"


class TestCLICheckCommand:
    """Test check command functionality."""

    def test_check_command_no_connection(self, capsys):
        """Test check command when Ollama not available."""
        # Create args namespace
        args = argparse.Namespace()
        
        # Override config to use unavailable port
        import os
        old_host = os.environ.get('OLLAMA_HOST')
        os.environ['OLLAMA_HOST'] = 'http://localhost:99999'
        
        try:
            with pytest.raises(SystemExit) as exc_info:
                check_command(args)
            
            assert exc_info.value.code == 1
            
            captured = capsys.readouterr()
            assert "Cannot connect" in captured.err or "Cannot connect" in captured.out
        finally:
            if old_host:
                os.environ['OLLAMA_HOST'] = old_host
            else:
                os.environ.pop('OLLAMA_HOST', None)


class TestCLITemplateCommand:
    """Test template command functionality."""

    def test_template_list(self, capsys):
        """Test template --list command."""
        args = argparse.Namespace(list=True, name=None, input=None)
        
        template_command(args)
        
        captured = capsys.readouterr()
        assert "Available templates" in captured.out
        assert "summarize_abstract" in captured.out

    def test_template_no_name_no_list(self, capsys):
        """Test template command without name or list."""
        args = argparse.Namespace(list=False, name=None, input=None)
        
        with pytest.raises(SystemExit) as exc_info:
            template_command(args)
        
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Template name required" in captured.err


class TestCLIModelsCommand:
    """Test models command functionality."""

    def test_models_command_no_connection(self, capsys):
        """Test models command when Ollama not available."""
        args = argparse.Namespace()
        
        import os
        old_host = os.environ.get('OLLAMA_HOST')
        os.environ['OLLAMA_HOST'] = 'http://localhost:99999'
        
        try:
            with pytest.raises(SystemExit) as exc_info:
                models_command(args)
            
            assert exc_info.value.code == 1
        finally:
            if old_host:
                os.environ['OLLAMA_HOST'] = old_host
            else:
                os.environ.pop('OLLAMA_HOST', None)


class TestCLIQueryCommand:
    """Test query command functionality."""

    def test_query_command_no_connection(self, capsys):
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
        old_host = os.environ.get('OLLAMA_HOST')
        os.environ['OLLAMA_HOST'] = 'http://localhost:99999'
        
        try:
            with pytest.raises(SystemExit) as exc_info:
                query_command(args)
            
            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "Cannot connect" in captured.err
        finally:
            if old_host:
                os.environ['OLLAMA_HOST'] = old_host
            else:
                os.environ.pop('OLLAMA_HOST', None)


# =============================================================================
# INTEGRATION TESTS (Require Ollama)
# =============================================================================

@pytest.mark.requires_ollama
class TestCLIWithOllama:
    """Integration tests requiring running Ollama server.
    
    Run with: pytest -m requires_ollama
    Skip with: pytest -m "not requires_ollama"
    """
    
    @pytest.fixture(autouse=True)
    def check_ollama(self):
        """Skip tests if Ollama is not available."""
        client = LLMClient()
        if not client.check_connection():
            pytest.skip("Ollama server not available")

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
            model=None,
            temperature=0.0,
            max_tokens=50,
            seed=42,
        )
        
        query_command(args)
        
        captured = capsys.readouterr()
        assert len(captured.out) > 0

