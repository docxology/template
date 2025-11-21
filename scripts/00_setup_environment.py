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


def log_stage(message: str) -> None:
    """Log a stage message."""
    print(f"\n[STAGE-00] {message}")


def log_success(message: str) -> None:
    """Log a success message."""
    print(f"  ✅ {message}")


def log_error(message: str) -> None:
    """Log an error message."""
    print(f"  ❌ {message}")


def log_warning(message: str) -> None:
    """Log a warning message."""
    print(f"  ⚠️  {message}")


def check_python_version() -> bool:
    """Verify Python 3.8+ is available."""
    log_stage("Checking Python version...")
    version_info = sys.version_info
    version_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
    
    if version_info.major < 3 or (version_info.major == 3 and version_info.minor < 8):
        log_error(f"Python 3.8+ required, found {version_str}")
        return False
    
    log_success(f"Python {version_str} available")
    return True


def check_dependencies() -> bool:
    """Verify required packages are installed, install if missing."""
    log_stage("Checking dependencies...")
    
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
            log_success(f"Package '{package}' available")
        except ImportError:
            log_error(f"Package '{package}' not found")
            missing_packages.append(package)
    
    # If packages are missing, try to install them using uv
    if missing_packages:
        return install_missing_packages(missing_packages)
    
    return True


def install_missing_packages(packages: list[str]) -> bool:
    """Install missing packages using uv."""
    log_stage(f"Installing {len(packages)} missing package(s) with uv...")
    
    # Check if uv is available
    if not shutil.which('uv'):
        log_error("uv package manager not found - cannot auto-install dependencies")
        log_error("Install uv with: pip install uv")
        log_error("Or install packages manually: pip install " + " ".join(packages))
        return False
    
    try:
        # Install all missing packages at once
        cmd = ['uv', 'pip', 'install'] + packages
        print(f"\n  Running: {' '.join(cmd)}\n")
        
        result = subprocess.run(cmd, check=False)
        
        if result.returncode == 0:
            # Verify installation
            log_stage("Verifying installation...")
            all_installed = True
            for package in packages:
                try:
                    __import__(package)
                    log_success(f"Package '{package}' installed successfully")
                except ImportError:
                    log_error(f"Package '{package}' installation failed")
                    all_installed = False
            
            return all_installed
        else:
            log_error(f"uv installation failed (exit code: {result.returncode})")
            return False
    except Exception as e:
        log_error(f"Failed to install packages: {e}")
        return False


def check_build_tools() -> bool:
    """Verify build tools are available."""
    log_stage("Checking build tools...")
    
    tools = {
        'pandoc': 'Document conversion',
        'xelatex': 'LaTeX compilation',
    }
    
    all_present = True
    for tool, purpose in tools.items():
        if shutil.which(tool):
            log_success(f"'{tool}' available ({purpose})")
        else:
            log_error(f"'{tool}' not found ({purpose})")
            all_present = False
    
    return all_present


def setup_directories() -> bool:
    """Create required directory structure."""
    log_stage("Setting up directory structure...")
    
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
            log_success(f"Directory ready: {directory}")
        return True
    except Exception as e:
        log_error(f"Failed to create directories: {e}")
        return False


def verify_source_structure() -> bool:
    """Verify source code structure exists."""
    log_stage("Verifying source code structure...")
    
    repo_root = Path(__file__).parent.parent
    
    required_dirs = [
        'src',
        'tests',
        'repo_utilities',
    ]
    
    optional_dirs = [
        'manuscript',
    ]
    
    all_present = True
    for directory in required_dirs:
        dir_path = repo_root / directory
        if dir_path.exists() and dir_path.is_dir():
            log_success(f"Directory found: {directory}")
        else:
            log_error(f"Directory not found: {directory}")
            all_present = False
    
    # Check optional directories
    for directory in optional_dirs:
        dir_path = repo_root / directory
        if dir_path.exists() and dir_path.is_dir():
            log_success(f"Directory found: {directory} (optional)")
        else:
            log_warning(f"Directory not found: {directory} (optional)")
    
    return all_present


def set_environment_variables() -> bool:
    """Configure environment variables for pipeline."""
    log_stage("Setting environment variables...")
    
    try:
        # Set matplotlib backend for headless operation
        os.environ['MPLBACKEND'] = 'Agg'
        log_success("MPLBACKEND=Agg")
        
        # Ensure UTF-8 encoding
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        log_success("PYTHONIOENCODING=utf-8")
        
        # Set project root in environment
        repo_root = Path(__file__).parent.parent
        os.environ['PROJECT_ROOT'] = str(repo_root)
        log_success(f"PROJECT_ROOT={repo_root}")
        
        return True
    except Exception as e:
        log_error(f"Failed to set environment variables: {e}")
        return False


def main() -> int:
    """Execute environment setup orchestration."""
    print("\n" + "="*60)
    print("STAGE 00: Environment Setup")
    print("="*60)
    
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
    print("\n" + "="*60)
    print("Setup Summary")
    print("="*60)
    
    all_passed = True
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {check_name}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n✅ Environment setup complete - ready to proceed")
        return 0
    else:
        print("\n❌ Environment setup failed - fix issues and try again")
        return 1


if __name__ == "__main__":
    exit(main())

