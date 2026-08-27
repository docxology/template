"""Real render-boundary tests for source-owned figure alternative text."""

from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._pdf_figure_alts import apply_pdf_figure_alts
from infrastructure.rendering._pdf_combined_latex import postprocess_latex
from infrastructure.rendering._pdf_title_page_latex import _latex_graphic_alt_text
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


@pytest.mark.parametrize(
    "registry_payload",
    [
        {
            "fig:dense": {
                "label": "fig:dense",
                "filename": "dense.png",
                "metadata": {
                    "alt_text": (
                        "Three blue trajectories descend at different rates; amber uncertainty bands narrow "
                        "after iteration 40, while the dashed baseline remains flat."
                    )
                },
            }
        },
        {
            "schema_version": "figure-registry-v1",
            "figures": [
                {
                    "label": "fig:dense",
                    "path": "dense.png",
                    "alt": (
                        "Three blue trajectories descend at different rates; amber uncertainty bands narrow "
                        "after iteration 40, while the dashed baseline remains flat."
                    ),
                }
            ],
        },
        {
            "schema_version": "figure-registry-v1",
            "figures": [
                {
                    "label": "fig:dense",
                    "path": "dense.png",
                    "alt_text": (
                        "Three blue trajectories descend at different rates; amber uncertainty bands narrow "
                        "after iteration 40, while the dashed baseline remains flat."
                    ),
                }
            ],
        },
    ],
    ids=["metadata-alt-text", "top-level-alt", "canonical-top-level-alt-text"],
)
def test_source_owned_registry_alt_reaches_real_combined_html(
    tmp_path: Path,
    registry_payload: object,
) -> None:
    rich_alt = (
        "Three blue trajectories descend at different rates; amber uncertainty bands narrow "
        "after iteration 40, while the dashed baseline remains flat."
    )

    rendered = _render_figure_html(tmp_path, registry_payload)

    assert f'alt="{html.escape(rich_alt, quote=True)}"' in rendered
    assert 'src="../figures/dense.png"' in rendered
    expected_caption = "Figure 1: Short visible caption" if shutil.which("pandoc-crossref") else "Short visible caption"
    assert f"<figcaption>{expected_caption}</figcaption>" in re.sub(r"\s+", " ", rendered)
    assert 'alt="Short visible caption"' not in rendered


def test_registry_replacement_uses_exact_alt_and_src_attributes(tmp_path: Path) -> None:
    registry_path = tmp_path / "figure_registry.json"
    rich_alt = "Three blue trajectories descend while amber intervals narrow."
    registry_path.write_text(
        json.dumps({"fig:dense": {"filename": "dense.png", "alt": rich_alt}}),
        encoding="utf-8",
    )
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><body><figure id="fig:dense"><img '
        'data-fig-alt="Preserve this provenance attribute." '
        'data-src="../figures/decoy.png" src="figures/dense.png" '
        'alt="Short visible caption"><figcaption>Visible caption.</figcaption>'
        "</figure></body></html>",
        encoding="utf-8",
    )

    WebRenderer._enhance_accessibility(html_file, registry_path=registry_path)

    rendered = html_file.read_text(encoding="utf-8")
    assert 'data-fig-alt="Preserve this provenance attribute."' in rendered
    assert 'data-src="../figures/decoy.png"' in rendered
    assert f'alt="{rich_alt}"' in rendered
    assert 'src="../figures/dense.png"' in rendered
    assert 'alt="Short visible caption"' not in rendered


def test_registry_replacement_preserves_latex_backslashes_in_alt(tmp_path: Path) -> None:
    """Registry alt text with LaTeX backslashes must not break re.sub replacement."""
    registry_path = tmp_path / "figure_registry.json"
    rich_alt = r"Phase portrait with \Omega resistance and \delta perturbation."
    registry_path.write_text(
        json.dumps({"fig:dense": {"filename": "dense.png", "alt": rich_alt}}),
        encoding="utf-8",
    )
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><body><figure id="fig:dense"><img src="figures/dense.png" '
        'alt="Short visible caption"><figcaption>Visible caption.</figcaption>'
        "</figure></body></html>",
        encoding="utf-8",
    )

    WebRenderer._enhance_accessibility(html_file, registry_path=registry_path)

    rendered = html_file.read_text(encoding="utf-8")
    assert f'alt="{html.escape(rich_alt, quote=True)}"' in rendered
    assert 'alt="Short visible caption"' not in rendered


