"""Environment setup and validation utilities.

This module provides comprehensive environment validation and setup for the research template.
It handles dependency checking, build tool validation, directory structure creation, and
provides robust uv package manager integration with graceful fallback mechanisms.

Key Features:
- uv package manager integration with automatic fallback to pip
- Comprehensive dependency validation with missing package detection
- Build tool availability checking (pandoc, xelatex, etc.)
- Directory structure setup for multi-project workflows
- Environment variable configuration for headless operation
- Post-setup validation functions for reliability verification

uv Integration:
The module prioritizes uv for dependency management due to its speed and reliability.
When uv is available, it uses 'uv sync' for workspace dependency management.
When uv is unavailable, it falls back to individual package installation via pip.
All uv operations include proper error handling and informative logging.

Usage Patterns:
    # Check system readiness
    python_ok = check_python_version()
    deps_ok, missing = check_dependencies()
    tools_ok = check_build_tools()

    # Setup environment
    dirs_ok = setup_directories(repo_root, "my_project")
    env_ok = set_environment_variables(repo_root)

    # Validate setup (with new functions)
    sync_ok, msg = validate_uv_sync_result(repo_root)
    missing_dirs = validate_directory_structure(repo_root, "my_project")
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
    """Install missing packages using uv with fallback to pip.

    Attempts to install packages using uv package manager for speed and reliability.
    If uv is not available, provides guidance for manual installation.

    The function uses 'uv add' to properly manage dependencies through pyproject.toml,
    then runs 'uv sync' to install all dependencies. This ensures consistent
    dependency resolution and lock file generation.

    Args:
        packages: List of package names to install

    Returns:
        True if installation successful, False otherwise

    Example:
        >>> success = install_missing_packages(['numpy', 'matplotlib'])
        >>> if success:
        ...     print("Packages installed successfully")
        ... else:
        ...     print("Installation failed - check uv availability")
    """
    logger.info(f"Installing {len(packages)} missing package(s) with uv...")
    
    # Check if uv is available
    if not shutil.which('uv'):
        logger.error("uv package manager not found - cannot auto-install dependencies")
        logger.error("Install uv with: pip install uv")
        logger.error("Or install packages manually: pip install " + " ".join(packages))
        return False
    
    try:
        # Use uv add to properly manage dependencies through pyproject.toml
        # First add to pyproject.toml, then sync
        for package in packages:
            add_cmd = ['uv', 'add', package]
            logger.info(f"Adding to pyproject.toml: {' '.join(add_cmd)}")
            add_result = subprocess.run(add_cmd, check=False, capture_output=True, text=True)
            if add_result.returncode != 0:
                logger.warning(f"Failed to add {package} to pyproject.toml: {add_result.stderr}")

        # Then sync to install all dependencies
        cmd = ['uv', 'sync']
        logger.info(f"Syncing dependencies: {' '.join(cmd)}")

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


def setup_directories(repo_root: Path, project_name: str = "project", directories: List[str] | None = None) -> bool:
    """Create required directory structure.

    Args:
        repo_root: Repository root directory
        project_name: Name of project in projects/ directory (default: "project")
        directories: List of directory paths to create (relative to repo_root).
                    If None, uses default directories.

    Returns:
        True if all directories created successfully, False otherwise
    """
    logger.info("Setting up directory structure...")

    if directories is None:
        # For multi-project, create both repo-level and project-level directories
        directories = [
            f'output/{project_name}',
            f'output/{project_name}/figures',
            f'output/{project_name}/data',
            f'output/{project_name}/tex',
            f'output/{project_name}/pdf',
            f'output/{project_name}/logs',
            f'output/{project_name}/reports',
            f'output/{project_name}/simulations',
            f'output/{project_name}/slides',
            f'output/{project_name}/web',
            f'output/{project_name}/llm',
            f'projects/{project_name}/output',
            f'projects/{project_name}/output/figures',
            f'projects/{project_name}/output/data',
            f'projects/{project_name}/output/pdf',
            f'projects/{project_name}/output/tex',
            f'projects/{project_name}/output/logs',
            f'projects/{project_name}/output/reports',
            f'projects/{project_name}/output/simulations',
            f'projects/{project_name}/output/slides',
            f'projects/{project_name}/output/web',
            f'projects/{project_name}/output/llm',
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


def check_uv_available() -> bool:
    """Check if uv package manager is available and working.

    Tests uv availability by running 'uv --version' command. uv is a fast
    Python package manager that provides reliable dependency resolution and
    virtual environment management.

    Returns:
        True if uv is available and functional, False otherwise

    Example:
        >>> if check_uv_available():
        ...     print("Using uv for fast dependency management")
        ... else:
        ...     print("Falling back to pip - consider installing uv")
    """
    try:
        result = subprocess.run(['uv', '--version'], capture_output=True, text=True, check=False)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.SubprocessError):
        return False


def get_python_command() -> list[str]:
    """Get the appropriate Python command for subprocess execution.

    Returns the optimal Python command based on available tools:
    - ['uv', 'run', 'python'] if uv is available (preferred for managed environments)
    - [sys.executable] otherwise (uses current Python interpreter)

    This ensures consistent Python execution across different environments and
    respects uv-managed virtual environments when available.

    Returns:
        List of command arguments suitable for subprocess.run()

    Example:
        >>> cmd = get_python_command()
        >>> result = subprocess.run(cmd + ['-c', 'print("hello")'], ...)
    """
    if check_uv_available():
        return ['uv', 'run', 'python']
    else:
        return [sys.executable]


def verify_source_structure(repo_root: Path, project_name: str = "project") -> bool:
    """Verify source code structure exists.

    For multi-project template, checks:
    - infrastructure/ - Generic reusable build tools
    - projects/{name}/ - Specified project structure

    Args:
        repo_root: Repository root directory
        project_name: Name of project in projects/ directory (default: "project")

    Returns:
        True if required directories exist, False otherwise
    """
    logger.info("Verifying source code structure...")

    # Core components (required for template operation)
    required_dirs = [
        'infrastructure',      # Generic tools (build_verifier, figure_manager, etc.)
        f'projects/{project_name}',  # Project directory
        f'projects/{project_name}/src',     # Source code
        f'projects/{project_name}/tests',   # Tests
    ]

    optional_dirs = [
        'scripts',             # Optional: orchestration scripts
        'tests',               # Optional: infrastructure tests
        f'projects/{project_name}/scripts',   # Optional: project scripts
        f'projects/{project_name}/manuscript', # Optional: manuscript
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

    Sets critical environment variables needed for the research template pipeline:
    - MPLBACKEND=Agg: Ensures matplotlib runs in headless mode for server environments
    - PYTHONIOENCODING=utf-8: Ensures consistent text encoding across platforms
    - PROJECT_ROOT: Points to repository root for relative path calculations

    Args:
        repo_root: Repository root directory

    Returns:
        True if environment variables set successfully, False otherwise

    Example:
        >>> from pathlib import Path
        >>> repo_root = Path("/path/to/template")
        >>> success = set_environment_variables(repo_root)
        >>> assert success is True
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


def validate_uv_sync_result(repo_root: Path) -> tuple[bool, str]:
    """Validate that uv sync completed successfully.

    Checks for the presence of expected artifacts after a uv sync operation:
    - .venv/ directory: Virtual environment created
    - uv.lock file: Dependency lock file generated

    Args:
        repo_root: Repository root directory where uv sync was run

    Returns:
        Tuple of (success: bool, message: str) describing validation result

    Example:
        >>> success, msg = validate_uv_sync_result(Path("."))
        >>> if success:
        ...     print("uv sync completed successfully")
        ... else:
        ...     print(f"uv sync validation failed: {msg}")
    """
    # Check for .venv directory
    venv_path = repo_root / ".venv"
    if not venv_path.exists():
        return False, "Virtual environment not created"

    # Check for uv.lock file
    lock_file = repo_root / "uv.lock"
    if not lock_file.exists():
        return False, "Lock file not generated"

    return True, "uv sync completed successfully"


def validate_directory_structure(repo_root: Path, project_name: str = "project") -> list[str]:
    """Validate that required directory structure exists.

    Checks for the presence of all directories created by setup_directories().
    This is useful for post-setup validation to ensure the environment is ready.

    Args:
        repo_root: Repository root directory
        project_name: Name of project in projects/ directory (default: "project")

    Returns:
        List of missing directory paths (empty list if all directories exist)

    Example:
        >>> missing = validate_directory_structure(Path("."), "my_project")
        >>> if missing:
        ...     print(f"Missing directories: {missing}")
        ... else:
        ...     print("All directories present")
    """
    required_dirs = [
        f'output/{project_name}',
        f'output/{project_name}/figures',
        f'output/{project_name}/data',
        f'output/{project_name}/tex',
        f'output/{project_name}/pdf',
        f'output/{project_name}/logs',
        f'output/{project_name}/reports',
        f'output/{project_name}/simulations',
        f'output/{project_name}/slides',
        f'output/{project_name}/web',
        f'output/{project_name}/llm',
        f'projects/{project_name}/output',
        f'projects/{project_name}/output/figures',
        f'projects/{project_name}/output/data',
        f'projects/{project_name}/output/pdf',
        f'projects/{project_name}/output/tex',
        f'projects/{project_name}/output/logs',
        f'projects/{project_name}/output/reports',
        f'projects/{project_name}/output/simulations',
        f'projects/{project_name}/output/slides',
        f'projects/{project_name}/output/web',
        f'projects/{project_name}/output/llm',
    ]

    missing = []
    for dir_path in required_dirs:
        full_path = repo_root / dir_path
        if not full_path.exists() or not full_path.is_dir():
            missing.append(dir_path)

    return missing
















