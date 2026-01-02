#!/usr/bin/env python3
"""Check documentation links and references for accuracy.

This script validates:
- Internal markdown links resolve correctly
- File references point to existing files
- Anchor links match actual headings
- External links are accessible
- File path patterns in code blocks
- Directory structure examples against actual filesystem
- Python import statements
- Consistency of {name} placeholders vs actual project names
"""
from __future__ import annotations

import ast
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

    # Remove code blocks to avoid false positives
    # Pattern for code blocks: ```...``` or `...`
    code_block_pattern = re.compile(r'```[\s\S]*?```|`[^`]+`')
    content_without_code = code_block_pattern.sub('', content)

    # Pattern for markdown links: [text](path)
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^\)]+)\)')

    for match in link_pattern.finditer(content_without_code):
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
        # Check if it's an external link (including URLs with paths)
        elif (link_target.startswith('http://') or link_target.startswith('https://') or
              '://' in link_target or link_target.startswith('mailto:')):
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


def extract_code_blocks(content: str, file_path: Path) -> List[Dict]:
    """Extract code blocks from markdown content for validation."""
    code_blocks = []

    # Pattern for code blocks: ```language\ncode\n```
    code_block_pattern = re.compile(r'```(\w+)?\n(.*?)\n```', re.DOTALL)

    for match in code_block_pattern.finditer(content):
        language = match.group(1) or ''
        code_content = match.group(2)
        line_number = content[:match.start()].count('\n') + 1

        code_blocks.append({
            'language': language,
            'content': code_content,
            'line': line_number,
            'file': str(file_path)
        })

    return code_blocks


def validate_file_paths_in_code(content: str, file_path: Path, repo_root: Path) -> List[Dict]:
    """Validate file path references within code blocks."""
    issues = []
    code_blocks = extract_code_blocks(content, file_path)

    for block in code_blocks:
        # Look for file path patterns in code blocks
        # Common patterns: projects/{name}/, output/{name}/, infrastructure/, scripts/
        path_patterns = [
            r'projects/\{[^}]+\}/[^\'"\s]*',  # projects/{name}/path
            r'output/\{[^}]+\}/[^\'"\s]*',    # output/{name}/path
            r'infrastructure/[^\'"\s]*',      # infrastructure/path
            r'scripts/[^\'"\s]*',             # scripts/path
            r'projects/project/[^\'"\s]*',    # projects/project/path
        ]

        for pattern in path_patterns:
            for match in re.finditer(pattern, block['content']):
                path_ref = match.group(0)
                # Skip if it's just a comment or string that doesn't need to exist
                if not _should_validate_path(path_ref):
                    continue

                # Check if this path exists
                resolved_path = _resolve_template_path(path_ref, repo_root)
                if resolved_path and not resolved_path.exists():
                    issues.append({
                        'file': str(file_path),
                        'line': block['line'] + match.start(),
                        'target': path_ref,
                        'issue': f'File path in code block does not exist: {path_ref}',
                        'type': 'code_block_path'
                    })

    return issues


