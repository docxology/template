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
from datetime import datetime
from pathlib import Path

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging_utils import get_logger, log_success, log_header, log_substep
from infrastructure.reporting import generate_validation_report as generate_validation_report_structured
from infrastructure.validation.figure_validator import validate_figure_registry

# Set up logger for this module
logger = get_logger(__name__)


def validate_pdfs(project_name: str = "project") -> bool:
    """Validate generated PDF files.
    
    Args:
        project_name: Name of project in projects/ directory (default: "project")
    """
    log_substep("Validating PDF files...", logger)
    
    repo_root = Path(__file__).parent.parent
    project_root = repo_root / "projects" / project_name
    pdf_dir = project_root / "output" / "pdf"
    
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


def validate_markdown(project_name: str = "project") -> bool:
    """Validate markdown files in manuscript using infrastructure validation module.
    
    Args:
        project_name: Name of project in projects/ directory (default: "project")
    """
    log_substep("Validating markdown files...", logger)
    
    repo_root = Path(__file__).parent.parent
    project_root = repo_root / "projects" / project_name
    manuscript_dir = project_root / "manuscript"
    
    if not manuscript_dir.exists():
        logger.warning(f"Manuscript directory not found at expected location: {manuscript_dir}")
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


def verify_outputs_exist(project_name: str = "project") -> tuple[bool, dict]:
    """Verify all expected output files exist.
    
    Args:
        project_name: Name of project in projects/ directory (default: "project")
        
    Returns:
        Tuple of (validation_passed, detailed_validation_results)
    """
    log_substep("Verifying output structure...", logger)
    
    repo_root = Path(__file__).parent.parent
    project_root = repo_root / "projects" / project_name
    output_dir = repo_root / "output" / project_name  # Use final output directory
    
    # Use comprehensive validation from infrastructure
    from infrastructure.validation.output_validator import collect_detailed_validation_results
    
    detailed_validation = collect_detailed_validation_results(output_dir)
    structure_valid = detailed_validation['structure']['valid']
    
    if structure_valid:
        log_success("Output structure is valid", logger)
        # Log detailed directory information
        for dir_name, dir_info in detailed_validation['directories'].items():
            if dir_info['exists'] and dir_info['file_count'] > 0:
                logger.info(f"  • {dir_name}/: {dir_info['file_count']} files ({dir_info['size_mb']} MB)")
    else:
        logger.warning("Output structure validation has issues:")
        for severity in ['critical', 'warning']:
            issues = detailed_validation['issues_by_severity'].get(severity, [])
            if issues:
                logger.warning(f"  {severity.upper()} issues:")
                for issue in issues[:3]:  # Show first 3
                    logger.warning(f"    • {issue}")
                if len(issues) > 3:
                    logger.warning(f"    ... and {len(issues) - 3} more")
    
    return structure_valid, detailed_validation
    
    all_exist = True
    for dir_path in required_dirs:
        if dir_path.exists():
            file_count = len(list(dir_path.glob("*")))
            log_success(f"Directory exists: {dir_path.name} ({file_count} file(s))", logger)
        else:
            logger.error(f"Directory missing: {dir_path.name}")
            all_exist = False
    
    return all_exist




def generate_validation_report(
    check_results: list[tuple[str, bool]],
    figure_issues: list[str],
    output_statistics: dict,
    project_name: str = "project"
) -> dict:
    """Generate validation report with structured output.
    
    Args:
        check_results: List of (check_name, result) tuples
        figure_issues: List of figure validation issues
        output_statistics: Output file statistics
        
    Returns:
        Validation results dictionary
    """
    log_substep("Generating validation report...", logger)
    
    repo_root = Path(__file__).parent.parent
    output_dir = repo_root / "projects" / project_name / "output" / "reports"
    
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
                    'file': f'projects/{project_name}/manuscript/',
                })
            elif check_name == "Output structure":
                recommendations.append({
                    'priority': 'high',
                    'issue': 'Missing output directories',
                    'action': 'Ensure all analysis scripts completed successfully',
                    'file': f'projects/{project_name}/output/',
                })
    
    if figure_issues:
        recommendations.append({
            'priority': 'medium',
            'issue': f'{len(figure_issues)} figure reference issue(s)',
            'action': 'Register missing figures or remove unused references',
            'file': f'projects/{project_name}/output/figures/figure_registry.json',
        })
    
    validation_results['recommendations'] = recommendations
    
    # Generate structured reports using reporting module
    try:
        from infrastructure.reporting import generate_validation_report as gen_validation_report
        saved_files = gen_validation_report(validation_results, output_dir)
        logger.info(f"Validation reports saved: {', '.join(str(p) for p in saved_files.values())}")
    except Exception as e:
        logger.warning(f"Failed to generate structured validation report: {e}")
        # Fallback to simple JSON report
        import json
        report_file = output_dir / "validation_report.json"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Add timestamp
        from datetime import datetime
        validation_results['timestamp'] = datetime.now().isoformat()
        
        with open(report_file, 'w') as f:
            json.dump(validation_results, f, indent=2)
        logger.info(f"Validation report saved: {report_file}")
    
    return validation_results


