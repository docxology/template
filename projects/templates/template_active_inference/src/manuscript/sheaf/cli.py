"""CLI helpers for sheaf manuscript composition."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from manuscript.sheaf import (
    ComposeOptions,
    MissingTrackPolicy,
    compose_all_sections,
    issues_have_errors,
    list_registered_tracks,
    load_manifest,
    validate_manifest,
)
from orchestration.coverage_pipeline import ensure_coverage_artifacts


def build_parser() -> argparse.ArgumentParser:
    """Build the sheaf composition command parser."""
    parser = argparse.ArgumentParser(
        description="Compose sheaf-bound manuscript sections from manifest + track registry.",
    )
    parser.add_argument(
        "--tracks",
        metavar="ID",
        help="Comma-separated track ids to include (default: all bound tracks per section).",
    )
    parser.add_argument(
        "--section",
        action="append",
        dest="sections",
        metavar="ID",
        help="Compose only these section ids (repeatable). Partial compose is draft-only.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on manifest validation errors, gray coverage cells, and missing non-optional tracks.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate manifest + registry; do not write composed markdown.",
    )
    parser.add_argument(
        "--list-tracks",
        action="store_true",
        help="Print registered track ids from manuscript/sheaf/tracks.yaml and exit.",
    )
    parser.add_argument(
        "--missing",
        choices=("skip", "warn", "error"),
        default=None,
        help="Override missing-track policy for this run.",
    )
    parser.add_argument(
        "--coverage-json",
        metavar="PATH",
        nargs="?",
        const="output/data/sheaf_coverage_matrix.json",
        help="Write coverage matrix JSON (default: output/data/sheaf_coverage_matrix.json).",
    )
    parser.add_argument(
        "--coverage-heatmap",
        metavar="PATH",
        nargs="?",
        const="output/figures/sheaf_coverage_heatmap.png",
        help="Write coverage heatmap PNG after JSON export (default path under output/figures/).",
    )
    return parser


def _emit_issues(issues: list) -> None:
    for issue in issues:
        print(f"{issue.level.upper()}: {issue.message}", file=sys.stderr)


def _coverage_paths(args: argparse.Namespace, project_root: Path) -> tuple[Path, Path]:
    return (
        project_root / (args.coverage_json or "output/data/sheaf_coverage_matrix.json"),
        project_root / (args.coverage_heatmap or "output/figures/sheaf_coverage_heatmap.png"),
    )


def _emit_coverage(args: argparse.Namespace, project_root: Path) -> int:
    if args.coverage_json is None and args.coverage_heatmap is None:
        return 0
    json_path, heatmap_path = _coverage_paths(args, project_root)
    render_heatmap = args.coverage_heatmap is not None
    json_out, png_out, page_out = ensure_coverage_artifacts(
        project_root,
        json_path=json_path,
        heatmap_path=heatmap_path if render_heatmap else None,
        write_page=render_heatmap,
        json_only=not render_heatmap and args.coverage_json is not None,
        render_heatmap=render_heatmap,
    )
    if render_heatmap and png_out is None:
        print("coverage heatmap generation failed", file=sys.stderr)
        return 1
    print(json_out)
    if png_out is not None:
        print(png_out)
    if page_out is not None:
        print(page_out)
    return 0


def run_compose_cli(
    argv: list[str] | None = None,
    *,
    project_root: Path,
) -> int:
    """Run the sheaf composition CLI for ``project_root``."""
    args = build_parser().parse_args(argv)

    if args.list_tracks:
        for spec in list_registered_tracks(project_root):
            opt = " (optional)" if spec.optional else ""
            print(f"{spec.id}\torder={spec.order}\trenderer={spec.renderer}{opt}")
        return 0

    manifest = load_manifest(
        project_root / "manuscript" / "sheaf" / "manifest.yaml",
        project_root=project_root,
    )
    if args.validate_only:
        issues = validate_manifest(manifest, project_root, strict_coverage=args.strict)
        _emit_issues(issues)
        if issues_have_errors(issues):
            return 1
        return _emit_coverage(args, project_root)

    enabled = frozenset(t.strip() for t in args.tracks.split(",") if t.strip()) if args.tracks else None
    section_ids = frozenset(args.sections) if args.sections else None
    missing = MissingTrackPolicy(args.missing) if args.missing else None
    options = ComposeOptions(
        enabled_tracks=enabled,
        section_ids=section_ids,
        missing_track=missing,
        strict=args.strict,
    )
    try:
        result = compose_all_sections(project_root, options=options)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    _emit_issues(result.issues)
    if issues_have_errors(result.issues):
        return 1
    for path in result.paths:
        print(path)
    return _emit_coverage(args, project_root)
