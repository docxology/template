"""Focused contract tests for :mod:`infrastructure.rendering.pdf_renderer`.

The canonical renderer suite covers the transformation helpers and combined
manuscript paths. These tests cover the public dispatch boundary and the
engine-resolution behavior with a real temporary executable, so missing local
toolchains produce explicit errors instead of silently passing.
"""

from __future__ import annotations

import stat
import subprocess
from pathlib import Path

import pytest

from infrastructure.core.exceptions import CompilationError, RenderingError
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.pdf_renderer import PDFRenderer


def _config(tmp_path: Path) -> RenderingConfig:
    output = tmp_path / "output"
    return RenderingConfig(
        output_dir=str(output),
        pdf_dir=str(output / "pdf"),
        manuscript_dir=str(tmp_path / "manuscript"),
        figures_dir=str(output / "figures"),
    )


def _write_executable(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


class TestPdfRendererDispatch:
    """Test format dispatch and deterministic engine selection."""

    def test_render_rejects_unsupported_source_format(self, tmp_path: Path) -> None:
        source = tmp_path / "document.txt"
        source.write_text("not a renderable document", encoding="utf-8")

        with pytest.raises(RenderingError, match="Unsupported file format"):
            PDFRenderer(_config(tmp_path)).render(source)

    def test_render_missing_tex_reports_compilation_error(self, tmp_path: Path) -> None:
        with pytest.raises(CompilationError, match="LaTeX file not found"):
            PDFRenderer(_config(tmp_path)).render(tmp_path / "missing.tex")

    def test_markdown_engine_candidates_are_deduplicated(self, tmp_path: Path) -> None:
        config = _config(tmp_path)
        config.latex_compiler = "xelatex"

        def resolve(executable: str) -> str | None:
            return f"/toolchain/{executable}" if executable in {"xelatex", "lualatex"} else None

        renderer = PDFRenderer(config, executable_resolver=resolve)

        assert renderer._markdown_pdf_engines() == ["xelatex", "lualatex"]

    def test_markdown_render_requires_pandoc(self, tmp_path: Path) -> None:
        source = tmp_path / "document.md"
        source.write_text("# Document\n", encoding="utf-8")
        config = _config(tmp_path)
        config.pandoc_path = "missing-pandoc"

        with pytest.raises(RenderingError, match="Pandoc not found"):
            PDFRenderer(config, executable_resolver=lambda _name: None).render_markdown(source)

    def test_markdown_render_uses_available_engine_and_writes_output(self, tmp_path: Path) -> None:
        source = tmp_path / "document.md"
        source.write_text("# Document\n", encoding="utf-8")
        pandoc = _write_executable(
            tmp_path / "pandoc-stub",
            "#!/bin/sh\n"
            "output=''\n"
            "previous=''\n"
            'for arg in "$@"; do\n'
            '  if [ "$previous" = "-o" ]; then output="$arg"; fi\n'
            '  previous="$arg"\n'
            "done\n"
            ': > "$output"\n',
        )
        config = _config(tmp_path)
        config.pandoc_path = str(pandoc)

        def resolve(executable: str) -> str | None:
            if executable == str(pandoc):
                return executable
            return "/toolchain/xelatex" if executable == "xelatex" else None

        output = PDFRenderer(config, executable_resolver=resolve).render_markdown(source)

        assert output == Path(config.pdf_dir) / "document.pdf"
        assert output.is_file()

    def test_markdown_render_propagates_process_failure(self, tmp_path: Path) -> None:
        source = tmp_path / "document.md"
        source.write_text("# Document\n", encoding="utf-8")
        config = _config(tmp_path)
        config.pandoc_path = "pandoc"

        def fail(_args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
            raise subprocess.CalledProcessError(1, "pandoc", stderr="invalid markdown")

        def resolve(executable: str) -> str | None:
            return "/toolchain/" + executable

        with pytest.raises(RenderingError, match="Failed to render markdown"):
            PDFRenderer(config, executable_resolver=resolve, process_runner=fail).render_markdown(source)


class TestPdfRendererConfiguration:
    """Test the real rendering configuration contract."""

    def test_default_config_uses_xelatex(self) -> None:
        assert RenderingConfig().latex_compiler == "xelatex"

    def test_custom_config_preserves_explicit_compiler(self) -> None:
        config = RenderingConfig(latex_compiler="pdflatex")
        assert config.latex_compiler == "pdflatex"
