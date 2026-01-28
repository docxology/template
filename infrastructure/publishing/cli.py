"""CLI interface for publishing operations.

Thin orchestrator wrapping infrastructure.publishing module functionality.
"""

import argparse
import os
import sys
from pathlib import Path

from infrastructure.core.logging_utils import get_logger

from .api import ZenodoClient
from .core import extract_publication_metadata, generate_citation_bibtex

logger = get_logger(__name__)


def extract_metadata_command(args: argparse.Namespace) -> None:
    """Extract and display publication metadata from manuscript files.

    Scans the specified manuscript directory for markdown files and extracts
    publication metadata including title, authors, abstract, and keywords.
    Results are printed to stdout.

    Args:
        args: Argparse namespace containing:
            - manuscript_dir (str): Path to directory containing markdown files.

    Returns:
        None. Prints metadata to stdout.

    Raises:
        SystemExit: If the directory does not exist or contains no markdown files.
    """
    manuscript_dir = Path(args.manuscript_dir)

    if not manuscript_dir.exists():
        logger.error("Directory not found: %s", manuscript_dir)
        sys.exit(1)

    logger.info("Extracting metadata from: %s", manuscript_dir)
    md_files = list(manuscript_dir.glob("*.md"))

    if not md_files:
        logger.error("No markdown files found")
        sys.exit(1)

    metadata = extract_publication_metadata(md_files)

    print(f"\nMetadata:")
    print(f"Title: {metadata.title}")
    print(f"Authors: {', '.join(metadata.authors)}")
    print(
        f"Abstract: {metadata.abstract[:200]}..."
        if metadata.abstract
        else "Abstract: N/A"
    )
    print(f"Keywords: {', '.join(metadata.keywords)}")


def generate_citation_command(args: argparse.Namespace) -> None:
    """Generate a formatted citation from manuscript metadata.

    Extracts metadata from manuscript markdown files and generates a citation
    in the requested format (currently BibTeX only). The citation is printed
    to stdout for easy copying or redirection.

    Args:
        args: Argparse namespace containing:
            - manuscript_dir (str): Path to directory containing markdown files.
            - format (str): Citation format ('bibtex', 'apa', or 'mla').

    Returns:
        None. Prints the formatted citation to stdout.

    Raises:
        SystemExit: If the directory does not exist, contains no markdown files,
            or if an unsupported format is requested.
    """
    manuscript_dir = Path(args.manuscript_dir)

    if not manuscript_dir.exists():
        logger.error("Directory not found: %s", manuscript_dir)
        sys.exit(1)

    md_files = list(manuscript_dir.glob("*.md"))
    if not md_files:
        logger.error("No markdown files found")
        sys.exit(1)

    metadata = extract_publication_metadata(md_files)

    if args.format == "bibtex":
        citation = generate_citation_bibtex(metadata)
    else:
        logger.error("Unsupported format: %s", args.format)
        sys.exit(1)

    print(citation)


def publish_zenodo_command(args: argparse.Namespace) -> None:
    """Upload and publish research outputs to Zenodo.

    Finds all PDF files in the specified output directory and uploads them
    to Zenodo as a new publication. Requires a valid Zenodo API token either
    via command-line argument or ZENODO_TOKEN environment variable.

    Args:
        args: Argparse namespace containing:
            - output_dir (str): Path to directory containing PDF files to upload.
            - token (str, optional): Zenodo API token. Falls back to ZENODO_TOKEN env.
            - title (str, optional): Publication title. Defaults to 'Research Publication'.
            - authors (str, optional): Comma-separated author names.
            - description (str, optional): Publication description text.

    Returns:
        None. Prints the Zenodo record ID on success.

    Raises:
        SystemExit: If no token is available, directory does not exist,
            no PDF files are found, or the upload fails.
    """
    token = args.token or os.getenv("ZENODO_TOKEN")
    if not token:
        logger.error("ZENODO_TOKEN environment variable not set")
        sys.exit(1)

    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        logger.error("Directory not found: %s", output_dir)
        sys.exit(1)

    # Find PDFs
    pdfs = list(output_dir.glob("**/*.pdf"))
    if not pdfs:
        logger.error("No PDF files found")
        sys.exit(1)

    logger.info("Publishing %d files to Zenodo", len(pdfs))
    client = ZenodoClient()

    # Use provided metadata or extract from manuscript
    metadata = {
        "title": args.title or "Research Publication",
        "authors": args.authors.split(",") if args.authors else ["Unknown"],
        "description": args.description or "Published research output",
    }

    try:
        record_id = client.upload_publication(metadata, pdfs)
        print(f"Published successfully! Record ID: {record_id}")
    except Exception as e:
        logger.error("Zenodo upload failed: %s", e)
        sys.exit(1)


def main() -> None:
    """Main CLI entry point for publishing operations.

    Parses command-line arguments and dispatches to the appropriate
    subcommand handler. Available commands:
        - extract-metadata: Extract publication metadata from manuscript files.
        - generate-citation: Generate citations in various formats.
        - publish-zenodo: Upload and publish to Zenodo repository.

    Returns:
        None. Exit code 0 on success, 1 on error.

    Raises:
        SystemExit: If no command is specified or if the command fails.
    """
    parser = argparse.ArgumentParser(
        description="Publish research outputs to academic platforms."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Extract metadata
    meta_parser = subparsers.add_parser("extract-metadata", help="Extract metadata")
    meta_parser.add_argument("manuscript_dir", help="Manuscript directory")
    meta_parser.set_defaults(func=extract_metadata_command)

    # Generate citation
    cite_parser = subparsers.add_parser("generate-citation", help="Generate citation")
    cite_parser.add_argument("manuscript_dir", help="Manuscript directory")
    cite_parser.add_argument(
        "--format",
        choices=["bibtex", "apa", "mla"],
        default="bibtex",
        help="Citation format",
    )
    cite_parser.set_defaults(func=generate_citation_command)

    # Publish to Zenodo
    zenodo_parser = subparsers.add_parser("publish-zenodo", help="Publish to Zenodo")
    zenodo_parser.add_argument("output_dir", help="Output directory with files")
    zenodo_parser.add_argument(
        "--token", help="Zenodo API token (or use ZENODO_TOKEN env)"
    )
    zenodo_parser.add_argument("--title", help="Publication title")
    zenodo_parser.add_argument("--authors", help="Comma-separated author list")
    zenodo_parser.add_argument("--description", help="Publication description")
    zenodo_parser.set_defaults(func=publish_zenodo_command)

    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except Exception as e:
        logger.error("Command failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
