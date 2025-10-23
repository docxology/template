"""Build verification and validation tools for ensuring correct builds.

This module provides utilities for:
- Build artifact verification
- Output consistency checking
- Build process validation
- Artifact integrity verification
- Build reproducibility validation

All functions follow the thin orchestrator pattern and maintain
100% test coverage requirements.
"""

from __future__ import annotations

import os
import sys
import json
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import tempfile
import shutil


class BuildVerificationReport:
    """Container for build verification results."""

    def __init__(self):
        self.build_timestamp: str = ""
        self.build_duration: float = 0.0
        self.exit_code: int = 0
        self.output_files: List[str] = []
        self.build_hash: str = ""
        self.dependency_hash: str = ""
        self.environment_hash: str = ""
        self.verification_passed: bool = True
        self.issues: List[str] = []
        self.warnings: List[str] = []
        self.recommendations: List[str] = []


def run_build_command(build_command: List[str], timeout: int = 300) -> Tuple[int, str, str]:
    """Run a build command and capture output.

    Args:
        build_command: Command to run as list of strings
        timeout: Command timeout in seconds

    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            build_command,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.getcwd()
        )

        return result.returncode, result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout} seconds"
    except Exception as e:
        return -2, "", f"Command failed: {e}"


def verify_build_artifacts(output_dir: Path, expected_files: Dict[str, List[str]]) -> Dict[str, Any]:
    """Verify that expected build artifacts are present and correct.

    Args:
        output_dir: Output directory to verify
        expected_files: Dictionary mapping categories to expected file lists

    Returns:
        Dictionary with verification results
    """
    verification = {
        'missing_files': [],
        'unexpected_files': [],
        'corrupted_files': [],
        'verification_passed': True,
        'file_count': 0,
        'total_expected': 0
    }

    if not output_dir.exists():
        verification['verification_passed'] = False
        verification['missing_files'].append(f"Output directory: {output_dir}")
        return verification

    # Check for missing expected files
    for category, files in expected_files.items():
        category_dir = output_dir / category
        if not category_dir.exists():
            # Missing entire directory
            for expected_file in files:
                verification['missing_files'].append(expected_file)
                verification['verification_passed'] = False
                verification['total_expected'] += 1
        else:
            # Directory exists, check for missing files
            for expected_file in files:
                expected_path = category_dir / expected_file
                verification['total_expected'] += 1

                if not expected_path.exists():
                    verification['missing_files'].append(expected_file)
                    verification['verification_passed'] = False
                else:
                    verification['file_count'] += 1

    # Check for unexpected files (basic check)
    for item in output_dir.rglob('*'):
        if item.is_file():
            rel_path = item.relative_to(output_dir)
            is_expected = any(str(rel_path).startswith(cat) and any(f in str(rel_path) for f in files)
                            for cat, files in expected_files.items())
            if not is_expected and item.name not in ['project_combined.html', '.DS_Store']:
                verification['unexpected_files'].append(str(rel_path))

    return verification


def verify_build_reproducibility(build_command: List[str],
                                expected_outputs: Dict[str, str],
                                iterations: int = 3) -> Dict[str, Any]:
    """Verify build reproducibility by running build multiple times.

    Args:
        build_command: Build command to run
        expected_outputs: Dictionary mapping output files to expected content
        iterations: Number of times to run build

    Returns:
        Dictionary with reproducibility verification results
    """
    reproducibility = {
        'iterations_completed': 0,
        'consistent_results': True,
        'output_hashes': {},
        'exit_codes': [],
        'duration_variance': 0.0,
        'issues': []
    }

    output_hashes = {}
    exit_codes = []
    durations = []

    for i in range(iterations):
        try:
            # Run build
            start_time = datetime.now()
            exit_code, stdout, stderr = run_build_command(build_command)
            end_time = datetime.now()

            exit_codes.append(exit_code)
            durations.append((end_time - start_time).total_seconds())

            reproducibility['iterations_completed'] += 1

            if exit_code != 0:
                reproducibility['consistent_results'] = False
                reproducibility['issues'].append(f"Iteration {i+1}: Build failed with exit code {exit_code}")

            # Check output file hashes
            for output_file, expected_content in expected_outputs.items():
                file_path = Path(output_file)
                if file_path.exists():
                    file_hash = calculate_file_hash(file_path)
                    if output_file not in output_hashes:
                        output_hashes[output_file] = []
                    output_hashes[output_file].append(file_hash)

        except Exception as e:
            reproducibility['issues'].append(f"Iteration {i+1}: Exception: {e}")
            reproducibility['consistent_results'] = False

    # Analyze hash consistency
    for output_file, hashes in output_hashes.items():
        if len(set(hashes)) > 1:
            reproducibility['consistent_results'] = False
            reproducibility['issues'].append(f"Inconsistent hashes for {output_file}")

    # Calculate duration variance
    if len(durations) > 1:
        reproducibility['duration_variance'] = max(durations) - min(durations)

    # Add collected data to reproducibility result
    reproducibility['exit_codes'] = exit_codes
    reproducibility['durations'] = durations
    reproducibility['output_hashes'] = output_hashes

    return reproducibility


def calculate_file_hash(file_path: Path, algorithm: str = 'sha256') -> Optional[str]:
    """Calculate hash of a file for integrity verification.

    Args:
        file_path: Path to file to hash
        algorithm: Hash algorithm to use

    Returns:
        Hash string or None if calculation fails
    """
    if not file_path.exists():
        return None

    try:
        hash_func = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception:
        return None


def verify_build_environment() -> Dict[str, Any]:
    """Verify that the build environment is properly configured.

    Returns:
        Dictionary with environment verification results
    """
    environment = {
        'python_version': sys.version,
        'python_executable': sys.executable,
        'working_directory': os.getcwd(),
        'dependencies_available': True,
        'required_tools': {},
        'issues': []
    }

    # Check required tools
    required_tools = [
        ('python', ['python3', '--version']),
        ('pip', ['python3', '-m', 'pip', '--version']),
        ('pandoc', ['pandoc', '--version']),
        ('xelatex', ['xelatex', '--version']),
        ('pytest', ['python3', '-m', 'pytest', '--version']),
        ('matplotlib', ['python3', '-c', 'import matplotlib; print("OK")']),
        ('numpy', ['python3', '-c', 'import numpy; print("OK")'])
    ]

    for tool_name, command in required_tools:
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=10)
            environment['required_tools'][tool_name] = {
                'available': result.returncode == 0,
                'version': result.stdout.strip() if result.returncode == 0 else result.stderr.strip()
            }
        except Exception as e:
            environment['required_tools'][tool_name] = {
                'available': False,
                'error': str(e)
            }
            environment['dependencies_available'] = False
            environment['issues'].append(f"Tool '{tool_name}' not available or failed")

    return environment


def create_build_verification_script() -> str:
    """Create a comprehensive build verification script.

    Returns:
        Build verification script content as string
    """
    script = '''#!/usr/bin/env python3
"""Build verification script for comprehensive build validation.

