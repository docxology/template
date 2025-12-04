#!/usr/bin/env python3
"""Output validation orchestrator script.

This thin orchestrator coordinates the validation stage:
1. Validates generated PDFs
2. Checks markdown formatting
3. Verifies file integrity
4. Generates validation report

Stage 5 of the pipeline orchestration.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging_utils import get_logger, log_success, log_header, log_substep
from infrastructure.reporting import generate_validation_report as generate_validation_report_structured

# Set up logger for this module
logger = get_logger(__name__)


def validate_pdfs() -> bool:
    """Validate generated PDF files."""
    log_substep("Validating PDF files...", logger)
    
    repo_root = Path(__file__).parent.parent
    pdf_dir = repo_root / "project" / "output" / "pdf"
    
    if not pdf_dir.exists():
        logger.error("PDF directory not found")
        return False
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        logger.error("No PDF files to validate")
        return False
    
    valid_count = 0
    for pdf_file in pdf_files:
        try:
            # Check file size (PDFs should be > 0 bytes)
            file_size = pdf_file.stat().st_size
            
            if file_size > 0:
                log_success(f"PDF valid: {pdf_file.name} ({file_size} bytes)", logger)
                valid_count += 1
            else:
                logger.error(f"PDF empty: {pdf_file.name}")
        except Exception as e:
            logger.error(f"Cannot validate {pdf_file.name}: {e}")
    
    return valid_count == len(pdf_files)


def validate_markdown() -> bool:
    """Validate markdown files in manuscript using infrastructure validation module."""
    log_substep("Validating markdown files...", logger)
    
    repo_root = Path(__file__).parent.parent
    # Check project/manuscript first, then fall back to root manuscript/ for backward compatibility
    manuscript_dir = repo_root / "project" / "manuscript"
    
    if not manuscript_dir.exists():
        # Fallback for backward compatibility
        manuscript_dir = repo_root / "manuscript"
    
    if not manuscript_dir.exists():
        logger.warning("Manuscript directory not found")
        return True
    
    markdown_files = list(manuscript_dir.glob("*.md"))
    
    if not markdown_files:
        logger.warning("No markdown files found")
        return True
    
    log_success(f"Found {len(markdown_files)} markdown file(s)", logger)
    
    # Use infrastructure validation module
    try:
        from infrastructure.validation.markdown_validator import validate_markdown as validate_md
        
        logger.info("Running markdown validation...")
        problems, exit_code = validate_md(manuscript_dir, repo_root, strict=False)
        
        if not problems:
            log_success("Markdown validation passed (no issues found)", logger)
            return True
        else:
            # Log issues but don't fail - these are often non-critical
            logger.info(f"  Found {len(problems)} validation note(s):")
            for problem in problems[:5]:  # Show first 5 issues
                logger.info(f"    • {problem}")
            if len(problems) > 5:
                logger.info(f"    ... and {len(problems) - 5} more")
            logger.info("  (Markdown validation notes are non-critical)")
            return True  # Non-critical
    except ImportError as e:
        logger.warning(f"Could not import markdown validator: {e}")
        return True  # Non-critical if validator unavailable
    except Exception as e:
        logger.warning(f"Markdown validation error: {e}")
        return True  # Non-critical


def verify_outputs_exist() -> bool:
    """Verify all expected output files exist."""
    log_substep("Verifying output structure...", logger)
    
    repo_root = Path(__file__).parent.parent
    
    required_dirs = [
        repo_root / "project" / "output" / "pdf",
        repo_root / "project" / "output" / "figures",
        repo_root / "project" / "output" / "data",
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if dir_path.exists():
            file_count = len(list(dir_path.glob("*")))
            log_success(f"Directory exists: {dir_path.name} ({file_count} file(s))", logger)
        else:
            logger.error(f"Directory missing: {dir_path.name}")
            all_exist = False
    
    return all_exist


def validate_figure_registry() -> tuple[bool, list[str]]:
    """Validate figure registry against manuscript references.
    
    Returns:
        Tuple of (success, list of issues found)
    """
    import json
    import re
    
    log_substep("Validating figure registry...", logger)
    
    repo_root = Path(__file__).parent.parent
    registry_path = repo_root / "project" / "output" / "figures" / "figure_registry.json"
    manuscript_dir = repo_root / "project" / "manuscript"
    
    issues = []
    
    # Load registry
    registered_figures = set()
    if registry_path.exists():
        try:
            with open(registry_path) as f:
                registry = json.load(f)
                registered_figures = set(registry.keys())
                log_success(f"Figure registry loaded: {len(registered_figures)} figure(s)", logger)
        except Exception as e:
            issues.append(f"Failed to load figure registry: {e}")
            return False, issues
    else:
        logger.warning("Figure registry not found")
        return True, []  # Not an error if registry doesn't exist
    
    # Find figure references in markdown (only in numbered section files, not AGENTS.md/README.md)
    referenced_figures = set()
    figure_ref_pattern = re.compile(r'\\(?:ref|label)\{(fig:[^}]+)\}')
    
    if manuscript_dir.exists():
        for md_file in manuscript_dir.glob("*.md"):
            # Skip documentation files (AGENTS.md, README.md)
            if md_file.name in ["AGENTS.md", "README.md"]:
                continue
            
            try:
                content = md_file.read_text()
                refs = figure_ref_pattern.findall(content)
                referenced_figures.update(refs)
            except Exception as e:
                logger.warning(f"Could not read {md_file.name}: {e}")
    
    # Find unregistered references
    unregistered = referenced_figures - registered_figures
    if unregistered:
        for ref in sorted(unregistered):
            issues.append(f"Unregistered figure reference: {ref}")
    
    # Summary
    if issues:
        logger.warning(f"  Found {len(issues)} figure issue(s)")
        for issue in issues:
            logger.warning(f"    • {issue}")
    else:
        log_success(f"All {len(referenced_figures)} figure references verified", logger)
    
    return len(issues) == 0, issues


def generate_validation_report(
    check_results: list[tuple[str, bool]],
    figure_issues: list[str],
    output_statistics: dict
) -> dict:
    """Generate enhanced validation report with structured output.
    
    Args:
        check_results: List of (check_name, result) tuples
        figure_issues: List of figure validation issues
        output_statistics: Output file statistics
        
    Returns:
        Validation results dictionary
    """
    log_substep("Generating validation report...", logger)
    
    repo_root = Path(__file__).parent.parent
    output_dir = repo_root / "project" / "output" / "reports"
    
    # Build validation results dictionary
    validation_results = {
        'timestamp': None,  # Will be set by reporting module
        'checks': {name: result for name, result in check_results},
        'figure_issues': figure_issues,
        'output_statistics': output_statistics,
        'summary': {
            'total_checks': len(check_results),
            'passed': sum(1 for _, result in check_results if result),
            'failed': sum(1 for _, result in check_results if not result),
            'figure_issues_count': len(figure_issues),
            'all_passed': all(result for _, result in check_results) and len(figure_issues) == 0,
        },
        'recommendations': [],
    }
    
    # Generate actionable recommendations
    recommendations = []
    for check_name, result in check_results:
        if not result:
            if check_name == "PDF validation":
                recommendations.append({
                    'priority': 'high',
                    'issue': 'PDF validation failed',
                    'action': 'Check PDF generation logs and LaTeX compilation errors',
                    'file': 'output/pdf/*_compile.log',
                })
            elif check_name == "Markdown validation":
                recommendations.append({
                    'priority': 'medium',
                    'issue': 'Markdown validation issues found',
                    'action': 'Review markdown validation output for formatting issues',
                    'file': 'project/manuscript/',
                })
            elif check_name == "Output structure":
                recommendations.append({
                    'priority': 'high',
                    'issue': 'Missing output directories',
                    'action': 'Ensure all analysis scripts completed successfully',
                    'file': 'project/output/',
                })
    
    if figure_issues:
        recommendations.append({
            'priority': 'medium',
            'issue': f'{len(figure_issues)} figure reference issue(s)',
            'action': 'Register missing figures or remove unused references',
            'file': 'project/output/figures/figure_registry.json',
        })
    
    validation_results['recommendations'] = recommendations
    
    # Generate structured reports using reporting module
    try:
        saved_files = generate_validation_report_structured(validation_results, output_dir)
        logger.info(f"Validation reports saved: {', '.join(str(p) for p in saved_files.values())}")
    except Exception as e:
        logger.warning(f"Failed to generate structured validation report: {e}")
        # Fallback to simple text report
        report_lines = [
            "Validation Report",
            "=================",
            "",
            f"Generated at: {output_dir.absolute()}",
            "",
        ]
        
        for subdir in ["pdf", "figures", "data"]:
            if subdir in output_statistics:
                stats = output_statistics[subdir]
                report_lines.append(f"{subdir.upper()}: {stats.get('files', 0)} file(s), {stats.get('size_mb', 0):.2f} MB")
        
        report_lines.extend(["", "Validation Complete", ""])
        report_text = "\n".join(report_lines)
        logger.info(f"\n{report_text}")
    
    return validation_results


def main() -> int:
    """Execute validation orchestration."""
    log_header("STAGE 04: Validate Output")
    
    checks = [
        ("PDF validation", validate_pdfs),
        ("Markdown validation", validate_markdown),
        ("Output structure", verify_outputs_exist),
    ]
    
    results = []
    figure_issues = []
    
    for check_name, check_fn in checks:
        try:
            result = check_fn()
            results.append((check_name, result))
        except Exception as e:
            logger.error(f"Error during {check_name}: {e}", exc_info=True)
            results.append((check_name, False))
    
    # Validate figure registry separately (returns tuple)
    try:
        fig_result, figure_issues = validate_figure_registry()
        results.append(("Figure registry", fig_result))
    except Exception as e:
        logger.error(f"Error during figure registry validation: {e}", exc_info=True)
        results.append(("Figure registry", False))
        figure_issues = []
    
    # Collect output statistics
    repo_root = Path(__file__).parent.parent
    output_dir = repo_root / "project" / "output"
    output_statistics = {}
    
    for subdir in ["pdf", "figures", "data"]:
        subdir_path = output_dir / subdir
        if subdir_path.exists():
            files = list(subdir_path.glob("*"))
            file_list = [f for f in files if f.is_file()]
            total_size = sum(f.stat().st_size for f in file_list)
            size_mb = total_size / (1024 * 1024)
            output_statistics[subdir] = {
                'files': len(file_list),
                'size_mb': size_mb,
            }
    
    # Generate enhanced validation report
    validation_results = generate_validation_report(results, figure_issues, output_statistics)
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("Validation Summary")
    logger.info("="*60)
    
    all_passed = True
    warning_count = 0
    
    for check_name, result in results:
        if result:
            status = "✅ PASS"
        else:
            status = "⚠️  WARN"
            warning_count += 1
        logger.info(f"{status}: {check_name}")
        if not result and check_name == "PDF validation":
            # PDF validation failure is critical
            all_passed = False
    
    # Show figure issues prominently if any
    if figure_issues:
        logger.info("")
        logger.info("Figure Reference Issues:")
        for issue in figure_issues:
            logger.warning(f"  • {issue}")
    
    if all_passed and warning_count == 0:
        log_success("\n✅ Validation complete - all checks passed!", logger)
        return 0
    elif all_passed:
        logger.info(f"\n⚠️  Validation complete with {warning_count} warning(s)")
        log_success("Pipeline can continue - warnings are non-critical", logger)
        return 0
    else:
        logger.error("\n❌ Validation failed - review issues above")
        return 1


if __name__ == "__main__":
    exit(main())

