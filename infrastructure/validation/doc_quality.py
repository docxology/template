"""Phase 4: Quality Assessment for documentation scanning."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

from infrastructure.validation.doc_models import QualityIssue


def assess_clarity(content: str, md_file: Path, lines: List[str], repo_root: Path) -> List[QualityIssue]:
    """Assess clarity and readability."""
    issues = []
    file_key = str(md_file.relative_to(repo_root))
    
    # Check for very long lines
    for i, line in enumerate(lines, 1):
        if len(line) > 120 and not line.startswith('```'):
            issues.append(QualityIssue(
                file=file_key,
                line=i,
                issue_type='clarity',
                issue_message="Line exceeds 120 characters - may affect readability",
                severity='info'
            ))
    
    return issues


def assess_actionability(content: str, md_file: Path, lines: List[str], repo_root: Path) -> List[QualityIssue]:
    """Assess actionability of instructions."""
    issues = []
    # Check for imperative verbs in instructions
    # This is a simplified check
    return issues


def assess_maintainability(content: str, md_file: Path, lines: List[str], repo_root: Path) -> List[QualityIssue]:
    """Assess maintainability (duplication, organization)."""
    issues = []
    # Check for duplicate content
    # This could be enhanced
    return issues


def check_formatting(content: str, md_file: Path, lines: List[str], repo_root: Path) -> List[QualityIssue]:
    """Check formatting consistency."""
    issues = []
    file_key = str(md_file.relative_to(repo_root))
    
    # Check heading hierarchy
    prev_level = 0
    for i, line in enumerate(lines, 1):
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            if level > prev_level + 1:
                issues.append(QualityIssue(
                    file=file_key,
                    line=i,
                    issue_type='formatting',
                    issue_message=f"Heading level jumps from {prev_level} to {level}",
                    severity='info'
                ))
            prev_level = level
    
    return issues


def group_quality_by_type(issues: List[QualityIssue]) -> Dict[str, int]:
    """Group quality issues by type."""
    types = defaultdict(int)
    for issue in issues:
        types[issue.issue_type] += 1
    return dict(types)


def group_quality_by_severity(issues: List[QualityIssue]) -> Dict[str, int]:
    """Group quality issues by severity."""
    severities = defaultdict(int)
    for issue in issues:
        severities[issue.severity] += 1
    return dict(severities)


def run_quality_phase(md_files: List[Path], repo_root: Path) -> Tuple[Dict, List[QualityIssue]]:
    """Run Phase 4: Quality Assessment.
    
    Args:
        md_files: List of markdown files to assess
        repo_root: Root path of the repository
        
    Returns:
        Tuple of (quality_report, quality_issues)
    """
    print("Phase 4: Quality Assessment...")
    
    quality_issues = []
    
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            # Check clarity and readability
            clarity_issues = assess_clarity(content, md_file, lines, repo_root)
            quality_issues.extend(clarity_issues)
            
            # Check actionability
            actionability_issues = assess_actionability(content, md_file, lines, repo_root)
            quality_issues.extend(actionability_issues)
            
            # Check maintainability
            maintainability_issues = assess_maintainability(content, md_file, lines, repo_root)
            quality_issues.extend(maintainability_issues)
            
            # Check formatting
            formatting_issues = check_formatting(content, md_file, lines, repo_root)
            quality_issues.extend(formatting_issues)
            
        except Exception as e:
            import sys
            print(f"  Warning: Error assessing {md_file}: {e}", file=sys.stderr)
    
    quality_report = {
        'total_issues': len(quality_issues),
        'by_type': group_quality_by_type(quality_issues),
        'severity_breakdown': group_quality_by_severity(quality_issues)
    }
    
    print(f"  Found {len(quality_issues)} quality issues")
    return quality_report, quality_issues