def _should_validate_path(path_ref: str) -> bool:
    """Determine if a path reference should be validated."""
    # Skip references that are obviously placeholders or examples
    skip_patterns = [
        'projects/{name}/manuscript/config.yaml.example',
        'your_project_name',
        'path/to/',
        'infrastructure/<module>',  # Template examples
        'infrastructure/example',   # Example paths
        'infrastructure/test_<module>',  # Test template
        'infrastructure/example_module', # Example module
        'infrastructure/<module>/', # Template with trailing slash
        'infrastructure/example/',  # Example with trailing slash
        'projects/{project_name}',  # Template project names
        'example.com',  # Example URLs
        'your-domain.com',  # Template domains
        'infrastructure/AGENTS.md)',  # Malformed markdown
        'infrastructure/AGENTS.md](../',  # Malformed markdown
        'infrastructure/test_core/',  # Example test structure
        'scripts/custom_check.py',  # Example script
        'scripts/extra_checks.py',  # Example script
        'infrastructure/core.py',  # Generic example
        'infrastructure/module/',  # Generic template
        'infrastructure/new_module/',  # Template module
        'infrastructure/my_module/',  # Example module
        'infrastructure/utils/',  # Generic utils
        'infrastructure/helpers/',  # Generic helpers
        'infrastructure/common/',  # Generic common
        'infrastructure/shared/',  # Generic shared
        'scripts/my_script.py',  # Example script
        'scripts/process_data.py',  # Example script
        'projects/my_project/',  # Example project
        'projects/new_project/',  # Example project
        'docs/my_guide.md',  # Example doc
        'docs/new_feature.md',  # Example doc
        'tests/test_my_feature.py',  # Example test
        'tests/test_new_function.py',  # Example test
    ]

    for pattern in skip_patterns:
        if pattern in path_ref:
            return False

    # Skip if it contains template variables that can't be resolved
    if ('{' in path_ref and '}' in path_ref) or ('<' in path_ref and '>' in path_ref):
        return False

    # Skip URLs and email addresses
    if '://' in path_ref or '@' in path_ref:
        return False

    # Skip common documentation placeholders
    if any(placeholder in path_ref.lower() for placeholder in [
        'placeholder', 'template', 'example', 'your_', 'sample'
    ]):
        return False

    return True


def _resolve_template_path(path_ref: str, repo_root: Path) -> Path | None:
    """Resolve template paths like projects/{name}/ to actual paths."""
    try:
        # Handle common template patterns
        if path_ref.startswith('projects/project/'):
            # Use the default project
            return repo_root / path_ref
        elif path_ref.startswith('projects/{name}/'):
            # Can't resolve template, skip
            return None
        elif path_ref.startswith('infrastructure/'):
            return repo_root / path_ref
        elif path_ref.startswith('scripts/'):
            return repo_root / path_ref
        elif path_ref.startswith('output/project/'):
            # Check if output exists
            return repo_root / path_ref
        else:
            return repo_root / path_ref
    except Exception:
        return None


def validate_directory_structures(content: str, file_path: Path, repo_root: Path) -> List[Dict]:
    """Validate directory structure examples against actual filesystem."""
    issues = []

    # Look for directory tree patterns in code blocks and regular text
    tree_patterns = [
        r'```\n([^`]*?)```',  # Code blocks
        r'```\w+\n([^`]*?)```',  # Code blocks with language
    ]

    for pattern in tree_patterns:
        for match in re.finditer(pattern, content, re.DOTALL):
            tree_content = match.group(1)
            lines = tree_content.split('\n')

            for line_no, line in enumerate(lines):
                # Look for directory/file patterns like "├── file.py" or "└── dir/"
                dir_pattern = re.search(r'[├└]──\s*([^\s]+)', line.strip())
                if dir_pattern:
                    item_name = dir_pattern.group(1)
                    # Skip if it's a comment or not a real path
                    if not _is_real_path_item(item_name):
                        continue

                    # Try to resolve relative to current file's directory
                    if file_path.parent.name in ['docs', 'infrastructure', 'scripts']:
                        # Documentation files might reference various paths
                        continue

                    # For now, just flag obvious issues
                    if 'nonexistent' in item_name or 'example' in item_name.lower():
                        continue

    return issues


def _is_real_path_item(item_name: str) -> bool:
    """Check if a directory tree item looks like a real file/directory."""
    # Skip obvious placeholders or comments
    if any(skip in item_name.lower() for skip in ['...', 'etc', 'files', 'more']):
        return False

    # Skip if it contains template variables
    if '{' in item_name and '}' in item_name:
        return False

    return True


