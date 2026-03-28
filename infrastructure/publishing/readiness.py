"""Publication readiness validation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from infrastructure.publishing.citations import extract_citations_from_markdown

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


def validate_publication_readiness(
    markdown_files: list[Path], pdf_files: list[Path]
) -> dict[str, Any]:
    """Validate that the project is ready for publication.

    Args:
        markdown_files: List of markdown files
        pdf_files: List of PDF files

    Returns:
        Dictionary with publication readiness assessment
    """

    readiness: dict[str, Any] = {
        "ready_for_publication": True,
        "completeness_score": 0,
        "missing_elements": [],
        "recommendations": [],
    }

    # Check document completeness by reading file content
    all_content = ""
    for md_file in markdown_files:
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                all_content += f.read()
        except (OSError, UnicodeDecodeError) as e:
            logger.debug(f"Skipping unreadable file {md_file}: {e}")
            continue

    # Check for section headings (e.g. "# Abstract", "## Introduction") rather than
    # bare substring matching to avoid false positives from body text mentions.
    _heading_re = re.compile(r"^#{1,3}\s+", re.MULTILINE)
    headings_lower = {
        m.string[m.end():m.end() + 60].split("\n")[0].strip().lower()
        for m in _heading_re.finditer(all_content)
    }

    def _has_section(*keywords: str) -> bool:
        return any(any(kw in h for h in headings_lower) for kw in keywords)

    has_abstract = _has_section("abstract")
    has_introduction = _has_section("introduction")
    has_methodology = _has_section("methodology", "methods", "approach")
    has_results = _has_section("results", "experimental", "evaluation", "findings")
    has_conclusion = _has_section("conclusion", "discussion", "summary")

    score = 0
    if has_abstract:
        score += 15
    if has_introduction:
        score += 15
    if has_methodology:
        score += 20
    if has_results:
        score += 20
    if has_conclusion:
        score += 15

    readiness["completeness_score"] = score

    if score < 80:
        readiness["ready_for_publication"] = False
        readiness["missing_elements"].append("Document structure incomplete")

    # Check PDF generation
    if not pdf_files:
        readiness["ready_for_publication"] = False
        readiness["missing_elements"].append("No PDF files generated")

    # Check for citations
    citations = extract_citations_from_markdown(markdown_files)
    if not citations:
        readiness["recommendations"].append("Consider adding citations to related work")

    # Check for figures
    figure_count = len(re.findall(r"\\includegraphics", all_content))
    if figure_count == 0:
        readiness["recommendations"].append("Consider adding figures to illustrate key concepts")

    # Final assessment
    if readiness["ready_for_publication"]:
        readiness["recommendations"].append("Project appears ready for publication!")
    else:
        readiness["recommendations"].append("Address missing elements before publication")

    return readiness
