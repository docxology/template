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


_REFERENCE_SECTION_RE = re.compile(
    r"\\(?:sub)?section\*?\{[^}]*\breferences\b[^}]*\}",
    flags=re.IGNORECASE | re.DOTALL,
)


def _has_explicit_reference_section(tex_content: str) -> bool:
    """Return whether the manuscript already supplies a references heading."""

    return bool(_REFERENCE_SECTION_RE.search(tex_content))


def _inline_bibsection_prefix() -> str:
    """Suppress natbib's automatic bibliography heading when prose already supplies one."""
    return "\\providecommand{\\bibsection}{}\n\\renewcommand{\\bibsection}{}\n\n"


def _bibliography_insertion(replacement: str, *, inline: bool) -> str:
    """Build the LaTeX insertion, preserving an explicit references section."""

    if inline:
        # natbib calls ``\\bibsection`` to emit its automatic heading.  The
        # manuscript's explicit references section is the authoritative title
        # in this mode, so suppress the duplicate while retaining the normal
        # bibliography environment and its citation behavior.
        return f"\n\n{_inline_bibsection_prefix()}{replacement}\n"
    return f"\n\n\\clearpage\n\n{replacement}\n"


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
    """Inject ``\\bibliography{stems}`` with a clean heading/layout contract.

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
    inline_bibliography = _has_explicit_reference_section(tex_content)
    insertion = _bibliography_insertion(replacement, inline=inline_bibliography)

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
        if inline_bibliography:
            if "\\renewcommand{\\bibsection}" not in before:
                tex_content = tex_content[:idx] + _inline_bibsection_prefix() + tex_content[idx:]
        elif "\\clearpage" not in before:
            tex_content = tex_content[:idx] + "\\clearpage\n\n" + tex_content[idx:]
            logger.info("✓ Inserted \\clearpage before \\bibliography{...}")
        return tex_content

    end_doc_idx = tex_content.rfind("\\end{document}")
    if end_doc_idx > 0:
        tex_content = tex_content[:end_doc_idx] + insertion + tex_content[end_doc_idx:]
        if inline_bibliography:
            logger.info("✓ Inserted inline \\bibliography{...} after explicit references section")
        else:
            logger.info("✓ Inserted \\clearpage and \\bibliography{...} before \\end{document}")
    else:
        logger.warning("⚠️  Could not find \\end{document} to insert bibliography")
    return tex_content
