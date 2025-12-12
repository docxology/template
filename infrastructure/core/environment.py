"""Environment setup and validation utilities.

This module provides functions for checking system requirements, dependencies,
build tools, and setting up the project environment.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

from infrastructure.core.logging_utils import get_logger, log_success

logger = get_logger(__name__)


def check_python_version() -> bool:
    """Verify Python 3.8+ is available.
    
    Returns:
        True if Python version is 3.8 or higher, False otherwise
    """
    logger.info("Checking Python version...")
    version_info = sys.version_info
    version_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
    
    if version_info.major < 3 or (version_info.major == 3 and version_info.minor < 8):
        logger.error(f"Python 3.8+ required, found {version_str}")
        return False
    
    log_success(f"Python {version_str} available", logger)
    return True


def check_dependencies(required_packages: List[str] | None = None) -> Tuple[bool, List[str]]:
    """Verify required packages are installed.
    
    Args:
        required_packages: List of package names to check. If None, uses default list.
        
    Returns:
        Tuple of (all_present, missing_packages)
    """
    logger.info("Checking dependencies...")
    
    if required_packages is None:
        # Core required packages (must be present)
        required_packages = [
            'numpy',
            'matplotlib',
            'pytest',
            'requests',
        ]
        # Optional packages (nice to have but not critical)
        optional_packages = ['scipy']
    else:
        optional_packages = []
    
    missing_packages = []
    optional_missing = []
    
    for package in required_packages:
        try:
            __import__(package)
            log_success(f"Package '{package}' available", logger)
        except ImportError:
            logger.error(f"Package '{package}' not found")
            missing_packages.append(package)
    
    # Check optional packages - warn but don't fail
    for package in optional_packages:
        try:
            __import__(package)
            log_success(f"Package '{package}' available", logger)
        except ImportError:
            logger.warning(f"Package '{package}' not found (optional)")
            optional_missing.append(package)
    
    if optional_missing:
        logger.info(f"Optional packages missing: {', '.join(optional_missing)}")
        logger.info("These are not critical but recommended for full functionality")
    
    return len(missing_packages) == 0, missing_packages


def install_missing_packages(packages: List[str]) -> bool:
    """Install missing packages using uv.
    
    Args:
        packages: List of package names to install
        
    Returns:
        True if installation successful, False otherwise
    """
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


def check_build_tools(required_tools: dict[str, str] | None = None) -> bool:
    """Verify build tools are available.
    
    Args:
        required_tools: Dictionary mapping tool names to descriptions.
                       If None, uses default tools.
        
    Returns:
        True if all tools are available, False otherwise
    """
    logger.info("Checking build tools...")
    
    if required_tools is None:
        required_tools = {
            'pandoc': 'Document conversion',
            'xelatex': 'LaTeX compilation',
        }
    
    all_present = True
    for tool, purpose in required_tools.items():
        if shutil.which(tool):
            log_success(f"'{tool}' available ({purpose})", logger)
        else:
            logger.error(f"'{tool}' not found ({purpose})")
            all_present = False
    
    return all_present


def setup_directories(repo_root: Path, directories: List[str] | None = None) -> bool:
    """Create required directory structure.
    
    Args:
        repo_root: Repository root directory
        directories: List of directory paths to create (relative to repo_root).
                    If None, uses default directories.
        
    Returns:
        True if all directories created successfully, False otherwise
    """
    logger.info("Setting up directory structure...")
    
    if directories is None:
        directories = [
            'output',
            'output/figures',
            'output/data',
            'output/tex',
            'output/pdf',
            'output/logs',
            'project/output',
            'project/output/logs',
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


def verify_source_structure(repo_root: Path) -> bool:
    """Verify source code structure exists.
    
    Checks for the core components of the repository architecture:
    - infrastructure/ - Generic reusable build tools
    - project/ - Standalone research project
    
    Args:
        repo_root: Repository root directory
        
    Returns:
        True if required directories exist, False otherwise
    """
    logger.info("Verifying source code structure...")
    
    # Core components (required for template operation)
    required_dirs = [
        'infrastructure',      # Generic tools (build_verifier, figure_manager, etc.)
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


def set_environment_variables(repo_root: Path) -> bool:
    """Configure environment variables for pipeline.
    
    Args:
        repo_root: Repository root directory
        
    Returns:
        True if environment variables set successfully, False otherwise
    """
    logger.info("Setting environment variables...")
    
    try:
        # Set matplotlib backend for headless operation
        os.environ['MPLBACKEND'] = 'Agg'
        log_success("MPLBACKEND=Agg", logger)
        
        # Ensure UTF-8 encoding
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        log_success("PYTHONIOENCODING=utf-8", logger)
        
        # Set project root in environment
        os.environ['PROJECT_ROOT'] = str(repo_root)
        log_success(f"PROJECT_ROOT={repo_root}", logger)
        
        return True
    except Exception as e:
        logger.error(f"Failed to set environment variables: {e}", exc_info=True)
        return False












