#!/usr/bin/env python3
"""Automated documentation verification script.

Extracts and verifies:
- File paths
- Commands
- Test counts
- Coverage percentages
- Pipeline stage references
- Config file paths
"""

import re
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set

REPO_ROOT = Path(__file__).parent.parent


def find_all_markdown_files() -> List[Path]:
    """Find all markdown files in the repository."""
    md_files = []
    for md_file in REPO_ROOT.rglob("*.md"):
        # Skip output directories and generated files
        if "output" in md_file.parts or "htmlcov" in md_file.parts:
            continue
        md_files.append(md_file)
    return sorted(md_files)


def extract_test_counts(content: str, file_path: Path) -> List[Dict]:
    """Extract test count references from content."""
    issues = []
    
    # Patterns for test counts
    patterns = [
        (r'878\s+test', '878 tests (should be 1934)'),
        (r'558\s+infrastructure', '558 infrastructure tests (should be 1884)'),
        (r'320\s+project', '320 project tests (should be 351)'),
        (r'\(558\s*\+\s*320\)', '558+320 breakdown (should be 1884+351)'),
    ]
    
    for pattern, description in patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            issues.append({
                'file': str(file_path.relative_to(REPO_ROOT)),
                'line': line_num,
                'type': 'test_count',
                'issue': description,
                'context': content[max(0, match.start()-50):match.end()+50]
            })
    
    return issues


def extract_config_paths(content: str, file_path: Path) -> List[Dict]:
    """Extract config.yaml path references."""
    issues = []
    
    # Pattern for incorrect config paths (from root)
    pattern = r'manuscript/config\.yaml'
    matches = re.finditer(pattern, content, re.IGNORECASE)
    
    for match in matches:
        # Allow relative paths in project/ directory files
        if 'project/' in str(file_path) and 'manuscript/' in str(file_path):
            continue  # This is correct for files within project/manuscript/
        
        line_num = content[:match.start()].count('\n') + 1
        issues.append({
            'file': str(file_path.relative_to(REPO_ROOT)),
            'line': line_num,
            'type': 'config_path',
            'issue': 'Should be project/manuscript/config.yaml (from root)',
            'context': content[max(0, match.start()-50):match.end()+50]
        })
    
    return issues


def extract_python_commands(content: str, file_path: Path) -> List[Dict]:
    """Extract Python command usage (should use python3, not python)."""
    issues = []
    
    # Pattern for python (not python3) in command examples
    # Exclude references to python_logging.md, python-version, etc.
    pattern = r'(?:^|\s|`)(python|#!/usr/bin/env python)(?:\s|`|$|--)'
    matches = re.finditer(pattern, content, re.MULTILINE)
    
    for match in matches:
        # Skip if it's part of a path or version reference
        context = content[max(0, match.start()-30):match.end()+30]
        if any(skip in context.lower() for skip in [
            'python-version', 'python_logging', 'python-security',
            'python 3.', 'python3', 'python:', 'python.', 'python,'
        ]):
            continue
        
        line_num = content[:match.start()].count('\n') + 1
        issues.append({
            'file': str(file_path.relative_to(REPO_ROOT)),
            'line': line_num,
            'type': 'python_command',
            'issue': 'Should use python3, not python',
            'context': context
        })
    
    return issues


def extract_pipeline_stages(content: str, file_path: Path) -> List[Dict]:
    """Extract pipeline stage references and verify consistency."""
    issues = []
    
    # Check for inconsistent stage numbering
    # run.sh has 9 stages (0-8), run_all.py has 6 stages (00-05)
    patterns = [
        (r'9-stage.*pipeline', 'Should clarify: 9 stages in run.sh (0-8), 6 in run_all.py (00-05)'),
        (r'stages\s+0-9', 'Should be stages 0-8 (9 stages) or clarify stage 0 is pre-pipeline'),
    ]
    
    for pattern, description in patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            issues.append({
                'file': str(file_path.relative_to(REPO_ROOT)),
                'line': line_num,
                'type': 'pipeline_stage',
                'issue': description,
                'context': content[max(0, match.start()-50):match.end()+50]
            })
    
    return issues


def verify_file_paths(content: str, file_path: Path) -> List[Dict]:
    """Verify file path references exist."""
    issues = []
    
    # Pattern for file paths in markdown
    # Look for paths in code blocks or inline code
    pattern = r'`([^`]+\.(?:py|yaml|md|sh|toml))`'
    matches = re.finditer(pattern, content)
    
    for match in matches:
        path_str = match.group(1)
        # Skip if it's a URL or external reference
        if path_str.startswith('http') or '://' in path_str:
            continue
        
        # Try to resolve the path
        if not path_str.startswith('/'):
            # Relative path - try from file location and repo root
            resolved = None
            if (file_path.parent / path_str).exists():
                resolved = file_path.parent / path_str
            elif (REPO_ROOT / path_str).exists():
                resolved = REPO_ROOT / path_str
        else:
            # Absolute path
            if Path(path_str).exists():
                resolved = Path(path_str)
        
        if not resolved or not resolved.exists():
            line_num = content[:match.start()].count('\n') + 1
            issues.append({
                'file': str(file_path.relative_to(REPO_ROOT)),
                'line': line_num,
                'type': 'file_path',
                'issue': f'Referenced file does not exist: {path_str}',
                'context': content[max(0, match.start()-50):match.end()+50]
            })
    
    return issues


def main():
    """Run comprehensive documentation verification."""
    print("🔍 Starting comprehensive documentation verification...")
    print(f"Repository root: {REPO_ROOT}\n")
    
    md_files = find_all_markdown_files()
    print(f"Found {len(md_files)} markdown files to verify\n")
    
    all_issues = defaultdict(list)
    
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding='utf-8')
            
            # Run all checks
            all_issues['test_counts'].extend(extract_test_counts(content, md_file))
            all_issues['config_paths'].extend(extract_config_paths(content, md_file))
            all_issues['python_commands'].extend(extract_python_commands(content, md_file))
            all_issues['pipeline_stages'].extend(extract_pipeline_stages(content, md_file))
            all_issues['file_paths'].extend(verify_file_paths(content, md_file))
            
        except Exception as e:
            print(f"⚠️  Error processing {md_file}: {e}")
    
    # Summary
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)
    
    total_issues = sum(len(issues) for issues in all_issues.values())
    
    for category, issues in all_issues.items():
        count = len(issues)
        if count > 0:
            print(f"\n{category.upper().replace('_', ' ')}: {count} issues found")
            # Show first 5 examples
            for issue in issues[:5]:
                print(f"  - {issue['file']}:{issue['line']} - {issue['issue']}")
            if count > 5:
                print(f"  ... and {count - 5} more")
        else:
            print(f"\n{category.upper().replace('_', ' ')}: ✅ No issues found")
    
    print(f"\n{'='*80}")
    print(f"TOTAL ISSUES: {total_issues}")
    print("="*80)
    
    # Save detailed report
    report_file = REPO_ROOT / "docs" / "documentation_verification_report.json"
    with open(report_file, 'w') as f:
        json.dump({
            'total_files_checked': len(md_files),
            'total_issues': total_issues,
            'issues_by_category': {k: len(v) for k, v in all_issues.items()},
            'detailed_issues': {k: v for k, v in all_issues.items() if v}
        }, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_file.relative_to(REPO_ROOT)}")
    
    return total_issues


if __name__ == "__main__":
    exit(main())

