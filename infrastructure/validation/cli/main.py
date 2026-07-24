"""CLI interface for validation operations.

Thin orchestrator wrapping infrastructure.validation module functionality.
"""

import argparse
import contextlib
import io
import json
import logging
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Iterator

from infrastructure.core.cli_scaffold import emit_schema
from infrastructure.core.exceptions import RenderingError
from infrastructure.core.logging.utils import get_logger
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.rendering.manuscript_discovery import discover_manuscript_files
from infrastructure.validation.integrity.checks import verify_output_integrity
from infrastructure.validation.integrity.link_validator import LinkValidator
from infrastructure.validation.content.markdown_validator import validate_markdown
from infrastructure.validation.content.pdf_validator import validate_pdf_rendering
from infrastructure.validation.evidence_registry import (
    build_project_evidence_registry,
    unsupported_citation_tokens,
    unsupported_number_tokens,
    validate_text_against_registry,
)
from infrastructure.validation.publication import (
    build_publication_audit,
    format_publication_audit_json,
    format_publication_audit_markdown,
    validate_publication_audit,
)

logger = get_logger(__name__)


@contextlib.contextmanager
def _suppress_stdout_fd() -> Iterator[None]:
    """Temporarily silence stdout, including already-bound logging handlers."""
    sys.stdout.flush()
    saved_stdout_fd = os.dup(1)
    try:
        with open(os.devnull, "w", encoding="utf-8") as devnull:
            os.dup2(devnull.fileno(), 1)
            yield
    finally:
        sys.stdout.flush()
        os.dup2(saved_stdout_fd, 1)
        os.close(saved_stdout_fd)


def validate_pdf_command(args: argparse.Namespace) -> None:
    """Handle PDF validation."""
    pdf_path = Path(args.pdf_path)

    if not pdf_path.exists():
        logger.error(f"PDF not found: {pdf_path}")
        raise SystemExit(1)

    logger.info(f"Validating PDF: {pdf_path}")
    report = validate_pdf_rendering(pdf_path, n_words=args.preview_words)

    logger.info("\nValidation Results:")
    logger.info(f"Total issues found: {report['issues']['total_issues']}")

    # report['issues'] values are integers (counts), not lists
    unresolved_refs_count = report["issues"].get("unresolved_references", 0)
    if unresolved_refs_count > 0:
        logger.info(f"Unresolved references: {unresolved_refs_count}")
        if args.verbose:
            logger.info("  (See PDF for details)")

    missing_citations_count = report["issues"].get("missing_citations", 0)
    if missing_citations_count > 0:
        logger.info(f"Missing citations: {missing_citations_count}")

    if args.verbose and report.get("first_words"):
        words_preview = report["first_words"][:500] if report["first_words"] else ""
        if words_preview:
            logger.info(f"\nFirst words:\n{words_preview}")

    raise SystemExit(0 if not report["summary"]["has_issues"] else 1)


def validate_markdown_command(args: argparse.Namespace) -> None:
    """Handle Markdown validation."""
    md_dir = Path(args.markdown_dir)
    repo_root = Path(args.repo_root) if args.repo_root else Path(".")

    if not md_dir.exists():
        logger.error(f"Directory not found: {md_dir}")
        raise SystemExit(1)

    logger.info(f"Validating Markdown in: {md_dir}")
    strict = bool(getattr(args, "strict", False))
    problems, exit_code = validate_markdown(str(md_dir), str(repo_root), strict=strict)

    if problems:
        for problem in problems:
            loc = f"[{problem.file_path}] " if problem.file_path else ""
            logger.info(f"  {loc}{problem.message}")
    else:
        logger.info("  No issues found!")

    raise SystemExit(exit_code)