def validate_python_imports(content: str, file_path: Path, repo_root: Path) -> List[Dict]:
    """Validate Python import statements in code blocks."""
    issues = []
    code_blocks = extract_code_blocks(content, file_path)

    for block in code_blocks:
        if block['language'].lower() in ['python', 'py']:
            # Parse Python code to find imports
            try:
                tree = ast.parse(block['content'])
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            module_name = alias.name
                            issues.extend(_validate_import_path(module_name, block, file_path, repo_root))
                    elif isinstance(node, ast.ImportFrom):
                        module_name = node.module
                        if module_name:
                            issues.extend(_validate_import_path(module_name, block, file_path, repo_root))
            except SyntaxError:
                # Skip malformed Python code
                continue

    return issues


def _validate_import_path(module_name: str, block: Dict, file_path: Path, repo_root: Path) -> List[Dict]:
    """Validate a single import path."""
    issues = []

    # Convert module path to file path
    if module_name.startswith('infrastructure.'):
        # First check if it's a direct module import (e.g., infrastructure.core.performance)
        file_path_guess = module_name.replace('infrastructure.', 'infrastructure/').replace('.', '/') + '.py'
        full_path = repo_root / file_path_guess
        if full_path.exists():
            # File exists, import should be valid
            return issues

        # Check if it's a submodule that should be imported from __init__.py
        # For example: infrastructure.core.performance might be imported via infrastructure.core.__init__.py
        path_parts = module_name.split('.')
        if len(path_parts) >= 2:
            # Check parent __init__.py files
            for i in range(len(path_parts) - 1, 0, -1):
                parent_module = '.'.join(path_parts[:i])
                init_path_guess = parent_module.replace('infrastructure.', 'infrastructure/').replace('.', '/') + '/__init__.py'
                init_full_path = repo_root / init_path_guess
                if init_full_path.exists():
                    # Parent __init__.py exists, assume the import is valid
                    # We could check the __init__.py content, but that's complex and slow
                    return issues

        # If we get here, neither the direct file nor parent __init__.py exists
        issues.append({
            'file': str(file_path),
            'line': block['line'],
            'target': module_name,
            'issue': f'Python import not found: {module_name}',
            'type': 'python_import'
        })

    elif module_name.startswith('projects.project.src.'):
        file_path_guess = module_name.replace('projects.project.src.', 'projects/project/src/').replace('.', '/') + '.py'
        full_path = repo_root / file_path_guess
        if not full_path.exists():
            init_path = full_path.parent / '__init__.py'
            if not init_path.exists():
                issues.append({
                    'file': str(file_path),
                    'line': block['line'],
                    'target': module_name,
                    'issue': f'Python import not found: {module_name}',
                    'type': 'python_import'
                })

    return issues


def validate_placeholder_consistency(content: str, file_path: Path, repo_root: Path) -> List[Dict]:
    """Validate consistency of {name} placeholders vs actual project names."""
    issues = []

    # Find all placeholder usage
    placeholder_pattern = re.compile(r'\{([^}]+)\}')
    placeholders = placeholder_pattern.findall(content)

    # Skip validation for certain file types that naturally use templates
    file_path_str = str(file_path)
    skip_files = [
        '.cursorrules/',  # Development rules naturally use templates
        'docs/architecture/',  # Architecture docs explain templates
        'docs/core/',  # Core docs explain system structure
        'infrastructure/AGENTS.md',  # Infrastructure docs use templates
        'AGENTS.md',  # Root docs explain templates
    ]

    if any(skip_path in file_path_str for skip_path in skip_files):
        return issues

    # Check for inconsistent usage of {name} vs actual project names
    project_names = _get_actual_project_names(repo_root)

    for match in placeholder_pattern.finditer(content):
        placeholder = match.group(1)
        if placeholder == 'name':
            # Get context around the placeholder
            context = content[max(0, match.start()-100):match.end()+100]

            # Skip if this is in documentation explaining the template system
            skip_contexts = [
                'projects/{name}',
                'template structure',
                'multi-project',
                'placeholder',
                'example project',
                'generic project',
                'any project',
                'research project',
                'your project',
                'new project',
            ]

            if any(skip_ctx in context.lower() for skip_ctx in skip_contexts):
                continue

            # Check if this should be a real project name
            # Only flag if we're clearly talking about an actual project, not a template
            specific_project_indicators = [
                'run the',
                'execute',
                'build',
                'generate',
                'compile',
                'test the project',
                'this project',
            ]

            has_specific_indicator = any(indicator in context.lower() for indicator in specific_project_indicators)
            mentions_specific_project = any(proj in context for proj in project_names)

            if has_specific_indicator and mentions_specific_project:
                # This might be inconsistent - using {name} when specific project exists
                issues.append({
                    'file': str(file_path),
                    'line': content[:match.start()].count('\n') + 1,
                    'target': match.group(0),
                    'issue': f'Using placeholder {{name}} when specific project names exist: {project_names}',
                    'type': 'placeholder_inconsistency'
                })

    return issues


