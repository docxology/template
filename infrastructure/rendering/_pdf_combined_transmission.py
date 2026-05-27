"""Transmission bookend helpers for combined PDF LaTeX injection."""

from __future__ import annotations

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

_BEGIN_TRANSMISSION_LABEL = r"\label{beginning-of-transmission}"
_END_TRANSMISSION_SECTION = r"\section*{END OF TRANSMISSION}"
_END_TRANSMISSION_SECTION_NUMBERED = r"\section{END OF TRANSMISSION}"
_TRANSMISSION_END_BOOKEND_MARKER = r"% transmission-end-bookend"


def _inject_toc_after_begin_transmission(tex_content: str, begin_doc_idx: int) -> str:
    """Insert table of contents immediately after the begin transmission bookend closes."""
    label_idx = tex_content.find(_BEGIN_TRANSMISSION_LABEL, begin_doc_idx)
    if label_idx < 0:
        logger.warning("⚠️  Begin transmission label not found; TOC not relocated")
        return tex_content

    samepage_end = tex_content.find(r"\end{samepage}", label_idx)
    if samepage_end < 0:
        logger.warning("⚠️  Begin transmission samepage envelope not found; TOC not relocated")
        return tex_content

    newpage_idx = tex_content.find(r"\newpage", samepage_end)
    if newpage_idx < 0:
        logger.warning("⚠️  Begin transmission closing newpage not found; TOC not relocated")
        return tex_content

    insert_at = newpage_idx + len(r"\newpage")
    toc_block = "\n\n\\tableofcontents\n\\newpage\n"
    if "\\tableofcontents" in tex_content[begin_doc_idx : insert_at + 200]:
        return tex_content
    return tex_content[:insert_at] + toc_block + tex_content[insert_at:]
