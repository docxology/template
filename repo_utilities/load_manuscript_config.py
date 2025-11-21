#!/usr/bin/env python3
"""
Load manuscript configuration from config.yaml and export as environment variables.

This script reads manuscript/config.yaml and exports the values as environment
variables for use by bash scripts. Environment variables take precedence over
config file values (for backward compatibility).

Usage:
    source <(python3 repo_utilities/load_manuscript_config.py)
    # or
    eval "$(python3 repo_utilities/load_manuscript_config.py)"
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
except ImportError:
    print("# Error: PyYAML not installed. Install with: pip install pyyaml", file=sys.stderr)
    print("# Falling back to environment variables only", file=sys.stderr)
    sys.exit(0)


def load_config(config_path: Path) -> Optional[Dict[str, Any]]:
    """Load configuration from YAML file."""
    if not config_path.exists():
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"# Warning: Failed to load config file: {e}", file=sys.stderr)
        return None


def format_author_details(authors: list, doi: str = "") -> str:
    """Format author details string for LaTeX."""
    if not authors:
        return ""
    
    # Get primary/corresponding author (first one marked corresponding, or first)
    primary = next((a for a in authors if a.get('corresponding', False)), authors[0])
    
    parts = []
    if primary.get('orcid'):
        parts.append(f"ORCID: {primary['orcid']}")
    if primary.get('email'):
        parts.append(f"Email: {primary['email']}")
    if doi:
        parts.append(f"DOI: {doi}")
    
    # Join with "\\\\ " (double backslash + space) for LaTeX line breaks
    # In Python string: "\\\\ " represents two backslashes followed by space
    return "\\\\ ".join(parts)


def format_author_name(authors: list) -> str:
    """Format author name(s) for display."""
    if not authors:
        return "Project Author"
    
    # For single author, return name
    if len(authors) == 1:
        return authors[0].get('name', 'Project Author')
    
    # For multiple authors, return first author "et al." or list
    # Keep it simple: return first author name
    return authors[0].get('name', 'Project Author')


def export_config(config: Dict[str, Any], output_format: str = 'bash') -> None:
    """Export configuration as bash environment variable assignments."""
    if not config:
        return
    
    # Paper title
    paper_title = config.get('paper', {}).get('title', '')
    if paper_title and 'PROJECT_TITLE' not in os.environ:
        print(f'export PROJECT_TITLE="{paper_title}"')
    
    # Authors
    authors = config.get('authors', [])
    if authors:
        author_name = format_author_name(authors)
        if 'AUTHOR_NAME' not in os.environ:
            print(f'export AUTHOR_NAME="{author_name}"')
        
        # Get first author's ORCID and email
        primary = authors[0]
        if 'AUTHOR_ORCID' not in os.environ and primary.get('orcid'):
            print(f'export AUTHOR_ORCID="{primary["orcid"]}"')
        if 'AUTHOR_EMAIL' not in os.environ and primary.get('email'):
            print(f'export AUTHOR_EMAIL="{primary["email"]}"')
    
    # DOI
    doi = config.get('publication', {}).get('doi', '')
    if doi and 'DOI' not in os.environ:
        print(f'export DOI="{doi}"')
    
    # Export full author details for LaTeX
    # Only set if not already in environment (backward compatibility)
    if 'AUTHOR_DETAILS' not in os.environ:
        author_details = format_author_details(authors, doi)
        if author_details:
            # Escape quotes for bash, but preserve backslashes as-is
            # (format_author_details already returns "\\\\ " for LaTeX)
            author_details_escaped = author_details.replace('"', '\\"')
            print(f'export AUTHOR_DETAILS="{author_details_escaped}"')


def main():
    """Main function to load and export configuration."""
    # Determine repository root (parent of repo_utilities/)
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    # Try project/manuscript/config.yaml first (new monophyletic structure)
    # Fall back to manuscript/config.yaml for backward compatibility
    config_path = repo_root / 'project' / 'manuscript' / 'config.yaml'
    if not config_path.exists():
        config_path = repo_root / 'manuscript' / 'config.yaml'
    
    # Load configuration
    config = load_config(config_path)
    
    # Export configuration (only if not already set in environment)
    if config:
        export_config(config)
    else:
        # No config file found - use defaults (already handled by render_pdf.sh)
        pass


if __name__ == '__main__':
    main()

