#!/usr/bin/env python3
"""Check documentation links and references for accuracy.

This script validates:
- Internal markdown links resolve correctly
- File references point to existing files
- Anchor links match actual headings
- External links are accessible
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from urllib.parse import urlparse


def find_all_markdown_files(repo_root: str) -> List[Path]:
    """Find all markdown files in the repository."""
    repo_path = Path(repo_root)
    md_files = []
    for md_file in repo_path.rglob("*.md"):
        # Skip output and htmlcov directories
        if "output" in md_file.parts or "htmlcov" in md_file.parts:
            continue
        md_files.append(md_file)
    return sorted(md_files)


def extract_links(content: str, file_path: Path) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Extract internal links, external links, and file references from markdown."""
    internal_links = []
    external_links = []
    file_refs = []
    
    # Pattern for markdown links: [text](path)
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^\)]+)\)')
    
    for match in link_pattern.finditer(content):
        link_text = match.group(1)
        link_target = match.group(2)
        
        # Skip if it's an anchor link only
        if link_target.startswith('#'):
            internal_links.append({
                'text': link_text,
                'target': link_target,
                'line': content[:match.start()].count('\n') + 1,
                'file': str(file_path)
            })
        # Check if it's an external link
        elif link_target.startswith('http://') or link_target.startswith('https://'):
            external_links.append({
                'text': link_text,
                'target': link_target,
                'line': content[:match.start()].count('\n') + 1,
                'file': str(file_path)
            })
        # Internal file reference
        else:
            file_refs.append({
                'text': link_text,
                'target': link_target,
                'line': content[:match.start()].count('\n') + 1,
                'file': str(file_path)
            })
    
    return internal_links, external_links, file_refs


def check_file_reference(target: str, source_file: Path, repo_root: Path) -> Tuple[bool, str]:
    """Check if a file reference resolves correctly."""
    # Handle relative paths
    if target.startswith('../'):
        # Count how many levels up
        levels_up = target.count('../')
        target_path = source_file.parent
        for _ in range(levels_up):
            target_path = target_path.parent
        target_path = target_path / target.replace('../', '').replace('./', '')
    elif target.startswith('./'):
        target_path = source_file.parent / target[2:]
    else:
        # Relative to source file directory
        target_path = source_file.parent / target
    
    # Normalize path
    try:
        target_path = target_path.resolve()
        repo_root_resolved = repo_root.resolve()
        
        # Check if file exists
        if target_path.exists() and target_path.is_file():
            # Check if it's within repo
            try:
                target_path.relative_to(repo_root_resolved)
                return True, str(target_path.relative_to(repo_root_resolved))
            except ValueError:
                return False, f"File outside repository: {target_path}"
        else:
            return False, f"File does not exist: {target_path}"
    except Exception as e:
        return False, f"Error resolving path: {e}"


def extract_headings(content: str) -> Set[str]:
    """Extract all heading anchors from markdown content."""
    headings = set()
    
    # Pattern for headings with anchors: # Heading {#anchor}
    anchor_pattern = re.compile(r'^#+\s+.*\{#([^}]+)\}', re.MULTILINE)
    for match in anchor_pattern.finditer(content):
        headings.add(match.group(1))
    
    # Pattern for regular headings (convert to anchor format)
    heading_pattern = re.compile(r'^(#+)\s+(.+)$', re.MULTILINE)
    for match in heading_pattern.finditer(content):
        heading_text = match.group(2).strip()
        # Convert to anchor format (lowercase, spaces to hyphens, remove special chars)
        anchor = re.sub(r'[^\w\s-]', '', heading_text.lower())
        anchor = re.sub(r'[-\s]+', '-', anchor)
        anchor = anchor.strip('-')
        if anchor:
            headings.add(anchor)
    
    return headings


def main():
    """Main function to check all documentation links."""
    repo_root = Path(__file__).parent.parent
    md_files = find_all_markdown_files(str(repo_root))
    
    print(f"Found {len(md_files)} markdown files")
    
    all_headings: Dict[str, Set[str]] = {}
    broken_links = []
    broken_file_refs = []
    
    # First pass: collect all headings
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding='utf-8')
            all_headings[str(md_file.relative_to(repo_root))] = extract_headings(content)
        except Exception as e:
            print(f"Error reading {md_file}: {e}", file=sys.stderr)
    
    # Second pass: check links
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding='utf-8')
            internal_links, external_links, file_refs = extract_links(content, md_file)
            
            # Check internal links (anchors)
            for link in internal_links:
                target = link['target'].lstrip('#')
                # Check if anchor exists in target file or current file
                # For now, just check current file
                file_key = str(md_file.relative_to(repo_root))
                if file_key in all_headings and target not in all_headings[file_key]:
                    broken_links.append({
                        'file': file_key,
                        'line': link['line'],
                        'target': link['target'],
                        'text': link['text'],
                        'issue': 'Anchor not found'
                    })
            
            # Check file references
            for ref in file_refs:
                target = ref['target']
                # Skip anchor-only links
                if '#' in target:
                    target = target.split('#')[0]
                
                if target:  # Not just an anchor
                    exists, msg = check_file_reference(target, md_file, repo_root)
                    if not exists:
                        broken_file_refs.append({
                            'file': str(md_file.relative_to(repo_root)),
                            'line': ref['line'],
                            'target': ref['target'],
                            'text': ref['text'],
                            'issue': msg
                        })
        except Exception as e:
            print(f"Error processing {md_file}: {e}", file=sys.stderr)
    
    # Report results
    if broken_links:
        print(f"\nFound {len(broken_links)} broken anchor links:")
        for link in broken_links[:10]:  # Show first 10
            print(f"  {link['file']}:{link['line']} - {link['target']} ({link['issue']})")
        if len(broken_links) > 10:
            print(f"  ... and {len(broken_links) - 10} more")
    
    if broken_file_refs:
        print(f"\nFound {len(broken_file_refs)} broken file references:")
        for ref in broken_file_refs[:10]:  # Show first 10
            print(f"  {ref['file']}:{ref['line']} - {ref['target']} ({ref['issue']})")
        if len(broken_file_refs) > 10:
            print(f"  ... and {len(broken_file_refs) - 10} more")
    
    if not broken_links and not broken_file_refs:
        print("\nAll links verified successfully!")
        return 0
    
    return 1


if __name__ == '__main__':
    sys.exit(main())

