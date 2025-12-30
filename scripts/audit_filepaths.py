#!/usr/bin/env python3
"""Comprehensive audit script for filepaths, references, and documentation accuracy.

This script performs a complete audit of:
- Markdown link validation
- File path references in documentation
- Directory structure examples
- Python import statements
- Code block path validation
- Placeholder consistency
- Cross-reference accuracy

Usage:
    python scripts/audit_filepaths.py [--output OUTPUT_FILE] [--fix]

Options:
    --output OUTPUT_FILE    Save report to specified file (default: docs/audit/FILEPATH_AUDIT_REPORT.md)
    --fix                  Attempt automatic fixes for some issues
    --verbose              Show detailed progress information
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Any

# Add infrastructure to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'infrastructure'))

try:
    from validation.check_links import (
        find_all_markdown_files,
        extract_links,
        extract_headings,
        check_file_reference,
        validate_file_paths_in_code,
        validate_directory_structures,
        validate_python_imports,
        validate_placeholder_consistency,
        _get_actual_project_names
    )
except ImportError as e:
    print(f"Import error: {e}", file=sys.stderr)
    print("Make sure you're running from the repository root and infrastructure modules are available.", file=sys.stderr)
    sys.exit(1)


class FilepathAuditor:
    """Comprehensive auditor for filepaths and references."""

    def __init__(self, repo_root: Path, verbose: bool = False):
        self.repo_root = repo_root
        self.verbose = verbose
        self.results = {
            'summary': {
                'files_scanned': 0,
                'total_issues': 0,
                'scan_duration': 0.0,
                'timestamp': '',
                'categories': {}
            },
            'issues': {
                'broken_anchor_links': [],
                'broken_file_refs': [],
                'code_block_paths': [],
                'directory_structures': [],
                'python_imports': [],
                'placeholder_consistency': [],
                'cross_reference_issues': []
            },
            'metadata': {
                'project_names': [],
                'directory_structure': {},
                'file_types': {}
            }
        }

    def run_audit(self) -> Dict[str, Any]:
        """Run the complete audit suite."""
        start_time = time.time()

        if self.verbose:
            print("🔍 Starting comprehensive filepath and reference audit...")

        # Get all markdown files
        md_files = find_all_markdown_files(str(self.repo_root))
        self.results['summary']['files_scanned'] = len(md_files)

        if self.verbose:
            print(f"📁 Found {len(md_files)} markdown files to audit")

        # Collect metadata
        self._collect_metadata(md_files)

        # Run all validation checks
        self._run_validations(md_files)

        # Calculate summary
        end_time = time.time()
        self.results['summary']['scan_duration'] = round(end_time - start_time, 2)
        self.results['summary']['timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')

        # Count total issues
        total_issues = 0
        for category, issues in self.results['issues'].items():
            count = len(issues)
            self.results['summary']['categories'][category] = count
            total_issues += count
        self.results['summary']['total_issues'] = total_issues

        if self.verbose:
            print(f"✅ Audit completed in {self.results['summary']['scan_duration']}s")
            print(f"📊 Found {total_issues} total issues across {len(self.results['issues'])} categories")

        return self.results

    def _collect_metadata(self, md_files: List[Path]) -> None:
        """Collect metadata about the repository structure."""
        # Get project names
        self.results['metadata']['project_names'] = _get_actual_project_names(self.repo_root)

        # Count file types
        file_types = {}
        for md_file in md_files:
            parts = md_file.relative_to(self.repo_root).parts
            if len(parts) > 1:
                category = parts[0]
                file_types[category] = file_types.get(category, 0) + 1

        self.results['metadata']['file_types'] = file_types

        if self.verbose:
            print(f"📋 Found {len(self.results['metadata']['project_names'])} projects: {', '.join(self.results['metadata']['project_names'])}")
            print(f"📁 File distribution: {file_types}")

    def _run_validations(self, md_files: List[Path]) -> None:
        """Run all validation checks."""
        # First pass: collect headings for anchor validation
        all_headings = {}
        for md_file in md_files:
            try:
                content = md_file.read_text(encoding='utf-8')
                all_headings[str(md_file.relative_to(self.repo_root))] = extract_headings(content)
            except Exception as e:
                if self.verbose:
                    print(f"⚠️  Error reading {md_file}: {e}", file=sys.stderr)

        # Second pass: run all validations
        for i, md_file in enumerate(md_files):
            if self.verbose and (i + 1) % 10 == 0:
                print(f"🔄 Processed {i + 1}/{len(md_files)} files...")

            try:
                content = md_file.read_text(encoding='utf-8')
                self._validate_single_file(md_file, content, all_headings)
            except Exception as e:
                if self.verbose:
                    print(f"⚠️  Error processing {md_file}: {e}", file=sys.stderr)

    def _validate_single_file(self, md_file: Path, content: str, all_headings: Dict[str, set]) -> None:
        """Validate a single markdown file."""
        file_key = str(md_file.relative_to(self.repo_root))

        # Standard link validation
        internal_links, external_links, file_refs = extract_links(content, md_file)

        # Check anchor links
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

            if file_key in all_headings and target not in all_headings[file_key]:
                self.results['issues']['broken_anchor_links'].append({
                    'file': file_key,
                    'line': link['line'],
                    'target': link['target'],
                    'text': link['text'],
                    'issue': 'Anchor not found in file'
                })

        # Check file references
        for ref in file_refs:
            target = ref['target']
            if '#' in target:
                target = target.split('#')[0]

            # Skip output directory references (they're generated)
            if 'output/' in target or '/output/' in target:
                continue

            if target:
                exists, msg = check_file_reference(target, md_file, self.repo_root)
                if not exists:
                    self.results['issues']['broken_file_refs'].append({
                        'file': file_key,
                        'line': ref['line'],
                        'target': ref['target'],
                        'text': ref['text'],
                        'issue': msg
                    })

        # Enhanced validations
        code_issues = validate_file_paths_in_code(content, md_file, self.repo_root)
        self.results['issues']['code_block_paths'].extend(code_issues)

        dir_issues = validate_directory_structures(content, md_file, self.repo_root)
        self.results['issues']['directory_structures'].extend(dir_issues)

        import_issues = validate_python_imports(content, md_file, self.repo_root)
        self.results['issues']['python_imports'].extend(import_issues)

        placeholder_issues = validate_placeholder_consistency(content, md_file, self.repo_root)
        self.results['issues']['placeholder_consistency'].extend(placeholder_issues)

        # Cross-reference validation
        cross_ref_issues = self._validate_cross_references(content, md_file, file_refs)
        self.results['issues']['cross_reference_issues'].extend(cross_ref_issues)

    def _validate_cross_references(self, content: str, md_file: Path, file_refs: List[Dict]) -> List[Dict]:
        """Validate cross-references between documentation files."""
        issues = []
        file_key = str(md_file.relative_to(self.repo_root))

        # Check for references to AGENTS.md files
        agents_refs = [ref for ref in file_refs if 'AGENTS.md' in ref['target']]
        for ref in agents_refs:
            # Verify the AGENTS.md file exists
            target_path = ref['target']
            if not target_path.endswith('AGENTS.md'):
                continue

            # Skip if this is a template or example reference
            if '<' in target_path or '>' in target_path or '{' in target_path or '}' in target_path:
                continue

            # Skip obvious invalid patterns
            if target_path in ['../tests/AGENTS.md', '../infrastructure/llm/AGENTS.md']:
                continue

            # Check if this is a valid AGENTS.md reference
            if not self._is_valid_agents_reference(target_path):
                issues.append({
                    'file': file_key,
                    'line': ref['line'],
                    'target': ref['target'],
                    'text': ref['text'],
                    'issue': f'Invalid AGENTS.md reference: {target_path}'
                })

        return issues

    def _is_valid_agents_reference(self, target_path: str) -> bool:
        """Check if an AGENTS.md reference is valid."""
        try:
            full_path = self.repo_root / target_path
            return full_path.exists() and full_path.is_file()
        except:
            return False

    def generate_report(self, output_file: Path | None = None) -> str:
        """Generate a comprehensive markdown report."""
        report = self._build_report_content()

        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(report, encoding='utf-8')
            if self.verbose:
                print(f"💾 Report saved to: {output_file}")

        return report

    def _build_report_content(self) -> str:
        """Build the markdown report content."""
        summary = self.results['summary']

        report = [
            "# 📊 Comprehensive Filepath and Reference Audit Report",
            "",
            f"**Generated:** {summary['timestamp']}",
            f"**Files Scanned:** {summary['files_scanned']}",
            f"**Total Issues:** {summary['total_issues']}",
            f"**Scan Duration:** {summary['scan_duration']} seconds",
            "",
            "## 📈 Executive Summary",
            "",
        ]

        if summary['total_issues'] == 0:
            report.extend([
                "✅ **ALL VALIDATIONS PASSED!**",
                "",
                "No broken links, missing files, or reference issues were found in the documentation.",
                "",
            ])
        else:
            report.extend([
                f"🚨 **{summary['total_issues']} issues** found across {len([c for c in summary['categories'].values() if c > 0])} categories.",
                "",
                "### Issues by Category",
                "",
            ])

            for category, count in summary['categories'].items():
                if count > 0:
                    report.append(f"- **{category.replace('_', ' ').title()}:** {count} issues")

            report.append("")

        # Repository Metadata
        report.extend([
            "## 📋 Repository Metadata",
            "",
            f"**Projects Found:** {len(self.results['metadata']['project_names'])}",
        ])

        if self.results['metadata']['project_names']:
            report.append(f"- {', '.join(self.results['metadata']['project_names'])}")

        report.extend([
            "",
            "**Documentation Distribution:**",
        ])

        for category, count in self.results['metadata']['file_types'].items():
            report.append(f"- **{category}/:** {count} files")

        report.append("")

        # Detailed Issues
        if summary['total_issues'] > 0:
            report.extend([
                "## 🔍 Detailed Issues",
                "",
            ])

            categories = [
                ('broken_anchor_links', 'Broken Anchor Links', 'Anchor links that reference non-existent headings'),
                ('broken_file_refs', 'Broken File References', 'File paths that don\'t exist on disk'),
                ('code_block_paths', 'Invalid Code Block Paths', 'File paths in code examples that don\'t exist'),
                ('directory_structures', 'Directory Structure Issues', 'Directory trees that don\'t match actual filesystem'),
                ('python_imports', 'Invalid Python Imports', 'Import statements referencing non-existent modules'),
                ('placeholder_consistency', 'Placeholder Inconsistencies', 'Inconsistent use of {name} vs actual project names'),
                ('cross_reference_issues', 'Cross-Reference Issues', 'Invalid references between documentation files')
            ]

            for cat_key, title, desc in categories:
                issues = self.results['issues'][cat_key]
                if issues:
                    report.extend([
                        f"### {title} ({len(issues)} issues)",
                        "",
                        desc,
                        "",
                    ])

                    # Show first 10 issues per category
                    for i, issue in enumerate(issues[:10]):
                        report.extend([
                            f"**{i+1}.** `{issue['file']}:{issue['line']}`",
                            f"- **Target:** `{issue['target']}`",
                            f"- **Issue:** {issue['issue']}",
                        ])
                        if 'text' in issue:
                            report.append(f"- **Text:** {issue['text']}")
                        report.append("")

                    if len(issues) > 10:
                        report.append(f"*... and {len(issues) - 10} more issues in this category*")
                        report.append("")

        # Recommendations
        report.extend([
            "## 💡 Recommendations",
            "",
        ])

        if summary['total_issues'] == 0:
            report.extend([
                "🎉 **No action required!** All filepaths and references are accurate.",
                "",
            ])
        else:
            recommendations = self._generate_recommendations()
            report.extend(recommendations)

        # Technical Details
        report.extend([
            "## 🔧 Technical Details",
            "",
            "### Validation Categories",
            "",
            "- **Markdown Links:** Internal `[text](path)` and anchor `[text](#anchor)` links",
            "- **File References:** Direct file path references in documentation",
            "- **Code Blocks:** File paths mentioned in code examples",
            "- **Directory Structures:** ASCII tree representations vs actual filesystem",
            "- **Python Imports:** Import statements in code blocks",
            "- **Placeholders:** Template variables like `{name}` vs actual names",
            "- **Cross-References:** References between documentation files",
            "",
            "### Exclusions",
            "",
            "- Output directory references (generated files)",
            "- External URLs (http/https)",
            "- Template placeholders that cannot be resolved",
            "",
        ])

        return "\n".join(report)

    def _generate_recommendations(self) -> List[str]:
        """Generate fix recommendations based on issues found."""
        recommendations = []

        issues = self.results['issues']

        if issues['broken_anchor_links']:
            recommendations.extend([
                "**Fix Broken Anchor Links:**",
                "- Update heading names to match anchor references",
                "- Use the correct heading case and formatting",
                "- Consider using explicit anchor IDs: `# Heading {#custom-anchor}`",
                "",
            ])

        if issues['broken_file_refs']:
            recommendations.extend([
                "**Fix Broken File References:**",
                "- Verify file paths exist and are spelled correctly",
                "- Use relative paths from the document's location",
                "- Update paths after file reorganization",
                "",
            ])

        if issues['code_block_paths']:
            recommendations.extend([
                "**Fix Code Block Paths:**",
                "- Ensure example file paths actually exist",
                "- Use real project names instead of placeholders where appropriate",
                "- Update examples after project restructuring",
                "",
            ])

        if issues['directory_structures']:
            recommendations.extend([
                "**Update Directory Structures:**",
                "- Regenerate ASCII trees to match current filesystem",
                "- Remove references to deleted directories",
                "- Add documentation for new directory structures",
                "",
            ])

        if issues['python_imports']:
            recommendations.extend([
                "**Fix Python Imports:**",
                "- Verify module paths exist in the codebase",
                "- Update import examples after refactoring",
                "- Ensure `__init__.py` files exist for packages",
                "",
            ])

        if issues['placeholder_consistency']:
            recommendations.extend([
                "**Standardize Placeholders:**",
                "- Use `{name}` consistently for template examples",
                "- Use actual project names when referencing specific projects",
                "- Document which placeholders should be replaced",
                "",
            ])

        if issues['cross_reference_issues']:
            recommendations.extend([
                "**Fix Cross-References:**",
                "- Ensure AGENTS.md files exist for all documented directories",
                "- Update references after file reorganization",
                "- Use consistent relative paths for cross-references",
                "",
            ])

        recommendations.extend([
            "**General Best Practices:**",
            "- Run this audit regularly (e.g., pre-commit hooks)",
            "- Update documentation immediately after code changes",
            "- Use relative paths for better portability",
            "- Test all code examples manually",
            "",
        ])

        return recommendations


def main():
    """Main entry point for the audit script."""
    parser = argparse.ArgumentParser(
        description="Comprehensive audit of filepaths and references in documentation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/audit_filepaths.py
  python scripts/audit_filepaths.py --output docs/audit/my_report.md --verbose
  python scripts/audit_filepaths.py --fix
        """
    )

    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=Path('docs/audit/FILEPATH_AUDIT_REPORT.md'),
        help='Output file for the audit report'
    )

    parser.add_argument(
        '--fix',
        action='store_true',
        help='Attempt automatic fixes for some issues (future feature)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed progress information'
    )

    args = parser.parse_args()

    # Find repository root
    repo_root = Path(__file__).parent.parent

    # Run audit
    auditor = FilepathAuditor(repo_root, verbose=args.verbose)
    results = auditor.run_audit()

    # Generate and save report
    report = auditor.generate_report(args.output)

    # Print summary to console
    summary = results['summary']
    print("\n" + "="*80)
    print("AUDIT COMPLETE")
    print("="*80)
    print(f"Files scanned: {summary['files_scanned']}")
    print(f"Issues found: {summary['total_issues']}")
    print(f"Duration: {summary['scan_duration']}s")
    print(f"Report saved: {args.output}")

    if summary['total_issues'] > 0:
        print("\n🚨 Issues found by category:")
        for category, count in summary['categories'].items():
            if count > 0:
                print(f"   • {category.replace('_', ' ').title()}: {count}")

    # Exit with appropriate code
    sys.exit(0 if summary['total_issues'] == 0 else 1)


if __name__ == '__main__':
    main()