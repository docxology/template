#!/usr/bin/env python3
"""Batch fix common documentation issues.

Fixes:
1. Test counts: 878 → 1934, 558 → 1884, 320 → 351
2. Config paths: manuscript/config.yaml → project/manuscript/config.yaml (from root)
"""

import re
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).parent.parent

# Fix patterns: (pattern, replacement, description)
FIXES = [
    # Test counts
    (r'\b878\s+test', '1934 test', 'Update total test count'),
    (r'878\s+tests\s+passing', '1934 tests passing', 'Update total test count'),
    (r'\(878\s+tests', '(1934 tests', 'Update total test count in parentheses'),
    (r'878/878\s+passing', '1934/1934 passing', 'Update test count in status'),
    (r'\b558\s+infrastructure', '1884 infrastructure', 'Update infrastructure test count'),
    (r'558\s+infra', '1884 infra', 'Update infrastructure test count (short)'),
    (r'\b320\s+project', '351 project', 'Update project test count'),
    (r'\(558\s*\+\s*320\)', '(1884 + 351)', 'Update test count breakdown'),
    (r'558\s+infrastructure\s+\+\s+320\s+project', '1884 infrastructure + 351 project', 'Update full test breakdown'),
    (r'558\s+infra\s+\+\s+320\s+project', '1884 infra + 351 project', 'Update test breakdown (short)'),
    
    # Config paths (from root only - skip files in project/ directory)
    # This will be handled more carefully below
]

# Files to skip (they may have correct relative paths)
SKIP_PATHS = [
    'project/manuscript/',
    'project/scripts/',
    'project/src/',
    'project/tests/',
    'project/AGENTS.md',
    'project/README.md',
]


def should_fix_config_path(file_path: Path) -> bool:
    """Determine if config path should be fixed in this file."""
    path_str = str(file_path)
    # Skip files in project/ directory (they may use relative paths correctly)
    for skip in SKIP_PATHS:
        if skip in path_str:
            return False
    return True


def fix_file(file_path: Path, dry_run: bool = False) -> List[Tuple[str, str, int]]:
    """Fix issues in a single file."""
    if not file_path.exists():
        return []
    
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        fixes_applied = []
        
        # Apply test count fixes
        for pattern, replacement, description in FIXES:
            matches = list(re.finditer(pattern, content, re.IGNORECASE))
            if matches:
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    fixes_applied.append((description, match.group(0), line_num))
        
        # Fix config paths (carefully)
        if should_fix_config_path(file_path):
            # Pattern for manuscript/config.yaml (not in project/ directory context)
            pattern = r'`manuscript/config\.yaml`'
            matches = list(re.finditer(pattern, content))
            if matches:
                content = re.sub(pattern, '`project/manuscript/config.yaml`', content)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    fixes_applied.append(('Fix config path', match.group(0), line_num))
            
            # Also fix in text (not code blocks)
            pattern = r'manuscript/config\.yaml'
            # But not if it's already project/manuscript/config.yaml
            if 'project/manuscript/config.yaml' not in content:
                matches = list(re.finditer(pattern, content))
                if matches:
                    # Check context - skip if in project/ directory reference
                    new_content = content
                    for match in reversed(matches):  # Reverse to preserve positions
                        before = content[max(0, match.start()-50):match.start()]
                        after = content[match.end():match.end()+50]
                        context = before + after
                        # Skip if it's clearly a relative path in project context
                        if 'project/' in before or 'project/' in after:
                            continue
                        new_content = new_content[:match.start()] + 'project/manuscript/config.yaml' + new_content[match.end():]
                        line_num = content[:match.start()].count('\n') + 1
                        fixes_applied.append(('Fix config path in text', match.group(0), line_num))
                    content = new_content
        
        # Write if changed
        if content != original and not dry_run:
            file_path.write_text(content, encoding='utf-8')
        
        return fixes_applied
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return []


def main():
    """Main function."""
    import sys
    
    dry_run = '--dry-run' in sys.argv
    
    print("🔧 Batch fixing documentation issues...")
    if dry_run:
        print("(DRY RUN - no files will be modified)\n")
    
    # Find all markdown files
    md_files = []
    for md_file in REPO_ROOT.rglob("*.md"):
        if "output" in md_file.parts or "htmlcov" in md_file.parts:
            continue
        md_files.append(md_file)
    
    print(f"Found {len(md_files)} markdown files\n")
    
    total_fixes = 0
    files_modified = 0
    
    for md_file in sorted(md_files):
        fixes = fix_file(md_file, dry_run=dry_run)
        if fixes:
            files_modified += 1
            total_fixes += len(fixes)
            rel_path = md_file.relative_to(REPO_ROOT)
            print(f"  {rel_path}: {len(fixes)} fixes")
            for desc, old, line in fixes[:3]:  # Show first 3
                print(f"    Line {line}: {desc}")
            if len(fixes) > 3:
                print(f"    ... and {len(fixes) - 3} more")
    
    print(f"\n{'='*60}")
    print(f"Total: {total_fixes} fixes in {files_modified} files")
    if dry_run:
        print("(DRY RUN - no files were modified)")
    print("="*60)


if __name__ == "__main__":
    main()

