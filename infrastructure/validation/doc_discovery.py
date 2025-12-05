"""Phase 1: Discovery and Inventory for documentation scanning."""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

from infrastructure.validation.doc_models import DocumentationFile


def find_markdown_files(repo_root: Path) -> List[Path]:
    """Find all markdown files excluding output/htmlcov and virtual environments."""
    exclude_dirs = {'output', 'htmlcov', '.venv', 'venv', '__pycache__', '.pytest_cache', 
                   '.git', 'node_modules', '.tox', 'dist', 'build', '.mypy_cache'}
    md_files = []
    for md_file in repo_root.rglob("*.md"):
        # Skip if any part of the path is in exclude list
        if not any(excluded in md_file.parts for excluded in exclude_dirs):
            md_files.append(md_file)
    return sorted(md_files)


def catalog_agents_readme(md_files: List[Path], repo_root: Path) -> List[str]:
    """Catalog all AGENTS.md and README.md files."""
    agents_readme = []
    for md_file in md_files:
        if md_file.name in ('AGENTS.md', 'README.md'):
            agents_readme.append(str(md_file.relative_to(repo_root)))
    return sorted(agents_readme)


def find_config_files(repo_root: Path) -> Dict[str, Path]:
    """Find configuration files."""
    exclude_dirs = {'output', 'htmlcov', '.venv', 'venv', '__pycache__', '.pytest_cache',
                   '.git', 'node_modules', '.tox', 'dist', 'build', '.mypy_cache'}
    config_patterns = ['pyproject.toml', 'config.yaml', '*.toml', '*.yaml', '*.yml']
    configs = {}
    
    for pattern in config_patterns:
        for config_file in repo_root.rglob(pattern):
            # Skip if any part of the path is in exclude list
            if not any(excluded in config_file.parts for excluded in exclude_dirs):
                if config_file.name not in configs:
                    configs[config_file.name] = config_file
    
    return configs


def find_script_files(repo_root: Path) -> List[Path]:
    """Find all script files (Python and shell) excluding virtual environments."""
    exclude_dirs = {'output', 'htmlcov', '.venv', 'venv', '__pycache__', '.pytest_cache',
                   '.git', 'node_modules', '.tox', 'dist', 'build', '.mypy_cache', 'tests'}
    scripts = []
    for ext in ['*.py', '*.sh']:
        for script in repo_root.rglob(ext):
            # Skip if any part of the path is in exclude list
            if not any(excluded in script.parts for excluded in exclude_dirs):
                # Only include scripts in specific directories
                if any(part in script.parts for part in ['scripts', 'repo_utilities', 'src']):
                    scripts.append(script)
    
    return sorted(scripts)


def create_hierarchy(md_files: List[Path], repo_root: Path) -> Dict[str, List[str]]:
    """Create documentation hierarchy map."""
    hierarchy = defaultdict(list)
    for md_file in md_files:
        rel_path = str(md_file.relative_to(repo_root))
        directory = str(md_file.parent.relative_to(repo_root))
        if directory == '.':
            directory = 'root'
        hierarchy[directory].append(rel_path)
    return dict(hierarchy)


def identify_cross_references(md_files: List[Path]) -> Set[str]:
    """Identify cross-reference patterns."""
    cross_refs = set()
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^\)]+)\)')
    
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding='utf-8')
            for match in link_pattern.finditer(content):
                target = match.group(2)
                if not target.startswith('http') and not target.startswith('#'):
                    cross_refs.add(target)
        except Exception:
            pass
    
    return cross_refs


