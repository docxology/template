"""LaTeX preamble and title-page injection for combined PDF rendering."""

from __future__ import annotations

import re

from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering._pdf_combined_transmission import _inject_toc_after_begin_transmission
from infrastructure.rendering._pdf_latex_helpers import (
    extract_preamble,
    generate_title_page_body,
    generate_title_page_preamble,
)

logger = get_logger(__name__)


def inject_latex_preamble(
    tex_content: str,
    manuscript_dir: Path,
    *,
    skip_title_page: bool = False,
) -> str:
    """Extract preamble from preamble.md and config.yaml, inject before \\begin{document}."""
    preamble_file = manuscript_dir / "preamble.md"
    preamble_content = ""
    if preamble_file.exists():
        preamble_content = extract_preamble(preamble_file)
        if preamble_content:
            logger.info(f"✓ Extracted preamble from {preamble_file.name}")
        else:
            logger.warning("⚠️  Preamble file found but no LaTeX content extracted")
    else:
        logger.debug(f"No preamble file found at {preamble_file}")

    title_page_preamble = generate_title_page_preamble(manuscript_dir)
    title_page_body = generate_title_page_body(manuscript_dir)

    # Ensure graphicx package is always included
    graphicx_required = r"\usepackage{graphicx}"
    if preamble_content and graphicx_required not in preamble_content:
        logger.info("⚠️  graphicx package not found in preamble, adding it")
        preamble_content = graphicx_required + "\n" + preamble_content
    elif not preamble_content:
        logger.info("⚠️  No preamble found, adding graphicx package")
        preamble_content = graphicx_required

    # Ensure geometry package is present so margins are configurable in one
    # place. Default to 0.75in margins (~half of the 1.5in article default)
    # for a denser, more contemporary page that still leaves room for the
    # title/TOC. Skip injection if a manuscript-supplied or pandoc-emitted
    # geometry declaration is already present in either the user preamble
    # or the assembled TeX preamble (the portion before ``\begin{document}``).
    geometry_pkg_re = re.compile(r"\\usepackage(?:\[[^\]]*\])?\{geometry\}")
    geometry_cmd_re = re.compile(r"\\geometry\s*\{")
    tex_preamble_only = tex_content.split("\\begin{document}", 1)[0]
    has_geometry_in_user_preamble = bool(geometry_pkg_re.search(preamble_content))
    has_geometry_in_tex_preamble = bool(
        geometry_pkg_re.search(tex_preamble_only) or geometry_cmd_re.search(tex_preamble_only)
    )
    if has_geometry_in_user_preamble or has_geometry_in_tex_preamble:
        logger.debug("geometry already declared; not re-injecting")
    else:
        geometry_line = r"\usepackage[margin=0.75in]{geometry}"
        preamble_content = geometry_line + "\n" + preamble_content
        logger.info("✓ Injected geometry package (0.75in margins)")

    begin_doc_idx = tex_content.find("\\begin{document}")

    # Inject package declarations and title-page preamble before \begin{document}
    if (preamble_content or title_page_preamble) and begin_doc_idx > 0:
        combined_preamble = ""
        if title_page_preamble:
            combined_preamble += "\n".join(title_page_preamble.split("\n")) + "\n\n"
        if preamble_content:
            combined_preamble += preamble_content + "\n\n"
        tex_content = tex_content[:begin_doc_idx] + combined_preamble + tex_content[begin_doc_idx:]
        begin_doc_idx += len(combined_preamble)
        logger.debug(f"✓ Inserted preamble ({len(combined_preamble)} chars) before \\begin{{document}}")

    # Insert title page body after \begin{document}
    if skip_title_page:
        if begin_doc_idx <= 0:
            return tex_content
        tex_content = _inject_toc_after_begin_transmission(tex_content, begin_doc_idx)
        logger.info("✓ Skipped auto title page (transmission bookends); TOC after begin bookend")
        return tex_content

    if not title_page_body or begin_doc_idx <= 0:
        return tex_content

    if "\\tableofcontents" in title_page_body:
        full_title_body = title_page_body
    else:
        full_title_body = title_page_body + "\n\\tableofcontents\n\\newpage"
    tex_preamble = tex_content[:begin_doc_idx]
    tex_body = tex_content[begin_doc_idx:]

    if "\\maketitle" in tex_body:
        logger.debug("✓ \\maketitle already present in LaTeX body - replacing with our full title/TOC body")
        tex_body = tex_body.replace("\\maketitle", full_title_body, 1)
    else:
        end_of_begin_doc = tex_body.find("\n") + 1
        if end_of_begin_doc > 0:
            tex_body = tex_body[:end_of_begin_doc] + "\n" + full_title_body + "\n\n" + tex_body[end_of_begin_doc:]
        logger.info(r"✓ Inserted title/opening matter after \begin{document}")

    return tex_preamble + tex_body