def test_labelled_html_figure_rejects_duplicate_registry_filename_owners(tmp_path: Path) -> None:
    registry_path = tmp_path / "figure_registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "fig:dense": {"filename": "shared.png", "alt": "Dense description."},
                "fig:other": {"filename": "shared.png", "alt": "Other description."},
            }
        ),
        encoding="utf-8",
    )
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><body><figure id="fig:dense"><img src="../figures/shared.png" '
        'alt="Authored description."><figcaption>Caption.</figcaption></figure></body></html>',
        encoding="utf-8",
    )

    with pytest.raises(RenderingError, match="multiple registry records"):
        WebRenderer._enhance_accessibility(html_file, registry_path=registry_path)


def test_unlabelled_figure_without_registry_match_preserves_authored_alt(tmp_path: Path) -> None:
    registry_path = tmp_path / "figure_registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "fig:canonical": {
                    "filename": "canonical.png",
                    "alt": "Canonical figure description.",
                }
            }
        ),
        encoding="utf-8",
    )
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><body><figure><img src="../figures/authored.png" '
        'alt="Authored figure description."><figcaption>Authored figure.</figcaption>'
        "</figure></body></html>",
        encoding="utf-8",
    )

    WebRenderer._enhance_accessibility(html_file, registry_path=registry_path)

    rendered = html_file.read_text(encoding="utf-8")
    assert 'alt="Authored figure description."' in rendered
    assert "Canonical figure description." not in rendered
    assert 'id="fig:' not in rendered


def test_registry_alt_reaches_combined_html_from_hydrated_manuscript_tree(tmp_path: Path) -> None:
    project = tmp_path / "project"
    manuscript_dir = project / "output" / "manuscript"
    figures_dir = project / "output" / "figures"
    web_dir = project / "output" / "web"
    manuscript_dir.mkdir(parents=True)
    figures_dir.mkdir(parents=True)
    source = manuscript_dir / "03_results.md"
    source.write_text(
        "# Results\n\n![Short caption](../figures/dense.png){#fig:dense}\n",
        encoding="utf-8",
    )
    (figures_dir / "dense.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    rich_alt = "Three blue trajectories descend while amber uncertainty bands narrow after iteration 40."
    (figures_dir / "figure_registry.json").write_text(
        json.dumps(
            {
                "fig:dense": {
                    "filename": "dense.png",
                    "metadata": {"alt_text": rich_alt},
                }
            }
        ),
        encoding="utf-8",
    )
    renderer = WebRenderer(
        RenderingConfig(
            output_dir=str(project / "output"),
            figures_dir=str(figures_dir),
            web_dir=str(web_dir),
        )
    )

    rendered = renderer.render_combined([source], manuscript_dir, "test").read_text(encoding="utf-8")

    assert f'alt="{rich_alt}"' in rendered
    assert 'src="../figures/dense.png"' in rendered
    assert "output/output/figures" not in rendered


def test_present_registry_label_with_mismatched_path_fails_render(tmp_path: Path) -> None:
    registry = {
        "fig:dense": {
            "label": "fig:dense",
            "filename": "different.png",
            "metadata": {"alt_text": "A meaningful description."},
        }
    }

    with pytest.raises(RenderingError, match="path does not match"):
        _render_figure_html(tmp_path, registry)


def test_registry_filename_match_without_rendered_label_fails(tmp_path: Path) -> None:
    registry_path = tmp_path / "figure_registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "fig:dense": {
                    "filename": "dense.png",
                    "metadata": {"alt_text": "A meaningful description."},
                }
            }
        ),
        encoding="utf-8",
    )
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><body><figure><img src="../figures/dense.png" alt="Authored description.">'
        "<figcaption>Visible caption.</figcaption></figure></body></html>",
        encoding="utf-8",
    )

    with pytest.raises(RenderingError, match="label/path mismatch"):
        WebRenderer._enhance_accessibility(html_file, registry_path=registry_path)


def test_present_registry_path_with_mismatched_label_fails_render(tmp_path: Path) -> None:
    registry = {
        "fig:other": {
            "label": "fig:other",
            "filename": "dense.png",
            "metadata": {"alt_text": "A meaningful description."},
        }
    }

    with pytest.raises(RenderingError, match="label/path mismatch"):
        _render_figure_html(tmp_path, registry)


