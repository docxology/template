"""CLI interface for validation operations.

Thin orchestrator wrapping infrastructure.validation module functionality.
"""

import argparse
import sys
from pathlib import Path

from .pdf_validator import validate_pdf_rendering
from .markdown_validator import validate_markdown
from .integrity import verify_output_integrity


def validate_pdf_command(args):
    """Handle PDF validation."""
    pdf_path = Path(args.pdf_path)

    if not pdf_path.exists():
        print(f"Error: PDF not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Validating PDF: {pdf_path}...")
    report = validate_pdf_rendering(pdf_path, n_words=args.preview_words)

    print(f"\nValidation Results:")
    print(f"Total issues found: {report['issues']['total_issues']}")

    if report['issues']['unresolved_refs']:
        print(f"Unresolved references: {len(report['issues']['unresolved_refs'])}")
        if args.verbose:
            for ref in report['issues']['unresolved_refs'][:5]:
                print(f"  - {ref}")

    if report['issues']['missing_citations']:
        print(f"Missing citations: {len(report['issues']['missing_citations'])}")

    if args.verbose and report['preview']['first_words']:
        print(f"\nFirst words:\n{' '.join(report['preview']['first_words'][:50])}")

    sys.exit(0 if report['summary']['has_issues'] == False else 1)


def validate_markdown_command(args):
    """Handle Markdown validation."""
    md_dir = Path(args.markdown_dir)
    repo_root = Path(args.repo_root) if args.repo_root else Path(".")

    if not md_dir.exists():
        print(f"Error: Directory not found: {md_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Validating Markdown in: {md_dir}...")
    problems, exit_code = validate_markdown(str(md_dir), str(repo_root))

    if problems:
        for problem in problems:
            print(f"  {problem}")
    else:
        print("  No issues found!")

    sys.exit(exit_code)


def verify_integrity_command(args):
    """Handle integrity verification."""
    output_dir = Path(args.output_dir)

    if not output_dir.exists():
        print(f"Error: Directory not found: {output_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Verifying integrity of: {output_dir}...")
    report = verify_output_integrity(output_dir)

    print(f"\nIntegrity Report:")
    print(f"Files checked: {report.get('total_files', 0)}")
    print(f"Issues found: {report.get('total_issues', 0)}")

    if args.verbose and report.get('issues'):
        for issue in report['issues'][:10]:
            print(f"  - {issue}")

    sys.exit(0 if report.get('total_issues', 0) == 0 else 1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Validate research output (PDFs, Markdown, integrity)."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # PDF validation
    pdf_parser = subparsers.add_parser("pdf", help="Validate PDF rendering")
    pdf_parser.add_argument("pdf_path", help="Path to PDF file")
    pdf_parser.add_argument(
        "--preview-words",
        type=int,
        default=200,
        help="Number of words to preview"
    )
    pdf_parser.add_argument("-v", "--verbose", action="store_true")
    pdf_parser.set_defaults(func=validate_pdf_command)

    # Markdown validation
    md_parser = subparsers.add_parser("markdown", help="Validate Markdown files")
    md_parser.add_argument("markdown_dir", help="Path to markdown directory")
    md_parser.add_argument(
        "--repo-root",
        help="Repository root directory"
    )
    md_parser.set_defaults(func=validate_markdown_command)

    # Integrity verification
    int_parser = subparsers.add_parser("integrity", help="Verify output integrity")
    int_parser.add_argument("output_dir", help="Path to output directory")
    int_parser.add_argument("-v", "--verbose", action="store_true")
    int_parser.set_defaults(func=verify_integrity_command)

    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

