"""Integrity verification tools for ensuring research output validity.

This module provides utilities for:
- Output file integrity checking
- Cross-reference validation
- Data consistency verification
- Build artifact validation
- Academic standard compliance

All functions follow the thin orchestrator pattern and maintain
100% test coverage requirements.
"""

from __future__ import annotations

import os
import re
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from collections import defaultdict


class IntegrityReport:
    """Container for integrity verification results."""

    def __init__(self):
        self.file_integrity: Dict[str, bool] = {}
        self.cross_reference_integrity: Dict[str, bool] = {}
        self.data_consistency: Dict[str, bool] = {}
        self.academic_standards: Dict[str, bool] = {}
        self.overall_integrity: bool = True
        self.issues: List[str] = []
        self.warnings: List[str] = []
        self.recommendations: List[str] = []


def verify_file_integrity(file_paths: List[Path], expected_hashes: Optional[Dict[str, str]] = None) -> Dict[str, bool]:
    """Verify file integrity using hash comparison.

    Args:
        file_paths: List of file paths to verify
        expected_hashes: Optional dictionary of expected hashes

    Returns:
        Dictionary mapping file paths to integrity status
    """
    integrity = {}

    for file_path in file_paths:
        if not file_path.exists():
            integrity[str(file_path)] = False
            continue

        try:
            # Calculate actual hash
            actual_hash = calculate_file_hash(file_path)

            if expected_hashes and str(file_path) in expected_hashes:
                expected = expected_hashes[str(file_path)]
                integrity[str(file_path)] = actual_hash == expected
            else:
                # Just verify file is readable and not corrupted
                integrity[str(file_path)] = actual_hash is not None

        except Exception:
            integrity[str(file_path)] = False

    return integrity


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


def verify_cross_references(markdown_files: List[Path]) -> Dict[str, bool]:
    """Verify cross-reference integrity in markdown files.

    Args:
        markdown_files: List of markdown files to check

    Returns:
        Dictionary mapping reference types to integrity status
    """
    integrity = {
        'equations': True,
        'figures': True,
        'tables': True,
        'sections': True,
        'citations': True
    }

    # Collect all labels and references
    labels = set()
    references = set()

    for md_file in markdown_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find all labels (both LaTeX and markdown style)
            latex_labels = re.findall(r'\\label\{([^}]+)\}', content)
            markdown_labels = re.findall(r'\{#([^}]+)\}', content)
            labels.update(latex_labels)
            labels.update(markdown_labels)

            # Find all references (both LaTeX and markdown style)
            ref_matches = re.findall(r'\\ref\{([^}]+)\}', content)
            eqref_matches = re.findall(r'\\eqref\{([^}]+)\}', content)
            references.update(ref_matches)
            references.update(eqref_matches)

        except Exception:
            integrity = {k: False for k in integrity}
            break

    # Check if all references have corresponding labels
    missing_labels = references - labels

    if missing_labels:
        integrity = {k: False for k in integrity}

    return integrity


def verify_data_consistency(data_files: List[Path]) -> Dict[str, bool]:
    """Verify data file consistency and integrity.

    Args:
        data_files: List of data files to check

    Returns:
        Dictionary mapping consistency checks to status
    """
    consistency = {
        'file_readable': True,
        'data_integrity': True,
        'metadata_consistent': True
    }

    for data_file in data_files:
        if not data_file.exists():
            consistency['file_readable'] = False
            continue

        try:
            # Try to read as different data formats
            file_extension = data_file.suffix.lower()

            if file_extension == '.json':
                with open(data_file, 'r') as f:
                    json.load(f)
            elif file_extension == '.csv':
                # Basic CSV validation
                with open(data_file, 'r') as f:
                    lines = f.readlines()
                    if len(lines) > 0:
                        first_line = lines[0].strip()
                        if ',' not in first_line and '\t' not in first_line:
                            consistency['data_integrity'] = False
            elif file_extension in ['.npz', '.npy']:
                # NumPy array validation
                import numpy as np
                data = np.load(data_file)
                if not hasattr(data, 'shape'):
                    consistency['data_integrity'] = False
            elif file_extension == '.pkl':
                # Pickle validation
                with open(data_file, 'rb') as f:
                    pickle.load(f)

        except Exception:
            consistency['data_integrity'] = False
            break

    return consistency