def test_present_registry_record_with_blank_alt_fails_render(tmp_path: Path) -> None:
    registry = {
        "fig:dense": {
            "label": "fig:dense",
            "filename": "dense.png",
            "metadata": {"alt_text": "   "},
        }
    }

    with pytest.raises(RenderingError, match="missing accessibility alt text"):
        _render_figure_html(tmp_path, registry)


@pytest.mark.parametrize(
    "filename",
    [
        "../secret.png",
        "/tmp/secret.png",
        "../figures/../secret.png",
        "figures/nested/../../secret.png",
        "dense.png?download=1",
        "dense.png#fragment",
    ],
)
def test_unsafe_registry_figure_path_fails_render(tmp_path: Path, filename: str) -> None:
    registry = {
        "fig:dense": {
            "label": "fig:dense",
            "filename": filename,
            "metadata": {"alt_text": "A meaningful description."},
        }
    }

    with pytest.raises(RenderingError, match="safe relative filename/path"):
        _render_figure_html(tmp_path, registry)


@pytest.mark.parametrize(
    "registry",
    [
        {"figures": {"label": "fig:dense"}},
        {"figures": [None]},
        [{"filename": "dense.png", "alt": "A description."}],
        {"not-a-figure": {"filename": "dense.png", "alt": "A description."}},
        {"fig:dense": {"label": "fig:dense", "alt": "A description."}},
    ],
)
def test_malformed_present_registry_fails_instead_of_degrading_to_authored_alt(
    tmp_path: Path,
    registry: object,
) -> None:
    with pytest.raises(RenderingError):
        _render_figure_html(tmp_path, registry)


def test_unregistered_figure_retains_nonblank_authored_alt_instead_of_caption(tmp_path: Path) -> None:
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><body><figure id="fig:authored"><img src="../figures/authored.png" '
        'alt="Author describes a steep blue curve."><figcaption>'
        "Figure 7: A short publication caption.</figcaption></figure></body></html>",
        encoding="utf-8",
    )

    WebRenderer._enhance_accessibility(html_file, registry_path=tmp_path / "missing-registry.json")

    rendered = html_file.read_text(encoding="utf-8")
    assert 'alt="Author describes a steep blue curve."' in rendered
    assert 'alt="Figure 7: A short publication caption."' not in rendered


def test_unregistered_cross_referenced_figure_with_blank_authored_alt_fails(tmp_path: Path) -> None:
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><body><figure id="fig:blank"><img src="../figures/blank.png" alt="">'
        "<figcaption>A non-decorative, cross-referenced result.</figcaption></figure></body></html>",
        encoding="utf-8",
    )

    with pytest.raises(RenderingError, match="blank authored alt text"):
        WebRenderer._enhance_accessibility(html_file, registry_path=tmp_path / "missing-registry.json")


def test_unlabelled_registry_reuse_gets_explicit_decorative_empty_alt(tmp_path: Path) -> None:
    registry_path = tmp_path / "figure_registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "fig:dense": {
                    "filename": "dense.png",
                    "metadata": {"alt_text": "Canonical long description for the labelled occurrence."},
                }
            }
        ),
        encoding="utf-8",
    )
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><body><p><img src="figures/dense.png"></p>'
        '<p><em>Reproduced from <a href="#fig:dense">Figure 2</a>.</em></p></body></html>',
        encoding="utf-8",
    )

    WebRenderer._enhance_accessibility(html_file, registry_path=registry_path)

    rendered = html_file.read_text(encoding="utf-8")
    assert '<img src="../figures/dense.png" alt=""' in rendered
    assert "Canonical long description" not in rendered


def test_unregistered_image_without_alt_fails_instead_of_becoming_decorative(tmp_path: Path) -> None:
    html_file = tmp_path / "index.html"
    html_file.write_text(
        '<html><body><p><img src="../figures/unknown.png"></p></body></html>',
        encoding="utf-8",
    )

    with pytest.raises(RenderingError, match="missing authored alt text"):
        WebRenderer._enhance_accessibility(html_file, registry_path=tmp_path / "missing-registry.json")


