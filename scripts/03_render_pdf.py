#!/usr/bin/env python3
"""PDF rendering orchestrator script.

This thin orchestrator coordinates the PDF rendering stage using the
infrastructure rendering module:
1. Discovers manuscript files
2. Uses RenderManager for multi-format rendering
3. Validates generated outputs
4. Reports rendering results

Stage 3 of the pipeline orchestration.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging_utils import get_logger, log_success, log_header
from infrastructure.core.progress import SubStageProgress
from infrastructure.core.exceptions import RenderingError, ValidationError
from infrastructure.rendering import RenderManager
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.manuscript_discovery import (
    discover_manuscript_files,
    verify_figures_exist,
)
from infrastructure.rendering.latex_package_validator import validate_preamble_packages

# Set up logger for this module
logger = get_logger(__name__)




def run_render_pipeline(project_name: str = "project") -> int:
    """Execute the PDF rendering pipeline using infrastructure rendering.
    
    This pipeline:
    1. Validates LaTeX packages (pre-flight check)
    2. Verifies figures from analysis stage
    3. Renders individual manuscript files to multiple formats
    4. Generates a combined PDF from all manuscript sections
    5. Reports on all generated outputs
    
    Args:
        project_name: Name of project in projects/ directory (default: "project")
    """
    logger.info(f"Executing PDF rendering pipeline for project '{project_name}'...")
    
    repo_root = Path(__file__).parent.parent
    project_root = repo_root / "projects" / project_name
    manuscript_dir = project_root / "manuscript"
    
    # Pre-flight: Validate LaTeX packages
    logger.info("Running pre-flight LaTeX package validation...")
    try:
        package_report = validate_preamble_packages(strict=False)
        
        if not package_report.all_required_available:
            logger.error("❌ Missing required LaTeX packages!")
            logger.error(f"   Missing: {', '.join(package_report.missing_required)}")
            logger.error(f"   Install: sudo tlmgr install {' '.join(package_report.missing_required)}")
            return 1
        
        if package_report.missing_optional:
            logger.warning(f"⚠️  Missing {len(package_report.missing_optional)} optional package(s):")
            for pkg in package_report.missing_optional:
                logger.warning(f"   - {pkg}")
            logger.warning("   PDF will render with reduced functionality")
            logger.info(f"   To install: sudo tlmgr install {' '.join(package_report.missing_optional)}")
        else:
            logger.info("✓ All LaTeX packages available")
            
    except ValidationError as e:
        logger.error(f"❌ LaTeX package validation failed: {e}")
        for suggestion in e.suggestions:
            logger.error(f"   {suggestion}")
        return 1
    except Exception as e:
        logger.warning(f"⚠️  Could not validate LaTeX packages: {e}")
        logger.warning("   Proceeding anyway - compilation may fail if packages are missing")
    
    # Verify figures from analysis stage
    logger.info("Verifying figures from analysis stage...")
    fig_status = verify_figures_exist(project_root, manuscript_dir)
    if fig_status["found_figures"]:
        logger.info(f"  Found figures: {', '.join(fig_status['found_figures'][:3])}")
        if len(fig_status["found_figures"]) > 3:
            logger.info(f"  ... and {len(fig_status['found_figures']) - 3} more")
    else:
        logger.warning("  ⚠️  No figures found - will render PDF with missing figures")
    
    # Discover files to render
    source_files = discover_manuscript_files(manuscript_dir)

    if not source_files:
        logger.warning("No manuscript files found")
        return 0

    # Log manuscript composition summary with file sizes
    logger.info("\n" + "="*60)
    logger.info(f"MANUSCRIPT COMPOSITION - Project: {project_name}")
    logger.info("="*60)

    md_files = [f for f in source_files if f.suffix == '.md']
    tex_files = [f for f in source_files if f.suffix == '.tex']

    if md_files:
        logger.info(f"Markdown sections ({len(md_files)}):")
        for f in md_files:
            size_kb = f.stat().st_size / 1024
            logger.info(f"  • {f.name:<40} ({size_kb:>6.1f} KB)")

        total_size_kb = sum(f.stat().st_size for f in md_files) / 1024
        logger.info(f"  {'Total markdown:':<40} ({total_size_kb:>6.1f} KB)")

    if tex_files:
        logger.info(f"LaTeX files ({len(tex_files)}):")
        for f in tex_files:
            size_kb = f.stat().st_size / 1024
            logger.info(f"  • {f.name:<40} ({size_kb:>6.1f} KB)")

    logger.info("="*60 + "\n")

    # Initialize render manager with absolute paths
    try:
        config = RenderingConfig(
            manuscript_dir=str(manuscript_dir),
            figures_dir=str(project_root / "output" / "figures"),
            output_dir=str(project_root / "output"),
            pdf_dir=str(project_root / "output" / "pdf"),
            web_dir=str(project_root / "output" / "web"),
            slides_dir=str(project_root / "output" / "slides"),
            poster_dir=str(project_root / "output" / "posters"),
        )
        figures_dir = project_root / "output" / "figures"
        manager = RenderManager(config, manuscript_dir=manuscript_dir, figures_dir=figures_dir)
        log_success("Initialized RenderManager from infrastructure.rendering", logger)
    except Exception as e:
        logger.error(f"Failed to initialize RenderManager: {e}")
        return 1
    
    # Separate markdown files (for combined PDF) from other files
    md_files = [f for f in source_files if f.suffix == '.md']
    other_files = [f for f in source_files if f.suffix != '.md']
    
    # Render individual files with progress tracking
    rendered_count = 0
    failed_files = []
    
    if source_files:
        progress = SubStageProgress(total=len(source_files), stage_name="Rendering Files")
        
        for i, source_file in enumerate(source_files, 1):
            progress.start_substage(i, source_file.name)
            
            try:
                # Use RenderManager to render in appropriate format
                outputs = manager.render_all(source_file)
                
                if outputs:
                    for output_path in outputs:
                        log_success(f"Generated: {output_path.name}", logger)
                    rendered_count += 1
                else:
                    logger.warning(f"  No output generated for {source_file.name}")
                    
            except RenderingError as re:
                logger.warning(f"  ❌ Rendering error for {source_file.name}: {re.message}")
                if re.context:
                    logger.debug(f"    Context: {re.context}")
                failed_files.append(source_file.name)
            except Exception as e:
                logger.warning(f"  ❌ Unexpected error rendering {source_file.name}: {e}")
                failed_files.append(source_file.name)
            
            progress.complete_substage()
    
    # Generate combined PDF from all markdown files
    if md_files:
        try:
            logger.info("\n" + "="*60)
            logger.info("Generating combined PDF manuscript...")
            combined_pdf = manager.render_combined_pdf(md_files, manuscript_dir, project_name)
            logger.info(f"✅ Generated combined PDF: {combined_pdf.name}")
            
        except RenderingError as re:
            logger.warning(f"❌ Rendering error generating combined PDF: {re.message}")
            if re.context:
                logger.debug(f"  Context: {re.context}")
            if re.suggestions:
                logger.info("  Suggestions:")
                for suggestion in re.suggestions:
                    logger.info(f"    • {suggestion}")
            # Don't fail the entire pipeline for combined PDF generation
        except Exception as e:
            logger.warning(f"❌ Unexpected error generating combined PDF: {e}")
            # Don't fail the entire pipeline for combined PDF generation
    
    # Report results
    logger.info(f"\nRendering Summary:")
    logger.info(f"  Individual files processed: {rendered_count}")
    logger.info(f"  Markdown files: {len(md_files)}")
    
    if failed_files:
        logger.warning(f"  Failed: {len(failed_files)} file(s)")
        for fname in failed_files:
            logger.warning(f"    - {fname}")

    # NEW: Generate and log comprehensive summary
    summary = generate_rendering_summary(project_name)
    log_rendering_summary(summary)

    log_success("PDF rendering pipeline completed", logger)
    return 0


def generate_rendering_summary(project_name: str = "project") -> dict:
    """Generate comprehensive summary of rendering results.

    Returns:
        Dictionary with rendering statistics and file information
    """
    repo_root = Path(__file__).parent.parent
    project_root = repo_root / "projects" / project_name
    output_dir = project_root / "output"

    summary = {
        "project": project_name,
        "individual_pdfs": [],
        "combined_pdf": None,
        "web_outputs": [],
        "slides": [],
        "total_size_kb": 0
    }

    # Collect individual PDFs
    pdf_dir = output_dir / "pdf"
    if pdf_dir.exists():
        for pdf in sorted(pdf_dir.glob("*.pdf")):
            if pdf.name != f"{project_name}_combined.pdf":
                size_kb = pdf.stat().st_size / 1024
                summary["individual_pdfs"].append({
                    "name": pdf.name,
                    "size_kb": size_kb
                })
                summary["total_size_kb"] += size_kb

    # Check combined PDF
    combined_pdf = pdf_dir / f"{project_name}_combined.pdf"
    if combined_pdf.exists():
        size_kb = combined_pdf.stat().st_size / 1024
        summary["combined_pdf"] = {
            "name": combined_pdf.name,
            "size_kb": size_kb,
            "path": str(combined_pdf)
        }
        summary["total_size_kb"] += size_kb

    # Collect web outputs
    web_dir = output_dir / "web"
    if web_dir.exists():
        for html in sorted(web_dir.glob("*.html")):
            size_kb = html.stat().st_size / 1024
            summary["web_outputs"].append({
                "name": html.name,
                "size_kb": size_kb
            })

    # Collect slides
    slides_dir = output_dir / "slides"
    if slides_dir.exists():
        for slide in sorted(slides_dir.glob("*.pdf")):
            size_kb = slide.stat().st_size / 1024
            summary["slides"].append({
                "name": slide.name,
                "size_kb": size_kb
            })

    return summary


def log_rendering_summary(summary: dict) -> None:
    """Log comprehensive rendering summary with formatted output."""
    logger.info("\n" + "="*60)
    logger.info("RENDERING RESULTS SUMMARY")
    logger.info("="*60)
    logger.info(f"Project: {summary['project']}")

    if summary['combined_pdf']:
        pdf = summary['combined_pdf']
        logger.info(f"\n📕 Combined Manuscript PDF:")
        logger.info(f"   {pdf['name']:<40} {pdf['size_kb']:>8.1f} KB")
        logger.info(f"   Location: {pdf['path']}")

    if summary['individual_pdfs']:
        logger.info(f"\n📄 Individual Section PDFs ({len(summary['individual_pdfs'])}):")
        for pdf in summary['individual_pdfs']:
            logger.info(f"   {pdf['name']:<40} {pdf['size_kb']:>8.1f} KB")

    if summary['web_outputs']:
        logger.info(f"\n🌐 Web Outputs ({len(summary['web_outputs'])}):")
        for web in summary['web_outputs']:
            logger.info(f"   {web['name']:<40} {web['size_kb']:>8.1f} KB")

    if summary['slides']:
        logger.info(f"\n📊 Presentation Slides ({len(summary['slides'])}):")
        for slide in summary['slides']:
            logger.info(f"   {slide['name']:<40} {slide['size_kb']:>8.1f} KB")

    logger.info(f"\n📦 Total Output Size: {summary['total_size_kb']:.1f} KB ({summary['total_size_kb']/1024:.2f} MB)")
    logger.info("="*60 + "\n")


def _check_citations_used(manuscript_dir: Path) -> bool:
    """Check if any manuscript files contain citation commands.

    Args:
        manuscript_dir: Directory containing manuscript files

    Returns:
        True if citations are found, False otherwise
    """
    import re

    # Common citation patterns in markdown/LaTeX
    citation_patterns = [
        r'\\cite\{[^}]+\}',     # \cite{key}
        r'\\citep\{[^}]+\}',    # \citep{key}
        r'\\citet\{[^}]+\}',    # \citet{key}
        r'\\citeauthor\{[^}]+\}', # \citeauthor{key}
        r'\\citeyear\{[^}]+\}', # \citeyear{key}
        r'@[^@\s]+\s',          # Pandoc citation syntax @key
    ]

    # Find all markdown files in manuscript directory
    manuscript_files = list(manuscript_dir.glob("*.md"))
    supplemental_dir = manuscript_dir / "supplemental"
    if supplemental_dir.exists():
        manuscript_files.extend(list(supplemental_dir.glob("*.md")))

    for md_file in manuscript_files:
        try:
            content = md_file.read_text(encoding='utf-8')
            for pattern in citation_patterns:
                if re.search(pattern, content):
                    return True
        except Exception as e:
            logger.debug(f"Could not read {md_file}: {e}")
            continue

    return False


def verify_pdf_outputs(project_name: str = "project") -> bool:
    """Verify that PDFs were generated with quality checks.
    
    Verifies:
    - PDF files exist
    - Combined manuscript PDF exists
    - PDFs have reasonable file size
    - Bibliography references are resolvable
    
    Args:
        project_name: Name of project in projects/ directory (default: "project")
    """
    logger.info("Verifying PDF outputs...")
    
    repo_root = Path(__file__).parent.parent
    project_root = repo_root / "projects" / project_name
    pdf_dir = project_root / "output" / "pdf"
    manuscript_dir = project_root / "manuscript"
    
    if not pdf_dir.exists():
        logger.error("PDF output directory not found")
        return False
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    combined_pdf = pdf_dir / f"{project_name}_combined.pdf"
    
    if pdf_files:
        log_success(f"Generated {len(pdf_files)} PDF file(s)", logger)
        
        # Check file sizes and validity
        valid_pdfs = 0
        failed_compilations = []

        for pdf_file in sorted(pdf_files):
            size_mb = pdf_file.stat().st_size / (1024 * 1024)
            size_kb = pdf_file.stat().st_size / 1024

            # Validate PDF is not empty
            if size_mb > 0.01:  # At least 10KB
                valid_pdfs += 1
                marker = "📕" if pdf_file == combined_pdf else "  "
                logger.info(f"  {marker} {pdf_file.name} ({size_mb:.2f} MB) ✓")
            else:
                # Enhanced detection of failed compilations
                marker = "📕" if pdf_file == combined_pdf else "  "
                status_msg = f"  {marker} {pdf_file.name}"

                if size_kb < 0.1:  # Less than 100 bytes - likely failed compilation
                    status_msg += f" - FAILED COMPILATION ({size_kb:.1f} KB)"
                    failed_compilations.append(pdf_file)

                    # Try to find and link to corresponding log file
                    log_file = pdf_file.parent / f"{pdf_file.stem}.log"
                    if log_file.exists():
                        status_msg += f" - Check log: {log_file.name}"
                    else:
                        # Try alternative log file patterns
                        alt_log = pdf_file.parent / f"_{pdf_file.stem}.log"
                        if alt_log.exists():
                            status_msg += f" - Check log: {alt_log.name}"

                    logger.error(status_msg)
                else:
                    # Small but not empty - might be a minimal document
                    status_msg += f" - file too small ({size_kb:.1f} KB)"
                    logger.warning(status_msg)
        
        # Check bibliography (only warn if citations are actually used)
        bib_file = manuscript_dir / "references.bib"
        citations_used = _check_citations_used(manuscript_dir)

        if bib_file.exists():
            logger.info("\n✅ Bibliography file found and will be processed")
        elif citations_used:
            logger.warning("\n⚠️  Bibliography file not found (citations detected in manuscript - bibliography processing will be skipped)")
        else:
            logger.info("\nℹ️  Bibliography file not found (no citations detected in manuscript - this is fine)")
        
        # Report failed compilations if any
        if failed_compilations:
            logger.error(f"\n❌ {len(failed_compilations)} PDF compilation(s) failed:")
            for pdf_file in failed_compilations:
                logger.error(f"  - {pdf_file.name} (0.0 KB - compilation failed)")

        # Check combined PDF specifically
        if combined_pdf.exists():
            size_mb = combined_pdf.stat().st_size / (1024 * 1024)
            if size_mb > 0.01:
                if failed_compilations:
                    logger.warning(f"\n⚠️  Combined manuscript PDF generated but {len(failed_compilations)} other PDF(s) failed to compile")
                else:
                    logger.info(f"\n✅ Combined manuscript PDF successfully generated!")
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


def main() -> int:
    """Execute PDF rendering orchestration."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Render PDF manuscript")
    parser.add_argument(
        '--project',
        default='project',
        help='Project name in projects/ directory (default: project)'
    )
    args = parser.parse_args()
    
    log_header(f"STAGE 03: Render PDF (Project: {args.project})", logger)
    
    # Log resource usage at start
    from infrastructure.core.logging_utils import log_resource_usage
    log_resource_usage("PDF rendering stage start", logger)
    
    try:
        # Run rendering pipeline
        exit_code = run_render_pipeline(args.project)
        
        if exit_code == 0:
            # Verify outputs
            outputs_valid = verify_pdf_outputs(args.project)
            
            if outputs_valid:
                log_success("PDF rendering complete - ready for validation", logger)
            else:
                logger.warning("PDF rendering completed but output verification failed")
        else:
            logger.error("PDF rendering failed - check logs for details")
        
        # Log resource usage at end
        log_resource_usage("PDF rendering stage end", logger)
        
        return exit_code
        
    except Exception as e:
        logger.error(f"Render pipeline error: {e}", exc_info=True)
        log_resource_usage("PDF rendering stage end (error)", logger)
        return 1


if __name__ == "__main__":
    exit(main())