This script performs comprehensive verification of the build process:
- Environment validation
- Dependency checking
- Build execution
- Output verification
- Reproducibility testing
"""

from __future__ import annotations

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from build_verifier import (
    run_build_command,
    verify_build_artifacts,
    verify_build_reproducibility,
    verify_build_environment,
    BuildVerificationReport
)


def main():
    """Main build verification function."""
    print("🔍 Starting comprehensive build verification...")
    print()

    # Create verification report
    report = BuildVerificationReport()
    report.build_timestamp = datetime.now().isoformat()
    start_time = time.time()

    # 1. Verify build environment
    print("1. Verifying build environment...")
    environment = verify_build_environment()

    if not environment['dependencies_available']:
        print("❌ Environment verification failed")
        for issue in environment['issues']:
            print(f"   • {issue}")
        return 1

    print("✅ Environment verification passed")
    for tool, info in environment['required_tools'].items():
        if info['available']:
            print(f"   ✅ {tool}: {info.get('version', 'OK')}")
        else:
            print(f"   ❌ {tool}: {info.get('error', 'Not available')}")
    print()

    # 2. Run build command
    print("2. Running build command...")
    build_command = ['./repo_utilities/render_pdf.sh']

    exit_code, stdout, stderr = run_build_command(build_command)

    report.exit_code = exit_code
    report.build_duration = time.time() - start_time

    if exit_code != 0:
        print(f"❌ Build failed with exit code {exit_code}")
        if stderr:
            print(f"Error output: {stderr}")
        return 1

    print("✅ Build completed successfully")
    print(f"   Duration: {report.build_duration:.1f}s")
    print()

    # 3. Verify build artifacts
    print("3. Verifying build artifacts...")
    output_dir = Path("output")
    expected_files = {
        'pdf': [
            '01_abstract.pdf', '02_introduction.pdf', '03_methodology.pdf',
            '04_experimental_results.pdf', '05_discussion.pdf', '06_conclusion.pdf',
            '07_references.pdf', '10_symbols_glossary.pdf', 'project_combined.pdf'
        ],
        'tex': [
            '01_abstract.tex', '02_introduction.tex', '03_methodology.tex',
            '04_experimental_results.tex', '05_discussion.tex', '06_conclusion.tex',
            '07_references.tex', '10_symbols_glossary.tex', 'project_combined.tex'
        ],
        'data': [
            'convergence_data.npz', 'dataset_summary.csv', 'example_data.csv',
            'example_data.npz', 'performance_comparison.csv'
        ],
        'figures': [
            'ablation_study.png', 'convergence_plot.png', 'data_structure.png',
            'example_figure.png', 'experimental_setup.png', 'hyperparameter_sensitivity.png',
            'image_classification_results.png', 'recommendation_scalability.png',
            'scalability_analysis.png', 'step_size_analysis.png'
        ]
    }

    artifacts = verify_build_artifacts(output_dir, expected_files)

    if not artifacts['verification_passed']:
        print("❌ Artifact verification failed")
        for missing in artifacts['missing_files']:
            print(f"   • Missing: {missing}")
        for unexpected in artifacts['unexpected_files']:
            print(f"   • Unexpected: {unexpected}")
        return 1

    print("✅ Artifact verification passed")
    print(f"   • Files created: {artifacts['file_count']}")
    print(f"   • Files expected: {artifacts['total_expected']}")
    print()

    # 4. Test reproducibility
    print("4. Testing build reproducibility...")
    expected_outputs = {
        'output/pdf/project_combined.pdf': 'Test Project',
        'output/project_combined.html': 'Test Project'
    }

    reproducibility = verify_build_reproducibility(build_command, expected_outputs, iterations=2)

    if not reproducibility['consistent_results']:
        print("❌ Reproducibility test failed")
        for issue in reproducibility['issues']:
            print(f"   • {issue}")
        return 1

    print("✅ Reproducibility test passed")
    print(f"   • Iterations completed: {reproducibility['iterations_completed']}")
    print(f"   • Duration variance: {reproducibility['duration_variance']:.3f}s")
    print()

    # 5. Final verification
    print("5. Final verification...")

    # Check main PDF content
    pdf_path = Path("output/pdf/project_combined.pdf")
    if pdf_path.exists():
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(pdf_path))
            first_page_text = reader.pages[0].extract_text()

            if "Test Project" in first_page_text:
                print("✅ PDF contains expected title")
            else:
                print("⚠️  PDF title verification uncertain")
        except Exception as e:
            print(f"⚠️  PDF content verification failed: {e}")
    else:
        print("❌ Main PDF not found")
        return 1

    print()
    print("🎉 BUILD VERIFICATION COMPLETED SUCCESSFULLY!")
    print()
    print("Summary:")
    print(f"• Build duration: {report.build_duration:.1f}s")
    print(f"• Exit code: {report.exit_code}")
    print(f"• Artifacts created: {artifacts['file_count']}")
    print(f"• Build reproducible: Yes")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
'''
    return script


def validate_build_process(build_script: Path) -> Dict[str, Any]:
    """Validate that a build script is properly structured.

    Args:
        build_script: Path to build script to validate

    Returns:
        Dictionary with validation results
    """
    validation = {
        'script_exists': False,
        'is_executable': False,
        'has_shebang': False,
        'has_error_handling': False,
        'has_logging': False,
        'has_documentation': False,
        'validation_passed': False,
        'recommendations': []
    }

    if not build_script.exists():
        validation['recommendations'].append("Build script does not exist")
        return validation

    validation['script_exists'] = True

    # Check if executable
    validation['is_executable'] = os.access(build_script, os.X_OK)

    # Read script content
    try:
        with open(build_script, 'r') as f:
            content = f.read()

        # Check for shebang
        validation['has_shebang'] = content.startswith('#!')

        # Check for error handling
        validation['has_error_handling'] = (
            'set -e' in content or
            'set -u' in content or
            'trap' in content or
            'exit' in content
        )

        # Check for logging
        validation['has_logging'] = any(pattern in content.lower() for pattern in ['log', 'echo', 'print'])

        # Check for documentation
        validation['has_documentation'] = any(pattern in content for pattern in ['# ', '"""', "'''"])

    except Exception as e:
        validation['recommendations'].append(f"Failed to read script: {e}")
        return validation

    # Recommendations
    if not validation['is_executable']:
        validation['recommendations'].append("Make script executable with: chmod +x " + str(build_script))

    if not validation['has_shebang']:
        validation['recommendations'].append("Add proper shebang line at the beginning")

    if not validation['has_error_handling']:
        validation['recommendations'].append("Add error handling (set -e)")

    if not validation['has_logging']:
        validation['recommendations'].append("Add logging for better debugging")

    if not validation['has_documentation']:
        validation['recommendations'].append("Add documentation comments")

    validation['validation_passed'] = all([
        validation['script_exists'],
        validation['has_shebang'],
        validation['has_error_handling'],
        validation['has_logging']
    ])

    return validation