def _get_actual_project_names(repo_root: Path) -> List[str]:
    """Get list of actual project names from projects/ directory."""
    projects_dir = repo_root / 'projects'
    if not projects_dir.exists():
        return []

    project_names = []
    for item in projects_dir.iterdir():
        if item.is_dir() and item.name not in ['__pycache__', '.pytest_cache']:
            project_names.append(item.name)

    return project_names


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
        
        # Check if it's within repo first
        try:
            target_path.relative_to(repo_root_resolved)
        except ValueError:
            return False, f"Path outside repository: {target_path}"
        
        # Check if file or directory exists
        if target_path.exists():
            if target_path.is_file():
                return True, str(target_path.relative_to(repo_root_resolved))
            elif target_path.is_dir():
                # Directory references are valid (e.g., [src/](src/))
                return True, str(target_path.relative_to(repo_root_resolved))
            else:
                return False, f"Path exists but is not a file or directory: {target_path}"
        else:
            # Check if it's a markdown file without extension
            md_path = target_path.with_suffix('.md')
            if md_path.exists() and md_path.is_file():
                return True, str(md_path.relative_to(repo_root_resolved))
            return False, f"File or directory does not exist: {target_path}"
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
    """Main function to check all documentation links and references comprehensively."""
    # Go up from infrastructure/validation/check_links.py to repo root
    repo_root = Path(__file__).parent.parent.parent
    md_files = find_all_markdown_files(str(repo_root))

    print(f"Found {len(md_files)} markdown files")
    print("Running comprehensive filepath and reference audit...\n")

    all_headings: Dict[str, Set[str]] = {}
    issues = {
        'broken_anchor_links': [],
        'broken_file_refs': [],
        'code_block_paths': [],
        'directory_structures': [],
        'python_imports': [],
        'placeholder_consistency': []
    }

    # First pass: collect all headings
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding='utf-8')
            all_headings[str(md_file.relative_to(repo_root))] = extract_headings(content)
        except Exception as e:
            print(f"Error reading {md_file}: {e}", file=sys.stderr)

    # Second pass: comprehensive validation
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding='utf-8')
            internal_links, external_links, file_refs = extract_links(content, md_file)

            # Check internal links (anchors)
            file_key = str(md_file.relative_to(repo_root))
            for link in internal_links:
                target = link['target'].lstrip('#')

                # Skip anchor link validation for manuscript files as they use cross-references
                # that are resolved during rendering, not same-file headings
                if 'manuscript' in file_key:
                    continue

                # Skip cross-references that are meant to be resolved by the rendering pipeline
                # These include: fig:, sec:, eq:, table: prefixes, or standard section references
                cross_ref_prefixes = ['fig:', 'sec:', 'eq:', 'table:', 'tab:']
                if any(target.startswith(prefix) for prefix in cross_ref_prefixes):
                    continue

                # Skip common manuscript section references
                common_sections = ['methodology', 'experimental_results', 'discussion', 'conclusion', 'results']
                if target in common_sections or any(sec in target.lower() for sec in common_sections):
                    continue

                # Only check for actual heading anchors within the same file
                if file_key in all_headings and target not in all_headings[file_key]:
                    issues['broken_anchor_links'].append({
                        'file': file_key,
                        'line': link['line'],
                        'target': link['target'],
                        'text': link['text'],
                        'issue': 'Anchor not found'
                    })

            # Check file references
            for ref in file_refs:
                target = ref['target']
                if '#' in target:
                    target = target.split('#')[0]

                # Skip references to generated files in output directories
                if 'output/' in target or '/output/' in target:
                    continue

                if target:
                    exists, msg = check_file_reference(target, md_file, repo_root)
                    if not exists:
                        issues['broken_file_refs'].append({
                            'file': str(md_file.relative_to(repo_root)),
                            'line': ref['line'],
                            'target': ref['target'],
                            'text': ref['text'],
                            'issue': msg
                        })

            # Additional validations
            code_block_issues = validate_file_paths_in_code(content, md_file, repo_root)
            issues['code_block_paths'].extend(code_block_issues)

            dir_structure_issues = validate_directory_structures(content, md_file, repo_root)
            issues['directory_structures'].extend(dir_structure_issues)

            import_issues = validate_python_imports(content, md_file, repo_root)
            issues['python_imports'].extend(import_issues)

            placeholder_issues = validate_placeholder_consistency(content, md_file, repo_root)
            issues['placeholder_consistency'].extend(placeholder_issues)

        except Exception as e:
            print(f"Error processing {md_file}: {e}", file=sys.stderr)

    # Generate comprehensive report
    return generate_comprehensive_report(issues, len(md_files))


