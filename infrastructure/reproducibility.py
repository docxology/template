"""Reproducibility tools for ensuring deterministic and verifiable research results.

This module provides utilities for:
- Version tracking and dependency management
- Deterministic random number generation
- Build verification and validation
- Environment capture and restoration
- Result verification and comparison

All functions follow the thin orchestrator pattern and maintain
100% test coverage requirements.
"""

from __future__ import annotations

import os
import sys
import json
import hashlib
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import pickle
import shutil


class ReproducibilityReport:
    """Container for reproducibility analysis results."""

    def __init__(self):
        self.environment_hash: str = ""
        self.dependency_hash: str = ""
        self.code_hash: str = ""
        self.data_hash: str = ""
        self.overall_hash: str = ""
        self.timestamp: str = ""
        self.platform_info: Dict[str, str] = {}
        self.dependency_info: List[Dict[str, str]] = []
        self.issues: List[str] = []
        self.recommendations: List[str] = []


def capture_environment_state() -> Dict[str, Any]:
    """Capture the current environment state for reproducibility.

    Returns:
        Dictionary with comprehensive environment information
    """
    # Platform information
    platform_info = {
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'python_executable': sys.executable,
        'working_directory': os.getcwd()
    }

    # Environment variables (filter sensitive ones)
    sensitive_vars = {'PATH', 'HOME', 'USER', 'USERNAME', 'SHELL', 'TERM'}
    env_vars = {
        k: v for k, v in os.environ.items()
        if k not in sensitive_vars and not k.startswith('__')
    }

    # Current working directory contents
    try:
        cwd_contents = list(Path('.').glob('*'))
        cwd_files = [str(f) for f in cwd_contents if f.is_file()]
        cwd_dirs = [str(d) for d in cwd_contents if d.is_dir()]
    except:
        cwd_files = []
        cwd_dirs = []

    return {
        'platform': platform_info,
        'environment_variables': env_vars,
        'current_directory_files': sorted(cwd_files),
        'current_directory_directories': sorted(cwd_dirs),
        'timestamp': datetime.now().isoformat()
    }