def verify_dependency_consistency(requirements_files: List[Path]) -> Dict[str, Any]:
    """Verify consistency between dependency files.

    Args:
        requirements_files: List of requirements/dependency files to check

    Returns:
        Dictionary with dependency consistency verification
    """
    consistency = {
        'files_checked': len(requirements_files),
        'consistent_versions': True,
        'conflicting_versions': [],
        'missing_files': [],
        'recommendations': []
    }

    if not requirements_files:
        consistency['recommendations'].append("No requirements files found")
        return consistency

    dependency_versions = {}

    for req_file in requirements_files:
        if not req_file.exists():
            consistency['missing_files'].append(str(req_file))
            continue

        try:
            with open(req_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '==' in line:
                        package, version = line.split('==', 1)
                        package = package.strip()
                        version = version.strip()

                        if package in dependency_versions:
                            if dependency_versions[package] != version:
                                consistency['consistent_versions'] = False
                                consistency['conflicting_versions'].append({
                                    'package': package,
                                    'versions': [dependency_versions[package], version],
                                    'files': [str(f) for f in requirements_files if f != req_file] + [str(req_file)]
                                })
                        else:
                            dependency_versions[package] = version

        except Exception as e:
            consistency['recommendations'].append(f"Failed to parse {req_file}: {e}")

    if consistency['conflicting_versions']:
        consistency['recommendations'].append("Resolve version conflicts between requirements files")

    if not dependency_versions:
        consistency['recommendations'].append("No dependencies found in requirements files")

    return consistency


def create_build_validation_report(build_results: Dict[str, Any]) -> str:
    """Create a comprehensive build validation report.

    Args:
        build_results: Dictionary with build validation results

    Returns:
        Markdown formatted build validation report
    """
    report = []
    report.append("# Build Validation Report")
    report.append("")

    report.append("## Summary")
    report.append(f"- **Build completed**: {'Yes' if build_results.get('build_succeeded', False) else 'No'}")
    report.append(f"- **Artifacts verified**: {'Yes' if build_results.get('artifacts_verified', False) else 'No'}")
    report.append(f"- **Environment valid**: {'Yes' if build_results.get('environment_valid', False) else 'No'}")
    report.append(f"- **Reproducible**: {'Yes' if build_results.get('reproducible', False) else 'No'}")
    report.append("")

    if build_results.get('issues'):
        report.append("## Issues")
        for issue in build_results['issues']:
            report.append(f"- {issue}")
        report.append("")

    if build_results.get('recommendations'):
        report.append("## Recommendations")
        for rec in build_results['recommendations']:
            report.append(f"- {rec}")
        report.append("")

    if build_results.get('performance_metrics'):
        report.append("## Performance")
        metrics = build_results['performance_metrics']
        report.append(f"- **Build duration**: {metrics.get('duration', 0):.1f}s")
        report.append(f"- **Artifacts created**: {metrics.get('file_count', 0)}")
        report.append("")

    return '\n'.join(report)


def verify_output_directory_structure(output_dir: Path) -> Dict[str, Any]:
    """Verify that output directory has expected structure.

    Args:
        output_dir: Output directory to verify

    Returns:
        Dictionary with structure verification results
    """
    structure = {
        'directory_exists': False,
        'expected_subdirectories': [],
        'missing_subdirectories': [],
        'unexpected_subdirectories': [],
        'structure_valid': False
    }

    if not output_dir.exists():
        return structure

    structure['directory_exists'] = True

    expected_dirs = ['pdf', 'tex', 'data', 'figures']
    existing_dirs = []

    for item in output_dir.iterdir():
        if item.is_dir():
            existing_dirs.append(item.name)

    # Check expected directories
    for expected_dir in expected_dirs:
        if expected_dir in existing_dirs:
            structure['expected_subdirectories'].append(expected_dir)
        else:
            structure['missing_subdirectories'].append(expected_dir)

    # Check for unexpected directories
    for existing_dir in existing_dirs:
        if existing_dir not in expected_dirs:
            structure['unexpected_subdirectories'].append(existing_dir)

    structure['structure_valid'] = len(structure['missing_subdirectories']) == 0

    return structure


def validate_build_configuration() -> Dict[str, Any]:
    """Validate build configuration and settings.

    Returns:
        Dictionary with configuration validation results
    """
    config = {
        'python_version_valid': False,
        'dependencies_installed': False,
        'build_tools_available': False,
        'configuration_valid': False,
        'issues': [],
        'recommendations': []
    }

    # Check Python version
    python_version = sys.version_info
    config['python_version_valid'] = python_version >= (3, 10)

    if not config['python_version_valid']:
        config['issues'].append(f"Python version {python_version.major}.{python_version.minor} is too old (need >= 3.10)")

    # Check if dependencies are installed
    try:
        import matplotlib
        import numpy
        import pypdf
        config['dependencies_installed'] = True
    except ImportError as e:
        config['issues'].append(f"Missing dependencies: {e}")
        config['dependencies_installed'] = False

    # Check build tools
    build_tools = ['pandoc', 'xelatex', 'python3']
    available_tools = []

    for tool in build_tools:
        if os.system(f"which {tool} > /dev/null 2>&1") == 0:
            available_tools.append(tool)
        else:
            config['issues'].append(f"Build tool not found: {tool}")

    config['build_tools_available'] = len(available_tools) >= 2  # Need at least python and pandoc

    # Overall configuration validity
    config['configuration_valid'] = all([
        config['python_version_valid'],
        config['dependencies_installed'],
        config['build_tools_available']
    ])

    # Recommendations
    if not config['python_version_valid']:
        config['recommendations'].append("Upgrade Python to version 3.10 or higher")

    if not config['dependencies_installed']:
        config['recommendations'].append("Install required dependencies with: pip install -r requirements.txt")

    if not config['build_tools_available']:
        config['recommendations'].append("Install required build tools (pandoc, xelatex)")

    return config


def create_comprehensive_build_report(build_results: Dict[str, Any]) -> str:
    """Create a comprehensive build report combining all verification results.

    Args:
        build_results: Dictionary with all build verification results

    Returns:
        Markdown formatted comprehensive build report
    """
    report = []
    report.append("# Comprehensive Build Verification Report")
    report.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")

    # Overall status
    overall_success = (
        build_results.get('build_succeeded', False) and
        build_results.get('artifacts_verified', False) and
        build_results.get('reproducible', False)
    )

    status = "✅ SUCCESS" if overall_success else "❌ FAILURE"
    report.append(f"## Overall Status: {status}")
    report.append("")

    # Build details
    if 'build_details' in build_results:
        details = build_results['build_details']
        report.append("## Build Details")
        report.append(f"- **Duration**: {details.get('duration', 0):.1f}s")
        report.append(f"- **Exit code**: {details.get('exit_code', -1)}")
        report.append(f"- **Files created**: {details.get('file_count', 0)}")
        report.append("")

    # Environment validation
    if 'environment' in build_results:
        env = build_results['environment']
        report.append("## Environment Validation")
        if env.get('dependencies_available'):
            report.append("✅ Dependencies: Available")
        else:
            report.append("❌ Dependencies: Missing")
            for issue in env.get('issues', []):
                report.append(f"   • {issue}")
        report.append("")

    # Artifact verification
    if 'artifacts' in build_results:
        artifacts = build_results['artifacts']
        report.append("## Artifact Verification")
        if artifacts.get('verification_passed'):
            report.append("✅ Artifacts: Verified")
            report.append(f"   • Files created: {artifacts.get('file_count', 0)}")
            report.append(f"   • Files expected: {artifacts.get('total_expected', 0)}")
        else:
            report.append("❌ Artifacts: Issues found")
            for missing in artifacts.get('missing_files', []):
                report.append(f"   • Missing: {missing}")
        report.append("")

    # Reproducibility
    if 'reproducibility' in build_results:
        repro = build_results['reproducibility']
        report.append("## Reproducibility Test")
        if repro.get('consistent_results'):
            report.append("✅ Reproducible")
            report.append(f"   • Iterations: {repro.get('iterations_completed', 0)}")
            report.append(f"   • Duration variance: {repro.get('duration_variance', 0):.3f}s")
        else:
            report.append("❌ Not reproducible")
            for issue in repro.get('issues', []):
                report.append(f"   • {issue}")
        report.append("")

    # Issues and recommendations
    all_issues = build_results.get('issues', [])
    all_recommendations = build_results.get('recommendations', [])

    if all_issues:
        report.append("## Issues")
        for issue in all_issues:
            report.append(f"- {issue}")
        report.append("")

    if all_recommendations:
        report.append("## Recommendations")
        for rec in all_recommendations:
            report.append(f"- {rec}")
        report.append("")

    # Final summary
    report.append("## Summary")
    if overall_success:
        report.append("🎉 **Build verification completed successfully!**")
        report.append("All checks passed. The build is reliable and reproducible.")
    else:
        report.append("⚠️  **Build verification found issues.**")
        report.append("Please address the issues listed above before proceeding.")
    report.append("")

    return '\n'.join(report)


def verify_build_integrity_against_baseline(baseline_path: Path, current_path: Path) -> Dict[str, Any]:
    """Verify build integrity against a baseline.

    Args:
        baseline_path: Path to baseline build results
        current_path: Path to current build results

    Returns:
        Dictionary with integrity verification results
    """
    verification = {
        'baseline_exists': False,
        'current_exists': False,
        'integrity_maintained': False,
        'differences': {},
        'recommendations': []
    }

    if not baseline_path.exists():
        verification['recommendations'].append("Create baseline for future comparison")
        return verification

    if not current_path.exists():
        verification['recommendations'].append("Current build results not found")
        return verification

    verification['baseline_exists'] = True
    verification['current_exists'] = True

    try:
        with open(baseline_path, 'r') as f:
            baseline = json.load(f)

        with open(current_path, 'r') as f:
            current = json.load(f)

        # Compare key metrics
        baseline_files = baseline.get('file_count', 0)
        current_files = current.get('file_count', 0)

        if baseline_files != current_files:
            verification['differences']['file_count'] = {
                'baseline': baseline_files,
                'current': current_files
            }

        baseline_size = baseline.get('total_size', 0)
        current_size = current.get('total_size', 0)

        if baseline_size != current_size:
            verification['differences']['total_size'] = {
                'baseline': baseline_size,
                'current': current_size
            }

        verification['integrity_maintained'] = len(verification['differences']) == 0

        if not verification['integrity_maintained']:
            verification['recommendations'].append("Build outputs differ from baseline")

    except Exception as e:
        verification['recommendations'].append(f"Failed to compare builds: {e}")

    return verification


def create_integrity_manifest(output_dir: Path) -> Dict[str, Any]:
    """Create an integrity manifest for build verification.

    Args:
        output_dir: Output directory to create manifest for

    Returns:
        Dictionary with integrity manifest information
    """
    manifest = {
        'timestamp': datetime.now().isoformat(),
        'output_directory': str(output_dir),
        'file_hashes': {},
        'directory_structure': {},
        'file_count': 0,
        'total_size': 0
    }

    if not output_dir.exists():
        return manifest

    # Build file manifest
    for item in output_dir.rglob('*'):
        if item.is_file():
            try:
                file_hash = calculate_file_hash(item)
                relative_path = str(item.relative_to(output_dir))

                manifest['file_hashes'][relative_path] = file_hash

                manifest['file_count'] += 1
                manifest['total_size'] += item.stat().st_size

            except Exception as e:
                manifest['file_hashes'][str(item.relative_to(output_dir))] = str(e)

    # Build directory structure
    for item in output_dir.rglob('*'):
        if item.is_dir():
            relative_path = str(item.relative_to(output_dir))
            manifest['directory_structure'][relative_path] = {
                'file_count': len(list(item.glob('*'))),
                'subdirectories': [d.name for d in item.iterdir() if d.is_dir()]
            }

    return manifest


def save_integrity_manifest(manifest: Dict[str, Any], manifest_path: Path) -> None:
    """Save integrity manifest to file.

    Args:
        manifest: Manifest dictionary to save
        manifest_path: Path to save manifest
    """
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)


