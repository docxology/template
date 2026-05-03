"""Command-line interface for citation export.

Subcommands:

* ``validate`` — round-trip-parse a ``.bib`` file; exits non-zero on syntax
  errors and reports the entry count + missing required fields per type.
* ``format`` — re-emit a ``.bib`` file using our canonical formatter so its
  layout matches ``projects/template_code_project/manuscript/references.bib``.
* ``convert`` — read a JSON file of literature-search :class:`Paper`-shaped
  records and emit a BibTeX file with auto-generated citation keys.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.reference.citation.bibtex_parser import BibParseError, parse_bibfile
from infrastructure.reference.citation.bibtex_writer import render_database, write_bibfile
from infrastructure.reference.citation.converter import paper_to_bibentry
from infrastructure.reference.citation.models import BibDatabase

logger = get_logger(__name__)

# Minimum required fields per BibTeX entry type (advisory, not strict).
_REQUIRED_FIELDS: dict[str, frozenset[str]] = {
    "article": frozenset({"title", "author", "year"}),
    "book": frozenset({"title", "author", "year"}),
    "inproceedings": frozenset({"title", "author", "booktitle", "year"}),
    "incollection": frozenset({"title", "author", "booktitle", "year"}),
    "phdthesis": frozenset({"title", "author", "year"}),
    "techreport": frozenset({"title", "author", "year"}),
    "misc": frozenset({"title"}),
}


def _cmd_validate(args: argparse.Namespace) -> int:
    path = Path(args.path)
    try:
        db = parse_bibfile(path)
    except BibParseError as exc:
        logger.error("BibTeX parse error in %s: %s", path, exc)
        return 2

    issues = 0
    for entry in db.entries:
        required = _REQUIRED_FIELDS.get(entry.entry_type, frozenset())
        missing = sorted(f for f in required if not entry.has(f))
        if missing:
            issues += 1
            logger.warning(
                "Entry %s (%s) missing required fields: %s",
                entry.citation_key,
                entry.entry_type,
                ", ".join(missing),
            )

    logger.info("Parsed %d entries from %s (%d with missing fields)", len(db), path, issues)
    return 1 if (issues > 0 and args.strict) else 0


def _cmd_format(args: argparse.Namespace) -> int:
    path = Path(args.path)
    db = parse_bibfile(path)
    output_path = Path(args.output) if args.output else path
    write_bibfile(output_path, db)
    logger.info("Reformatted %d entries → %s", len(db), output_path)
    return 0


def _cmd_convert(args: argparse.Namespace) -> int:
    # Local import to keep the citation module importable without the
    # search module being available (e.g. on minimal installs).
    from infrastructure.search.literature.models import Paper

    raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "papers" in raw:
        records = raw["papers"]
    elif isinstance(raw, list):
        records = raw
    else:
        logger.error("Input %s must be a list of papers or {'papers': [...]}", args.input)
        return 2

    db = BibDatabase()
    for record in records:
        paper = Paper.from_dict(record)
        db.add(paper_to_bibentry(paper))

    output_path = Path(args.output)
    if args.output == "-":
        sys.stdout.write(render_database(db))
    else:
        write_bibfile(output_path, db)
        logger.info("Wrote %d entries → %s", len(db), output_path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m infrastructure.reference.citation",
        description="BibTeX validation, formatting, and Paper→BibTeX conversion.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="Parse a .bib file and report issues.")
    p_validate.add_argument("path", help="Path to .bib file")
    p_validate.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when entries are missing required fields.",
    )
    p_validate.set_defaults(func=_cmd_validate)

    p_format = sub.add_parser("format", help="Re-emit a .bib file in canonical format.")
    p_format.add_argument("path", help="Path to .bib file")
    p_format.add_argument("--output", "-o", help="Output path (default: overwrite input)")
    p_format.set_defaults(func=_cmd_format)

    p_convert = sub.add_parser("convert", help="Convert a JSON file of Paper records to BibTeX.")
    p_convert.add_argument("input", help="Input JSON path")
    p_convert.add_argument(
        "output",
        help="Output .bib path, or '-' for stdout",
    )
    p_convert.set_defaults(func=_cmd_convert)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