def validate_prerender_command(args: argparse.Namespace) -> None:
    """Run the strict source-markdown gate without triggering a full render.

    Mirrors the gate that :func:`PDFRenderer.render_combined` runs before
    Pandoc/xelatex (see
    ``infrastructure/rendering/_pdf_combined_renderer.py::prevalidate_for_render``).
    Useful as a pre-commit check or interactive verification step.

    Exits 0 when the manuscript is render-ready, 1 when any pitfall or
    undefined citation is found.
    """
    # Import from validation leaf — not the rendering package.
    from infrastructure.validation.content.prerender import prevalidate_for_render

    manuscript_dir = Path(args.manuscript_dir)
    if not manuscript_dir.exists():
        logger.error(f"Manuscript directory not found: {manuscript_dir}")
        raise SystemExit(1)

    repo_root = Path(args.repo_root) if args.repo_root else None
    bib_file = Path(args.bib) if args.bib else None

    logger.info(f"Pre-render validation: {manuscript_dir}")
    try:
        prevalidate_for_render(manuscript_dir, repo_root=repo_root, bib_file=bib_file)
    except RenderingError as exc:
        for line in str(exc).splitlines():
            logger.error(line)
        raise SystemExit(1) from exc

    logger.info("No render-blocking pitfalls or undefined citations found.")
    raise SystemExit(0)


def verify_integrity_command(args: argparse.Namespace) -> None:
    """Handle integrity verification."""
    output_dir = Path(args.output_dir)

    if not output_dir.exists():
        logger.error(f"Directory not found: {output_dir}")
        raise SystemExit(1)

    logger.info(f"Verifying integrity of: {output_dir}")
    report = verify_output_integrity(output_dir)

    # IntegrityReport is an object, not a dict
    total_files = len(report.file_integrity)
    total_issues = len(report.issues)

    logger.info("\nIntegrity Report:")
    logger.info(f"Files checked: {total_files}")
    logger.info(f"Issues found: {total_issues}")
    logger.info(f"Overall integrity: {'PASS' if report.overall_integrity else 'FAIL'}")

    if args.verbose and report.issues:
        logger.info("\nIssues:")
        for issue in report.issues[:10]:
            logger.info(f"  - {issue}")

    if args.verbose and report.warnings:
        logger.info("\nWarnings:")
        for warning in report.warnings[:10]:
            logger.info(f"  - {warning}")

    raise SystemExit(0 if report.overall_integrity else 1)


def validate_links_command(args: argparse.Namespace) -> None:
    """Handle link validation."""
    repo_root = Path(args.repo_root) if args.repo_root else Path.cwd()

    if not repo_root.exists():
        logger.error(f"Repository root not found: {repo_root}")
        raise SystemExit(1)

    logger.info(f"Validating links in repository: {repo_root}")

    validator = LinkValidator(repo_root)
    results = validator.validate_all_markdown_files()
    report = validator.generate_report(results)

    # Count broken links
    total_broken = sum(len(file_results["broken"]) for file_results in results.values())

    if args.output:
        output_path = Path(args.output)
        _tmp = output_path.with_suffix(output_path.suffix + ".tmp")
        try:
            _tmp.write_text(report, encoding="utf-8")
            _tmp.replace(output_path)
        except OSError:
            _tmp.unlink(missing_ok=True)
            raise
        logger.info(f"Report saved to: {output_path}")
    else:
        logger.info(report)

    if total_broken > 0:
        logger.info(f"\n❌ Found {total_broken} broken link(s)")
        raise SystemExit(1)
    else:
        logger.info("\n✅ All links valid!")
        raise SystemExit(0)


def validate_evidence_command(args: argparse.Namespace) -> None:
    """Validate manuscript numbers and citations against the verified registry."""
    project_root = Path(args.project_root)
    manuscript_dir = Path(args.manuscript_dir) if args.manuscript_dir else project_root / "manuscript"
    if not project_root.exists():
        logger.error(f"Project root not found: {project_root}")
        raise SystemExit(1)
    if not manuscript_dir.exists():
        logger.error(f"Manuscript directory not found: {manuscript_dir}")
        raise SystemExit(1)

    registry = build_project_evidence_registry(project_root)
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in discover_manuscript_files(manuscript_dir)
        if path.is_file() and path.suffix.lower() == ".md"
    )
    report = validate_text_against_registry(text, registry)
    payload = {
        "unsupported_numbers": unsupported_number_tokens(report),
        "unsupported_citations": unsupported_citation_tokens(report),
        "has_issues": report.has_issues,
    }

    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        logger.info(f"Evidence report saved to: {output_path}")
    else:
        logger.info(json.dumps(payload, indent=2, sort_keys=True))

    raise SystemExit(1 if report.has_issues and args.fail_on_issues else 0)


