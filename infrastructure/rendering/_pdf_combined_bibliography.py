"""Bibliography injection for combined PDF rendering."""

from __future__ import annotations

import re

from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering._pdf_combined_transmission import (
    _END_TRANSMISSION_SECTION,
    _END_TRANSMISSION_SECTION_NUMBERED,
    _TRANSMISSION_END_BOOKEND_MARKER,
)

logger = get_logger(__name__)


def discover_manuscript_bib_paths(manuscript_dir: Path) -> list[Path]:
    """Return sorted ``*.bib`` paths beside the manuscript (multi-database projects)."""
    return sorted(manuscript_dir.glob("*.bib"))


def inject_bibliography(
    tex_content: str,
    bib_exists: bool,
    bib_stems: str = "references",
    *,
    before_end_transmission: bool = False,
) -> str:
    """Ensure bibliography starts on a new page; set ``\\bibliography{stems}``.

    ``bib_stems`` is a comma-separated list of database names without ``.bib``
    (e.g. ``references`` or ``references,references_deep``).

    When ``before_end_transmission`` is true, insert before the END bookend section
    instead of before ``\\end{document}``.
    """
    bib_marker = "\\bibliography{"
    # ``\\printbibliography`` belongs to biblatex, while this renderer uses
    # natbib/BibTeX.  Remove manuscript-level biblatex commands before the
    # canonical ``\\bibliography{...}`` insertion so stale generated sections
    # cannot trigger an undefined-control-sequence failure.
    tex_content = re.sub(r"^\s*\\printbibliography\s*$", "", tex_content, flags=re.MULTILINE)
    if not bib_exists:
        return tex_content

    replacement = r"\bibliography{" + bib_stems + "}"
    insertion = f"\n\n\\clearpage\n\n{replacement}\n"

    if before_end_transmission:
        end_idx = tex_content.find(_TRANSMISSION_END_BOOKEND_MARKER)
        if end_idx < 0:
            end_idx = tex_content.find(_END_TRANSMISSION_SECTION)
        if end_idx < 0:
            end_idx = tex_content.find(_END_TRANSMISSION_SECTION_NUMBERED)
        if end_idx < 0:
            end_idx = tex_content.find(r"\label{end-of-transmission}")
        if end_idx < 0:
            logger.warning("⚠️  END transmission section not found; bibliography stays at document end")
            before_end_transmission = False
        elif bib_marker in tex_content:
            tex_content = re.sub(
                r"\\bibliography\{[^}]*\}",
                lambda _m: replacement,
                tex_content,
                count=1,
            )
            idx = tex_content.find(bib_marker)
            if idx > end_idx:
                tex_content = tex_content.replace(f"\\clearpage\n\n{replacement}\n", "", 1)
                tex_content = tex_content.replace(f"\n\n\\clearpage\n\n{replacement}\n", "", 1)
                tex_content = tex_content[:end_idx] + insertion + tex_content[end_idx:]
                logger.info("✓ Moved \\bibliography{...} before END OF TRANSMISSION")
            return tex_content
        else:
            tex_content = tex_content[:end_idx] + insertion + tex_content[end_idx:]
            logger.info("✓ Inserted \\bibliography{...} before END OF TRANSMISSION")
            return tex_content

    if bib_marker in tex_content:
        tex_content = re.sub(
            r"\\bibliography\{[^}]*\}",
            lambda _m: replacement,
            tex_content,
            count=1,
        )
        idx = tex_content.find(bib_marker)
        before = tex_content[max(0, idx - 80) : idx]
        if "\\clearpage" not in before:
            tex_content = tex_content[:idx] + "\\clearpage\n\n" + tex_content[idx:]
            logger.info("✓ Inserted \\clearpage before \\bibliography{...}")
        return tex_content

    end_doc_idx = tex_content.rfind("\\end{document}")
    if end_doc_idx > 0:
        tex_content = tex_content[:end_doc_idx] + f"\n\n\\clearpage\n\n{replacement}\n" + tex_content[end_doc_idx:]
        logger.info("✓ Inserted \\clearpage and \\bibliography{...} before \\end{document}")
    else:
        logger.warning("⚠️  Could not find \\end{document} to insert bibliography")
    return tex_content
