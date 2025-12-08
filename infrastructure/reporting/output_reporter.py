"""Output reporting utilities.

This module provides functions for generating output summaries and
collecting output statistics.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


def generate_output_summary(output_dir: Path, stats: Dict, structure_validation: Dict | None = None) -> None:
    """Generate summary of output copying results.
    
    Args:
        output_dir: Path to output directory
        stats: Dictionary with copy statistics
        structure_validation: Optional validation results dict
    """
    logger.info("\n" + "="*60)
    logger.info("Output Copying Summary")
    logger.info("="*60)
    
    logger.info(f"\nOutput directory: {output_dir}")
    logger.info(f"\nFiles copied by directory:")
    logger.info(f"  • PDF files: {stats['pdf_files']}")
    logger.info(f"  • Web files: {stats['web_files']}")
    logger.info(f"  • Slides files: {stats['slides_files']}")
    logger.info(f"  • Figures: {stats['figures_files']}")
    logger.info(f"  • Data files: {stats['data_files']}")
    logger.info(f"  • Reports: {stats['reports_files']}")
    logger.info(f"  • Simulations: {stats['simulations_files']}")
    logger.info(f"  • LLM reviews: {stats['llm_files']}")
    logger.info(f"  • Log files: {stats['logs_files']}")
    logger.info(f"  • Combined PDF (root): {stats['combined_pdf']}")
    logger.info(f"\n  Total files copied: {stats['total_files']}")
    
    # Include structure validation if provided
    if structure_validation:
        logger.info(f"\nDirectory structure:")
        for item, info in structure_validation.get("directory_structure", {}).items():
            if info.get("exists"):
                if "size_mb" in info and "files" in info:
                    logger.info(f"  ✓ {item}: {info['files']} files, {info['size_mb']} MB")
                elif "size_mb" in info:
                    logger.info(f"  ✓ {item}: {info['size_mb']} MB")
                elif "files" in info:
                    logger.info(f"  ✓ {item}: {info['files']} files")
            else:
                logger.info(f"  ✗ {item}: Not found")
    
    if stats["errors"]:
        logger.info(f"\nWarnings/Errors ({len(stats['errors'])}):")
        for error in stats["errors"]:
            logger.warning(f"  • {error}")
    
    logger.info("")


def collect_output_statistics(repo_root: Path) -> Dict:
    """Collect output file statistics.
    
    Args:
        repo_root: Repository root path
        
    Returns:
        Dictionary with output statistics
    """
    output_dir = repo_root / "project" / "output"
    stats = {
        'pdf_files': 0,
        'figures': 0,
        'data_files': 0,
        'total_size_mb': 0.0,
    }
    
    if output_dir.exists():
        pdf_dir = output_dir / "pdf"
        if pdf_dir.exists():
            pdf_files = list(pdf_dir.glob("*.pdf"))
            stats['pdf_files'] = len(pdf_files)
            stats['total_size_mb'] += sum(f.stat().st_size for f in pdf_files) / (1024 * 1024)
        
        figures_dir = output_dir / "figures"
        if figures_dir.exists():
            figure_files = list(figures_dir.glob("*.png")) + list(figures_dir.glob("*.pdf"))
            stats['figures'] = len(figure_files)
            stats['total_size_mb'] += sum(f.stat().st_size for f in figure_files) / (1024 * 1024)
        
        data_dir = output_dir / "data"
        if data_dir.exists():
            data_files = list(data_dir.glob("*"))
            stats['data_files'] = len([f for f in data_files if f.is_file()])
            stats['total_size_mb'] += sum(f.stat().st_size for f in data_files if f.is_file()) / (1024 * 1024)
    
    return stats



