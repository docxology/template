"""Output reporting utilities.

This module provides functions for generating output summaries and
collecting output statistics.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


def generate_output_summary(
    output_dir: Path, 
    stats: Dict[str, Any], 
    structure_validation: Optional[Dict[str, Any]] = None
) -> None:
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


def collect_output_statistics(repo_root: Path, project_name: str = "project") -> Dict[str, Any]:
    """Collect comprehensive output file statistics.

    Args:
        repo_root: Repository root path
        project_name: Name of the project (default: "project")

    Returns:
        Dictionary with comprehensive output statistics including:
        - File counts by category
        - File sizes by category
        - Largest files
        - Missing expected files
        - Total size and file count
    """
    output_dir = repo_root / "projects" / project_name / "output"
    
    stats = {
        'directories': {},
        'total_files': 0,
        'total_size_mb': 0.0,
        'largest_files': [],
        'missing_expected_files': [],
        'file_counts_by_type': {},
        'sizes_by_category': {}
    }
    
    # Expected output directories
    expected_dirs = ['pdf', 'web', 'slides', 'figures', 'data', 'reports', 'simulations', 'llm', 'logs']
    
    for dir_name in expected_dirs:
        subdir = output_dir / dir_name
        
        if subdir.exists() and subdir.is_dir():
            files = list(subdir.rglob('*'))
            files = [f for f in files if f.is_file()]
            
            # Calculate total size
            sizes = [(f.stat().st_size, f) for f in files]
            total_size = sum(size for size, _ in sizes)
            size_mb = total_size / (1024 * 1024)
            
            # Find largest files in this directory
            largest_in_dir = sorted(sizes, key=lambda x: x[0], reverse=True)[:3]
            largest_files_info = [{
                'name': f.name,
                'size_mb': f"{size / (1024 * 1024):.2f}",
                'path': str(f.relative_to(output_dir))
            } for size, f in largest_in_dir]
            
            # Count files by extension
            extensions = {}
            for f in files:
                ext = f.suffix.lower() or 'no_extension'
                extensions[ext] = extensions.get(ext, 0) + 1
            
            stats['directories'][dir_name] = {
                'exists': True,
                'file_count': len(files),
                'size_mb': f"{size_mb:.2f}",
                'total_size_bytes': total_size,
                'largest_files': largest_files_info,
                'extensions': extensions
            }
            
            stats['total_files'] += len(files)
            stats['total_size_mb'] += size_mb
            stats['sizes_by_category'][dir_name] = size_mb
            
            # Track all largest files across directories
            for size, f in largest_in_dir:
                stats['largest_files'].append({
                    'name': f.name,
                    'size_mb': f"{size / (1024 * 1024):.2f}",
                    'category': dir_name,
                    'path': str(f.relative_to(output_dir))
                })
        else:
            stats['directories'][dir_name] = {
                'exists': False,
                'file_count': 0,
                'size_mb': "0.00",
                'total_size_bytes': 0
            }
            stats['missing_expected_files'].append(f"{dir_name}/ directory")
    
    # Sort largest files by size
    stats['largest_files'] = sorted(
        stats['largest_files'], 
        key=lambda x: float(x['size_mb']), 
        reverse=True
    )[:10]  # Keep top 10
    
    # Check for expected combined PDF
    combined_pdf_found = False
    for pdf_name in [f"{project_name}_combined.pdf", "project_combined.pdf"]:
        pdf_path = output_dir / pdf_name
        if pdf_path.exists():
            combined_pdf_found = True
            break
    
    if not combined_pdf_found:
        stats['missing_expected_files'].append(f"{project_name}_combined.pdf or project_combined.pdf")
    
    # Add file type counts
    all_extensions = {}
    for dir_info in stats['directories'].values():
        if dir_info['exists']:
            for ext, count in dir_info.get('extensions', {}).items():
                all_extensions[ext] = all_extensions.get(ext, 0) + count
    stats['file_counts_by_type'] = all_extensions

    # Add simplified keys for backward compatibility with tests
    stats['pdf_files'] = stats['directories'].get('pdf', {}).get('file_count', 0)
    stats['figures'] = stats['directories'].get('figures', {}).get('file_count', 0)
    stats['data_files'] = stats['directories'].get('data', {}).get('file_count', 0)

    return stats


def generate_detailed_output_report(
    output_dir: Path,
    stats: Dict[str, Any]
) -> str:
    """Generate detailed output statistics report.
    
    Args:
        output_dir: Path to output directory
        stats: Output statistics dictionary
        
    Returns:
        Formatted report string
    """
    lines = [
        "",
        "OUTPUT STATISTICS REPORT",
        "=" * 60,
        "",
        f"Output Directory: {output_dir}",
        "",
        f"Total Files: {stats['total_files']}",
        f"Total Size: {stats['total_size_mb']:.2f} MB",
        "",
        "Files by Category:",
    ]
    
    for dir_name, dir_info in stats['directories'].items():
        if dir_info['exists'] and dir_info['file_count'] > 0:
            lines.append(f"  • {dir_name}: {dir_info['file_count']} files ({dir_info['size_mb']} MB)")
    
    if stats['largest_files']:
        lines.append("")
        lines.append("Largest Files:")
        for file_info in stats['largest_files'][:5]:
            lines.append(f"  • {file_info['name']}: {file_info['size_mb']} MB ({file_info['category']})")
    
    if stats['missing_expected_files']:
        lines.append("")
        lines.append("Missing Expected Files:")
        for missing in stats['missing_expected_files']:
            lines.append(f"  ⚠  {missing}")
    
    if stats['file_counts_by_type']:
        lines.append("")
        lines.append("File Types:")
        for ext, count in sorted(stats['file_counts_by_type'].items(), key=lambda x: x[1], reverse=True)[:10]:
            lines.append(f"  • {ext}: {count} file(s)")
    
    lines.append("")
    
    return "\n".join(lines)
















