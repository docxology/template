#!/usr/bin/env python3
"""Complete pipeline orchestrator - runs all stages in sequence.

This master orchestrator coordinates the core build pipeline (6 stages):
1. STAGE 00: Environment Setup - Prepare the environment
2. STAGE 01: Run Tests - Execute test suite with coverage
3. STAGE 02: Run Analysis - Execute analysis and figure generation
4. STAGE 03: Render PDF - Generate PDFs from markdown
5. STAGE 04: Validate Output - Validate all generated outputs
6. STAGE 05: Copy Outputs - Copy final deliverables to root output/

Note: This is the CORE pipeline (6 stages) for manuscript building. 
For the full pipeline with optional LLM review and translations (10 stages: 0-9), use ./run_manuscript.sh --pipeline.

One-line execution for complete end-to-end build.

Architecture:
    This is a generic entry point orchestrator (Layer 1 - Infrastructure).
    It discovers and invokes all stage scripts without project-specific logic.
    Follows the thin orchestrator pattern - coordination only, no business logic.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging_utils import (
    get_logger, log_header, log_success, log_timing, format_error_with_suggestions,
    log_stage_with_eta, format_duration, calculate_eta, log_resource_usage
)
from infrastructure.core.exceptions import PipelineError
from infrastructure.core.checkpoint import CheckpointManager, StageResult
from infrastructure.core.performance import PerformanceMonitor, get_system_resources
from infrastructure.core.script_discovery import discover_orchestrators
from infrastructure.core.file_operations import clean_output_directories
from infrastructure.reporting import (
    generate_pipeline_report,
    save_pipeline_report,
    generate_error_summary,
    collect_output_statistics,
)

# Set up logger for this module
logger = get_logger(__name__)


def clean_output_directories_stage(total_stages: int) -> float:
    """Clean output directories for a fresh pipeline start.
    
    Removes all contents from both project/output/ and output/ directories,
    then recreates the expected subdirectory structure.
    
    This ensures each pipeline run starts with a clean state and all
    generated outputs are fresh.
    
    Args:
        total_stages: Total number of stages for display
        
    Returns:
        Duration of the clean operation in seconds
    """
    start_time = time.time()
    repo_root = Path(__file__).parent.parent
    
    logger.info(f"\n[0/{total_stages}] Clean Output Directories")
    logger.info("-" * 70)
    
    clean_output_directories(repo_root)
    
    return time.time() - start_time


def run_stage(
    stage_script: Path, 
    stage_num: int, 
    total_stages: int,
    pipeline_start: Optional[float] = None
) -> int:
    """Execute a single pipeline stage.
    
    Args:
        stage_script: Path to the stage script
        stage_num: Current stage number (1-based)
        total_stages: Total number of stages
        pipeline_start: Pipeline start time for ETA calculation
        
    Returns:
        Exit code from the stage script (0=success, non-zero=failure)
        
    Example:
        >>> exit_code = run_stage(Path("00_setup_environment.py"), 1, 5)
        >>> exit_code
        0
    """
    stage_name = stage_script.stem.replace("_", " ").title()
    repo_root = Path(__file__).parent.parent
    
    # Use ETA-enabled stage logging if pipeline start time provided
    if pipeline_start is not None:
        log_stage_with_eta(stage_num, total_stages, stage_name, pipeline_start, logger)
    else:
        logger.info(f"\n[{stage_num}/{total_stages}] {stage_name}")
        logger.info("-" * 70)
    
    cmd = [sys.executable, str(stage_script)]
    
    try:
        with log_timing(f"Stage {stage_num}", logger):
            result = subprocess.run(
                cmd,
                cwd=str(repo_root),
                check=False
            )
        
        return result.returncode
    except Exception as e:
        logger.error(f"Failed to execute stage: {e}", exc_info=True)
        return 1


def run_pipeline(orchestrators: list[Path], clean_duration: float = 0.0, resume: bool = False) -> int:
    """Execute all pipeline stages in sequence.
    
    Args:
        orchestrators: List of orchestrator script paths to execute
        clean_duration: Duration of the clean stage (if already run)
        resume: Whether to resume from checkpoint if available
        
    Returns:
        Exit code (0=all stages succeeded, 1=at least one stage failed)
        
    Raises:
        PipelineError: If no orchestrators provided
    """
    if not orchestrators:
        raise PipelineError("No orchestrators found", context={"scripts_dir": "scripts/"})
    
    log_header("CORE PIPELINE ORCHESTRATION (6 stages)", logger)
    
    total_stages = len(orchestrators) + 1  # +1 for clean stage
    logger.info(f"\nFound {total_stages} stage(s) to execute (including clean):")
    logger.info("  0. Clean Output Directories")
    for i, script in enumerate(orchestrators, 1):
        logger.info(f"  {i}. {script.name}")
    logger.info("\nNote: This is the core pipeline. For full pipeline with LLM stages, use ./run_manuscript.sh --pipeline")
    
    # Initialize checkpoint manager
    checkpoint_manager = CheckpointManager()
    
    # Try to resume from checkpoint if requested
    start_stage = 0
    start_time = time.time()
    stage_results: list[dict] = []
    
    if resume:
        # Validate checkpoint before resuming
        is_valid, error_msg = checkpoint_manager.validate_checkpoint()
        if not is_valid:
            logger.error(f"Cannot resume from checkpoint: {error_msg}")
            logger.info("  Starting fresh pipeline instead")
            logger.info("  To clear checkpoint: rm -f project/output/.checkpoints/pipeline_checkpoint.json")
            resume = False
        
        if resume:
            checkpoint = checkpoint_manager.load_checkpoint()
            if checkpoint:
                logger.info(f"Resuming from checkpoint: stage {checkpoint.last_stage_completed}/{checkpoint.total_stages}")
                logger.info(f"  Pipeline started: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(checkpoint.pipeline_start_time))}")
                start_stage = checkpoint.last_stage_completed + 1
                start_time = checkpoint.pipeline_start_time
                # Convert StageResult objects back to dicts for compatibility
                stage_results = [
                    {
                        'name': sr.name,
                        'exit_code': sr.exit_code,
                        'duration': sr.duration,
                    }
                    for sr in checkpoint.stage_results
                ]
            else:
                logger.warning("Checkpoint file exists but could not be loaded")
                logger.info("  Starting fresh pipeline instead")
                resume = False
    
    # If not resuming, start fresh
    if not stage_results:
        stage_results = [{
            'name': 'clean_output_directories',
            'exit_code': 0,
            'duration': clean_duration,
        }]
    
    # Execute each stage starting from resume point
    for i, stage_script in enumerate(orchestrators, start_stage):
        if i == 0:
            continue  # Skip clean stage if resuming (already done)
        
        stage_start = time.time()
        # Log resource usage at stage start
        log_resource_usage(f"Stage {i} start", logger)
        
        exit_code = run_stage(stage_script, i, len(orchestrators), start_time)
        
        stage_duration = time.time() - stage_start
        # Log resource usage at stage end
        log_resource_usage(f"Stage {i} end", logger)
        
        # Collect resource usage metrics
        try:
            from infrastructure.core.performance import get_system_resources
            resources = get_system_resources()
            if resources:
                logger.debug(
                    f"Stage {i} resources: Memory: {resources.get('process_memory_mb', 0):.0f}MB, "
                    f"CPU: {resources.get('cpu_percent', 0):.1f}%"
                )
        except Exception:
            pass  # Resource monitoring optional
        
        # Create StageResult for checkpoint
        stage_result = StageResult(
            name=stage_script.stem,
            exit_code=exit_code,
            duration=stage_duration,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            completed=(exit_code == 0)
        )
        
        stage_results.append({
            'name': stage_script.stem,
            'exit_code': exit_code,
            'duration': stage_duration,
        })
        
        # Save checkpoint after each successful stage
        # Note: Test stage (01) returns exit_code=0 even with failures if they're within
        # tolerance configured via MAX_TEST_FAILURES, MAX_INFRA_TEST_FAILURES, or
        # MAX_PROJECT_TEST_FAILURES environment variables
        if exit_code == 0:
            checkpoint_manager.save_checkpoint(
                pipeline_start_time=start_time,
                last_stage_completed=i,
                stage_results=[StageResult(**sr) for sr in stage_results],
                total_stages=len(orchestrators)
            )
            log_success(f"Stage {i} completed ({stage_duration:.1f}s)", logger)
        else:
            logger.error(f"Stage {i} failed - stopping pipeline")
            logger.error(f"  To allow test failures, set MAX_TEST_FAILURES environment variable")
            break
    
    # Clear checkpoint on successful completion
    if all(r['exit_code'] == 0 for r in stage_results):
        checkpoint_manager.clear_checkpoint()
    
    # Generate summary
    total_duration = time.time() - start_time + clean_duration
    return_summary(stage_results, total_duration)
    
    # Generate consolidated pipeline report
    try:
        repo_root = Path(__file__).parent.parent
        output_dir = repo_root / "project" / "output" / "reports"
        
        # Load test results if available
        test_results = None
        test_report_path = output_dir / "test_results.json"
        if test_report_path.exists():
            import json
            with open(test_report_path) as f:
                test_results = json.load(f)
        
        # Collect performance metrics
        performance_metrics = {
            'total_duration': total_duration,
            'average_stage_duration': sum(r['duration'] for r in stage_results) / len(stage_results) if stage_results else 0,
            'system_resources': get_system_resources(),
        }
        
        # Collect errors if any
        errors = []
        for result in stage_results:
            if result['exit_code'] != 0:
                errors.append({
                    'type': 'stage_failure',
                    'stage': result['name'],
                    'message': f"Stage {result['name']} failed with exit code {result['exit_code']}",
                    'exit_code': result['exit_code'],
                })
        
        error_summary = None
        if errors:
            error_summary = generate_error_summary(errors, output_dir)
        
        # Collect output statistics
        output_statistics = collect_output_statistics(repo_root)
        
        # Generate pipeline report
        report = generate_pipeline_report(
            stage_results=stage_results,
            total_duration=total_duration,
            repo_root=repo_root,
            test_results=test_results,
            performance_metrics=performance_metrics,
            error_summary=error_summary,
            output_statistics=output_statistics,
        )
        
        # Save report in multiple formats
        saved_files = save_pipeline_report(report, output_dir, formats=['json', 'html', 'markdown'])
        logger.info(f"\nPipeline report saved: {', '.join(str(p) for p in saved_files.values())}")
        
    except Exception as e:
        logger.warning(f"Failed to generate pipeline report: {e}")
        # Don't fail pipeline if report generation fails
    
    # Return appropriate exit code
    if all(r['exit_code'] == 0 for r in stage_results):
        return 0
    else:
        return 1




def return_summary(results: list[dict], total_duration: float) -> None:
    """Generate and print pipeline summary with performance metrics.
    
    Args:
        results: List of stage results with name, exit_code, duration
        total_duration: Total pipeline execution time in seconds
    """
    log_header("PIPELINE SUMMARY", logger)
    
    logger.info(f"\nStages Executed: {len(results)}")
    logger.info(f"Total Time: {total_duration:.1f}s\n")
    
    # Calculate performance metrics
    durations = [r['duration'] for r in results if r['exit_code'] == 0]
    total_stage_time = sum(durations)
    avg_time = total_stage_time / len(durations) if durations else 0
    
    # Find slowest and fastest stages
    slowest_idx = 0
    slowest_duration = 0
    fastest_idx = 0
    fastest_duration = float('inf')
    
    for i, result in enumerate(results):
        if result['exit_code'] == 0:
            duration = result['duration']
            if duration > slowest_duration:
                slowest_duration = duration
                slowest_idx = i
            if duration < fastest_duration and i > 0:  # Skip clean stage
                fastest_duration = duration
                fastest_idx = i
    
    # Display stage results with percentages
    for i, result in enumerate(results):
        stage_name = result['name'].replace('_', ' ').title()
        exit_code = result['exit_code']
        duration = result['duration']
        percentage = (duration / total_duration * 100) if total_duration > 0 else 0
        
        if exit_code == 0:
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        # Highlight bottleneck
        bottleneck_marker = ""
        if i == slowest_idx and slowest_duration > 10:
            bottleneck_marker = " ⚠ bottleneck"
        
        # Stage 0 is clean, others are 1-indexed
        logger.info(f"{status}: Stage {i:02d} - {stage_name} ({duration:.1f}s, {percentage:.1f}%){bottleneck_marker}")
    
    # Performance metrics
    logger.info(f"\nPerformance Metrics:")
    logger.info(f"  Average Stage Time: {avg_time:.1f}s")
    if slowest_duration > 0:
        slowest_name = results[slowest_idx]['name'].replace('_', ' ').title()
        slowest_pct = (slowest_duration / total_duration * 100) if total_duration > 0 else 0
        logger.info(f"  Slowest Stage: Stage {slowest_idx:02d} - {slowest_name} ({slowest_duration:.1f}s, {slowest_pct:.1f}%)")
    if fastest_duration < float('inf') and fastest_idx > 0:
        fastest_name = results[fastest_idx]['name'].replace('_', ' ').title()
        logger.info(f"  Fastest Stage: Stage {fastest_idx:02d} - {fastest_name} ({fastest_duration:.1f}s)")
    
    # Final summary
    passed = sum(1 for r in results if r['exit_code'] == 0)
    total = len(results)
    
    logger.info(f"\nResult: {passed}/{total} stages completed successfully")
    
    if passed == total:
        log_success("PIPELINE COMPLETE - All stages successful!", logger)
    else:
        logger.error("PIPELINE FAILED - Fix issues and retry")


def main() -> int:
    """Execute complete pipeline orchestration.
    
    Supports --resume flag to resume from checkpoint.
    
    Returns:
        Exit code (0=success, 1=failure)
        
    Example:
        >>> exit_code = main()
        >>> sys.exit(exit_code)
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run complete pipeline orchestration")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume pipeline from last checkpoint (if available)"
    )
    args = parser.parse_args()
    
    logger.info("""
╔══════════════════════════════════════════════════════════════════════╗
║                   PROJECT BUILD PIPELINE                             ║
║                   End-to-End Orchestration                           ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Discover stages first to get total count
        repo_root = Path(__file__).parent.parent
        orchestrators = discover_orchestrators(repo_root)
        
        if not orchestrators:
            raise PipelineError("No pipeline stages found")
        
        total_stages = len(orchestrators) + 1  # +1 for clean stage
        
        # Stage 0: Clean output directories (skip if resuming)
        clean_duration = 0.0
        if not args.resume:
            clean_duration = clean_output_directories_stage(total_stages)
        else:
            logger.info("Resuming from checkpoint - skipping clean stage")
        
        # Run pipeline with clean duration and resume flag
        exit_code = run_pipeline(orchestrators, clean_duration, resume=args.resume)
        
        # Final exit
        if exit_code == 0:
            logger.info("\n" + "="*70)
            log_success("COMPLETE - Ready for deployment", logger)
            logger.info("="*70 + "\n")
        else:
            logger.info("\n" + "="*70)
            logger.error("INCOMPLETE - Fix issues and retry")
            logger.info("="*70 + "\n")
        
        return exit_code
        
    except PipelineError as e:
        logger.error(format_error_with_suggestions(e))
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())