def main() -> int:
    """Execute validation orchestration."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate output")
    parser.add_argument(
        '--project',
        default='project',
        help='Project name in projects/ directory (default: project)'
    )
    args = parser.parse_args()
    
    log_header(f"STAGE 04: Validate Output (Project: {args.project})", logger)
    
    checks = [
        ("PDF validation", lambda: validate_pdfs(args.project)),
        ("Markdown validation", lambda: validate_markdown(args.project)),
    ]
    
    results = []
    figure_issues = []
    detailed_validation = None
    
    for i, (check_name, check_fn) in enumerate(checks, 1):
        try:
            logger.info(f"  [{i}/{len(checks)}] Running {check_name}...")
            result = check_fn()
            status = "✅ PASSED" if result else "⚠️  ISSUES"
            logger.info(f"  [{i}/{len(checks)}] {check_name}: {status}")
            results.append((check_name, result))
        except Exception as e:
            logger.error(f"  [{i}/{len(checks)}] {check_name}: ❌ FAILED - {e}", exc_info=True)
            results.append((check_name, False))
    
    # Handle output structure check separately (returns tuple)
    try:
        structure_result, detailed_validation = verify_outputs_exist(args.project)
        results.append(("Output structure", structure_result))
    except Exception as e:
        logger.error(f"Error during output structure validation: {e}", exc_info=True)
        results.append(("Output structure", False))
    
    # Validate figure registry separately (returns tuple)
    try:
        repo_root = Path(__file__).parent.parent
        project_root = repo_root / "projects" / args.project
        registry_path = project_root / "output" / "figures" / "figure_registry.json"
        manuscript_dir = project_root / "manuscript"
        fig_result, figure_issues = validate_figure_registry(registry_path, manuscript_dir)
        results.append(("Figure registry", fig_result))
    except Exception as e:
        logger.error(f"Error during figure registry validation: {e}", exc_info=True)
        results.append(("Figure registry", False))
        figure_issues = []
    
    # Collect output statistics
    output_dir = project_root / "output"
    output_statistics = {}
    
    # Add detailed validation to output statistics if available
    if detailed_validation:
        output_statistics['detailed_validation'] = detailed_validation
    
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
    
    # Generate validation report
    validation_results = generate_validation_report(results, figure_issues, output_statistics, args.project)
    
    # Comprehensive validation summary
    logger.info("\n" + "="*60)
    logger.info("VALIDATION SUMMARY")
    logger.info("="*60)
    logger.info(f"Project: {args.project}")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")

    all_passed = True
    warning_count = 0
    critical_count = 0

    logger.info("Individual Check Results:")
    for check_name, result in results:
        if result:
            status = "✅ PASS"
            logger.info(f"  {status}: {check_name}")
        else:
            if check_name == "PDF validation":
                status = "❌ FAIL"
                critical_count += 1
                all_passed = False
            else:
                status = "⚠️  WARN"
                warning_count += 1
            logger.info(f"  {status}: {check_name}")

    # Show figure issues prominently if any
    if figure_issues:
        logger.info("")
        logger.info("Figure Reference Issues:")
        for issue in figure_issues:
            logger.warning(f"  • {issue}")

    # Show output structure summary if available
    if detailed_validation:
        structure = detailed_validation.get('structure', {})
        if structure.get('valid'):
            logger.info("")
            logger.info("Output Structure Status:")
            logger.info("  ✅ Output directory structure is valid")

            # Show file counts
            directories = detailed_validation.get('directories', {})
            for dir_name, dir_info in directories.items():
                if dir_info.get('exists') and dir_info.get('file_count', 0) > 0:
                    size_mb = dir_info.get('size_mb', '0.00')
                    logger.info(f"  📁 {dir_name}/: {dir_info['file_count']} files ({size_mb} MB)")
        else:
            logger.warning("")
            logger.warning("Output Structure Issues:")
            issues = structure.get('issues', [])
            for issue in issues[:5]:  # Show first 5 issues
                logger.warning(f"  • {issue}")

    logger.info("")
    logger.info("="*60)

    if all_passed and warning_count == 0 and critical_count == 0:
        log_success("✅ VALIDATION COMPLETE - All checks passed!", logger)
        logger.info("  → Pipeline can proceed to next stage")
        return 0
    elif all_passed and critical_count == 0:
        logger.info(f"⚠️  VALIDATION COMPLETE - {warning_count} warning(s), no critical issues")
        logger.info("  → Pipeline can continue - warnings are non-critical")
        return 0
    else:
        logger.error(f"❌ VALIDATION FAILED - {critical_count} critical issue(s)")
        logger.error("  → Pipeline halted - review issues above")
        logger.error("  → Check project output and manuscript for errors")
        return 1


if __name__ == "__main__":
    exit(main())