def test_tagged_pdf_replaces_pandoc_caption_alt_with_registry_text(tmp_path: Path) -> None:
    registry_path = tmp_path / "figure_registry.json"
    rich_alt = "Blue & amber curves fall from 9% to 1_000 units # reproducibly."
    registry_path.write_text(
        json.dumps(
            {
                "fig:dense": {
                    "filename": "dense.png",
                    "metadata": {"alt_text": rich_alt},
                }
            }
        ),
        encoding="utf-8",
    )
    tex = (
        r"\begin{figure}"
        r"\pandocbounded{\includegraphics[keepaspectratio,alt={Short caption on {[}0, 6{]}}]"
        r"{../figures/dense.png}}"
        r"\caption{Short visible caption}\label{fig:dense}"
        r"\end{figure}"
    )

    rendered = apply_pdf_figure_alts(tex, registry_path, tagged_pdf=True)

    assert f"alt={{{_latex_graphic_alt_text(rich_alt)}}}" in rendered
    assert "Short caption" not in rendered
    assert r"{../figures/dense.png}" in rendered


def test_tagged_pdf_rejects_registry_path_under_mismatched_figure_label(tmp_path: Path) -> None:
    registry_path = tmp_path / "figure_registry.json"
    registry_path.write_text(
        json.dumps({"fig:dense": {"filename": "dense.png", "alt": "Registry description."}}),
        encoding="utf-8",
    )
    tex = (
        r"\begin{figure}\includegraphics[alt={Authored description.}]{../figures/dense.png}"
        r"\caption{Caption}\label{fig:other}\end{figure}"
    )

    with pytest.raises(RenderingError, match="label/path mismatch"):
        apply_pdf_figure_alts(tex, registry_path, tagged_pdf=True)


def test_tagged_pdf_rejects_registry_label_rendering_mismatched_path(tmp_path: Path) -> None:
    registry_path = tmp_path / "figure_registry.json"
    registry_path.write_text(
        json.dumps({"fig:dense": {"filename": "dense.png", "alt": "Registry description."}}),
        encoding="utf-8",
    )
    tex = (
        r"\begin{figure}\includegraphics[alt={Authored description.}]{../figures/other.png}"
        r"\caption{Caption}\label{fig:dense}\end{figure}"
    )

    with pytest.raises(RenderingError, match="label/path mismatch"):
        apply_pdf_figure_alts(tex, registry_path, tagged_pdf=True)


def test_labelled_tagged_pdf_figure_rejects_duplicate_registry_filename_owners(
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "figure_registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "fig:dense": {"filename": "shared.png", "alt": "Dense description."},
                "fig:other": {"filename": "shared.png", "alt": "Other description."},
            }
        ),
        encoding="utf-8",
    )
    tex = (
        r"\begin{figure}\includegraphics[alt={Authored description.}]{../figures/shared.png}"
        r"\caption{Caption}\label{fig:dense}\end{figure}"
    )

    with pytest.raises(RenderingError, match="multiple registry records"):
        apply_pdf_figure_alts(tex, registry_path, tagged_pdf=True)


def test_tagged_pdf_unlabelled_registry_reuse_preserves_nonblank_authored_alt(tmp_path: Path) -> None:
    registry_path = tmp_path / "figure_registry.json"
    registry_path.write_text(
        json.dumps({"fig:dense": {"filename": "dense.png", "alt": "Registry description."}}),
        encoding="utf-8",
    )
    tex = r"\includegraphics[keepaspectratio,alt={Repeated caption}]{../figures/dense.png}"

    rendered = apply_pdf_figure_alts(tex, registry_path, tagged_pdf=True)

    assert rendered == tex
    assert "Repeated caption" in rendered
    assert "Registry description" not in rendered


