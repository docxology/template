#!/usr/bin/env python3
"""Environment setup orchestrator script.

This thin orchestrator prepares the environment for the complete project pipeline:
1. Verifies Python version and dependencies
2. Sets up directory structure
3. Configures environment variables
4. Validates build tools availability

Stage 1 of the pipeline orchestration.
"""
from __future__ import annotations

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Add infrastructure to path for logging
sys.path.insert(0, str(Path(__file__).parent.parent / "infrastructure"))

from logging_utils import get_logger, log_success, log_error, log_header

# Set up logger for this module
logger = get_logger(__name__)


def check_python_version() -> bool:
    """Verify Python 3.8+ is available."""
    logger.info("Checking Python version...")
    version_info = sys.version_info
    version_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
    
    if version_info.major < 3 or (version_info.major == 3 and version_info.minor < 8):
        logger.error(f"Python 3.8+ required, found {version_str}")
        return False
    
    log_success(f"Python {version_str} available", logger)
    return True


def check_dependencies() -> bool:
    """Verify required packages are installed, install if missing."""
    logger.info("Checking dependencies...")
    
    required_packages = [
        'numpy',
        'matplotlib',
        'pytest',
        'scipy',
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            log_success(f"Package '{package}' available", logger)
        except ImportError:
            logger.error(f"Package '{package}' not found")
            missing_packages.append(package)
    
    # If packages are missing, try to install them using uv
    if missing_packages:
        return install_missing_packages(missing_packages)
    
    return True


def install_missing_packages(packages: list[str]) -> bool:
    """Install missing packages using uv."""
    logger.info(f"Installing {len(packages)} missing package(s) with uv...")
    
    # Check if uv is available
    if not shutil.which('uv'):
        logger.error("uv package manager not found - cannot auto-install dependencies")
        logger.error("Install uv with: pip install uv")
        logger.error("Or install packages manually: pip install " + " ".join(packages))
        return False
    
    try:
        # Install all missing packages at once
        cmd = ['uv', 'pip', 'install'] + packages
        logger.info(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, check=False)
        
        if result.returncode == 0:
            # Verify installation
            logger.info("Verifying installation...")
            all_installed = True
            for package in packages:
                try:
                    __import__(package)
                    log_success(f"Package '{package}' installed successfully", logger)
                except ImportError:
                    logger.error(f"Package '{package}' installation failed")
                    all_installed = False
            
            return all_installed
        else:
            logger.error(f"uv installation failed (exit code: {result.returncode})")
            return False
    except Exception as e:
        logger.error(f"Failed to install packages: {e}", exc_info=True)
        return False


def check_build_tools() -> bool:
    """Verify build tools are available."""
    logger.info("Checking build tools...")
    
    tools = {
        'pandoc': 'Document conversion',
        'xelatex': 'LaTeX compilation',
    }
    
    all_present = True
    for tool, purpose in tools.items():
        if shutil.which(tool):
            log_success(f"'{tool}' available ({purpose})", logger)
        else:
            logger.error(f"'{tool}' not found ({purpose})")
            all_present = False
    
    return all_present


def setup_directories() -> bool:
    """Create required directory structure."""
    logger.info("Setting up directory structure...")
    
    repo_root = Path(__file__).parent.parent
    
    directories = [
        'output',
        'output/figures',
        'output/data',
        'output/tex',
        'output/pdf',
    ]
    
    try:
        for directory in directories:
            dir_path = repo_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            log_success(f"Directory ready: {directory}", logger)
        return True
    except Exception as e:
        logger.error(f"Failed to create directories: {e}", exc_info=True)
        return False


def verify_source_structure() -> bool:
    """Verify source code structure exists.
    
    Checks for the three core components of the repository architecture:
    - infrastructure/ - Generic reusable build tools
    - repo_utilities/ - Build orchestration scripts
    - project/ - Standalone research project
    """
    logger.info("Verifying source code structure...")
    
    repo_root = Path(__file__).parent.parent
    
    # Core components (required for template operation)
    required_dirs = [
        'infrastructure',      # Generic tools (build_verifier, figure_manager, etc.)
        'repo_utilities',      # Build scripts (render_pdf.sh, validate_markdown.py, etc.)
        'project',             # Standalone project with src/, tests/, scripts/, manuscript/
    ]
    
    optional_dirs = [
        'scripts',             # Optional: orchestration scripts (can be elsewhere)
        'tests',               # Optional: infrastructure tests
    ]
    
    all_present = True
    for directory in required_dirs:
        dir_path = repo_root / directory
        if dir_path.exists() and dir_path.is_dir():
            log_success(f"Directory found: {directory}", logger)
        else:
            logger.error(f"Directory not found: {directory}")
            all_present = False
    
    # Check optional directories
    for directory in optional_dirs:
        dir_path = repo_root / directory
        if dir_path.exists() and dir_path.is_dir():
            log_success(f"Directory found: {directory} (optional)", logger)
        else:
            logger.warning(f"Directory not found: {directory} (optional)")
    
    return all_present


def set_environment_variables() -> bool:
    """Configure environment variables for pipeline."""
    logger.info("Setting environment variables...")
    
    try:
        # Set matplotlib backend for headless operation
        os.environ['MPLBACKEND'] = 'Agg'
        log_success("MPLBACKEND=Agg", logger)
        
        # Ensure UTF-8 encoding
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        log_success("PYTHONIOENCODING=utf-8", logger)
        
        # Set project root in environment
        repo_root = Path(__file__).parent.parent
        os.environ['PROJECT_ROOT'] = str(repo_root)
        log_success(f"PROJECT_ROOT={repo_root}", logger)
        
        return True
    except Exception as e:
        logger.error(f"Failed to set environment variables: {e}", exc_info=True)
        return False


def main() -> int:
    """Execute environment setup orchestration."""
    log_header("STAGE 00: Environment Setup", logger)
    
    checks = [
        ("Python version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Build tools", check_build_tools),
        ("Directory structure", setup_directories),
        ("Source structure", verify_source_structure),
        ("Environment variables", set_environment_variables),
    ]
    
    results = []
    for check_name, check_fn in checks:
        try:
            result = check_fn()
            results.append((check_name, result))
        except Exception as e:
            log_error(f"Error during {check_name}: {e}")
            results.append((check_name, False))
    
    # Summary
    log_header("Setup Summary")
    
    all_passed = True
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {check_name}")
        if not result:
            all_passed = False
    
    if all_passed:
        log_success("\n✅ Environment setup complete - ready to proceed")
        return 0
    else:
        log_error("\n❌ Environment setup failed - fix issues and try again")
        return 1


if __name__ == "__main__":
    exit(main())

