"""CLI interface for literature search operations.

Thin orchestrator wrapping infrastructure.literature module functionality.
"""

import argparse
import os
import sys
from pathlib import Path

from .core import LiteratureSearch
from .config import LiteratureConfig


def search_command(args):
    """Handle literature search command."""
    config = LiteratureConfig()
    manager = LiteratureSearch(config)

    print(f"Searching for: {args.query}...")
    results = manager.search(
        query=args.query,
        sources=args.sources.split(",") if args.sources else None,
        limit=args.limit
    )

    if not results:
        print("No results found.")
        return

    for i, paper in enumerate(results, 1):
        print(f"\n{i}. {paper.title}")
        print(f"   Authors: {', '.join(paper.authors)}")
        print(f"   Year: {paper.year}")
        if paper.doi:
            print(f"   DOI: {paper.doi}")
        if paper.citation_count:
            print(f"   Citations: {paper.citation_count}")

        # Add to library (both BibTeX and JSON index)
        citation_key = manager.add_to_library(paper)
        print(f"   Citation key: {citation_key}")

        if args.download and paper.pdf_url:
            path = manager.download_paper(paper)
            if path:
                print(f"   Downloaded: {path}")

    print(f"\nAdded {len(results)} papers to library.")


def library_list_command(args):
    """Handle library list command."""
    # Use from_env() to respect environment variables for testing
    config = LiteratureConfig.from_env() if any(os.environ.get(k) for k in ['LITERATURE_LIBRARY_INDEX', 'LITERATURE_BIBTEX_FILE', 'LITERATURE_DOWNLOAD_DIR']) else LiteratureConfig()
    manager = LiteratureSearch(config)

    entries = manager.get_library_entries()

    if not entries:
        print("Library is empty.")
        return

    print(f"Library contains {len(entries)} entries:\n")

    for entry in entries:
        pdf_status = "✓" if entry.get("pdf_path") else "✗"
        year = entry.get("year", "n/d")
        authors = entry.get("authors", [])
        author_str = authors[0] if authors else "Unknown"
        if len(authors) > 1:
            author_str += " et al."

        print(f"[{pdf_status}] {entry['citation_key']}")
        title = entry.get('title', 'No title')
        print(f"    {title[:70]}{'...' if len(title) > 70 else ''}")
        print(f"    {author_str} ({year})")
        if entry.get("doi"):
            print(f"    DOI: {entry['doi']}")
        print()


def library_export_command(args):
    """Handle library export command."""
    config = LiteratureConfig()
    manager = LiteratureSearch(config)

    output_path = Path(args.output) if args.output else None

    try:
        path = manager.export_library(output_path, format=args.format)
        print(f"Library exported to: {path}")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def library_stats_command(args):
    """Handle library stats command."""
    # Use from_env() to respect environment variables for testing
    config = LiteratureConfig.from_env() if any(os.environ.get(k) for k in ['LITERATURE_LIBRARY_INDEX', 'LITERATURE_BIBTEX_FILE', 'LITERATURE_DOWNLOAD_DIR']) else LiteratureConfig()
    manager = LiteratureSearch(config)

    stats = manager.get_library_stats()

    print("Library Statistics")
    print("=" * 40)
    print(f"Total entries: {stats.get('total_entries', 0)}")
    print(f"Downloaded PDFs: {stats.get('downloaded_pdfs', 0)}")

    if stats.get("oldest_year") and stats.get("newest_year"):
        print(f"Year range: {stats['oldest_year']} - {stats['newest_year']}")

    if stats.get("sources"):
        print("\nBy Source:")
        for source, count in stats["sources"].items():
            print(f"  {source}: {count}")

    if stats.get("years"):
        print("\nBy Year (recent first):")
        for year, count in list(stats["years"].items())[:10]:
            print(f"  {year}: {count}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Search scientific literature and manage references."
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
        help="Comma-separated sources (arxiv,semanticscholar)"
    )
    search_parser.add_argument(
        "--download",
        action="store_true",
        help="Download PDF files"
    )
    search_parser.set_defaults(func=search_command)

    # Library command group
    library_parser = subparsers.add_parser("library", help="Manage paper library")
    library_subparsers = library_parser.add_subparsers(dest="library_command")

    # Library list
    list_parser = library_subparsers.add_parser("list", help="List papers in library")
    list_parser.set_defaults(func=library_list_command)

    # Library export
    export_parser = library_subparsers.add_parser("export", help="Export library")
    export_parser.add_argument(
        "--format",
        choices=["json"],
        default="json",
        help="Export format (default: json)"
    )
    export_parser.add_argument(
        "--output", "-o",
        help="Output file path"
    )
    export_parser.set_defaults(func=library_export_command)

    # Library stats
    stats_parser = library_subparsers.add_parser("stats", help="Show library statistics")
    stats_parser.set_defaults(func=library_stats_command)

    args = parser.parse_args()

    # Check for missing command or missing function handler - consolidate to single exit
    needs_help = False
    help_parser = parser
    
    if not args.command:
        needs_help = True
    elif args.command == "library" and not hasattr(args, "func"):
        needs_help = True
        help_parser = library_parser
    elif not hasattr(args, "func"):
        needs_help = True
    
    if needs_help:
        help_parser.print_help()
        sys.exit(1)
        return  # Prevent execution if sys.exit is mocked in tests

    # At this point, we know args.func exists, so safe to call
    try:
        args.func(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