def verify_academic_standards(markdown_files: List[Path]) -> Dict[str, bool]:
    """Verify compliance with academic writing standards.

    Args:
        markdown_files: List of markdown files to check

    Returns:
        Dictionary mapping academic standards to compliance status
    """
    standards = {
        'has_abstract': False,
        'has_introduction': False,
        'has_methodology': False,
        'has_results': False,
        'has_discussion': False,
        'has_conclusion': False,
        'has_references': False,
        'proper_citations': True,
        'equation_labels': True,
        'figure_captions': True
    }

    combined_content = ""

    for md_file in markdown_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                combined_content += f.read() + '\n'
        except Exception:
            standards = {k: False for k in standards}
            break

    # Check for required sections
    content_lower = combined_content.lower()

    standards['has_abstract'] = bool(re.search(r'\\section\{.*abstract|#\s*abstract', content_lower))
    standards['has_introduction'] = bool(re.search(r'\\section\{.*introduction|#\s*introduction', content_lower))
    standards['has_methodology'] = bool(re.search(r'\\section\{.*methodology|#\s*methodology|#\s*methods', content_lower))
    standards['has_results'] = bool(re.search(r'\\section\{.*results?|#\s*results?', content_lower))
    standards['has_discussion'] = bool(re.search(r'\\section\{.*discussion|#\s*discussion', content_lower))
    standards['has_conclusion'] = bool(re.search(r'\\section\{.*conclusion|#\s*conclusion', content_lower))
    standards['has_references'] = bool(re.search(r'\\section\{.*references?|#\s*references?|\\bibliography', content_lower))

    # Check for citations
    citation_patterns = [
        r'\\cite\{[^}]+\}',
        r'\\[a-z]*cite[a-z]*\{[^}]+\}',
        r'\[\d+\]',
        r'\(\d+\)'
    ]

    has_citations = any(re.search(pattern, combined_content) for pattern in citation_patterns)
    if not has_citations:
        standards['proper_citations'] = False

    # Check for equation labels
    equation_labels = re.findall(r'\\label\{eq:[^}]+\}', combined_content)
    if equation_labels:
        standards['equation_labels'] = True

    # Check for figure captions
    figure_captions = re.findall(r'\\caption\{[^}]+\}', combined_content)
    if figure_captions:
        standards['figure_captions'] = True

    return standards


def verify_output_integrity(output_dir: Path) -> IntegrityReport:
    """Perform comprehensive integrity verification of all outputs.

    Args:
        output_dir: Output directory to verify

    Returns:
        IntegrityReport with comprehensive verification results
    """
    report = IntegrityReport()

    if not output_dir.exists():
        report.issues.append(f"Output directory does not exist: {output_dir}")
        report.overall_integrity = False
        return report

    # Find all output files
    pdf_files = list(output_dir.rglob('*.pdf'))
    data_files = list(output_dir.rglob('*.csv')) + list(output_dir.rglob('*.npz')) + list(output_dir.rglob('*.json'))
    markdown_files = list(output_dir.rglob('*.md'))  # Look for markdown files in output directory

    # Verify file integrity
    report.file_integrity = verify_file_integrity(pdf_files + data_files)

    # Check for any file integrity failures
    if not all(report.file_integrity.values()):
        report.issues.append("Some output files failed integrity verification")
        report.overall_integrity = False

    # Verify cross-references
    report.cross_reference_integrity = verify_cross_references(markdown_files)

    # Check for any cross-reference failures
    if not all(report.cross_reference_integrity.values()):
        report.issues.append("Cross-reference integrity issues found")
        report.overall_integrity = False

    # Verify data consistency
    report.data_consistency = verify_data_consistency(data_files)

    # Check for any data consistency failures
    if not all(report.data_consistency.values()):
        report.issues.append("Data consistency issues found")
        report.overall_integrity = False

    # Verify academic standards
    report.academic_standards = verify_academic_standards(markdown_files)

    # Check for any academic standards failures
    missing_standards = [k for k, v in report.academic_standards.items() if not v]
    if missing_standards:
        report.warnings.append(f"Missing academic standards: {', '.join(missing_standards)}")

    # Generate recommendations
    if not report.overall_integrity:
        report.recommendations.append("Fix integrity issues before proceeding")
        report.recommendations.append("Check file permissions and paths")
        report.recommendations.append("Verify all cross-references are properly defined")

    if report.warnings:
        report.recommendations.append("Consider addressing academic standard warnings")

    return report


