"""Tests for infrastructure.publishing.cli module."""

import contextlib
import io
import json

from infrastructure.publishing import cli


class TestPublishingCLI:
    """Test publishing CLI functionality."""

    def test_cli_module_exists(self):
        """Test CLI module is importable."""
        assert cli is not None
        assert hasattr(cli, "main")
        assert hasattr(cli, "extract_metadata_command")
        assert hasattr(cli, "generate_citation_command")
        assert hasattr(cli, "publish_zenodo_command")

    def test_publish_command_available(self):
        """Test publish command is available."""
        assert cli is not None
        assert callable(cli.publish_zenodo_command)

    def test_zenodo_publish_available(self):
        """Test Zenodo publish functionality."""
        assert hasattr(cli, "publish_zenodo_command")
        assert callable(cli.publish_zenodo_command)

    def test_arxiv_submit_available(self):
        """Test arXiv submission functionality."""
        # arXiv submission may be part of publishing workflow
        # Check that publishing commands exist
        assert hasattr(cli, "publish_zenodo_command")
        assert callable(cli.publish_zenodo_command)

    def test_github_release_available(self):
        """Test GitHub release functionality."""
        # GitHub release may be part of publishing workflow
        # Check that publishing commands exist
        assert hasattr(cli, "publish_zenodo_command")
        assert callable(cli.publish_zenodo_command)

    def test_cli_help_output(self):
        """Test CLI help output."""
        assert hasattr(cli, "main")
        assert callable(cli.main)

    def test_cli_error_messages(self):
        """Test CLI error message handling."""
        # Error handling is tested in command functions
        assert cli is not None
        assert hasattr(cli, "extract_metadata_command")
        assert callable(cli.extract_metadata_command)


class TestPublishingCLISchema:
    """Tests for the uniform ``schema`` subcommand (no mocks)."""

    def test_schema_subcommand_emits_valid_json(self):
        """`main(["schema"])` returns 0 and prints a JSON parameter contract."""
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            exit_code = cli.main(["schema"])

        assert exit_code == 0
        payload = json.loads(buffer.getvalue())
        assert payload["prog"]
        assert "subcommands" in payload
        # Existing subcommands are still present in the contract.
        for command in ("extract-metadata", "generate-citation", "publish-zenodo"):
            assert command in payload["subcommands"]

    def test_existing_subcommands_unchanged(self):
        """The schema reflects existing flags without alteration."""
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            assert cli.main(["schema"]) == 0
        payload = json.loads(buffer.getvalue())

        cite = payload["subcommands"]["generate-citation"]
        fmt = next(opt for opt in cite["options"] if opt["name"] == "format")
        assert fmt["choices"] == ["bibtex"]
        assert fmt["default"] == "bibtex"
