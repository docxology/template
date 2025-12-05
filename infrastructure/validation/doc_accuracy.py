"""Phase 2: Accuracy Verification for documentation scanning."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import yaml

from infrastructure.validation.doc_models import AccuracyIssue, LinkIssue


def extract_headings(content: str) -> Set[str]:
    """Extract all heading anchors from markdown."""
    headings = set()
    
    # Pattern for headings with explicit anchors
    anchor_pattern = re.compile(r'^#+\s+.*\{#([^}]+)\}', re.MULTILINE)
    for match in anchor_pattern.finditer(content):
        headings.add(match.group(1))
    
    # Pattern for regular headings (convert to anchor format)
    heading_pattern = re.compile(r'^(#+)\s+(.+)$', re.MULTILINE)
    for match in heading_pattern.finditer(content):
        heading_text = match.group(2).strip()
        # Convert to anchor format
        anchor = re.sub(r'[^\w\s-]', '', heading_text.lower())
        anchor = re.sub(r'[-\s]+', '-', anchor)
        anchor = anchor.strip('-')
        if anchor:
            headings.add(anchor)
    
    return headings


def resolve_file_path(target: str, source_file: Path, repo_root: Path) -> Tuple[bool, str]:
    """Resolve a file path relative to source file."""
    if target.startswith('../'):
        levels_up = target.count('../')
        target_path = source_file.parent
        for _ in range(levels_up):
            target_path = target_path.parent
        target_path = target_path / target.replace('../', '').replace('./', '')
    elif target.startswith('./'):
        target_path = source_file.parent / target[2:]
    else:
        target_path = source_file.parent / target
    
    try:
        target_path = target_path.resolve()
        repo_root_resolved = repo_root.resolve()
        
        if target_path.exists() and target_path.is_file():
            try:
                target_path.relative_to(repo_root_resolved)
                return True, ""
            except ValueError:
                return False, f"File outside repository: {target_path}"
        else:
            return False, f"File does not exist: {target_path}"
    except Exception as e:
        return False, f"Error resolving path: {e}"


def check_links(md_files: List[Path], repo_root: Path, all_headings: Dict[str, Set[str]]) -> List[LinkIssue]:
    """Check all links in markdown files."""
    issues = []
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^\)]+)\)')
    
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding='utf-8')
            file_key = str(md_file.relative_to(repo_root))
            
            for match in link_pattern.finditer(content):
                link_text = match.group(1)
                target = match.group(2)
                line_num = content[:match.start()].count('\n') + 1
                
                # Check anchor links
                if target.startswith('#'):
                    anchor = target.lstrip('#')
                    if file_key in all_headings:
                        if anchor not in all_headings[file_key]:
                            issues.append(LinkIssue(
                                file=file_key,
                                line=line_num,
                                link_text=link_text,
                                target=target,
                                issue_type='broken_anchor',
                                issue_message=f"Anchor '{anchor}' not found in file"
                            ))
                
                # Check file references
                elif not target.startswith('http'):
                    file_part = target.split('#')[0] if '#' in target else target
                    if file_part:
                        resolved = resolve_file_path(file_part, md_file, repo_root)
                        if not resolved[0]:
                            issues.append(LinkIssue(
                                file=file_key,
                                line=line_num,
                                link_text=link_text,
                                target=target,
                                issue_type='broken_file',
                                issue_message=resolved[1]
                            ))
        except Exception as e:
            print(f"  Warning: Error checking links in {md_file}: {e}", file=sys.stderr)
    
    return issues


def extract_script_name(command: str) -> Optional[str]:
    """Extract script name from command."""
    # Look for ./script.sh or python script.py patterns
    match = re.search(r'\./([\w/]+\.(?:sh|py))', command)
    if match:
        return match.group(1)
    match = re.search(r'python.*?([\w/]+\.py)', command)
    if match:
        return match.group(1)
    return None


def verify_commands(md_files: List[Path], repo_root: Path) -> List[AccuracyIssue]:
    """Verify commands in documentation match actual implementations."""
    issues = []
    command_pattern = re.compile(r'```(?:bash|sh|shell)?\n(.*?)\n```', re.DOTALL)
    
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding='utf-8')
            file_key = str(md_file.relative_to(repo_root))
            
            for match in command_pattern.finditer(content):
                command_block = match.group(1)
                line_num = content[:match.start()].count('\n') + 1
                
                # Check for common script references
                for line in command_block.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Check if script exists
                        if './' in line or line.startswith('python'):
                            script_name = extract_script_name(line)
                            if script_name:
                                script_path = repo_root / script_name
                                if not script_path.exists():
                                    issues.append(AccuracyIssue(
                                        file=file_key,
                                        line=line_num,
                                        issue_type='command',
                                        issue_message=f"Referenced script '{script_name}' does not exist",
                                        severity='error'
                                    ))
        except Exception:
            pass
    
    return issues


def check_file_paths(md_files: List[Path], repo_root: Path) -> List[AccuracyIssue]:
    """Check file paths mentioned in documentation."""
    issues = []
    path_pattern = re.compile(r'`([\w/\.\-]+)`')
    
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding='utf-8')
            file_key = str(md_file.relative_to(repo_root))
            
            for match in path_pattern.finditer(content):
                path_str = match.group(1)
                line_num = content[:match.start()].count('\n') + 1
                
                # Check if it looks like a file path
                if '/' in path_str or path_str.endswith(('.md', '.py', '.sh', '.yaml', '.toml')):
                    resolved = resolve_file_path(path_str, md_file, repo_root)
                    if not resolved[0] and 'output' not in path_str:
                        issues.append(AccuracyIssue(
                            file=file_key,
                            line=line_num,
                            issue_type='path',
                            issue_message=f"Referenced path '{path_str}' may not exist: {resolved[1]}",
                            severity='warning'
                        ))
        except Exception:
            pass
    
    return issues


def validate_config_options(md_files: List[Path], config_files: Dict[str, Path]) -> List[AccuracyIssue]:
    """Validate configuration options mentioned in docs."""
    issues = []
    
    # Load actual config files
    config_data = {}
    if 'config.yaml' in config_files:
        try:
            with open(config_files['config.yaml'], 'r') as f:
                config_data['yaml'] = yaml.safe_load(f) or {}
        except Exception:
            pass
    
    # Check documentation for config references
    # This is a simplified check - could be enhanced to actually validate against config schema
    
    return issues


def check_terminology(md_files: List[Path]) -> List[AccuracyIssue]:
    """Check terminology consistency across documentation."""
    issues = []
    # This would check for inconsistent terminology
    # For now, return empty - could be enhanced with a terminology dictionary
    return issues


def run_accuracy_phase(
    md_files: List[Path],
    repo_root: Path,
    config_files: Dict[str, Path]
) -> Tuple[Dict, List[LinkIssue], List[AccuracyIssue], Dict[str, Set[str]]]:
    """Run Phase 2: Accuracy Verification.
    
    Args:
        md_files: List of markdown files to check
        repo_root: Root path of the repository
        config_files: Dictionary of config file paths
        
    Returns:
        Tuple of (accuracy_report, link_issues, accuracy_issues, all_headings)
    """
    print("Phase 2: Accuracy Verification...")
    
    # Collect headings for anchor validation
    all_headings: Dict[str, Set[str]] = {}
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding='utf-8')
            all_headings[str(md_file.relative_to(repo_root))] = extract_headings(content)
        except Exception as e:
            print(f"  Warning: Error reading {md_file}: {e}", file=sys.stderr)
    
    # Check links
    link_issues = check_links(md_files, repo_root, all_headings)
    print(f"  Found {len(link_issues)} link issues")
    
    # Verify commands
    command_issues = verify_commands(md_files, repo_root)
    print(f"  Found {len(command_issues)} command accuracy issues")
    
    # Check file paths
    path_issues = check_file_paths(md_files, repo_root)
    print(f"  Found {len(path_issues)} file path issues")
    
    # Validate configuration options
    config_issues = validate_config_options(md_files, config_files)
    print(f"  Found {len(config_issues)} configuration issues")
    
    # Check terminology consistency
    terminology_issues = check_terminology(md_files)
    print(f"  Found {len(terminology_issues)} terminology issues")
    
    # Combine all accuracy issues
    accuracy_issues = command_issues + path_issues + config_issues + terminology_issues
    
    accuracy_report = {
        'link_issues': len(link_issues),
        'command_issues': len(command_issues),
        'path_issues': len(path_issues),
        'config_issues': len(config_issues),
        'terminology_issues': len(terminology_issues),
        'total_issues': len(link_issues) + len(accuracy_issues)
    }
    
    return accuracy_report, link_issues, accuracy_issues, all_headings