def generate_integrity_report(report: IntegrityReport) -> str:
    """Generate a human-readable integrity report.

    Args:
        report: IntegrityReport with verification results

    Returns:
        Formatted integrity report string
    """
    lines = []
    lines.append("=" * 60)
    lines.append("🔍 INTEGRITY VERIFICATION REPORT")
    lines.append("=" * 60)

    # Overall status
    status = "✅ PASSED" if report.overall_integrity else "❌ FAILED"
    lines.append(f"Overall Integrity: {status}")
    lines.append("")

    # File integrity
    lines.append("📁 File Integrity:")
    for file_path, integrity in report.file_integrity.items():
        status = "✅" if integrity else "❌"
        lines.append(f"  {status} {file_path}")
    lines.append("")

    # Cross-reference integrity
    lines.append("🔗 Cross-Reference Integrity:")
    for ref_type, integrity in report.cross_reference_integrity.items():
        status = "✅" if integrity else "❌"
        lines.append(f"  {status} {ref_type}")
    lines.append("")

    # Data consistency
    lines.append("📊 Data Consistency:")
    for check_type, integrity in report.data_consistency.items():
        status = "✅" if integrity else "❌"
        lines.append(f"  {status} {check_type}")
    lines.append("")

    # Academic standards
    lines.append("🎓 Academic Standards:")
    for standard, compliance in report.academic_standards.items():
        status = "✅" if compliance else "⚠️"
        lines.append(f"  {status} {standard}")
    lines.append("")

    # Issues
    if report.issues:
        lines.append("❌ Issues Found:")
        for issue in report.issues:
            lines.append(f"  • {issue}")
        lines.append("")

    # Warnings
    if report.warnings:
        lines.append("⚠️  Warnings:")
        for warning in report.warnings:
            lines.append(f"  • {warning}")
        lines.append("")

    # Recommendations
    if report.recommendations:
        lines.append("💡 Recommendations:")
        for rec in report.recommendations:
            lines.append(f"  • {rec}")
        lines.append("")

    lines.append("=" * 60)

    return '\n'.join(lines)


