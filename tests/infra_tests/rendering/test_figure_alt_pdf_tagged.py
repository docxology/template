"""Tagged-PDF figure alt-text registry wiring tests (split from test_figure_alt_wiring.py)."""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._pdf_figure_alts import apply_pdf_figure_alts
from infrastructure.rendering._pdf_title_page_latex import _latex_graphic_alt_text


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
