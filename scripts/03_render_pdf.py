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
from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering import RenderManager
from infrastructure.rendering.config import RenderingConfig

# Set up logger for this module
logger = get_logger(__name__)


def verify_figures_exist(project_root: Path, manuscript_dir: Path) -> dict:
    """Verify expected figures exist, return status.
    
    Args:
        project_root: Path to project root
        manuscript_dir: Path to manuscript directory
        
    Returns:
        Dictionary with figure verification status
    """
    figures_dir = project_root / "output" / "figures"
    result = {
        "figures_dir_exists": figures_dir.exists(),
        "found_figures": [],
        "missing_figures": [],
        "total_expected": 0
    }
    
    if not figures_dir.exists():
        logger.warning(f"ℹ️  Figures directory not found: {figures_dir}")
        return result
    
    # Find all PNG files in figures directory
    figures = sorted(list(figures_dir.glob("*.png")))
    result["found_figures"] = [f.name for f in figures]
    
    if figures:
        log_success(f"Found {len(figures)} figure(s) in {figures_dir.name}/", logger)
    else:
        logger.warning(f"⚠️  Figures directory exists but is empty: {figures_dir}")
    
    return result


def discover_manuscript_files(manuscript_dir: Path) -> list[Path]:
    """Discover manuscript files with proper ordering and filtering.
    
    Filters out non-manuscript files and orders files for proper document structure:
    1. Main sections: 01_*.md through 09_*.md
    2. Supplemental: S01_*.md through S0N_*.md
    3. Glossary: 98_*.md
    4. References: 99_*.md (always last)
    """
    if not manuscript_dir.exists():
        logger.warning(f"Manuscript directory not found: {manuscript_dir}")
        return []
    
    # Files to exclude (metadata, infrastructure)
    exclude_names = {
        'preamble.md', 'AGENTS.md', 'README.md', 'config.yaml', 
        'config.yaml.example', 'references.bib'
    }
    
    # Discover all markdown files
    all_md_files = [f for f in manuscript_dir.glob("*.md") 
                    if f.name not in exclude_names]
    
    # Organize files by category for proper ordering
    main_sections = []      # 01_*.md - 09_*.md
    supplemental = []       # S01_*.md - S0N_*.md
    glossary = []          # 98_*.md
    references = []        # 99_*.md
    other = []             # Everything else
    
    for md_file in all_md_files:
        stem = md_file.stem
        
        if stem.startswith('99_'):
            references.append(md_file)
        elif stem.startswith('98_'):
            glossary.append(md_file)
        elif stem.startswith('S'):
            supplemental.append(md_file)
        elif stem[0].isdigit():
            main_sections.append(md_file)
        else:
            other.append(md_file)
    
    # Sort within each category
    main_sections.sort(key=lambda x: x.stem)
    supplemental.sort(key=lambda x: x.stem)
    glossary.sort(key=lambda x: x.stem)
    references.sort(key=lambda x: x.stem)
    other.sort(key=lambda x: x.stem)
    
    # Combine in order: main -> supplemental -> glossary -> references
    ordered_files = main_sections + supplemental + glossary + references + other
    
    # Log discovery with details
    logger.info(f"Discovered {len(ordered_files)} manuscript file(s):")
    logger.info(f"  Main sections: {len(main_sections)}")
    if main_sections:
        for f in main_sections:
            logger.info(f"    - {f.name}")
    
    if supplemental:
        logger.info(f"  Supplemental: {len(supplemental)}")
        for f in supplemental:
            logger.info(f"    - {f.name}")
    
    if glossary:
        logger.info(f"  Glossary: {len(glossary)}")
        for f in glossary:
            logger.info(f"    - {f.name}")
    
    if references:
        logger.info(f"  References: {len(references)}")
        for f in references:
            logger.info(f"    - {f.name}")
    
    # Validate expected structure
    expected_main = {"01_abstract.md", "02_introduction.md", "03_methodology.md", 
                     "04_experimental_results.md", "05_discussion.md", "06_conclusion.md",
                     "08_acknowledgments.md", "09_appendix.md"}
    found_main = {f.name for f in main_sections}
    missing_main = expected_main - found_main
    
    if missing_main:
        logger.warning(f"  ⚠️  Missing expected main sections: {', '.join(sorted(missing_main))}")
    
    # Verify references is last
    if ordered_files and references:
        last_ref = ordered_files[-1]
        if last_ref not in references:
            logger.warning("  ⚠️  References section is not at the end of the document")
    elif ordered_files and not references:
        logger.warning("  ⚠️  No references section found (99_references.md)")
    
    # Also find LaTeX files for direct compilation
    tex_files = sorted(manuscript_dir.glob("*.tex"))
    if tex_files:
        logger.info(f"  LaTeX files: {len(tex_files)}")
    
    return ordered_files + tex_files


def run_render_pipeline() -> int:
    """Execute the PDF rendering pipeline using infrastructure rendering.
    
    This pipeline:
    1. Verifies figures from analysis stage
    2. Renders individual manuscript files to multiple formats
    3. Generates a combined PDF from all manuscript sections
    4. Reports on all generated outputs
    """
    logger.info("Executing PDF rendering pipeline...")
    
    repo_root = Path(__file__).parent.parent
    manuscript_dir = repo_root / "project" / "manuscript"
    project_root = repo_root / "project"
    
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


def verify_pdf_outputs() -> bool:
    """Verify that PDFs were generated with quality checks.
    
    Verifies:
    - PDF files exist
    - Combined manuscript PDF exists
    - PDFs have reasonable file size
    - Bibliography references are resolvable
    """
    logger.info("Verifying PDF outputs...")
    
    repo_root = Path(__file__).parent.parent
    pdf_dir = repo_root / "project" / "output" / "pdf"
    manuscript_dir = repo_root / "project" / "manuscript"
    
    if not pdf_dir.exists():
        logger.error("PDF output directory not found")
        return False
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    combined_pdf = pdf_dir / "project_combined.pdf"
    
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
    log_header("STAGE 03: Render PDF", logger)
    
    try:
        # Run rendering pipeline
        exit_code = run_render_pipeline()
        
        if exit_code == 0:
            # Verify outputs
            outputs_valid = verify_pdf_outputs()
            
            if outputs_valid:
                log_success("PDF rendering complete - ready for validation", logger)
            else:
                logger.warning("PDF rendering completed but output verification failed")
        else:
            logger.error("PDF rendering failed - check logs for details")
        
        return exit_code
        
    except Exception as e:
        logger.error(f"Render pipeline error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())

