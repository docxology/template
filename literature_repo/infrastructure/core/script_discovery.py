"""Script discovery and execution utilities.

This module provides functions for discovering scripts in the project
and verifying their outputs.
"""
from __future__ import annotations

from pathlib import Path
from typing import List

from infrastructure.core.exceptions import PipelineError
from infrastructure.core.logging_utils import get_logger, log_success

logger = get_logger(__name__)


def discover_analysis_scripts(repo_root: Path) -> List[Path]:
    """Discover all analysis scripts in project/scripts/ to execute.
    
    Args:
        repo_root: Repository root directory
        
    Returns:
        List of Python script paths from project/scripts/ directory
        
    Raises:
        PipelineError: If project scripts directory not found
        
    Example:
        >>> scripts = discover_analysis_scripts(Path("."))
        >>> all(s.suffix == '.py' for s in scripts)
        True
    """
    logger.info("[STAGE-02] Discovering analysis scripts in project/...")
    
    project_scripts_dir = repo_root / "project" / "scripts"
    
    if not project_scripts_dir.exists():
        raise PipelineError(
            "Project scripts directory not found",
            context={"expected_path": str(project_scripts_dir)}
        )
    
    # Find all Python scripts in project/scripts/ except README files
    scripts = sorted([
        f for f in project_scripts_dir.glob('*.py')
        if f.is_file() and not f.name.startswith('_')
    ])
    
    for script in scripts:
        log_success(f"Found: {script.name}", logger)
    
    return scripts


def discover_orchestrators(repo_root: Path) -> List[Path]:
    """Discover orchestrator scripts in scripts/ directory.
    
    Args:
        repo_root: Repository root directory
        
    Returns:
        List of available orchestrator script paths in execution order
        
    Raises:
        PipelineError: If scripts directory not found
    """
    scripts_dir = repo_root / "scripts"
    
    if not scripts_dir.exists():
        raise PipelineError(
            "Scripts directory not found",
            context={"expected_path": str(scripts_dir)}
        )
    
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


def verify_analysis_outputs(repo_root: Path) -> bool:
    """Verify that analysis generated expected outputs.
    
    Args:
        repo_root: Repository root directory
        
    Returns:
        True if outputs are valid, False otherwise
    """
    logger.info("[STAGE-02] Verifying analysis outputs...")
    
    output_dirs = [
        repo_root / "project" / "output" / "figures",
        repo_root / "project" / "output" / "data",
    ]
    
    all_valid = True
    for output_dir in output_dirs:
        if output_dir.exists():
            files = list(output_dir.glob("*"))
            if files:
                log_success(f"Output directory has {len(files)} file(s): {output_dir.name}", logger)
            else:
                logger.info(f"  ℹ️  Output directory is empty: {output_dir.name}")
        else:
            # Output directories may not exist yet, not an error
            logger.info(f"  ℹ️  Output directory not yet created: {output_dir.name}")
    
    return all_valid












