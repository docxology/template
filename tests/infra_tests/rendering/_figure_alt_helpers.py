"""Shared helpers for the split figure alt-text wiring test modules (formerly test_figure_alt_wiring.py)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.web_renderer import WebRenderer


def _render_figure_html(tmp_path: Path, registry_payload: object) -> str:
    manuscript_dir = tmp_path / "manuscript"
    figures_dir = tmp_path / "output" / "figures"
    web_dir = tmp_path / "output" / "web"
    manuscript_dir.mkdir()
    figures_dir.mkdir(parents=True)
    source = manuscript_dir / "03_results.md"
    source.write_text(
        "# Results\n\n![Short visible caption](../output/figures/dense.png){#fig:dense}\n",
        encoding="utf-8",
    )
    (figures_dir / "dense.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (figures_dir / "figure_registry.json").write_text(
        json.dumps(registry_payload),
        encoding="utf-8",
    )
    renderer = WebRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            figures_dir=str(figures_dir),
            web_dir=str(web_dir),
        )
    )
    return renderer.render_combined([source], manuscript_dir, "test").read_text(encoding="utf-8")


def _run_lualatex(workdir: Path, jobname: str, tex: str) -> subprocess.CompletedProcess[str]:
    source = workdir / f"{jobname}.tex"
    source.write_text(tex, encoding="utf-8")
    return subprocess.run(
        ["lualatex", "-interaction=nonstopmode", "-halt-on-error", f"-jobname={jobname}", source.name],
        cwd=workdir,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=60,
    )


def _pdf_structure_alt_texts(pdf_path: Path) -> list[str]:
    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    structure_root = reader.trailer["/Root"].get("/StructTreeRoot")
    alt_texts: list[str] = []

    def visit(node: object) -> None:
        get_object = getattr(node, "get_object", None)
        if callable(get_object):
            node = get_object()
        if isinstance(node, dict):
            alt = node.get("/Alt")
            if alt is not None:
                alt_texts.append(str(alt))
            children = node.get("/K")
            if children is not None:
                visit(children)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    if structure_root is not None:
        visit(structure_root)
    return alt_texts
