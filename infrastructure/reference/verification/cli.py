"""CLI for reference-existence verification.

Examples::

    # Offline: resolve only from cache; report unchecked entries honestly.
    uv run python -m infrastructure.reference.verification verify references.bib

    # Online: resolve against Crossref/OpenAlex/arXiv and cache the answers.
    uv run python -m infrastructure.reference.verification verify references.bib --live

    # Gate a manuscript before submission (fails on fabricated/mismatch/anachronism).
    uv run python -m infrastructure.reference.verification verify references.bib \\
        --live --as-of-year 2026 --fail-on-issues

    # Clear the persistent resolution cache.
    uv run python -m infrastructure.reference.verification cache-clear
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from infrastructure.core.cli_scaffold import emit_schema
from infrastructure.core.logging.utils import get_logger
from infrastructure.reference.verification.cache import ResolutionCache
from infrastructure.reference.verification.models import VerificationReport
from infrastructure.reference.verification.resolver import ReferenceResolver
from infrastructure.reference.verification.verifier import verify_bibfile

logger = get_logger(__name__)


def _default_cache_path() -> Path:
    return Path.home() / ".cache" / "template" / "reference-verification.db"


def _build_resolver(args: argparse.Namespace) -> ReferenceResolver:
    cache = None if args.no_cache else ResolutionCache(Path(args.cache) if args.cache else _default_cache_path())
    return ReferenceResolver(
        cache=cache,
        allow_network=bool(args.live),
        mailto=args.mailto,
    )


def cmd_verify(args: argparse.Namespace) -> int:
    """Verify every reference in a ``.bib`` file."""
    bibfile = Path(args.bibfile)
    if not bibfile.is_file():
        logger.error("bib file not found: %s", bibfile)
        return 2
    resolver = _build_resolver(args)
    report = verify_bibfile(bibfile, resolver, as_of_year=args.as_of_year)

    if args.json:
        sys.stdout.write(json.dumps(report.to_dict(), indent=2, ensure_ascii=False) + "\n")
    else:
        _print_human(report)

    if report.has_blocking and not args.warn_only:
        return 1
    return 0


def cmd_cache_clear(args: argparse.Namespace) -> int:
    """Delete every cached resolution."""
    cache = ResolutionCache(Path(args.cache) if args.cache else _default_cache_path())
    removed = cache.clear()
    logger.info("cleared %d cached resolution(s) from %s", removed, cache.db_path)
    return 0


def _print_human(report: VerificationReport) -> None:
    logger.info("%s", report.summary_line())
    logger.info("network used: %s", report.network_used)
    for verdict in report.verdicts:
        if verdict.is_ok:
            continue
        logger.info("  [%s] %s — %s", verdict.status.value, verdict.citation_key, verdict.detail)
    if report.has_blocking:
        logger.error("%d blocking issue(s) found", len(report.blocking))


def _add_cache_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--cache", default=None, help=f"SQLite cache path (default: {_default_cache_path()})")
    p.add_argument("--no-cache", action="store_true", help="Disable the persistent resolution cache")


def build_parser() -> argparse.ArgumentParser:
    """Create the argparse parser for the verification CLI."""
    parser = argparse.ArgumentParser(
        description="Verify that cited references exist and match their metadata",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_verify = sub.add_parser("verify", help="Verify references in a .bib file")
    p_verify.add_argument("bibfile", help="Path to the .bib file to verify")
    p_verify.add_argument(
        "--live",
        action="store_true",
        help="Allow network calls to Crossref/OpenAlex/arXiv (default: offline, cache-only)",
    )
    p_verify.add_argument(
        "--as-of-year",
        type=int,
        default=None,
        help="Manuscript year; references dated after it are flagged as anachronisms",
    )
    p_verify.add_argument("--mailto", default=None, help="Contact email for Crossref polite pool")
    p_verify.add_argument("--json", action="store_true", help="Emit the report as JSON to stdout")
    p_verify.add_argument(
        "--fail-on-issues",
        action="store_true",
        help="(default behavior) exit non-zero when blocking issues are found",
    )
    p_verify.add_argument(
        "--warn-only",
        action="store_true",
        help="Always exit 0, even when blocking issues are found",
    )
    _add_cache_args(p_verify)
    p_verify.set_defaults(func=cmd_verify)

    p_clear = sub.add_parser("cache-clear", help="Clear the persistent resolution cache")
    _add_cache_args(p_clear)
    p_clear.set_defaults(func=cmd_cache_clear)

    p_schema = sub.add_parser("schema", help="Print this CLI's parameter schema as JSON and exit")
    p_schema.set_defaults(func=lambda _args: emit_schema(build_parser()))

    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the reference-verification CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