def validate_prose_quality_command(args: argparse.Namespace) -> None:
    """Scan manuscript prose for AI-writing fingerprints (advisory by default)."""
    from infrastructure.validation.content.ai_writing import analyze_prose
    from infrastructure.validation.docs._io import read_markdown

    target = Path(args.path)
    if not target.exists():
        logger.error(f"Path not found: {target}")
        raise SystemExit(1)

    text: str
    if target.is_dir():
        md_files = sorted(p for p in target.rglob("*.md") if p.is_file())
        chunks = [read_markdown(p) for p in md_files]
        text = "\n\n".join(chunk for chunk in chunks if chunk is not None)
    else:
        loaded_text = read_markdown(target)
        if loaded_text is None:
            logger.error(f"Could not read: {target}")
            raise SystemExit(1)
        text = loaded_text

    report = analyze_prose(text)

    if args.json:
        logger.info(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        logger.info("Prose quality report:")
        logger.info(
            "words=%d sentences=%d em-dash/1k=%.1f ai-terms/1k=%.1f burstiness=%.2f",
            report.word_count,
            report.sentence_count,
            report.em_dash_per_1k,
            report.ai_term_per_1k,
            report.burstiness,
        )
        for hit in report.ai_term_hits:
            logger.info("  ai-term: %r ×%d", hit.term, hit.count)
        for flag in report.flags:
            logger.info("  ⚠ %s", flag)

    raise SystemExit(1 if report.has_flags and args.fail_on_flags else 0)


def publication_audit_command(args: argparse.Namespace) -> None:
    """Run the deterministic public-exemplar publication audit."""
    repo_root = Path(args.repo_root).resolve()
    projects = [args.project] if args.project else list(PUBLIC_PROJECT_NAMES)
    logging.getLogger("infrastructure.core.pipeline.dag").setLevel(logging.WARNING)
    if args.format == "json":
        with _suppress_stdout_fd(), contextlib.redirect_stdout(io.StringIO()):
            report = build_publication_audit(
                repo_root,
                projects,
                rendered=args.rendered,
                require_figure_accessibility=args.require_figure_accessibility,
            )
    else:
        report = build_publication_audit(
            repo_root,
            projects,
            rendered=args.rendered,
            require_figure_accessibility=args.require_figure_accessibility,
        )
    rendered = (
        format_publication_audit_json(report) if args.format == "json" else format_publication_audit_markdown(report)
    )
    if args.output:
        output = Path(args.output)
        if not output.is_absolute():
            output = repo_root / output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        logger.info("Publication audit written to %s", output)
    else:
        print(rendered, end="")
    raise SystemExit(validate_publication_audit(report, strict=args.strict))


def build_parser() -> argparse.ArgumentParser:
    """Construct the validation CLI argument parser.

    Extracted from :func:`main` so the ``schema`` subcommand can introspect the
    full parser. Adds no behavior beyond the existing subcommands plus the
    additive ``schema`` subcommand.
    """
    parser = argparse.ArgumentParser(description="Validate research output (PDFs, Markdown, integrity).")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # PDF validation
    pdf_parser = subparsers.add_parser("pdf", help="Validate PDF rendering")
    pdf_parser.add_argument("pdf_path", help="Path to PDF file")
    pdf_parser.add_argument("--preview-words", type=int, default=200, help="Number of words to preview")
    pdf_parser.add_argument("-v", "--verbose", action="store_true")
    pdf_parser.set_defaults(func=validate_pdf_command)

    # Markdown validation
    md_parser = subparsers.add_parser("markdown", help="Validate Markdown files")
    md_parser.add_argument("markdown_dir", help="Path to markdown directory")
    md_parser.add_argument("--repo-root", help="Repository root directory")
    md_parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when any ERROR-severity markdown issue is found",
    )
    md_parser.set_defaults(func=validate_markdown_command)

    # Pre-render strict gate
    prer_parser = subparsers.add_parser(
        "prerender",
        help="Strict source-markdown gate: pitfalls + undefined citations",
    )
    prer_parser.add_argument("manuscript_dir", help="Path to manuscript directory (source markdown set)")
    prer_parser.add_argument("--repo-root", help="Repository root for relative-path display")
    prer_parser.add_argument("--bib", help="Explicit references.bib path (overrides discovery)")
    prer_parser.set_defaults(func=validate_prerender_command)

    # Integrity verification
    int_parser = subparsers.add_parser("integrity", help="Verify output integrity")
    int_parser.add_argument("output_dir", help="Path to output directory")
    int_parser.add_argument("-v", "--verbose", action="store_true")
    int_parser.set_defaults(func=verify_integrity_command)

    # Link validation
    link_parser = subparsers.add_parser("links", help="Validate markdown links")
    link_parser.add_argument("--repo-root", help="Repository root directory (default: current directory)")
    link_parser.add_argument("--output", help="Output file for validation report")
    link_parser.set_defaults(func=validate_links_command)

    # Evidence registry validation
    evidence_parser = subparsers.add_parser(
        "evidence",
        help="Validate manuscript claims against registered project evidence",
    )
    evidence_parser.add_argument("project_root", help="Path to project root")
    evidence_parser.add_argument("--manuscript-dir", help="Path to manuscript markdown directory")
    evidence_parser.add_argument("--output-json", help="Write JSON evidence report")
    evidence_parser.add_argument(
        "--fail-on-issues",
        action="store_true",
        help="Exit non-zero when unsupported facts are found",
    )
    evidence_parser.set_defaults(func=validate_evidence_command)

    # Prose quality (AI-writing fingerprint) scan
    prose_parser = subparsers.add_parser(
        "prose-quality",
        help="Scan manuscript prose for AI-writing fingerprints (em-dash density, stock phrasing, burstiness)",
    )
    prose_parser.add_argument("path", help="Markdown file or directory to scan")
    prose_parser.add_argument("--json", action="store_true", help="Emit the report as JSON")
    prose_parser.add_argument(
        "--fail-on-flags",
        action="store_true",
        help="Exit non-zero when any AI-writing flag is raised (advisory by default)",
    )
    prose_parser.set_defaults(func=validate_prose_quality_command)

    publication_parser = subparsers.add_parser(
        "publication-audit",
        help="Audit public exemplars for deterministic publication readiness",
    )
    publication_parser.add_argument("--repo-root", default=".", help="Repository root")
    project_group = publication_parser.add_mutually_exclusive_group()
    project_group.add_argument("--project", help="Qualified project name under projects/")
    project_group.add_argument(
        "--all-public",
        action="store_true",
        help="Audit every project in PUBLIC_PROJECT_NAMES",
    )
    publication_parser.add_argument(
        "--rendered",
        action="store_true",
        help="Require and validate generated publication outputs and reports",
    )
    publication_parser.add_argument(
        "--strict",
        action="store_true",
        help="Also exit non-zero when review_required findings are present",
    )
    publication_parser.add_argument(
        "--require-figure-accessibility",
        action="store_true",
        help="Require explicit alt text for every referenced registered figure",
    )
    publication_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    publication_parser.add_argument("--output", help="Write the report to a file instead of stdout")
    publication_parser.set_defaults(func=publication_audit_command)

    # Schema introspection (additive; emits the whole CLI's JSON parameter contract)
    schema_parser = subparsers.add_parser(
        "schema",
        help="Print this CLI's parameter schema as JSON and exit",
    )
    schema_parser.set_defaults(func=None)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Main CLI entry point.

    Returns 0 for the ``schema`` subcommand; all other subcommands dispatch to a
    handler that raises :class:`SystemExit` with the command's own exit code
    (behavior unchanged from before the refactor).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if getattr(args, "command", None) == "schema":
        return emit_schema(parser)

    if not hasattr(args, "func"):
        parser.print_help()
        raise SystemExit(1)

    try:
        args.func(args)
    except Exception as e:  # noqa: BLE001
        logger.error(f"{e}")
        raise SystemExit(1) from e
    return 0


if __name__ == "__main__":
    main()
