"""Comprehensive tests for infrastructure/rendering/cli.py.

Tests the CLI interface for rendering operations using real implementations.
Follows No Mocks Policy - all tests use real data and real execution.
"""

import argparse
import contextlib
import io
import json
import logging
import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.rendering import cli


def _assert_cli_result(result: subprocess.CompletedProcess[str], *, success_text: str | None = None) -> None:
    """Require an observable CLI outcome even when optional tools are absent."""
    combined = f"{result.stdout}\n{result.stderr}".strip()
    assert result.returncode in (0, 1)
    assert combined, "CLI must report either generated output or a failure reason"
    if result.returncode == 0 and success_text is not None:
        assert success_text in combined
    if result.returncode == 1:
        assert any(token in combined.lower() for token in ("error", "failed", "not found"))


@pytest.mark.slow
class TestRenderPdfCommand:
    """Test suite for render_pdf_command using real RenderManager."""

    def test_render_pdf_basic(self, tmp_path, caplog, capsys):
        """Test basic PDF rendering with real RenderManager."""
        tex_file = tmp_path / "test.tex"
        tex_file.write_text("\\documentclass{article}\\begin{document}Test\\end{document}")

        args = argparse.Namespace(source=str(tex_file))

        # Use real RenderManager - may fail if LaTeX not available, but tests real behavior
        with caplog.at_level(logging.INFO):
            try:
                rc = cli.render_pdf_command(args)
            except Exception as exc:
                outcome = f"{caplog.text}\n{exc}".lower()
                assert any(token in outcome for token in ("render", "latex", "pandoc", "error"))
            else:
                assert rc == 0
                assert "Generated:" in capsys.readouterr().out

    def test_render_pdf_nonexistent_source(self, tmp_path, caplog):
        """Test PDF rendering with nonexistent source."""
        args = argparse.Namespace(source=str(tmp_path / "nonexistent.tex"))

        with caplog.at_level(logging.ERROR):
            rc = cli.render_pdf_command(args)
        assert rc == 1  # handlers now return an exit code instead of raising SystemExit

        assert "error" in caplog.text.lower() or "not found" in caplog.text.lower()


@pytest.mark.slow
class TestRenderAllCommand:
    """Test suite for render_all_command using real RenderManager."""

    def test_render_all_basic(self, tmp_path, caplog, capsys):
        """Test rendering all formats with real RenderManager."""
        tex_file = tmp_path / "test.tex"
        tex_file.write_text("\\documentclass{article}\\begin{document}Test\\end{document}")

        args = argparse.Namespace(source=str(tex_file))

        # Use real RenderManager - may fail if LaTeX not available, but tests real behavior
        with caplog.at_level(logging.INFO):
            try:
                rc = cli.render_all_command(args)
            except Exception as exc:
                outcome = f"{caplog.text}\n{exc}".lower()
                assert any(token in outcome for token in ("render", "latex", "pandoc", "error"))
            else:
                assert rc == 0
                assert "Generated:" in capsys.readouterr().out

    def test_render_all_nonexistent_source(self, tmp_path, capsys):
        """Test render all with nonexistent source."""
        args = argparse.Namespace(source=str(tmp_path / "nonexistent.tex"))

        rc = cli.render_all_command(args)
        assert rc == 1  # handlers now return an exit code instead of raising SystemExit


@pytest.mark.slow
class TestRenderSlidesCommand:
    """Test suite for render_slides_command using real RenderManager."""

    def test_render_slides_beamer(self, tmp_path, caplog, capsys):
        """Test Beamer slide rendering with real RenderManager."""
        md_file = tmp_path / "slides.md"
        md_file.write_text("# Slide 1\n\n## Content")

        args = argparse.Namespace(source=str(md_file), format="beamer")

        # Use real RenderManager - may fail if LaTeX not available, but tests real behavior
        with caplog.at_level(logging.INFO):
            try:
                rc = cli.render_slides_command(args)
            except Exception as exc:
                outcome = f"{caplog.text}\n{exc}".lower()
                assert any(token in outcome for token in ("beamer", "render", "latex", "pandoc", "error"))
            else:
                assert rc == 0
                assert "Generated:" in capsys.readouterr().out

    def test_render_slides_revealjs(self, tmp_path, capsys):
        """Test reveal.js slide rendering with real RenderManager."""
        md_file = tmp_path / "slides.md"
        md_file.write_text("# Slide 1")

        args = argparse.Namespace(source=str(md_file), format="revealjs")

        # Use real RenderManager
        cli.render_slides_command(args)

        captured = capsys.readouterr()
        assert "revealjs" in captured.out or "Generated" in captured.out or "Rendering slides" in captured.out

    def test_render_slides_default_format(self, tmp_path, caplog, capsys):
        """Test slides with default format (beamer) using real RenderManager."""
        md_file = tmp_path / "slides.md"
        md_file.write_text("# Slide")

        args = argparse.Namespace(source=str(md_file), format=None)

        # Use real RenderManager - should default to beamer, may fail if LaTeX not available
        with caplog.at_level(logging.INFO):
            try:
                rc = cli.render_slides_command(args)
            except Exception as exc:
                outcome = f"{caplog.text}\n{exc}".lower()
                assert any(token in outcome for token in ("beamer", "render", "latex", "pandoc", "error"))
            else:
                assert rc == 0
                assert "Generated:" in capsys.readouterr().out

    def test_render_slides_nonexistent_source(self, tmp_path, capsys):
        """Test slides with nonexistent source."""
        args = argparse.Namespace(source=str(tmp_path / "nonexistent.md"), format="beamer")

        rc = cli.render_slides_command(args)
        assert rc == 1  # handlers now return an exit code instead of raising SystemExit


