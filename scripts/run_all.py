#!/usr/bin/env python3
"""Complete pipeline orchestrator - runs all stages in sequence.

This master orchestrator coordinates the entire build pipeline:
1. STAGE 00: Environment Setup - Prepare the environment
2. STAGE 01: Run Tests - Execute test suite with coverage
3. STAGE 02: Run Analysis - Execute analysis and figure generation
4. STAGE 03: Render PDF - Generate PDFs from markdown
5. STAGE 04: Validate Output - Validate all generated outputs
6. STAGE 05: Copy Outputs - Copy final deliverables to root output/

One-line execution for complete end-to-end build.

Architecture:
    This is a generic entry point orchestrator (Layer 1 - Infrastructure).
    It discovers and invokes all stage scripts without project-specific logic.
    Follows the thin orchestrator pattern - coordination only, no business logic.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging_utils import get_logger, log_header, log_success, log_timing
from infrastructure.core.exceptions import PipelineError

# Set up logger for this module
logger = get_logger(__name__)


def clean_output_directories() -> None:
    """Clean output directories for a fresh pipeline start.
    
    Removes all contents from both project/output/ and output/ directories,
    then recreates the expected subdirectory structure.
    
    This ensures each pipeline run starts with a clean state and all
    generated outputs are fresh.
    """
    repo_root = Path(__file__).parent.parent
    
    output_dirs = [
        repo_root / "project" / "output",
        repo_root / "output",
    ]
    
    subdirs = ["pdf", "figures", "data", "reports", "simulations", "slides", "web"]
    
    logger.info("\n[0/N] Clean Output Directories")
    logger.info("-" * 70)
    
    for output_dir in output_dirs:
        relative_path = output_dir.relative_to(repo_root)
        
        if output_dir.exists():
            logger.info(f"  Cleaning {relative_path}/...")
            # Remove all contents
            for item in output_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
        else:
            logger.info(f"  Creating {relative_path}/...")
        
        # Recreate subdirectory structure
        for subdir in subdirs:
            (output_dir / subdir).mkdir(parents=True, exist_ok=True)
        
        log_success(f"Cleaned {relative_path}/ (recreated subdirectories)", logger)
    
    log_success("Output directories cleaned - fresh start", logger)


def discover_orchestrators() -> list[Path]:
    """Discover orchestrator scripts in order.
    
    Returns:
        List of available orchestrator script paths in execution order
        
    Raises:
        PipelineError: If no orchestrators are found
        
    Example:
        >>> orchestrators = discover_orchestrators()
        >>> len(orchestrators)
        6
    """
    repo_root = Path(__file__).parent.parent
    scripts_dir = repo_root / "scripts"
    
    orchestrators = [
        scripts_dir / "00_setup_environment.py",
        scripts_dir / "01_run_tests.py",
        scripts_dir / "02_run_analysis.py",
        scripts_dir / "03_render_pdf.py",
        scripts_dir / "04_validate_output.py",
        scripts_dir / "05_copy_outputs.py",
    ]
    
    available = [s for s in orchestrators if s.exists()]
    
    if len(available) < len(orchestrators):
        missing = [s.name for s in orchestrators if s not in available]
        logger.warning(f"Some orchestrators not found: {', '.join(missing)}")
    
    return available


def run_stage(stage_script: Path, stage_num: int, total_stages: int) -> int:
    """Execute a single pipeline stage.
    
    Args:
        stage_script: Path to the stage script
        stage_num: Current stage number (1-based)
        total_stages: Total number of stages
        
    Returns:
        Exit code from the stage script (0=success, non-zero=failure)
        
    Example:
        >>> exit_code = run_stage(Path("00_setup_environment.py"), 1, 5)
        >>> exit_code
        0
    """
    stage_name = stage_script.stem.replace("_", " ").title()
    repo_root = Path(__file__).parent.parent
    
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


def run_pipeline(orchestrators: list[Path]) -> int:
    """Execute all pipeline stages in sequence.
    
    Args:
        orchestrators: List of orchestrator script paths to execute
        
    Returns:
        Exit code (0=all stages succeeded, 1=at least one stage failed)
        
    Raises:
        PipelineError: If no orchestrators provided
    """
    if not orchestrators:
        raise PipelineError("No orchestrators found", context={"scripts_dir": "scripts/"})
    
    log_header("COMPLETE PIPELINE ORCHESTRATION", logger)
    
    logger.info(f"\nFound {len(orchestrators)} stage(s) to execute:")
    for i, script in enumerate(orchestrators, 1):
        logger.info(f"  {i}. {script.name}")
    
    # Track execution
    stage_results = []
    start_time = time.time()
    
    # Execute each stage
    for i, stage_script in enumerate(orchestrators, 1):
        stage_start = time.time()
        exit_code = run_stage(stage_script, i, len(orchestrators))
        stage_duration = time.time() - stage_start
        
        stage_results.append({
            'name': stage_script.stem,
            'exit_code': exit_code,
            'duration': stage_duration,
        })
        
        if exit_code != 0:
            logger.error(f"Stage {i} failed - stopping pipeline")
            break
        else:
            log_success(f"Stage {i} completed ({stage_duration:.1f}s)", logger)
    
    # Generate summary
    total_duration = time.time() - start_time
    return_summary(stage_results, total_duration)
    
    # Return appropriate exit code
    if all(r['exit_code'] == 0 for r in stage_results):
        return 0
    else:
        return 1


def return_summary(results: list[dict], total_duration: float) -> None:
    """Generate and print pipeline summary.
    
    Args:
        results: List of stage results with name, exit_code, duration
        total_duration: Total pipeline execution time in seconds
    """
    log_header("PIPELINE SUMMARY", logger)
    
    logger.info(f"\nStages Executed: {len(results)}")
    logger.info(f"Total Time: {total_duration:.1f}s\n")
    
    for i, result in enumerate(results, 1):
        stage_name = result['name'].replace('_', ' ').title()
        exit_code = result['exit_code']
        duration = result['duration']
        
        if exit_code == 0:
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        logger.info(f"{status}: Stage {i:02d} - {stage_name} ({duration:.1f}s)")
    
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
    
    Returns:
        Exit code (0=success, 1=failure)
        
    Example:
        >>> exit_code = main()
        >>> sys.exit(exit_code)
    """
    logger.info("""
╔══════════════════════════════════════════════════════════════════════╗
║                   PROJECT BUILD PIPELINE                             ║
║                   End-to-End Orchestration                           ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Stage 0: Clean output directories for fresh start
        clean_output_directories()
        
        # Discover stages
        orchestrators = discover_orchestrators()
        
        if not orchestrators:
            raise PipelineError("No pipeline stages found")
        
        # Run pipeline
        exit_code = run_pipeline(orchestrators)
        
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
        logger.error(f"Pipeline error: {e}", exc_info=True)
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())