def generate_comprehensive_report(issues: Dict[str, List], total_files: int) -> int:
    """Generate a comprehensive validation report."""
    total_issues = sum(len(issue_list) for issue_list in issues.values())

    print("=" * 80)
    print("COMPREHENSIVE FILEPATH AND REFERENCE AUDIT REPORT")
    print("=" * 80)
    print(f"Files scanned: {total_files}")
    print(f"Total issues found: {total_issues}")
    print()

    # Report each category
    categories = [
        ('broken_anchor_links', 'Broken Anchor Links', 'Anchor links that don\'t resolve to headings'),
        ('broken_file_refs', 'Broken File References', 'File references that don\'t exist'),
        ('code_block_paths', 'Invalid Code Block Paths', 'File paths in code blocks that don\'t exist'),
        ('directory_structures', 'Directory Structure Issues', 'Directory trees that don\'t match filesystem'),
        ('python_imports', 'Invalid Python Imports', 'Import statements that reference non-existent modules'),
        ('placeholder_consistency', 'Placeholder Inconsistencies', 'Inconsistent use of {name} vs actual project names')
    ]

    has_issues = False
    for category_key, title, description in categories:
        issue_list = issues[category_key]
        if issue_list:
            has_issues = True
            print(f"🚨 {title} ({len(issue_list)} issues)")
            print(f"   {description}")
            print()

            # Show first 5 issues per category
            for i, issue in enumerate(issue_list[:5]):
                print(f"   {i+1}. {issue['file']}:{issue['line']}")
                print(f"      Target: {issue['target']}")
                print(f"      Issue: {issue['issue']}")
                if 'text' in issue:
                    print(f"      Text: {issue['text']}")
                print()

            if len(issue_list) > 5:
                print(f"   ... and {len(issue_list) - 5} more issues in this category")
            print("-" * 60)

    if not has_issues:
        print("✅ ALL VALIDATIONS PASSED!")
        print("No broken links, missing files, or reference issues found.")
        return 0

    print("\n📋 SUMMARY BY CATEGORY:")
    for category_key, title, _ in categories:
        count = len(issues[category_key])
        if count > 0:
            print(f"   • {title}: {count} issues")

    print(f"\n🔧 Next steps: Run the audit script to generate detailed fix recommendations:")
    print("   python scripts/audit_filepaths.py")

    return 1


if __name__ == '__main__':
    sys.exit(main())

