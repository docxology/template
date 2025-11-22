"""CLI interface for publishing operations.

Thin orchestrator wrapping infrastructure.publishing module functionality.
"""

import argparse
import os
import sys
from pathlib import Path

from .core import extract_publication_metadata, generate_citation_bibtex
from .api import ZenodoClient


def extract_metadata_command(args):
    """Extract publication metadata."""
    manuscript_dir = Path(args.manuscript_dir)

    if not manuscript_dir.exists():
        print(f"Error: Directory not found: {manuscript_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Extracting metadata from: {manuscript_dir}...")
    md_files = list(manuscript_dir.glob("*.md"))

    if not md_files:
        print("Error: No markdown files found", file=sys.stderr)
        sys.exit(1)

    metadata = extract_publication_metadata(md_files)

    print(f"\nMetadata:")
    print(f"Title: {metadata.get('title', 'N/A')}")
    print(f"Authors: {', '.join(metadata.get('authors', []))}")
    print(f"Abstract: {metadata.get('abstract', 'N/A')[:200]}...")
    print(f"Keywords: {', '.join(metadata.get('keywords', []))}")


def generate_citation_command(args):
    """Generate citation in specified format."""
    manuscript_dir = Path(args.manuscript_dir)

    if not manuscript_dir.exists():
        print(f"Error: Directory not found: {manuscript_dir}", file=sys.stderr)
        sys.exit(1)

    md_files = list(manuscript_dir.glob("*.md"))
    if not md_files:
        print("Error: No markdown files found", file=sys.stderr)
        sys.exit(1)

    metadata = extract_publication_metadata(md_files)

    if args.format == "bibtex":
        citation = generate_citation_bibtex(metadata)
    else:
        print(f"Error: Unsupported format: {args.format}", file=sys.stderr)
        sys.exit(1)

    print(citation)


def publish_zenodo_command(args):
    """Publish to Zenodo."""
    token = args.token or os.getenv("ZENODO_TOKEN")
    if not token:
        print("Error: ZENODO_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        print(f"Error: Directory not found: {output_dir}", file=sys.stderr)
        sys.exit(1)

    # Find PDFs
    pdfs = list(output_dir.glob("**/*.pdf"))
    if not pdfs:
        print("Error: No PDF files found", file=sys.stderr)
        sys.exit(1)

    print(f"Publishing {len(pdfs)} files to Zenodo...")
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
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main CLI entry point."""
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
        help="Citation format"
    )
    cite_parser.set_defaults(func=generate_citation_command)

    # Publish to Zenodo
    zenodo_parser = subparsers.add_parser("publish-zenodo", help="Publish to Zenodo")
    zenodo_parser.add_argument("output_dir", help="Output directory with files")
    zenodo_parser.add_argument("--token", help="Zenodo API token (or use ZENODO_TOKEN env)")
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
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

