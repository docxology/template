"""Rendering pipeline summary and verification utilities.

This module provides:
- Rendering output summary generation
- Summary logging with formatted output
- PDF output verification with quality checks
- Citation detection in manuscript files
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from infrastructure.core.logging.utils import get_logger, log_success

logger = get_logger(__name__)


def generate_rendering_summary(project_name: str = "project") -> dict[str, Any]:
    """Generate comprehensive summary of rendering results.

    Returns:
        Dictionary with rendering statistics and file information
    """
    repo_root = Path(__file__).parent.parent.parent
    project_root = repo_root / "projects" / project_name
    output_dir = project_root / "output"

    summary: dict[str, Any] = {
        "project": project_name,
        "individual_pdfs": [],
        "combined_pdf": None,
        "combined_html": None,
        "web_outputs": [],
        "slides": [],
        "total_size_kb": 0,
    }

    project_basename = Path(project_name).name

    pdf_dir = output_dir / "pdf"
    if pdf_dir.exists():
        for pdf in sorted(pdf_dir.glob("*.pdf")):
            if pdf.name != f"{project_basename}_combined.pdf":
                size_kb = pdf.stat().st_size / 1024
                summary["individual_pdfs"].append({"name": pdf.name, "size_kb": size_kb})
                summary["total_size_kb"] += size_kb

    combined_pdf = pdf_dir / f"{project_basename}_combined.pdf"
    if combined_pdf.exists():
        size_kb = combined_pdf.stat().st_size / 1024
        summary["combined_pdf"] = {
            "name": combined_pdf.name,
            "size_kb": size_kb,
            "path": str(combined_pdf),
        }
        summary["total_size_kb"] += size_kb

    web_dir = output_dir / "web"
    if web_dir.exists():
        combined_html = web_dir / "index.html"
        if combined_html.exists():
            size_kb = combined_html.stat().st_size / 1024
            summary["combined_html"] = {
                "name": combined_html.name,
                "size_kb": size_kb,
                "path": str(combined_html),
            }
            summary["total_size_kb"] += size_kb

    if web_dir.exists():
        for html in sorted(web_dir.glob("*.html")):
            if html.name != "index.html":
                size_kb = html.stat().st_size / 1024
                summary["web_outputs"].append({"name": html.name, "size_kb": size_kb})

    slides_dir = output_dir / "slides"
    if slides_dir.exists():
        for slide in sorted(slides_dir.glob("*.pdf")):
            size_kb = slide.stat().st_size / 1024
            summary["slides"].append({"name": slide.name, "size_kb": size_kb})

    return summary


def log_rendering_summary(summary: dict[str, Any]) -> None:
    """Log comprehensive rendering summary with formatted output."""
    logger.info("\n" + "=" * 60)
    logger.info("RENDERING RESULTS SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Project: {summary['project']}")

    if summary["combined_pdf"]:
        pdf = summary["combined_pdf"]
        logger.info("\n📕 Combined Manuscript PDF:")
        logger.info(f"   {pdf['name']:<40} {pdf['size_kb']:>8.1f} KB")
        logger.info(f"   Location: {pdf['path']}")

    if summary["combined_html"]:
        html = summary["combined_html"]
        logger.info("\n🌐 Combined Manuscript HTML:")
        logger.info(f"   {html['name']:<40} {html['size_kb']:>8.1f} KB")
        logger.info(f"   Location: {html['path']}")

    if summary["individual_pdfs"]:
        logger.info(f"\n📄 Individual Section PDFs ({len(summary['individual_pdfs'])}):")
        for pdf in summary["individual_pdfs"]:
            logger.info(f"   {pdf['name']:<40} {pdf['size_kb']:>8.1f} KB")

    if summary["web_outputs"]:
        logger.info(f"\n🌐 Web Outputs ({len(summary['web_outputs'])}):")
        for web in summary["web_outputs"]:
            logger.info(f"   {web['name']:<40} {web['size_kb']:>8.1f} KB")

    if summary["slides"]:
        logger.info(f"\n📊 Presentation Slides ({len(summary['slides'])}):")
        for slide in summary["slides"]:
            logger.info(f"   {slide['name']:<40} {slide['size_kb']:>8.1f} KB")

    logger.info(
        f"\n📦 Total Output Size: {summary['total_size_kb']:.1f} KB ({summary['total_size_kb'] / 1024:.2f} MB)"
    )
    logger.info("=" * 60 + "\n")


def _check_citations_used(manuscript_dir: Path) -> bool:
    """Check if any manuscript files contain citation commands."""
    citation_patterns = [
        r"\\cite\{[^}]+\}",
        r"\\citep\{[^}]+\}",
        r"\\citet\{[^}]+\}",
        r"\\citeauthor\{[^}]+\}",
        r"\\citeyear\{[^}]+\}",
        r"@[^@\s]+\s",
    ]

    manuscript_files = list(manuscript_dir.glob("*.md"))
    supplemental_dir = manuscript_dir / "supplemental"
    if supplemental_dir.exists():
        manuscript_files.extend(list(supplemental_dir.glob("*.md")))

    for md_file in manuscript_files:
        try:
            content = md_file.read_text(encoding="utf-8")
            for pattern in citation_patterns:
                if re.search(pattern, content):
                    return True
        except (OSError, UnicodeDecodeError) as e:
            logger.debug(f"Could not read {md_file}: {e}")
            continue
    return False


def verify_pdf_outputs(project_name: str = "project") -> bool:
    """Verify that PDFs were generated with quality checks."""
    logger.info("Verifying PDF outputs...")

    repo_root = Path(__file__).parent.parent.parent
    project_root = repo_root / "projects" / project_name
    pdf_dir = project_root / "output" / "pdf"
    manuscript_dir = project_root / "manuscript"

    if not pdf_dir.exists():
        logger.error("PDF output directory not found")
        return False

    pdf_files = list(pdf_dir.glob("*.pdf"))
    project_basename = Path(project_name).name
    combined_pdf = pdf_dir / f"{project_basename}_combined.pdf"

    if pdf_files:
        log_success(f"Generated {len(pdf_files)} PDF file(s)", logger)

        valid_pdfs = 0
        failed_compilations = []

        for pdf_file in sorted(pdf_files):
            size_mb = pdf_file.stat().st_size / (1024 * 1024)
            size_kb = pdf_file.stat().st_size / 1024

            if size_mb > 0.01:
                valid_pdfs += 1
                marker = "📕" if pdf_file == combined_pdf else "  "
                logger.info(f"  {marker} {pdf_file.name} ({size_mb:.2f} MB) ✓")
            else:
                marker = "📕" if pdf_file == combined_pdf else "  "
                status_msg = f"  {marker} {pdf_file.name}"

                if size_kb < 0.1:
                    status_msg += f" - FAILED COMPILATION ({size_kb:.1f} KB)"
                    failed_compilations.append(pdf_file)
                    log_file = pdf_file.parent / f"{pdf_file.stem}.log"
                    if log_file.exists():
                        status_msg += f" - Check log: {log_file.name}"
                    else:
                        alt_log = pdf_file.parent / f"_{pdf_file.stem}.log"
                        if alt_log.exists():
                            status_msg += f" - Check log: {alt_log.name}"
                    logger.error(status_msg)
                else:
                    status_msg += f" - file too small ({size_kb:.1f} KB)"
                    logger.warning(status_msg)

        bib_file = manuscript_dir / "references.bib"
        citations_used = _check_citations_used(manuscript_dir)

        if bib_file.exists():
            logger.info("\n✅ Bibliography file found and will be processed")
        elif citations_used:
            logger.warning(
                "\n⚠️  Bibliography file not found (citations detected in manuscript - bibliography processing will be skipped)"
            )
        else:
            logger.info(
                "\nℹ️  Bibliography file not found (no citations detected in manuscript - this is fine)"
            )

        if failed_compilations:
            logger.error(f"\n❌ {len(failed_compilations)} PDF compilation(s) failed:")
            for pdf_file in failed_compilations:
                logger.error(f"  - {pdf_file.name} (0.0 KB - compilation failed)")

        if combined_pdf.exists():
            size_mb = combined_pdf.stat().st_size / (1024 * 1024)
            if size_mb > 0.01:
                if failed_compilations:
                    logger.warning(
                        f"\n⚠️  Combined manuscript PDF generated but {len(failed_compilations)} other PDF(s) failed to compile"
                    )
                else:
                    logger.info("\n✅ Combined manuscript PDF successfully generated!")
                logger.info(f"  File size: {size_mb:.2f} MB")
                logger.info(f"  Valid PDFs: {valid_pdfs}/{len(pdf_files)}")
            else:
                logger.error(f"\n❌ Combined manuscript PDF compilation failed ({size_mb:.3f} MB)")
                return False
        else:
            logger.error("\n❌ Combined manuscript PDF not found")
            return False

        return valid_pdfs > 0 and not failed_compilations
    else:
        logger.error("No PDF files found in output directory")
        return False