def test_tagged_pdf_unlabelled_registry_reuse_without_authored_alt_stays_decorative(
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "figure_registry.json"
    registry_path.write_text(
        json.dumps({"fig:dense": {"filename": "dense.png", "alt": "Registry description."}}),
        encoding="utf-8",
    )
    tex = r"\includegraphics[keepaspectratio]{../figures/dense.png}"

    rendered = apply_pdf_figure_alts(tex, registry_path, tagged_pdf=True)

    assert "alt={}" in rendered
    assert "Registry description" not in rendered


@pytest.mark.parametrize("registry_present", [False, True])
def test_tagged_pdf_unregistered_graphic_without_authored_alt_fails(
    tmp_path: Path,
    registry_present: bool,
) -> None:
    registry_path = tmp_path / "figure_registry.json"
    if registry_present:
        registry_path.write_text(
            json.dumps({"fig:dense": {"filename": "dense.png", "alt": "Registry description."}}),
            encoding="utf-8",
        )
    tex = r"\includegraphics[keepaspectratio]{../figures/unknown.png}"

    with pytest.raises(RenderingError, match="missing nonblank authored alt text"):
        apply_pdf_figure_alts(tex, registry_path, tagged_pdf=True)


def test_tagged_pdf_unregistered_figure_preserves_nonblank_authored_alt(tmp_path: Path) -> None:
    registry_path = tmp_path / "figure_registry.json"
    registry_path.write_text(
        json.dumps({"fig:dense": {"filename": "dense.png", "alt": "Registry description."}}),
        encoding="utf-8",
    )
    tex = (
        r"\begin{figure}\includegraphics[alt={Authored blue slope description.}]{../figures/other.png}"
        r"\caption{Caption}\label{fig:other}\end{figure}"
    )

    rendered = apply_pdf_figure_alts(tex, registry_path, tagged_pdf=True)

    assert rendered == tex


def test_tagged_pdf_unlabelled_figure_cannot_consume_registry_path(tmp_path: Path) -> None:
    registry_path = tmp_path / "figure_registry.json"
    registry_path.write_text(
        json.dumps({"fig:dense": {"filename": "dense.png", "alt": "Registry description."}}),
        encoding="utf-8",
    )
    tex = (
        r"\begin{figure}\includegraphics[alt={Authored description.}]{../figures/dense.png}"
        r"\caption{Caption}\end{figure}"
    )

    with pytest.raises(RenderingError, match="unlabelled figure"):
        apply_pdf_figure_alts(tex, registry_path, tagged_pdf=True)


def test_untagged_pdf_does_not_claim_registry_alt_support(tmp_path: Path) -> None:
    registry_path = tmp_path / "figure_registry.json"
    registry_path.write_text(
        json.dumps({"fig:dense": {"filename": "dense.png", "alt": "Registry description."}}),
        encoding="utf-8",
    )
    tex = r"\includegraphics[alt={Authored caption}]{../figures/dense.png}"

    rendered = apply_pdf_figure_alts(tex, registry_path, tagged_pdf=False)

    assert rendered == tex


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


@pytest.mark.requires_latex
@pytest.mark.timeout(60)
def test_registry_alt_reaches_real_tagged_pdf_structure_tree(tmp_path: Path) -> None:
    if shutil.which("lualatex") is None:
        pytest.skip("lualatex is not installed")

    pdf_dir = tmp_path / "output" / "pdf"
    figures_dir = tmp_path / "output" / "figures"
    pdf_dir.mkdir(parents=True)
    figures_dir.mkdir(parents=True)
    probe_tex = postprocess_latex(
        r"\documentclass{article}\begin{document}probe\end{document}",
        tagged_pdf=True,
        language="en",
    )
    probe = _run_lualatex(pdf_dir, "tagged-figure-probe", probe_tex)
    if probe.returncode != 0:
        pytest.skip("installed LuaLaTeX does not support the repository's tagged-PDF metadata mode")

    from PIL import Image

    Image.new("RGB", (8, 8), color=(30, 60, 90)).save(figures_dir / "dense.png")
    registry_path = figures_dir / "figure_registry.json"
    rich_alt = "Blue & amber curves fall from 9% to 1_000 units # reproducibly."
    registry_path.write_text(
        json.dumps({"fig:dense": {"filename": "dense.png", "alt": rich_alt}}),
        encoding="utf-8",
    )
    tex = postprocess_latex(
        r"\documentclass{article}\usepackage{graphicx}\begin{document}"
        r"\begin{figure}\includegraphics[alt={Short caption}]{../figures/dense.png}"
        r"\caption{Short caption}\label{fig:dense}\end{figure}"
        r"\end{document}",
        tagged_pdf=True,
        language="en",
    )
    tex = apply_pdf_figure_alts(tex, registry_path, tagged_pdf=True)

    compiled = _run_lualatex(pdf_dir, "tagged-registry-alt", tex)

    assert compiled.returncode == 0, compiled.stdout
    assert _pdf_structure_alt_texts(pdf_dir / "tagged-registry-alt.pdf") == [rich_alt]
