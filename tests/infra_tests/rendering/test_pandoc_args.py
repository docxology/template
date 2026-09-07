"""Tests for the shared combined-edition pandoc argument assembly.

The DOCX, EPUB, and ebook lanes must hand one manuscript to pandoc under the
same resource-path, filter, crossref, and citation contract. These tests pin
the builder's contract order and prove the combined export lanes carry the
full resource-path triple (a missing leg silently drops images). Renderer
and ``which`` interception ride the same dependency-injection seams the
production code exposes (``docx_renderer=``/``epub_renderer=``/``which=``);
no module state is patched.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from infrastructure.core.logging.diagnostic import DiagnosticReporter
from infrastructure.rendering import RenderManager
from infrastructure.rendering._combined_exports import render_combined_docx, render_combined_epub
from infrastructure.rendering._pandoc_args import combined_pandoc_args
from infrastructure.rendering.config import RenderingConfig

pytestmark = pytest.mark.timeout(120)

_CROSSREF_STUB = "/usr/bin/pandoc-crossref"


def _resource_paths(args: list[str]) -> list[str]:
    """Return the values of every ``--resource-path=`` argument, in order."""
    return [arg.removeprefix("--resource-path=") for arg in args if arg.startswith("--resource-path=")]


def _make_manager(tmp_path: Path) -> RenderManager:
    """Create a RenderManager with all output dirs under tmp_path."""
    cfg = RenderingConfig(
        pdf_dir=str(tmp_path / "output/pdf"),
        docx_dir=str(tmp_path / "output/docx"),
        epub_dir=str(tmp_path / "output/epub"),
        figures_dir=str(tmp_path / "output/figures"),
        web_dir=str(tmp_path / "output/web"),
        output_dir=str(tmp_path / "output"),
    )
    return RenderManager(config=cfg)


def _combined_md_fixture(project_root: Path, text: str) -> None:
    """Place a combined markdown where resolve_combined_markdown finds it."""
    pdf_dir = project_root / "output" / "pdf"
    pdf_dir.mkdir(parents=True)
    (pdf_dir / "_combined_manuscript.md").write_text(text, encoding="utf-8")


def test_combined_pandoc_args_emits_contract_order(tmp_path: Path) -> None:
    """Resource paths, formalism filter, crossref, then citeproc + bibliographies."""
    manuscript_dir = tmp_path / "manuscript"
    figures_dir = tmp_path / "output" / "figures"
    bib = manuscript_dir / "references.bib"
    bib.parent.mkdir(parents=True)
    bib.write_text("@article{test, title={Test}}\n", encoding="utf-8")

    # Pin the crossref-present branch: CI installs pandoc but not
    # pandoc-crossref, so the real resolver is environment-dependent.
    args = combined_pandoc_args(
        [manuscript_dir, figures_dir, figures_dir.parent],
        [bib],
        edition="DOCX",
        which=lambda _name: _CROSSREF_STUB,
    )

    assert _resource_paths(args) == [str(manuscript_dir), str(figures_dir), str(figures_dir.parent)]
    formalism = [i for i, arg in enumerate(args) if arg.startswith("--lua-filter")]
    crossref = [i for i, arg in enumerate(args) if arg == "--filter"]
    citeproc = args.index("--citeproc")
    assert formalism and crossref and formalism[0] < crossref[0] < citeproc
    assert args[citeproc + 1 :] == [f"--bibliography={bib}"]


def test_combined_pandoc_args_without_bibliographies_omits_citeproc(tmp_path: Path) -> None:
    """No resolved bibliography means no citeproc machinery is appended."""
    args = combined_pandoc_args([tmp_path], [], edition="ebook", which=lambda _name: _CROSSREF_STUB)

    assert "--citeproc" not in args
    assert not [arg for arg in args if arg.startswith("--bibliography=")]
    assert "--filter" in args


def test_combined_pandoc_args_warns_by_edition_without_crossref(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A missing pandoc-crossref degrades to an edition-named warning."""
    import infrastructure.rendering._pandoc_args as module

    with caplog.at_level("WARNING", logger=module.logger.name):
        combined_pandoc_args([tmp_path], [], edition="EPUB", which=lambda _name: None)

    assert any("EPUB @fig:/@sec:/@tbl:/@eq:" in record.message for record in caplog.records)


def _fake_renderer(output_name: str) -> Any:
    """Return a renderer double recording kwargs, resolving to a real result."""

    def renderer(*args: object, **kwargs: object) -> SimpleNamespace:
        renderer.captured = kwargs
        return SimpleNamespace(output_path=Path(output_name), size_bytes=1024)

    renderer.captured = {}
    return renderer


@pytest.mark.parametrize("render_lane", ["docx", "epub"])
def test_combined_lanes_carry_full_resource_path_triple(
    tmp_path: Path,
    render_lane: str,
) -> None:
    """Every combined edition passes manuscript, figures, and figures-parent legs."""
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    _combined_md_fixture(tmp_path, "# Combined\n\nContent.\n")
    manager = _make_manager(tmp_path)
    reporter = DiagnosticReporter("test_project")
    fake = _fake_renderer(f"test.{render_lane}")

    if render_lane == "docx":
        render_combined_docx(manager, manuscript_dir, "myproject", reporter, docx_renderer=fake)
    else:
        render_combined_epub(manager, manuscript_dir, "myproject", reporter, epub_renderer=fake)

    extra_args = fake.captured["extra_args"]
    assert isinstance(extra_args, list)
    resource_values = _resource_paths(extra_args)
    assert len(resource_values) == 3, f"resource-path triple incomplete: {resource_values}"
    assert str(manuscript_dir) in resource_values
    assert any(value.endswith("/figures") for value in resource_values), f"figures leg missing from {resource_values}"
    assert any(value.endswith("/output") for value in resource_values), (
        f"figures-parent leg missing from {resource_values}"
    )
