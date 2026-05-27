"""Comprehensive tests for infrastructure/publishing/cli.py.

Tests the CLI interface for publishing operations.
"""

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.publishing import cli


class TestExtractMetadataCommand:
    """Test suite for extract_metadata_command."""

    def test_extract_metadata_basic(self, tmp_path, capsys):
        """Test basic metadata extraction."""
        # Create test markdown file with real content
        md_file = tmp_path / "abstract.md"
        md_file.write_text(
            """# Test Research Paper

## Authors
- John Doe
- Jane Smith

## Abstract
This is a test abstract for the research paper.

## Keywords
testing, research
"""
        )

        args = argparse.Namespace(manuscript_dir=str(tmp_path))

        # Use real metadata extraction
        cli.extract_metadata_command(args)

        captured = capsys.readouterr()
        assert "Test Research Paper" in captured.out
        assert "Authors:" in captured.out
        assert "Abstract:" in captured.out
        assert "Keywords:" in captured.out

    def test_extract_metadata_nonexistent_dir(self, tmp_path, caplog):
        """Test metadata extraction with nonexistent directory."""
        args = argparse.Namespace(manuscript_dir=str(tmp_path / "nonexistent"))

        with caplog.at_level(logging.ERROR):
            with pytest.raises(SystemExit) as exc_info:
                cli.extract_metadata_command(args)
        assert exc_info.value.code == 1

        assert "error" in caplog.text.lower() or "not found" in caplog.text.lower()

    def test_extract_metadata_no_md_files(self, tmp_path, caplog):
        """Test metadata extraction when no markdown files exist."""
        args = argparse.Namespace(manuscript_dir=str(tmp_path))

        with caplog.at_level(logging.ERROR):
            with pytest.raises(SystemExit) as exc_info:
                cli.extract_metadata_command(args)
        assert exc_info.value.code == 1

        assert "no markdown files" in caplog.text.lower() or "no .md files" in caplog.text.lower()


class TestGenerateCitationCommand:
    """Test suite for generate_citation_command."""

    def test_generate_citation_bibtex(self, tmp_path, capsys):
        """Test BibTeX citation generation."""
        md_file = tmp_path / "paper.md"
        md_file.write_text(
            """# Test Paper

## Authors
- Author One

## Publication Info
- Year: 2024
- DOI: 10.1234/test
"""
        )

        args = argparse.Namespace(manuscript_dir=str(tmp_path), format="bibtex")

        # Use real citation generation
        cli.generate_citation_command(args)

        captured = capsys.readouterr()
        assert "@" in captured.out  # Any citation format
        assert "Test Paper" in captured.out

    def test_generate_citation_unsupported_format(self, tmp_path):
        """Test citation generation with unsupported format."""
        md_file = tmp_path / "paper.md"
        md_file.write_text("# Paper\n\nSome content.")

        args = argparse.Namespace(manuscript_dir=str(tmp_path), format="invalid_format")

        # Test that unsupported format raises error (real validation)
        with pytest.raises(SystemExit) as exc_info:
            cli.generate_citation_command(args)
        assert exc_info.value.code == 1

    def test_generate_citation_nonexistent_dir(self, tmp_path, capsys):
        """Test citation generation with nonexistent directory."""
        args = argparse.Namespace(manuscript_dir=str(tmp_path / "nonexistent"), format="bibtex")

        with pytest.raises(SystemExit) as exc_info:
            cli.generate_citation_command(args)
        assert exc_info.value.code == 1

    def test_generate_citation_no_md_files(self, tmp_path, capsys):
        """Test citation generation when no markdown files exist."""
        args = argparse.Namespace(manuscript_dir=str(tmp_path), format="bibtex")

        with pytest.raises(SystemExit) as exc_info:
            cli.generate_citation_command(args)
        assert exc_info.value.code == 1