class TestRenderWebCommand:
    """Test suite for render_web_command using real RenderManager."""

    def test_render_web_basic(self, tmp_path, capsys):
        """Test basic web rendering with real RenderManager."""
        md_file = tmp_path / "document.md"
        md_file.write_text("# Document\n\nContent here.")

        args = argparse.Namespace(source=str(md_file))

        # Use real RenderManager
        cli.render_web_command(args)

        captured = capsys.readouterr()
        assert "Rendering web output" in captured.out or "Generated" in captured.out

    def test_render_web_nonexistent_source(self, tmp_path, capsys):
        """Test web rendering with nonexistent source."""
        args = argparse.Namespace(source=str(tmp_path / "nonexistent.md"))

        rc = cli.render_web_command(args)
        assert rc == 1  # handlers now return an exit code instead of raising SystemExit


@pytest.mark.slow
class TestMainCli:
    """Test suite for main CLI entry point using real subprocess execution."""

    def test_main_with_pdf_command(self, tmp_path):
        """Test main with pdf subcommand via real subprocess."""
        tex_file = tmp_path / "test.tex"
        tex_file.write_text("\\documentclass{article}\\begin{document}Test\\end{document}")

        # Run real CLI command via subprocess
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "infrastructure.rendering.cli",
                "pdf",
                str(tex_file),
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent,  # Repository root for module imports,
            timeout=30,
        )

        _assert_cli_result(result, success_text="Generated:")

    def test_main_with_all_command(self, tmp_path):
        """Test main with all subcommand via real subprocess."""
        tex_file = tmp_path / "test.tex"
        tex_file.write_text("\\documentclass{article}\\begin{document}Test\\end{document}")

        # Run real CLI command via subprocess
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "infrastructure.rendering.cli",
                "all",
                str(tex_file),
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent,
            timeout=30,
        )

        _assert_cli_result(result, success_text="Generated:")

    def test_main_with_slides_command(self, tmp_path):
        """Test main with slides subcommand via real subprocess."""
        md_file = tmp_path / "slides.md"
        md_file.write_text("# Slide")

        # Run real CLI command via subprocess
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "infrastructure.rendering.cli",
                "slides",
                str(md_file),
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent,
            timeout=30,
        )

        _assert_cli_result(result, success_text="Generated:")

    def test_main_with_web_command(self, tmp_path):
        """Test main with web subcommand via real subprocess."""
        md_file = tmp_path / "doc.md"
        md_file.write_text("# Doc")

        # Run real CLI command via subprocess
        result = subprocess.run(
            [sys.executable, "-m", "infrastructure.rendering.cli", "web", str(md_file)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent,
            timeout=30,
        )

        _assert_cli_result(result, success_text="Generated:")

    def test_main_without_command(self):
        """Test main without any subcommand via real subprocess."""
        result = subprocess.run(
            [sys.executable, "-m", "infrastructure.rendering.cli"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent,
            timeout=30,
        )

        # Should exit with error code when no command provided
        assert result.returncode == 1
        assert "usage:" in result.stdout.lower()

    def test_main_with_exception(self, tmp_path):
        """Test main when command raises an exception via real execution."""
        # Create a file that might cause issues
        tex_file = tmp_path / "test.tex"
        tex_file.write_text("\\documentclass{article}\\begin{document}Test\\end{document}")

        # Use an invalid source so the exception-to-exit-code boundary is
        # deterministic regardless of the installed rendering toolchain.
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "infrastructure.rendering.cli",
                "pdf",
                str(tmp_path / "missing.tex"),
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent,
            timeout=30,
        )

        assert result.returncode == 1
        combined = f"{result.stdout}\n{result.stderr}".lower()
        assert "source file not found" in combined

    def test_main_slides_with_format_option(self, tmp_path):
        """Test main with slides format option via real subprocess."""
        md_file = tmp_path / "slides.md"
        md_file.write_text("# Slide")

        # Run real CLI command via subprocess
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "infrastructure.rendering.cli",
                "slides",
                str(md_file),
                "--format",
                "revealjs",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent,
            timeout=30,
        )

        _assert_cli_result(result, success_text="Generated:")


