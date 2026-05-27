"""Transmission bookend helpers for combined PDF LaTeX injection."""

from __future__ import annotations

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

_BEGIN_TRANSMISSION_LABEL = r"\label{beginning-of-transmission}"
_END_TRANSMISSION_SECTION = r"\section*{END OF TRANSMISSION}"
_END_TRANSMISSION_SECTION_NUMBERED = r"\section{END OF TRANSMISSION}"
_TRANSMISSION_END_BOOKEND_MARKER = r"% transmission-end-bookend"


def _inject_toc_after_begin_transmission(tex_content: str, begin_doc_idx: int, title_page_body: str = "") -> str:
    """Insert the cover/title page then the table of contents after the begin bookend.

    With transmission bookends enabled, page 1 is the BEGINNING OF TRANSMISSION
    bookend. The cover/title page (``\\maketitle`` — ``\\title``/``\\author``/``\\date``
    are already placed in the preamble) is inserted as **page 2**, followed by the
    table of contents, then the manuscript body. When *title_page_body* is empty the
    cover is skipped and only the TOC is relocated (legacy behaviour).
    """
    label_idx = tex_content.find(_BEGIN_TRANSMISSION_LABEL, begin_doc_idx)
    if label_idx < 0:
        logger.warning("⚠️  Begin transmission label not found; cover/TOC not relocated")
        return tex_content

    samepage_end = tex_content.find(r"\end{samepage}", label_idx)
    if samepage_end < 0:
        logger.warning("⚠️  Begin transmission samepage envelope not found; cover/TOC not relocated")
        return tex_content

    newpage_idx = tex_content.find(r"\newpage", samepage_end)
    if newpage_idx < 0:
        logger.warning("⚠️  Begin transmission closing newpage not found; cover/TOC not relocated")
        return tex_content

    insert_at = newpage_idx + len(r"\newpage")
    window = tex_content[begin_doc_idx : insert_at + 200]
    if "\\tableofcontents" in window:
        return tex_content

    cover_block = ""
    body = title_page_body.strip()
    if body and "\\maketitle" not in window:
        cover_block = "\n\n" + body + "\n\\newpage\n"
        logger.info("✓ Inserted cover/title page as page 2 (after begin transmission bookend)")
    block = cover_block + "\n\\tableofcontents\n\\newpage\n"
    return tex_content[:insert_at] + block + tex_content[insert_at:]
