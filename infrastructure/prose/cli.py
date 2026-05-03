"""Command-line interface for prose analysis.

Subcommands:

* ``metrics`` — compute readability metrics for a single file or
  directory and emit JSON.
* ``outline`` — render the heading outline of a Markdown file.
* ``quality`` — flag passive-voice candidates, hedge words, and long
  sentences.
* ``report`` — full :class:`ManuscriptReport` over a manuscript directory.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.prose.analysis import (
    analyze_quality,
    analyze_structure,
    compute_metrics,
    render_outline,
)
from infrastructure.prose.markdown import normalise_for_prose
from infrastructure.prose.report import analyze_manuscript, write_report

logger = get_logger(__name__)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _cmd_metrics(args: argparse.Namespace) -> int:
    text = _read(Path(args.path))
    plain = normalise_for_prose(text)
    metrics = compute_metrics(plain)
    sys.stdout.write(json.dumps(metrics.to_dict(), indent=2) + "\n")
    return 0


def _cmd_outline(args: argparse.Namespace) -> int:
    text = _read(Path(args.path))
    structure = analyze_structure(text)
    sys.stdout.write(render_outline(structure) + "\n")
    return 0


def _cmd_quality(args: argparse.Namespace) -> int:
    text = _read(Path(args.path))
    plain = normalise_for_prose(text)
    quality = analyze_quality(plain, long_sentence_threshold=args.long_sentence_threshold)
    sys.stdout.write(json.dumps(quality.to_dict(), indent=2) + "\n")
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    report = analyze_manuscript(args.manuscript_dir)
    if args.output == "-" or not args.output:
        sys.stdout.write(report.to_json() + "\n")
    else:
        write_report(report, args.output)
        logger.info("Wrote report → %s", args.output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m infrastructure.prose.cli",
        description="Prose analysis: metrics, outline, quality, full report.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_metrics = sub.add_parser("metrics", help="Readability metrics for a single file.")
    p_metrics.add_argument("path", help="Markdown file path")
    p_metrics.set_defaults(func=_cmd_metrics)

    p_outline = sub.add_parser("outline", help="Heading outline of a Markdown file.")
    p_outline.add_argument("path", help="Markdown file path")
    p_outline.set_defaults(func=_cmd_outline)

    p_quality = sub.add_parser("quality", help="Editorial quality flags.")
    p_quality.add_argument("path", help="Markdown file path")
    p_quality.add_argument(
        "--long-sentence-threshold",
        type=int,
        default=35,
        help="Word count above which a sentence is flagged as long (default: 35).",
    )
    p_quality.set_defaults(func=_cmd_quality)

    p_report = sub.add_parser("report", help="Full report over a manuscript directory.")
    p_report.add_argument("manuscript_dir", help="Path to a manuscript/ directory")
    p_report.add_argument("--output", "-o", default="-", help="Output path or '-' for stdout")
    p_report.set_defaults(func=_cmd_report)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
