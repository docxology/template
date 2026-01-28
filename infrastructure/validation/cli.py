"""CLI interface for validation operations.

Thin orchestrator wrapping infrastructure.validation module functionality.
"""

import argparse
import sys
from pathlib import Path

from infrastructure.core.logging_utils import get_logger

from .integrity import verify_output_integrity
from .link_validator import LinkValidator
from .markdown_validator import validate_markdown
from .pdf_validator import validate_pdf_rendering

logger = get_logger(__name__)


def validate_pdf_command(args: argparse.Namespace) -> None:
    """Handle PDF validation."""
    pdf_path = Path(args.pdf_path)

    if not pdf_path.exists():
        logger.error(f"PDF not found: {pdf_path}")
        sys.exit(1)

    logger.info(f"Validating PDF: {pdf_path}")
    report = validate_pdf_rendering(pdf_path, n_words=args.preview_words)

    print(f"\nValidation Results:")
    print(f"Total issues found: {report['issues']['total_issues']}")

    # report['issues'] values are integers (counts), not lists
    unresolved_refs_count = report["issues"].get("unresolved_references", 0)
    if unresolved_refs_count > 0:
        print(f"Unresolved references: {unresolved_refs_count}")
        if args.verbose:
            print("  (See PDF for details)")

    missing_citations_count = report["issues"].get("missing_citations", 0)
    if missing_citations_count > 0:
        print(f"Missing citations: {missing_citations_count}")

    if args.verbose and report.get("first_words"):
        words_preview = report["first_words"][:500] if report["first_words"] else ""
        if words_preview:
            print(f"\nFirst words:\n{words_preview}")

    sys.exit(0 if not report["summary"]["has_issues"] else 1)


def validate_markdown_command(args: argparse.Namespace) -> None:
    """Handle Markdown validation."""
    md_dir = Path(args.markdown_dir)
    repo_root = Path(args.repo_root) if args.repo_root else Path(".")

    if not md_dir.exists():
        logger.error(f"Directory not found: {md_dir}")
        sys.exit(1)

    logger.info(f"Validating Markdown in: {md_dir}")
    problems, exit_code = validate_markdown(str(md_dir), str(repo_root))

    if problems:
        for problem in problems:
            print(f"  {problem}")
    else:
        print("  No issues found!")

    sys.exit(exit_code)


def verify_integrity_command(args: argparse.Namespace) -> None:
    """Handle integrity verification."""
    output_dir = Path(args.output_dir)

    if not output_dir.exists():
        logger.error(f"Directory not found: {output_dir}")
        sys.exit(1)

    logger.info(f"Verifying integrity of: {output_dir}")
    report = verify_output_integrity(output_dir)

    # IntegrityReport is an object, not a dict
    total_files = len(report.file_integrity)
    total_issues = len(report.issues)

    print(f"\nIntegrity Report:")
    print(f"Files checked: {total_files}")
    print(f"Issues found: {total_issues}")
    print(f"Overall integrity: {'PASS' if report.overall_integrity else 'FAIL'}")

    if args.verbose and report.issues:
        print("\nIssues:")
        for issue in report.issues[:10]:
            print(f"  - {issue}")

    if args.verbose and report.warnings:
        print("\nWarnings:")
        for warning in report.warnings[:10]:
            print(f"  - {warning}")

    sys.exit(0 if report.overall_integrity else 1)


def validate_links_command(args: argparse.Namespace) -> None:
    """Handle link validation."""
    repo_root = Path(args.repo_root) if args.repo_root else Path.cwd()

    if not repo_root.exists():
        logger.error(f"Repository root not found: {repo_root}")
        sys.exit(1)

    logger.info(f"Validating links in repository: {repo_root}")

    validator = LinkValidator(repo_root)
    results = validator.validate_all_markdown_files()
    report = validator.generate_report(results)

    # Count broken links
    total_broken = sum(len(file_results["broken"]) for file_results in results.values())

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(report, encoding="utf-8")
        logger.info(f"Report saved to: {output_path}")
    else:
        print(report)

    if total_broken > 0:
        print(f"\n❌ Found {total_broken} broken link(s)")
        sys.exit(1)
    else:
        print("\n✅ All links valid!")
        sys.exit(0)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Validate research output (PDFs, Markdown, integrity)."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # PDF validation
    pdf_parser = subparsers.add_parser("pdf", help="Validate PDF rendering")
    pdf_parser.add_argument("pdf_path", help="Path to PDF file")
    pdf_parser.add_argument(
        "--preview-words", type=int, default=200, help="Number of words to preview"
    )
    pdf_parser.add_argument("-v", "--verbose", action="store_true")
    pdf_parser.set_defaults(func=validate_pdf_command)

    # Markdown validation
    md_parser = subparsers.add_parser("markdown", help="Validate Markdown files")
    md_parser.add_argument("markdown_dir", help="Path to markdown directory")
    md_parser.add_argument("--repo-root", help="Repository root directory")
    md_parser.set_defaults(func=validate_markdown_command)

    # Integrity verification
    int_parser = subparsers.add_parser("integrity", help="Verify output integrity")
    int_parser.add_argument("output_dir", help="Path to output directory")
    int_parser.add_argument("-v", "--verbose", action="store_true")
    int_parser.set_defaults(func=verify_integrity_command)

    # Link validation
    link_parser = subparsers.add_parser("links", help="Validate markdown links")
    link_parser.add_argument(
        "--repo-root", help="Repository root directory (default: current directory)"
    )
    link_parser.add_argument("--output", help="Output file for validation report")
    link_parser.set_defaults(func=validate_links_command)

    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except Exception as e:
        logger.error(f"{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