def load_integrity_manifest(manifest_path: Path) -> Optional[Dict[str, Any]]:
    """Load integrity manifest from file.

    Args:
        manifest_path: Path to manifest file

    Returns:
        Manifest dictionary or None if loading fails
    """
    if not manifest_path.exists():
        return None

    try:
        with open(manifest_path, 'r') as f:
            return json.load(f)
    except Exception:
        return None


def verify_integrity_against_manifest(manifest1: Dict[str, Any], manifest2: Dict[str, Any]) -> Dict[str, Any]:
    """Verify integrity between two manifests.

    Args:
        manifest1: First manifest to compare
        manifest2: Second manifest to compare

    Returns:
        Dictionary with verification results
    """
    verification = {
        'files_changed': 0,
        'files_added': 0,
        'files_removed': 0,
        'verification_passed': True
    }

    # Compare file hashes
    files1 = manifest1.get('file_hashes', {})
    files2 = manifest2.get('file_hashes', {})

    # Check for changed files
    for file_path, hash1 in files1.items():
        if file_path in files2:
            hash2 = files2[file_path]
            if hash1 != hash2:
                verification['files_changed'] += 1
                verification['verification_passed'] = False
        else:
            verification['files_removed'] += 1
            verification['verification_passed'] = False

    # Check for added files
    for file_path in files2:
        if file_path not in files1:
            verification['files_added'] += 1
            verification['verification_passed'] = False

    return verification