def validate_build_artifacts(output_dir: Path, expected_files: Optional[Dict[str, List[str]]] = None) -> Dict[str, Any]:
    """Validate that all expected build artifacts are present and correct.

    Args:
        output_dir: Output directory to validate
        expected_files: Optional dictionary of expected files by category

    Returns:
        Dictionary with validation results
    """
    validation = {
        'expected_files': [],
        'missing_files': [],
        'unexpected_files': [],
        'validation_passed': True
    }

    # Expected output structure (use provided expected_files or default)
    if expected_files is None:
        expected_structure = {
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
    else:
        expected_structure = expected_files

    # Check for missing expected files and directories
    for category, files in expected_structure.items():
        category_dir = output_dir / category
        if not category_dir.exists():
            # Missing entire directory
            for expected_file in files:
                validation['missing_files'].append(expected_file)
                validation['validation_passed'] = False
        else:
            # Directory exists, check for missing files
            for expected_file in files:
                expected_path = category_dir / expected_file
                if not expected_path.exists():
                    validation['missing_files'].append(expected_file)
                    validation['validation_passed'] = False
                else:
                    validation['expected_files'].append(expected_file)

    # Check for unexpected files (basic check)
    for item in output_dir.rglob('*'):
        if item.is_file():
            rel_path = item.relative_to(output_dir)
            is_expected = any(str(rel_path).startswith(cat) and any(f in str(rel_path) for f in files)
                            for cat, files in expected_structure.items())
            if not is_expected and item.name != 'project_combined.html':
                validation['unexpected_files'].append(str(rel_path))

    return validation


def check_file_permissions(output_dir: Path) -> Dict[str, Any]:
    """Check file permissions and accessibility.

    Args:
        output_dir: Output directory to check

    Returns:
        Dictionary with permission check results
    """
    permissions = {
        'readable': True,
        'writable': True,
        'executable': True,
        'issues': []
    }

    if not output_dir.exists():
        permissions['readable'] = False
        permissions['issues'].append(f"Output directory does not exist: {output_dir}")
        return permissions

    try:
        # Test read access
        test_file = output_dir / '.permission_test'
        test_file.write_text('test')
        test_file_content = test_file.read_text()
        test_file.unlink()

        if test_file_content != 'test':
            permissions['readable'] = False
            permissions['writable'] = False
            permissions['issues'].append("File read/write test failed")

    except Exception as e:
        permissions['writable'] = False
        permissions['issues'].append(f"Permission test failed: {e}")

    return permissions


def verify_output_completeness(output_dir: Path) -> Dict[str, Any]:
    """Verify that all expected outputs are present and complete.

    Args:
        output_dir: Output directory to verify

    Returns:
        Dictionary with completeness verification results
    """
    completeness = {
        'pdf_complete': True,
        'figures_complete': True,
        'data_complete': True,
        'latex_complete': True,
        'html_complete': True,
        'missing_outputs': [],
        'incomplete_outputs': []
    }

    # Check PDF completeness
    pdf_dir = output_dir / 'pdf'
    if pdf_dir.exists():
        expected_pdfs = [
            '01_abstract.pdf', '02_introduction.pdf', '03_methodology.pdf',
            '04_experimental_results.pdf', '05_discussion.pdf', '06_conclusion.pdf',
            '07_references.pdf', '10_symbols_glossary.pdf', 'project_combined.pdf'
        ]

        for pdf_file in expected_pdfs:
            pdf_path = pdf_dir / pdf_file
            if not pdf_path.exists():
                completeness['pdf_complete'] = False
                completeness['missing_outputs'].append(f"PDF: {pdf_file}")
            elif pdf_path.stat().st_size == 0:
                completeness['pdf_complete'] = False
                completeness['incomplete_outputs'].append(f"Empty PDF: {pdf_file}")

    # Check figures completeness
    figures_dir = output_dir / 'figures'
    if not figures_dir.exists():
        completeness['figures_complete'] = False
        completeness['missing_outputs'].append("Figures directory")
    elif figures_dir.exists():
        expected_figures = [
            'ablation_study.png', 'convergence_plot.png', 'data_structure.png',
            'example_figure.png', 'experimental_setup.png', 'hyperparameter_sensitivity.png',
            'image_classification_results.png', 'recommendation_scalability.png',
            'scalability_analysis.png', 'step_size_analysis.png'
        ]

        for fig_file in expected_figures:
            fig_path = figures_dir / fig_file
            if not fig_path.exists():
                completeness['figures_complete'] = False
                completeness['missing_outputs'].append(f"Figure: {fig_file}")
            elif fig_path.stat().st_size < 1000:  # Very small file
                completeness['incomplete_outputs'].append(f"Small figure: {fig_file}")

    # Check data completeness
    data_dir = output_dir / 'data'
    if not data_dir.exists():
        completeness['data_complete'] = False
        completeness['missing_outputs'].append("Data directory")
    elif data_dir.exists():
        expected_data = [
            'convergence_data.npz', 'dataset_summary.csv', 'example_data.csv',
            'example_data.npz', 'performance_comparison.csv'
        ]

        for data_file in expected_data:
            data_path = data_dir / data_file
            if not data_path.exists():
                completeness['data_complete'] = False
                completeness['missing_outputs'].append(f"Data: {data_file}")
            elif data_path.stat().st_size == 0:
                completeness['data_complete'] = False
                completeness['incomplete_outputs'].append(f"Empty data: {data_file}")

    # Check LaTeX completeness
    tex_dir = output_dir / 'tex'
    if not tex_dir.exists():
        completeness['latex_complete'] = False
        completeness['missing_outputs'].append("LaTeX directory")
    elif tex_dir.exists():
        expected_tex = [
            '01_abstract.tex', '02_introduction.tex', '03_methodology.tex',
            '04_experimental_results.tex', '05_discussion.tex', '06_conclusion.tex',
            '07_references.tex', '10_symbols_glossary.tex', 'project_combined.tex'
        ]

        for tex_file in expected_tex:
            tex_path = tex_dir / tex_file
            if not tex_path.exists():
                completeness['latex_complete'] = False
                completeness['missing_outputs'].append(f"LaTeX: {tex_file}")
            elif tex_path.stat().st_size == 0:
                completeness['latex_complete'] = False
                completeness['incomplete_outputs'].append(f"Empty LaTeX: {tex_file}")

    # Check HTML completeness
    html_file = output_dir / 'project_combined.html'
    if not html_file.exists():
        completeness['html_complete'] = False
        completeness['missing_outputs'].append("HTML: project_combined.html")
    elif html_file.stat().st_size == 0:
        completeness['html_complete'] = False
        completeness['incomplete_outputs'].append("Empty HTML: project_combined.html")

    return completeness


def create_integrity_manifest(output_dir: Path) -> Dict[str, Any]:
    """Create an integrity manifest for all output files.

    Args:
        output_dir: Output directory to create manifest for

    Returns:
        Dictionary with comprehensive integrity manifest
    """
    manifest = {
        'timestamp': os.path.getctime(output_dir) if output_dir.exists() else None,
        'file_count': 0,
        'total_size': 0,
        'file_hashes': {},
        'directory_structure': {}
    }

    if not output_dir.exists():
        return manifest

    # Calculate file hashes and collect metadata
    for item in output_dir.rglob('*'):
        if item.is_file():
            rel_path = str(item.relative_to(output_dir))
            file_hash = calculate_file_hash(item)
            file_size = item.stat().st_size

            manifest['file_hashes'][rel_path] = {
                'hash': file_hash,
                'size': file_size,
                'modified': item.stat().st_mtime
            }

            manifest['file_count'] += 1
            manifest['total_size'] += file_size

    # Create directory structure
    for dir_path in output_dir.rglob('*'):
        if dir_path.is_dir():
            rel_path = str(dir_path.relative_to(output_dir))
            manifest['directory_structure'][rel_path] = {
                'file_count': len(list(dir_path.glob('*'))),
                'total_size': sum(f.stat().st_size for f in dir_path.glob('*') if f.is_file())
            }

    return manifest


def save_integrity_manifest(manifest: Dict[str, Any], output_path: Path) -> None:
    """Save integrity manifest to file.

    Args:
        manifest: Integrity manifest dictionary
        output_path: Path to save manifest
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)


def load_integrity_manifest(manifest_path: Path) -> Optional[Dict[str, Any]]:
    """Load integrity manifest from file.

    Args:
        manifest_path: Path to manifest file

    Returns:
        Integrity manifest dictionary or None if loading fails
    """
    if not manifest_path.exists():
        return None

    try:
        with open(manifest_path, 'r') as f:
            return json.load(f)
    except Exception:
        return None


def verify_integrity_against_manifest(current_manifest: Dict[str, Any],
                                     saved_manifest: Dict[str, Any]) -> Dict[str, Any]:
    """Verify current integrity against a saved manifest.

    Args:
        current_manifest: Current integrity manifest
        saved_manifest: Saved integrity manifest for comparison

    Returns:
        Dictionary with integrity verification results
    """
    verification = {
        'file_count_changed': current_manifest['file_count'] != saved_manifest['file_count'],
        'total_size_changed': current_manifest['total_size'] != saved_manifest['total_size'],
        'files_changed': 0,
        'files_added': 0,
        'files_removed': 0,
        'details': {}
    }

    current_files = set(current_manifest['file_hashes'].keys())
    saved_files = set(saved_manifest['file_hashes'].keys())

    # Check for changed files
    for file_path in current_files & saved_files:
        current_hash = current_manifest['file_hashes'][file_path]['hash']
        saved_hash = saved_manifest['file_hashes'][file_path]['hash']

        if current_hash != saved_hash:
            verification['files_changed'] += 1
            verification['details'][file_path] = 'modified'

    # Check for added files
    for file_path in current_files - saved_files:
        verification['files_added'] += 1
        verification['details'][file_path] = 'added'

    # Check for removed files
    for file_path in saved_files - current_files:
        verification['files_removed'] += 1
        verification['details'][file_path] = 'removed'

    return verification
