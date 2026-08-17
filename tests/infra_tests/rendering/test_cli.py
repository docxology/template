"""Tests for infrastructure.rendering.cli — real parser and main() outcomes."""

from infrastructure.rendering import cli


class TestRenderingCLI:
    """Test rendering CLI functionality."""

    def test_cli_help_lists_format_commands(self) -> None:
        help_text = cli.build_parser().format_help()
        assert "Render documents in multiple formats" in help_text
        assert "pdf" in help_text
        assert "slides" in help_text
        assert "web" in help_text
        assert "{pdf,all,slides,web,schema}" in help_text or "slides" in help_text

    def test_cli_missing_command_returns_error(self) -> None:
        assert cli.main([]) == 1

    def test_cli_unknown_format_is_rejected(self) -> None:
        try:
            cli.main(["slides", "unused.md", "--format", "not-a-format"])
        except SystemExit as exc:
            assert exc.code == 2
        else:
            raise AssertionError("invalid --format must be rejected by argparse")

    def test_web_command_missing_source_returns_error(self, tmp_path) -> None:
        assert cli.main(["web", str(tmp_path / "missing.md")]) == 1

    def test_pdf_command_missing_source_returns_error(self, tmp_path) -> None:
        assert cli.main(["pdf", str(tmp_path / "missing.tex")]) == 1