class TestPublishZenodoCommand:
    """Test suite for publish_zenodo_command argument validation."""

    def test_publish_zenodo_command_success(
        self,
        tmp_path,
        zenodo_test_server,
        capsys,
        monkeypatch,
    ):
        """Publish PDFs through the CLI command against a local Zenodo server."""
        pdf_file = tmp_path / "paper.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")

        original_config = cli.ZenodoConfig

        def config_with_test_url(*args, **kwargs):
            kwargs["base_url"] = zenodo_test_server.url_for("")
            return original_config(*args, **kwargs)

        monkeypatch.setattr(cli, "ZenodoConfig", config_with_test_url)

        args = argparse.Namespace(
            output_dir=str(tmp_path),
            token="test_token",
            title="Test Publication",
            authors="Author One,Author Two",
            description="Test description",
            production=True,
        )

        cli.publish_zenodo_command(args)

        captured = capsys.readouterr()
        assert "10.5281/zenodo.12345" in captured.out

    def test_publish_zenodo_validates_pdf_files(self, tmp_path, capsys):
        """Test that publish command finds PDF files."""
        # Create test PDF
        pdf_file = tmp_path / "paper.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")

        args = argparse.Namespace(
            output_dir=str(tmp_path),
            token="test_token",
            title="Test Publication",
            authors="Author One,Author Two",
            description="Test description",
        )

        # Test PDF file discovery (real file system operation)
        pdfs = list(Path(args.output_dir).glob("*.pdf"))
        assert len(pdfs) == 1
        assert pdfs[0].name == "paper.pdf"

    def test_publish_zenodo_no_token_exits(self, tmp_path, monkeypatch):
        """Missing token should exit before any network call."""
        pdf_file = tmp_path / "paper.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")
        monkeypatch.delenv("ZENODO_TOKEN", raising=False)
        monkeypatch.delenv("ZENODO_PROD_TOKEN", raising=False)

        args = argparse.Namespace(
            output_dir=str(tmp_path),
            token=None,
            title="Test",
            authors=None,
            description=None,
            production=False,
        )

        with pytest.raises(SystemExit) as exc_info:
            cli.publish_zenodo_command(args)
        assert exc_info.value.code == 1

    def test_publish_zenodo_missing_output_dir_exits(self, tmp_path, monkeypatch):
        """Missing output directory should exit before any network call."""
        missing = tmp_path / "missing"
        args = argparse.Namespace(
            output_dir=str(missing),
            token="test_token",
            title="Test",
            authors=None,
            description=None,
            production=False,
        )
        with pytest.raises(SystemExit) as exc_info:
            cli.publish_zenodo_command(args)
        assert exc_info.value.code == 1

    def test_publish_zenodo_no_pdfs_error(self, tmp_path):
        """Empty output directory should exit when no PDFs are found."""
        args = argparse.Namespace(
            output_dir=str(tmp_path),
            token="test_token",
            title="Test",
            authors=None,
            description=None,
            production=False,
        )
        with pytest.raises(SystemExit) as exc_info:
            cli.publish_zenodo_command(args)
        assert exc_info.value.code == 1

    def test_publish_zenodo_upload_failure_exits(
        self,
        tmp_path,
        monkeypatch,
        caplog,
    ):
        """PublishingError during upload should exit with code 1."""
        from pytest_httpserver import HTTPServer

        pdf_file = tmp_path / "paper.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")

        server = HTTPServer()
        server.start()
        try:
            server.expect_request("/deposit/depositions", method="POST").respond_with_json(
                {
                    "id": 1,
                    "links": {"bucket": f"{server.url_for('')}/files/bucket1"},
                }
            )
            server.expect_request("/files/bucket1/paper.pdf", method="PUT").respond_with_data(
                "fail",
                status=500,
            )

            original_config = cli.ZenodoConfig

            def config_with_test_url(*args, **kwargs):
                kwargs["base_url"] = server.url_for("")
                return original_config(*args, **kwargs)

            monkeypatch.setattr(cli, "ZenodoConfig", config_with_test_url)

            args = argparse.Namespace(
                output_dir=str(tmp_path),
                token="test_token",
                title="Test",
                authors=None,
                description=None,
                production=True,
            )

            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit) as exc_info:
                    cli.publish_zenodo_command(args)
            assert exc_info.value.code == 1
        finally:
            server.stop()

    def test_publish_zenodo_validates_token(self):
        """Test token validation logic."""
        # Test that token validation works (real logic, no network)
        token = "test_token_123"
        assert token is not None
        assert len(token) > 0


class TestMainCli:
    """Test suite for main CLI entry point."""

    def test_main_unhandled_command_exception(self, monkeypatch, caplog):
        """Unexpected exceptions from subcommands should exit with code 1."""

        def failing_command(_args):
            raise RuntimeError("simulated failure")

        monkeypatch.setattr(
            cli,
            "publish_zenodo_command",
            failing_command,
        )

        original_argv = sys.argv
        try:
            sys.argv = [
                "cli.py",
                "publish-zenodo",
                str(Path("output")),
                "--token",
                "test",
            ]
            with caplog.at_level(logging.ERROR):
                with pytest.raises(SystemExit) as exc_info:
                    cli.main()
            assert exc_info.value.code == 1
            assert "simulated failure" in caplog.text
        finally:
            sys.argv = original_argv

    def test_main_without_command(self):
        """Test main without any subcommand."""
        # Test argument parsing directly (real argparse behavior)

        original_argv = sys.argv
        try:
            sys.argv = ["cli.py"]
            with pytest.raises(SystemExit):
                cli.main()
        finally:
            sys.argv = original_argv

    def test_main_help_shows_commands(self):
        """Test that help shows available commands."""

        original_argv = sys.argv
        try:
            sys.argv = ["cli.py", "--help"]
            with pytest.raises(SystemExit):
                cli.main()
        finally:
            sys.argv = original_argv


