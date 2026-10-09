"""Project successful source-owned Mermaid figures into native Office images.

The PDF preprocessor's raw TeX is its output contract. This Office projection
requires that exact successful output for every original fence. A verbatim
fallback can never become an accepted image or an omitted source occurrence.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from infrastructure.rendering._pdf_mermaid import (
    _MERMAID_BLOCK_RE,
    _caption_for_markdown,
    _caption_text,
    _first_alt,
    _latex_caption,
    _normalise_mermaid_source,
    _source_hash,
)
from infrastructure.rendering._pdf_title_page_latex import _latex_graphic_alt_text


@dataclass(frozen=True)
class OfficeMermaidProjection:
    """Projected content and retained source-to-image occurrence bindings."""

    content: str
    occurrences: tuple[dict[str, object], ...]


def project_office_mermaid_figures(preprocessed: str, combined_source: str) -> OfficeMermaidProjection:
    """Restore original captions/alternatives after successful PDF preprocessing.

    Call only for DOCX/EPUB after the existing combined preprocessor. The PNG
    targets and width constraint follow its existing production route;
    source captions retain their original Unicode and Markdown semantics.
    Native acceptance must independently bind each DSL, generated PNG, genuine
    producer process, package image and native ink. This function grants no gate.
    """
    if max(len(preprocessed.encode()), len(combined_source.encode())) > 32 * 1024 * 1024:
        raise ValueError("Office Mermaid projection exceeds the finite source budget")
    matches = tuple(_MERMAID_BLOCK_RE.finditer(combined_source))
    if len(matches) > 100:
        raise ValueError("Office Mermaid projection exceeds the finite fence budget")
    result = preprocessed
    rows = []
    for ordinal, match in enumerate(matches):
        original = match.group("source").strip()
        normal = _normalise_mermaid_source(original)
        if not normal:
            raise ValueError("Office Mermaid source contains an empty diagram")
        caption = _caption_text(match)
        alternative = _first_alt(match.group("alts")) or caption or "Mermaid diagram"
        # Reconstruct the literal successful production output independently of
        # any producer receipt. Its fallback uses verbatim and cannot match.
        stem = f"inline_mermaid_{ordinal + 1:04d}_{_source_hash(normal)}"
        target = f"../figures/mermaid_inline/{stem}.png"
        expected = (
            "\n\\begin{figure}[htbp]\n\\centering\n"
            "\\includegraphics[width=0.82\\linewidth,height=4.2in,keepaspectratio,"
            f"alt={{{_latex_graphic_alt_text(alternative)}}}]{{{target}}}\n"
            f"\\caption{{{_latex_caption(_caption_for_markdown(caption or alternative))}}}\n"
            "\\end{figure}\n"
        )
        if result.count(expected) != 1:
            raise ValueError(
                f"Office Mermaid source occurrence {ordinal} has no unique successful production figure; "
                "a fallback or changed figure remains a source obligation"
            )
        visible = caption or alternative
        if "\n" in visible or "\r" in visible or "\n" in alternative or "\r" in alternative:
            raise ValueError("Office Mermaid caption/alternative exceeds the admitted single-line form")
        # Explicit alt travels through the existing Office pre/post Lua passes.
        # Do not manufacture a crossref label absent from the original source.
        projected = (
            f"\n![{visible}]({target})"
            f"{{width=82% data-template-max-height=4.2in "
            f'style="max-height: 4.2in; height: auto; object-fit: contain;" '
            f"alt={json.dumps(alternative, ensure_ascii=False)}}}\n"
        )
        result = result.replace(expected, projected, 1)
        rows.append(
            {
                "ordinal": ordinal,
                "source_range": [match.start(), match.end()],
                "original_source_sha256": hashlib.sha256(original.encode()).hexdigest(),
                "normal_source_sha256": hashlib.sha256(normal.encode()).hexdigest(),
                "production_stem": stem,
                "image_target": target,
                "caption": visible,
                "alternative": alternative,
                "native_height_limit_requires_layout_witness": True,
                "production_figure_sha256": hashlib.sha256(expected.encode()).hexdigest(),
                "projected_markdown_sha256": hashlib.sha256(projected.encode()).hexdigest(),
            }
        )
    return OfficeMermaidProjection(result, tuple(rows))


def validate_office_mermaid_projection(
    preprocessed: str,
    combined_source: str,
    projected: str,
    occurrences: tuple[dict[str, object], ...],
    production: dict[str, object],
) -> None:
    """Recompute portable source projection and bind its original producer rows.

    The caller first replays the genuine original production record, then binds
    every projected asset's actual package/native image through the full Office
    image witness. This check cannot replace either obligation.
    """
    rebuilt = project_office_mermaid_figures(preprocessed, combined_source)
    diagrams = production.get("diagrams")
    if rebuilt.content != projected or rebuilt.occurrences != occurrences:
        raise ValueError("portable Office Mermaid source/caption/alternative projection differs")
    if not isinstance(diagrams, list) or len(diagrams) != len(occurrences):
        raise ValueError("Office Mermaid projection omitted an original producer occurrence")
    for source_row, produced in zip(occurrences, diagrams, strict=True):
        if not isinstance(produced, dict) or any(
            source_row[key] != produced.get(key)
            for key in ("ordinal", "source_range", "original_source_sha256", "normal_source_sha256", "production_stem")
        ):
            raise ValueError("Office Mermaid image projection belongs to a changed source diagram")
