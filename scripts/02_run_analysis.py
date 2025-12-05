#!/usr/bin/env python3
"""Analysis and figure generation orchestrator script.

This thin orchestrator coordinates the analysis and figure generation stage:
1. Discovers all analysis scripts in project/scripts/
2. Executes them in order
3. Collects generated outputs from project/output/
4. Validates output quality

**Entry Point 3:** Generic orchestrator for template
- Works with any project by looking in project/scripts/
- Does NOT implement analysis logic
- Delegates to project-specific scripts

Stage 3 of the pipeline orchestration.

Architecture:
    This is a generic entry point (Layer 1 - Infrastructure).
    It discovers and executes project-specific scripts from project/scripts/
    without knowing their implementation details. Follows thin orchestrator pattern.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging_utils import get_logger, log_operation, log_success, log_progress, format_error_with_suggestions
from infrastructure.core.progress import SubStageProgress
from infrastructure.core.exceptions import ScriptExecutionError, PipelineError
from infrastructure.core.script_discovery import (
    discover_analysis_scripts,
    verify_analysis_outputs,
)

# Set up logger for this module
logger = get_logger(__name__)


def run_analysis_script(script_path: Path, repo_root: Path) -> int:
    """Execute a single analysis script.
    
    Args:
        script_path: Path to the script to execute
        repo_root: Repository root directory
        
    Returns:
        Exit code from script execution
        
    Raises:
        ScriptExecutionError: If script execution fails critically
    """
    logger.info(f"\n  Running: {script_path.name}")
    
    cmd = [sys.executable, str(script_path)]
    
    project_root = repo_root / "project"
    
    try:
        with log_operation(f"Execute {script_path.name}", logger):
            result = subprocess.run(
                cmd,
                cwd=str(project_root),
                capture_output=False,
                check=False
            )
        
        if result.returncode != 0:
            logger.error(f"Script failed: {script_path.name} (exit code: {result.returncode})")
            logger.info(f"  Troubleshooting:")
            logger.info(f"    - Run script manually: python3 {script_path}")
            logger.info(f"    - Check script syntax: python3 -m py_compile {script_path}")
            logger.info(f"    - Verify dependencies: Check imports in {script_path.name}")
            logger.info(f"    - Review script logs above for specific error details")
        
        return result.returncode
    except Exception as e:
        raise ScriptExecutionError(
            f"Failed to execute {script_path.name}",
            context={"script": str(script_path), "error": str(e)}
        ) from e


def run_analysis_pipeline(scripts: list[Path]) -> int:
    """Execute all analysis scripts in sequence.
    
    Args:
        scripts: List of script paths to execute
        
    Returns:
        Exit code (0=success, non-zero=at least one script failed)
    """
    logger.info("[STAGE-02] Executing analysis pipeline...")
    
    repo_root = Path(__file__).parent.parent
    
    if not scripts:
        logger.info("  No analysis scripts found - skipping stage")
        return 0
    
    successful_scripts = []
    failed_scripts = []
    
    # Use sub-stage progress tracking with EMA for better ETA
    progress = SubStageProgress(
        total=len(scripts),
        stage_name="Analysis Pipeline",
        use_ema=True
    )
    
    for i, script in enumerate(scripts, 1):
        progress.start_substage(i, script.name)
        exit_code = run_analysis_script(script, repo_root)
        progress.complete_substage()
        
        # Log progress with ETA every few scripts
        if i % 2 == 0 or i == len(scripts):
            progress.log_progress()

        if exit_code == 0:
            successful_scripts.append(script.name)
        else:
            failed_scripts.append(script.name)

    # Consolidated success message
    if successful_scripts:
        script_list = ", ".join(successful_scripts)
        log_success(f"Analysis scripts completed: {len(successful_scripts)}/{len(scripts)} ({script_list})", logger)

    if failed_scripts:
        logger.error(f"\n{len(failed_scripts)} script(s) failed:")
        for script_name in failed_scripts:
            logger.error(f"  Failed: {script_name}")
        logger.info(f"\n  Troubleshooting:")
        logger.info(f"    - Review error messages above for each failed script")
        logger.info(f"    - Run scripts individually to isolate issues")
        logger.info(f"    - Check script dependencies and imports")
        logger.info(f"    - Verify input data files exist if required")
        return 1

    return 0




def main() -> int:
    """Execute analysis orchestration.
    
    Returns:
        Exit code (0=success, 1=failure)
    """
    logger.info("\n" + "="*60)
    logger.info("STAGE 02: Run Analysis")
    logger.info("="*60)
    
    # Log resource usage at start
    from infrastructure.core.logging_utils import log_resource_usage
    log_resource_usage("Analysis stage start", logger)
    
    try:
        repo_root = Path(__file__).parent.parent
        
        # Discover scripts
        scripts = discover_analysis_scripts(repo_root)
        
        if not scripts:
            logger.info("  No analysis scripts found - skipping stage")
            return 0
        
        # Run analysis pipeline
        exit_code = run_analysis_pipeline(scripts)
        
        if exit_code == 0:
            # Verify outputs
            outputs_valid = verify_analysis_outputs(repo_root)
            
            if outputs_valid:
                log_success("Analysis complete - ready for PDF rendering", logger)
            else:
                logger.warning("\nAnalysis complete but output verification failed")
        else:
            logger.error("\nAnalysis failed - fix issues and try again")
        
        # Log resource usage at end
        log_resource_usage("Analysis stage end", logger)
        
        return exit_code
        
    except (ScriptExecutionError, PipelineError) as e:
        logger.error(format_error_with_suggestions(e))
        log_resource_usage("Analysis stage end (error)", logger)
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        log_resource_usage("Analysis stage end (error)", logger)
        return 1


if __name__ == "__main__":
    exit(main())