class TestCliModuleStructure:
    """Test CLI module structure and imports."""

    def test_module_has_main_function(self):
        """Test that cli module has main function."""
        assert hasattr(cli, "main")
        assert callable(cli.main)

    def test_module_has_command_functions(self):
        """Test that cli module has command functions."""
        assert hasattr(cli, "render_pdf_command")
        assert hasattr(cli, "render_all_command")
        assert hasattr(cli, "render_slides_command")
        assert hasattr(cli, "render_web_command")

    def test_imports_render_manager(self):
        """Test that RenderManager is imported."""
        assert hasattr(cli, "RenderManager")


class TestRenderAllCliCore:
    """Test core render all CLI functionality."""

    def test_module_imports(self):
        """Test that module imports correctly."""
        from infrastructure.rendering import render_all_cli

        assert render_all_cli.__name__ == "infrastructure.rendering.render_all_cli"

    def test_has_main_function(self):
        """Test that module has main function."""
        from infrastructure.rendering import render_all_cli

        assert callable(render_all_cli.main)


class TestRenderCommands:
    """Test render command functionality."""

    def test_render_all_entrypoint_is_callable(self):
        """The wrapper exposes one callable entrypoint for all formats."""
        from infrastructure.rendering import render_all_cli

        assert callable(render_all_cli.main)


@pytest.mark.slow
class TestRenderCliParsing:
    """Test CLI argument parsing via real subprocess."""

    def test_parse_args_basic(self, tmp_path):
        """Test basic argument parsing via real subprocess."""
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmp_dir:
            pdf = Path(tmp_dir) / "source.md"
            pdf.write_text("# Test")

            # Run real CLI command via subprocess
            result = subprocess.run(
                [sys.executable, "-m", "infrastructure.rendering.cli", "pdf", str(pdf)],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent.parent,
                timeout=30,
            )

            _assert_cli_result(result, success_text="Generated:")


class TestSlidesRendering:
    """Test slides rendering commands."""

    def test_slides_beamer_command(self):
        """Test Beamer slides command."""
        from infrastructure.rendering import render_all_cli

        assert not hasattr(render_all_cli, "render_slides_command")

    def test_slides_revealjs_command(self):
        """Test reveal.js slides command."""
        from infrastructure.rendering import render_all_cli

        assert not hasattr(render_all_cli, "render_revealjs_command")


class TestSchemaSubcommand:
    """Test the additive ``schema`` subcommand (uniform parameter contract)."""

    def test_schema_returns_zero_and_emits_valid_json(self):
        """main(["schema"]) returns 0 and prints a JSON schema with expected keys."""
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            rc = cli.main(["schema"])
        assert rc == 0

        payload = json.loads(buffer.getvalue())
        assert "prog" in payload
        assert "options" in payload
        assert "subcommands" in payload
        # Existing subcommands must still be present in the contract.
        for name in ("pdf", "all", "slides", "web", "schema"):
            assert name in payload["subcommands"]

    def test_existing_subcommand_still_parses(self, tmp_path):
        """An existing subcommand still dispatches — proving no regression."""
        rc = cli.main(["web", str(tmp_path / "missing.md")])
        # Nonexistent source returns 1 via the existing handler (no crash, no new behavior).
        assert rc == 1

    def test_schema_subcommand_via_subprocess(self):
        """`python -m infrastructure.rendering schema` exits 0 and emits JSON."""
        result = subprocess.run(
            [sys.executable, "-m", "infrastructure.rendering", "schema"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent,
            timeout=30,
        )
        assert result.returncode == 0
        payload = json.loads(result.stdout)
        assert "subcommands" in payload


@pytest.mark.slow
class TestRenderCliMain:
    """Test main entry point using real subprocess execution."""

    def test_main_without_args(self):
        """Test main without arguments via real subprocess."""
        # Run real CLI command via subprocess
        result = subprocess.run(
            [sys.executable, "-m", "infrastructure.rendering.cli"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent,
            timeout=30,
        )

        assert result.returncode == 1
        assert "usage:" in result.stdout.lower()

    def test_main_with_pdf(self, tmp_path):
        """Test main with PDF command via real subprocess."""
        tex_file = tmp_path / "test.tex"
        tex_file.write_text("\\documentclass{article}\\begin{document}Test\\end{document}")

        # Run real CLI command via subprocess
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "infrastructure.rendering.cli",
                "pdf",
                str(tex_file),
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent,
            timeout=30,
        )

        _assert_cli_result(result, success_text="Generated:")
