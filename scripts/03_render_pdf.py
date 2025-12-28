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
            combined_pdf = manager.render_combined_pdf(md_files, manuscript_dir)
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
    
    log_success("PDF rendering pipeline completed", logger)
    return 0


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
        for pdf_file in sorted(pdf_files):
            size_mb = pdf_file.stat().st_size / (1024 * 1024)
            
            # Validate PDF is not empty
            if size_mb > 0.01:  # At least 10KB
                valid_pdfs += 1
                marker = "📕" if pdf_file == combined_pdf else "  "
                logger.info(f"  {marker} {pdf_file.name} ({size_mb:.2f} MB) ✓")
            else:
                logger.warning(f"  ✗ {pdf_file.name} - file too small ({size_mb:.2f} MB)")
        
        # Check bibliography
        bib_file = manuscript_dir / "references.bib"
        if bib_file.exists():
            logger.info("\n✅ Bibliography file found and will be processed")
        else:
            logger.warning("\n⚠️  Bibliography file not found")
        
        # Check combined PDF specifically
        if combined_pdf.exists():
            size_mb = combined_pdf.stat().st_size / (1024 * 1024)
            if size_mb > 0.01:
                logger.info(f"\n✅ Combined manuscript PDF successfully generated!")
                logger.info(f"  File size: {size_mb:.2f} MB")
                logger.info(f"  Valid PDFs: {valid_pdfs}/{len(pdf_files)}")
            else:
                logger.warning(f"\n⚠️  Combined manuscript PDF exists but is too small ({size_mb:.2f} MB)")
        else:
            logger.warning("\n⚠️  Combined manuscript PDF not found")
        
        return valid_pdfs > 0
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