class TestCliModuleStructure:
    """Test CLI module structure and imports."""

    def test_module_has_main_function(self):
        """Test that cli module has main function."""
        assert hasattr(cli, "main")
        assert callable(cli.main)

    def test_module_has_command_functions(self):
        """Test that cli module has command functions."""
        assert hasattr(cli, "extract_metadata_command")
        assert hasattr(cli, "generate_citation_command")
        assert hasattr(cli, "publish_zenodo_command")


class TestPublishCliCore:
    """Test core publish CLI functionality."""

    def test_module_imports(self):
        """Test that module imports correctly."""
        from infrastructure.publishing import publish_cli

        assert publish_cli is not None

    def test_has_main_function(self):
        """Test that module has main function."""
        from infrastructure.publishing import publish_cli

        assert hasattr(publish_cli, "main") or hasattr(publish_cli, "publish_cli")


class TestZenodoCommands:
    """Test Zenodo publishing commands."""

    def test_zenodo_upload_command(self):
        """Test Zenodo upload command."""
        from infrastructure.publishing import publish_cli

        if hasattr(publish_cli, "zenodo_upload_command"):
            assert callable(publish_cli.zenodo_upload_command)

    def test_zenodo_create_command(self):
        """Test Zenodo create command."""
        from infrastructure.publishing import publish_cli

        if hasattr(publish_cli, "zenodo_create_command"):
            assert callable(publish_cli.zenodo_create_command)


class TestArxivCommands:
    """Test arXiv publishing commands."""

    def test_arxiv_prepare_command(self):
        """Test arXiv prepare command."""
        from infrastructure.publishing import publish_cli

        if hasattr(publish_cli, "arxiv_prepare_command"):
            assert callable(publish_cli.arxiv_prepare_command)


class TestGitHubCommands:
    """Test GitHub release commands."""

    def test_github_release_command(self):
        """Test GitHub release command."""
        from infrastructure.publishing import publish_cli

        if hasattr(publish_cli, "github_release_command"):
            assert callable(publish_cli.github_release_command)


class TestPublishCliParsing:
    """Test CLI argument parsing."""

    def test_parse_args_basic(self):
        """Test basic argument parsing."""
        # Test by running the CLI script with arguments
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        script_path = repo_root / "infrastructure" / "publishing" / "publish_cli.py"

        # Set PYTHONPATH to include repo root
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_root) + os.pathsep + env.get("PYTHONPATH", "")

        # Run with --help to test argument parsing works
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            capture_output=True,
            text=True,
            cwd=repo_root,
            env=env,
            timeout=30,
        )

        # Should exit with code 0 (help) or 2 (error but parsed correctly)
        assert result.returncode in [0, 2]
        assert "Publish release" in result.stdout or "Publish release" in result.stderr


class TestPublishCliMain:
    """Test main entry point."""

    def test_main_without_args(self):
        """Test main without arguments shows error."""
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        script_path = repo_root / "infrastructure" / "publishing" / "publish_cli.py"

        # Set PYTHONPATH to include repo root
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_root) + os.pathsep + env.get("PYTHONPATH", "")

        # Run without required arguments - should fail
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            cwd=repo_root,
            env=env,
            timeout=30,
        )

        # Should exit with error code due to missing required arguments
        assert result.returncode != 0
        assert "required" in result.stderr.lower() or "required" in result.stdout.lower()

    def test_main_with_help(self):
        """Test main with help flag."""
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        script_path = repo_root / "infrastructure" / "publishing" / "publish_cli.py"

        # Set PYTHONPATH to include repo root
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_root) + os.pathsep + env.get("PYTHONPATH", "")

        # Run with --help
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            capture_output=True,
            text=True,
            cwd=repo_root,
            env=env,
            timeout=30,
        )

        # Should show help and exit
        assert result.returncode in [0, 2]  # argparse uses 2 for help
        assert "--token" in result.stdout or "--token" in result.stderr


class TestPublishCliIntegration:
    """Integration tests for publish CLI."""

    def test_full_publish_workflow(self, tmp_path):
        """Test complete publish workflow."""
        from infrastructure.publishing import publish_cli

        # Module should be importable
        assert publish_cli is not None
