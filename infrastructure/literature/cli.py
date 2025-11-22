"""CLI interface for literature search operations.

Thin orchestrator wrapping infrastructure.literature module functionality.
"""

import argparse
import sys
from pathlib import Path

from .core import LiteratureSearch
from .config import LiteratureConfig


def search_command(args):
    """Handle literature search command."""
    config = LiteratureConfig()
    manager = LiteratureSearch(config)

    print(f"Searching for: {args.query}...")
    results = manager.search_papers(
        query=args.query,
        sources=args.sources.split(",") if args.sources else None,
        limit=args.limit
    )

    for i, paper in enumerate(results, 1):
        print(f"\n{i}. {paper.title}")
        print(f"   Authors: {', '.join(paper.authors)}")
        print(f"   Year: {paper.year}")
        if paper.doi:
            print(f"   DOI: {paper.doi}")

        manager.add_to_library(paper)

        if args.download and paper.pdf_url:
            path = manager.download_paper(paper)
            if path:
                print(f"   Downloaded to: {path}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Search scientific literature from multiple sources."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search for papers")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "--limit", type=int, default=10, help="Maximum results (default: 10)"
    )
    search_parser.add_argument(
        "--sources",
        default=None,
        help="Comma-separated sources (arxiv,semanticscholar,crossref,pubmed)"
    )
    search_parser.add_argument(
        "--download",
        action="store_true",
        help="Download PDF files"
    )
    search_parser.set_defaults(func=search_command)

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

