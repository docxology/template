"""Real-render tests for infrastructure.rendering.mermaid_figure (no mocks).

Skips the real-render tests cleanly when ``mmdc`` (mermaid-cli) is not on
PATH — matches the opt-in-tool pattern used elsewhere in this repo (e.g.
Ollama-gated LLM tests). The error-path test does not require ``mmdc``.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering.mermaid_figure import render_mermaid_png

_MMDC_AVAILABLE = shutil.which("mmdc") is not None

_SIMPLE_DIAGRAM = """flowchart TB
    A[Start] --> B[End]
"""


def test_render_mermaid_png_raises_clear_error_without_mmdc(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(shutil, "which", lambda _name: None)
    with pytest.raises(RenderingError, match="mmdc"):
        render_mermaid_png(_SIMPLE_DIAGRAM, tmp_path / "diagram.png")


@pytest.mark.skipif(not _MMDC_AVAILABLE, reason="mmdc (mermaid-cli) not installed")
def test_render_mermaid_png_produces_real_file(tmp_path: Path):
    output = render_mermaid_png(_SIMPLE_DIAGRAM, tmp_path / "diagram.png")
    assert output.is_file()
    assert output.stat().st_size > 100


@pytest.mark.skipif(not _MMDC_AVAILABLE, reason="mmdc (mermaid-cli) not installed")
def test_render_mermaid_png_writes_mmd_sidecar_for_cache_check(tmp_path: Path):
    output_path = tmp_path / "diagram.png"
    render_mermaid_png(_SIMPLE_DIAGRAM, output_path)
    sidecar = output_path.with_suffix(".mmd")
    assert sidecar.is_file()
    assert sidecar.read_text(encoding="utf-8").rstrip("\n") == _SIMPLE_DIAGRAM.rstrip("\n")


@pytest.mark.skipif(not _MMDC_AVAILABLE, reason="mmdc (mermaid-cli) not installed")
def test_render_mermaid_png_is_a_noop_when_source_unchanged(tmp_path: Path):
    output_path = tmp_path / "diagram.png"
    render_mermaid_png(_SIMPLE_DIAGRAM, output_path)
    first_mtime = output_path.stat().st_mtime_ns

    render_mermaid_png(_SIMPLE_DIAGRAM, output_path)
    second_mtime = output_path.stat().st_mtime_ns

    assert first_mtime == second_mtime, "unchanged source should skip re-invoking mmdc, not rewrite the PNG"


@pytest.mark.skipif(not _MMDC_AVAILABLE, reason="mmdc (mermaid-cli) not installed")
def test_render_mermaid_png_re_renders_when_source_changes(tmp_path: Path):
    output_path = tmp_path / "diagram.png"
    render_mermaid_png(_SIMPLE_DIAGRAM, output_path)
    first_bytes = output_path.read_bytes()

    different_diagram = "flowchart TB\n    A[Start] --> B[Middle] --> C[End]\n"
    render_mermaid_png(different_diagram, output_path)
    second_bytes = output_path.read_bytes()

    assert first_bytes != second_bytes