def categorize_documentation(md_files: List[Path], repo_root: Path) -> Dict[str, List[str]]:
    """Categorize documentation files."""
    categories = defaultdict(list)
    
    for md_file in md_files:
        rel_path = str(md_file.relative_to(repo_root))
        
        if 'docs/' in rel_path:
            if 'AGENTS' in md_file.name or 'README' in md_file.name:
                categories['directory_docs'].append(rel_path)
            elif 'HOW_TO' in md_file.name or 'GETTING_STARTED' in md_file.name:
                categories['user_guides'].append(rel_path)
            elif 'ARCHITECTURE' in md_file.name or 'WORKFLOW' in md_file.name:
                categories['architecture'].append(rel_path)
            elif 'API' in md_file.name or 'REFERENCE' in md_file.name:
                categories['api_docs'].append(rel_path)
            else:
                categories['general_docs'].append(rel_path)
        elif 'manuscript/' in rel_path:
            categories['manuscript'].append(rel_path)
        elif md_file.name in ('AGENTS.md', 'README.md'):
            categories['directory_docs'].append(rel_path)
        else:
            categories['other'].append(rel_path)
    
    return dict(categories)


def analyze_documentation_file(md_file: Path, repo_root: Path) -> DocumentationFile:
    """Analyze a documentation file and extract metadata."""
    try:
        content = md_file.read_text(encoding='utf-8')
        rel_path = str(md_file.relative_to(repo_root))
        directory = str(md_file.parent.relative_to(repo_root))
        
        # Determine category
        category = 'other'
        if 'docs/' in rel_path:
            category = 'documentation'
        elif 'manuscript/' in rel_path:
            category = 'manuscript'
        elif md_file.name in ('AGENTS.md', 'README.md'):
            category = 'directory_doc'
        
        # Count words and lines
        words = len(content.split())
        lines = len(content.split('\n'))
        
        # Check for links and code blocks
        has_links = bool(re.search(r'\[.*?\]\(.*?\)', content))
        has_code_blocks = bool(re.search(r'```', content))
        
        # Get modification time
        mtime = datetime.fromtimestamp(md_file.stat().st_mtime).isoformat()
        
        return DocumentationFile(
            path=str(md_file),
            relative_path=rel_path,
            directory=directory,
            name=md_file.name,
            category=category,
            word_count=words,
            line_count=lines,
            has_links=has_links,
            has_code_blocks=has_code_blocks,
            last_modified=mtime
        )
    except Exception as e:
        import sys
        print(f"  Warning: Error analyzing {md_file}: {e}", file=sys.stderr)
        return DocumentationFile(
            path=str(md_file),
            relative_path=str(md_file.relative_to(repo_root)),
            directory=str(md_file.parent.relative_to(repo_root)),
            name=md_file.name
        )


def run_discovery_phase(repo_root: Path) -> Dict:
    """Run Phase 1: Discovery and Inventory.
    
    Args:
        repo_root: Root path of the repository
        
    Returns:
        Dictionary with discovery results
    """
    print("Phase 1: Discovery and Inventory...")
    
    # Find all markdown files
    md_files = find_markdown_files(repo_root)
    print(f"  Found {len(md_files)} markdown files")
    
    # Catalog AGENTS.md and README.md files
    agents_readme = catalog_agents_readme(md_files, repo_root)
    print(f"  Found {len(agents_readme)} AGENTS.md/README.md files")
    
    # Identify configuration files
    config_files = find_config_files(repo_root)
    print(f"  Found {len(config_files)} configuration files")
    
    # Map script files
    script_files = find_script_files(repo_root)
    print(f"  Found {len(script_files)} script files")
    
    # Create documentation hierarchy
    hierarchy = create_hierarchy(md_files, repo_root)
    
    # Identify cross-reference patterns
    cross_refs = identify_cross_references(md_files)
    
    # Categorize documentation
    categories = categorize_documentation(md_files, repo_root)
    
    # Build documentation file metadata
    documentation_files = []
    for md_file in md_files:
        doc_file = analyze_documentation_file(md_file, repo_root)
        documentation_files.append(doc_file)
    
    inventory = {
        'markdown_files': len(md_files),
        'agents_readme_files': len(agents_readme),
        'config_files': len(config_files),
        'script_files': len(script_files),
        'hierarchy': hierarchy,
        'cross_references': len(cross_refs),
        'categories': categories,
        'agents_readme_list': agents_readme,
        'config_files_list': list(config_files.keys()),
        'script_files_list': [str(s.relative_to(repo_root)) for s in script_files],
        'documentation_files': documentation_files
    }
    
    return inventory