def capture_dependency_state() -> List[Dict[str, str]]:
    """Capture dependency information for reproducibility.

    Returns:
        List of dependency information dictionaries
    """
    dependencies = []

    try:
        # Try to get pip freeze output
        result = subprocess.run([sys.executable, '-m', 'pip', 'freeze'],
                              capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if '==' in line:
                    package, version = line.split('==', 1)
                    dependencies.append({
                        'package': package.strip(),
                        'version': version.strip(),
                        'source': 'pip'
                    })
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Also try uv if available
    try:
        result = subprocess.run(['uv', 'pip', 'freeze'],
                              capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if '==' in line:
                    package, version = line.split('==', 1)
                    # Update or add uv version
                    existing = next((d for d in dependencies if d['package'] == package), None)
                    if existing:
                        existing['source'] = 'uv'
                        existing['version'] = version.strip()
                    else:
                        dependencies.append({
                            'package': package.strip(),
                            'version': version.strip(),
                            'source': 'uv'
                        })
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return sorted(dependencies, key=lambda x: x['package'])


def calculate_file_hash(file_path: Path, algorithm: str = 'sha256') -> Optional[str]:
    """Calculate hash of a file for integrity verification.

    Args:
        file_path: Path to file to hash
        algorithm: Hash algorithm to use ('sha256', 'md5', etc.)

    Returns:
        Hash string or None if file doesn't exist
    """
    if not file_path.exists():
        return None

    hash_func = hashlib.new(algorithm)

    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception:
        return None


def calculate_directory_hash(directory_path: Path, algorithm: str = 'sha256') -> Optional[str]:
    """Calculate hash of all files in a directory.

    Args:
        directory_path: Path to directory to hash
        algorithm: Hash algorithm to use

    Returns:
        Hash string or None if directory doesn't exist
    """
    if not directory_path.exists() or not directory_path.is_dir():
        return None

    hash_func = hashlib.new(algorithm)
    file_hashes = []

    try:
        for file_path in sorted(directory_path.rglob('*')):
            if file_path.is_file():
                file_hash = calculate_file_hash(file_path, algorithm)
                if file_hash:
                    file_hashes.append(file_hash)

        if file_hashes:
            combined = ''.join(file_hashes)
            hash_func.update(combined.encode())
            return hash_func.hexdigest()
    except Exception:
        return None

    return None


def generate_reproducibility_report(output_dir: Path) -> ReproducibilityReport:
    """Generate comprehensive reproducibility report.

    Args:
        output_dir: Directory to analyze for reproducibility

    Returns:
        ReproducibilityReport with comprehensive analysis
    """
    report = ReproducibilityReport()
    report.timestamp = datetime.now().isoformat()

    # Capture environment state
    env_state = capture_environment_state()
    report.platform_info = env_state['platform']

    # Calculate environment hash
    env_json = json.dumps(env_state, sort_keys=True)
    report.environment_hash = hashlib.sha256(env_json.encode()).hexdigest()

    # Capture dependency state
    deps = capture_dependency_state()
    report.dependency_info = deps

    # Calculate dependency hash
    deps_json = json.dumps(deps, sort_keys=True)
    report.dependency_hash = hashlib.sha256(deps_json.encode()).hexdigest()

    # Calculate code hash (src/ directory)
    src_dir = Path('src')
    if src_dir.exists():
        report.code_hash = calculate_directory_hash(src_dir) or ""

    # Calculate data hash (output/data/ directory)
    data_dir = output_dir / 'data'
    report.data_hash = calculate_directory_hash(data_dir) or "no_data_directory"

    # Calculate overall hash
    all_hashes = f"{report.environment_hash}{report.dependency_hash}{report.code_hash}{report.data_hash}"
    report.overall_hash = hashlib.sha256(all_hashes.encode()).hexdigest()

    # Generate recommendations
    if not deps:
        report.recommendations.append("Consider capturing dependency information for better reproducibility")

    if not report.code_hash:
        report.issues.append("No source code found to hash")

    if not report.data_hash:
        report.recommendations.append("Consider including data files for complete reproducibility")

    return report


def save_reproducibility_report(report: ReproducibilityReport, output_path: Path) -> None:
    """Save reproducibility report to file.

    Args:
        report: ReproducibilityReport to save
        output_path: Path to save report (typically JSON file)
    """
    # Convert to serializable dict
    report_dict = {
        'environment_hash': report.environment_hash,
        'dependency_hash': report.dependency_hash,
        'code_hash': report.code_hash,
        'data_hash': report.data_hash,
        'overall_hash': report.overall_hash,
        'timestamp': report.timestamp,
        'platform_info': report.platform_info,
        'dependency_info': report.dependency_info,
        'issues': report.issues,
        'recommendations': report.recommendations
    }

    # Create directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(report_dict, f, indent=2)


def load_reproducibility_report(report_path: Path) -> Optional[ReproducibilityReport]:
    """Load reproducibility report from file.

    Args:
        report_path: Path to report file

    Returns:
        ReproducibilityReport or None if loading fails
    """
    if not report_path.exists():
        return None

    try:
        with open(report_path, 'r') as f:
            data = json.load(f)

        report = ReproducibilityReport()
        report.environment_hash = data.get('environment_hash', '')
        report.dependency_hash = data.get('dependency_hash', '')
        report.code_hash = data.get('code_hash', '')
        report.data_hash = data.get('data_hash', '')
        report.overall_hash = data.get('overall_hash', '')
        report.timestamp = data.get('timestamp', '')
        report.platform_info = data.get('platform_info', {})
        report.dependency_info = data.get('dependency_info', [])
        report.issues = data.get('issues', [])
        report.recommendations = data.get('recommendations', [])

        return report
    except Exception:
        return None


def verify_reproducibility(current_report: ReproducibilityReport,
                          previous_report: ReproducibilityReport) -> Dict[str, Any]:
    """Verify reproducibility by comparing current and previous reports.

    Args:
        current_report: Current reproducibility report
        previous_report: Previous reproducibility report for comparison

    Returns:
        Dictionary with verification results
    """
    verification = {
        'environment_changed': current_report.environment_hash != previous_report.environment_hash,
        'dependencies_changed': current_report.dependency_hash != previous_report.dependency_hash,
        'code_changed': current_report.code_hash != previous_report.code_hash,
        'data_changed': current_report.data_hash != previous_report.data_hash,
        'overall_changed': current_report.overall_hash != previous_report.overall_hash,
        'recommendations': []
    }

    if verification['environment_changed']:
        verification['recommendations'].append(
            "Environment has changed - ensure platform compatibility"
        )

    if verification['dependencies_changed']:
        verification['recommendations'].append(
            "Dependencies have changed - verify version compatibility"
        )

    if verification['code_changed']:
        verification['recommendations'].append(
            "Source code has changed - verify functionality preservation"
        )

    if verification['data_changed']:
        verification['recommendations'].append(
            "Data files have changed - verify data integrity"
        )

    if not any(verification.values()):
        verification['recommendations'].append(
            "All components unchanged - excellent reproducibility!"
        )

    return verification


def create_reproducible_environment() -> Dict[str, Any]:
    """Create environment configuration for reproducible builds.

    Returns:
        Dictionary with environment settings for reproducibility
    """
    # Set deterministic random seeds
    random_seeds = {
        'python_random': 42,
        'numpy_random': 42,
        'tensorflow_random': 42,
        'torch_random': 42
    }

    # Environment variables for deterministic behavior
    env_vars = {
        'PYTHONHASHSEED': '42',
        'MPLBACKEND': 'Agg',  # Headless matplotlib
        'OMP_NUM_THREADS': '1',  # Single-threaded for reproducibility
        'MKL_NUM_THREADS': '1',
        'NUMEXPR_NUM_THREADS': '1',
        'OPENBLAS_NUM_THREADS': '1'
    }

    return {
        'random_seeds': random_seeds,
        'environment_variables': env_vars,
        'recommendations': [
            "Set these environment variables before running experiments",
            "Use fixed random seeds for reproducible results",
            "Consider using deterministic algorithms when possible"
        ]
    }


def generate_build_manifest(output_dir: Path) -> Dict[str, Any]:
    """Generate a comprehensive build manifest for reproducibility.

    Args:
        output_dir: Output directory to analyze

    Returns:
        Dictionary with build manifest information
    """
    # Count files and directories
    file_count = 0
    dir_count = 0
    file_manifest = {}

    if output_dir.exists():
        for root, dirs, files in os.walk(output_dir):
            dir_count += len(dirs)
            file_count += len(files)
            for file in files:
                file_path = Path(root) / file
                try:
                    file_manifest[str(file_path.relative_to(output_dir))] = {
                        'size': file_path.stat().st_size,
                        'modified': file_path.stat().st_mtime
                    }
                except:
                    pass

    # Calculate total size
    total_size = sum(f.get('size', 0) for f in file_manifest.values())

    manifest = {
        'timestamp': datetime.now().isoformat(),
        'file_count': file_count,
        'directory_count': dir_count,
        'total_size': total_size,
        'build_info': {
            'platform': platform.platform(),
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'working_directory': os.getcwd()
        },
        'file_manifest': file_manifest,
        'directory_structure': {},
        'dependencies': capture_dependency_state()
    }

    # Analyze output directory structure
    if output_dir.exists():
        for item in output_dir.rglob('*'):
            if item.is_file():
                rel_path = item.relative_to(output_dir)
                file_hash = calculate_file_hash(item)
                manifest['file_manifest'][str(rel_path)] = {
                    'size': item.stat().st_size,
                    'modified': datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
                    'hash': file_hash
                }

    return manifest


def save_build_manifest(manifest: Dict[str, Any], output_path: Path) -> None:
    """Save build manifest to file.

    Args:
        manifest: Build manifest dictionary
        output_path: Path to save manifest
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)


def verify_build_integrity(manifest_path: Path, output_dir: Path) -> Dict[str, Any]:
    """Verify build integrity against a saved manifest.

    Args:
        manifest_path: Path to saved manifest file
        output_dir: Current output directory to verify

    Returns:
        Dictionary with integrity verification results
    """
    if not manifest_path.exists():
        return {'error': 'Manifest file not found'}

    try:
        with open(manifest_path, 'r') as f:
            saved_manifest = json.load(f)

        verification = {
            'timestamp': datetime.now().isoformat(),
            'manifest_timestamp': saved_manifest.get('timestamp', 'unknown'),
            'files_verified': 0,
            'files_missing': 0,
            'files_changed': 0,
            'files_added': 0,
            'details': {}
        }

        saved_files = saved_manifest.get('file_manifest', {})

        # Check existing files
        for rel_path, saved_info in saved_files.items():
            current_path = output_dir / rel_path

            if not current_path.exists():
                verification['files_missing'] += 1
                verification['details'][rel_path] = 'missing'
            else:
                current_hash = calculate_file_hash(current_path)
                saved_hash = saved_info.get('hash')

                if current_hash == saved_hash:
                    verification['files_verified'] += 1
                    verification['details'][rel_path] = 'verified'
                else:
                    verification['files_changed'] += 1
                    verification['details'][rel_path] = 'changed'

        # Check for new files
        for item in output_dir.rglob('*'):
            if item.is_file():
                rel_path = str(item.relative_to(output_dir))
                if rel_path not in saved_files:
                    verification['files_added'] += 1
                    verification['details'][rel_path] = 'added'

        return verification

    except Exception as e:
        return {'error': f'Failed to verify integrity: {e}'}


def create_reproducible_script_template(script_name: str) -> str:
    """Create a template for reproducible research scripts.

    Args:
        script_name: Name of the script to create template for

    Returns:
        Template script content as string
    """
    template = f'''#!/usr/bin/env python3
"""Reproducible research script: {script_name}

This script demonstrates best practices for reproducible research:
- Fixed random seeds for deterministic results
- Environment variable configuration
- Comprehensive logging and error handling
- Output validation and verification
"""

from __future__ import annotations

import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime

# Import reproducibility utilities
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from reproducibility import (
    capture_environment_state,
    capture_dependency_state,
    generate_reproducibility_report,
    save_reproducibility_report
)


def setup_reproducible_environment():
    """Setup environment for reproducible execution."""
    # Set random seeds
    import random
    import numpy as np

    random.seed(42)
    np.random.seed(42)

    # Set environment variables for deterministic behavior
    os.environ['PYTHONHASHSEED'] = '42'
    os.environ['MPLBACKEND'] = 'Agg'

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def main():
    """Main reproducible research function."""
    setup_reproducible_environment()

    # Capture environment state for reproducibility
    env_state = capture_environment_state()
    deps = capture_dependency_state()

    # Generate reproducibility report
    output_dir = Path("output")
    report = generate_reproducibility_report(output_dir)

    # Save reproducibility information
    report_path = output_dir / "reproducibility_report.json"
    save_reproducibility_report(report, report_path)

    logging.info(f"Reproducibility report saved to: {{report_path}}")

    # Your research code here
    # ... perform experiments ...
    # ... generate results ...
    # ... save outputs ...

    logging.info("Research completed successfully")


if __name__ == "__main__":
    main()
'''
    return template


def validate_experiment_reproducibility(experiment_results: Dict[str, Any],
                                       expected_results: Dict[str, Any],
                                       tolerance: float = 1e-6) -> Dict[str, Any]:
    """Validate that experiment results are reproducible within tolerance.

    Args:
        experiment_results: Current experiment results
        expected_results: Expected/previous results for comparison
        tolerance: Numerical tolerance for floating point comparisons

    Returns:
        Dictionary with reproducibility validation results
    """
    validation = {
        'reproducible': True,
        'differences': {},
        'recommendations': []
    }

    # Compare numerical results
    for key, expected_value in expected_results.items():
        if key in experiment_results:
            current_value = experiment_results[key]

            if isinstance(current_value, (int, float)) and isinstance(expected_value, (int, float)):
                diff = abs(current_value - expected_value)
                if diff > tolerance:
                    validation['reproducible'] = False
                    validation['differences'][key] = {
                        'expected': expected_value,
                        'current': current_value,
                        'difference': diff
                    }

    if not validation['reproducible']:
        validation['recommendations'].append(
            "Results differ from expected values - check for non-deterministic behavior"
        )
        validation['recommendations'].append(
            "Consider using fixed random seeds and deterministic algorithms"
        )

    return validation


def create_version_snapshot(output_dir: Path, snapshot_name: str = "version_snapshot") -> Path:
    """Create a version snapshot of the current build for future comparison.

    Args:
        output_dir: Output directory to snapshot
        snapshot_name: Name for the snapshot

    Returns:
        Path to created snapshot file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_file = output_dir / f"{snapshot_name}_{timestamp}.json"

    # Create comprehensive snapshot
    snapshot = {
        'timestamp': datetime.now().isoformat(),
        'name': snapshot_name,
        'environment': capture_environment_state(),
        'dependencies': capture_dependency_state(),
        'manifest': generate_build_manifest(output_dir)
    }

    with open(snapshot_file, 'w') as f:
        json.dump(snapshot, f, indent=2)

    return snapshot_file


def compare_snapshots(snapshot1_path: Path, snapshot2_path: Path) -> Dict[str, Any]:
    """Compare two version snapshots for changes.

    Args:
        snapshot1_path: Path to first snapshot
        snapshot2_path: Path to second snapshot

    Returns:
        Dictionary with comparison results
    """
    if not snapshot1_path.exists() or not snapshot2_path.exists():
        return {'error': 'One or both snapshot files not found'}

    try:
        with open(snapshot1_path, 'r') as f:
            snap1 = json.load(f)
        with open(snapshot2_path, 'r') as f:
            snap2 = json.load(f)

        comparison = {
            'snapshot1_timestamp': snap1.get('timestamp', 'unknown'),
            'snapshot2_timestamp': snap2.get('timestamp', 'unknown'),
            'differences': {},
            'recommendations': []
        }

        # Compare environment
        env1 = json.dumps(snap1.get('environment', {}), sort_keys=True)
        env2 = json.dumps(snap2.get('environment', {}), sort_keys=True)

        if env1 != env2:
            comparison['differences']['environment'] = {
                'changed': True,
                'details': 'Environment state differs between snapshots'
            }

        # Compare dependencies
        deps1_list = snap1.get('dependencies', [])
        deps2_list = snap2.get('dependencies', [])

        deps1_dict = {d['package']: d['version'] for d in deps1_list}
        deps2_dict = {d['package']: d['version'] for d in deps2_list}

        if deps1_dict != deps2_dict:
            comparison['differences']['dependencies'] = {
                'changed': True,
                'details': 'Dependency versions differ between snapshots'
            }

        # Compare file manifests
        manifest1 = snap1.get('manifest', {}).get('file_manifest', {})
        manifest2 = snap2.get('manifest', {}).get('file_manifest', {})

        if manifest1 != manifest2:
            comparison['differences']['files'] = {
                'changed': True,
                'details': 'File manifests differ between snapshots'
            }

        if not comparison['differences']:
            comparison['recommendations'].append("Snapshots are identical - excellent reproducibility!")

        return comparison

    except Exception as e:
        return {'error': f'Failed to compare snapshots: {e}'}
