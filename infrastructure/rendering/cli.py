"""CLI interface for rendering operations.

Thin orchestrator wrapping infrastructure.rendering module functionality.
"""

import argparse
import sys
from pathlib import Path

from .core import RenderManager


def render_pdf_command(args):
    """Handle PDF rendering."""
    manager = RenderManager()
    source = Path(args.source)

    if not source.exists():
        print(f"Error: Source file not found: {source}", file=sys.stderr)
        sys.exit(1)

    print(f"Rendering PDF: {source}...")
    output = manager.render_pdf(source)
    print(f"Generated: {output}")


def render_all_command(args):
    """Handle rendering all formats."""
    manager = RenderManager()
    source = Path(args.source)

    if not source.exists():
        print(f"Error: Source file not found: {source}", file=sys.stderr)
        sys.exit(1)

    print(f"Rendering all formats: {source}...")
    outputs = manager.render_all(source)

    for output in outputs:
        print(f"Generated: {output}")


def render_slides_command(args):
    """Handle slide rendering."""
    manager = RenderManager()
    source = Path(args.source)

    if not source.exists():
        print(f"Error: Source file not found: {source}", file=sys.stderr)
        sys.exit(1)

    fmt = args.format or "beamer"
    print(f"Rendering slides ({fmt}): {source}...")
    output = manager.render_slides(source, format=fmt)
    print(f"Generated: {output}")


def render_web_command(args):
    """Handle web output rendering."""
    manager = RenderManager()
    source = Path(args.source)

    if not source.exists():
        print(f"Error: Source file not found: {source}", file=sys.stderr)
        sys.exit(1)

    print(f"Rendering web output: {source}...")
    output = manager.render_web(source)
    print(f"Generated: {output}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Render documents in multiple formats (PDF, HTML, slides)."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # PDF rendering
    pdf_parser = subparsers.add_parser("pdf", help="Render PDF")
    pdf_parser.add_argument("source", help="Source file (TeX or Markdown)")
    pdf_parser.set_defaults(func=render_pdf_command)

    # All formats
    all_parser = subparsers.add_parser("all", help="Render all formats")
    all_parser.add_argument("source", help="Source file")
    all_parser.set_defaults(func=render_all_command)

    # Slides
    slides_parser = subparsers.add_parser("slides", help="Render slides")
    slides_parser.add_argument("source", help="Source file")
    slides_parser.add_argument(
        "--format",
        choices=["beamer", "revealjs"],
        default="beamer",
        help="Output format"
    )
    slides_parser.set_defaults(func=render_slides_command)

    # Web
    web_parser = subparsers.add_parser("web", help="Render web output")
    web_parser.add_argument("source", help="Source file")
    web_parser.set_defaults(func=render_web_command)

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

