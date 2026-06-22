"""CLI surface for ``python -m infrastructure.doctor``.

Subcommands (all support ``--repo-root`` and ``--json``):

* ``diagnose`` (default) — run every detector, print findings + score.
* ``fix`` — diagnose, then apply fixes through the safety chokepoint.
    * ``--plan`` prints the plan without applying.
    * ``--apply`` actually executes.
    * ``--aggressive`` raises the therapy cap from conservative →
      radical (still backed up, still reversible where the fix says so).
    * ``--select CODE[,CODE...]`` narrows to specific finding codes.
    * ``--fix-id ID[,ID...]`` narrows to specific fixers.
* ``undo`` — undo the last applied action (``--last``) or a specific
  ``--action-id``.
* ``history`` — print the action journal.
* ``capabilities`` — JSON describing every detector and fixer; the
  agent-facing manifest.
* ``robot-docs`` — agent-readable, stable-text manual.

Every subcommand exits with a stable code (see :mod:`.reporter`).
"""

import argparse
import json
import sys
from pathlib import Path

from infrastructure.core.cli_scaffold import emit_schema
from infrastructure.core.logging.utils import get_logger
from infrastructure.doctor.detectors import DETECTORS, run_detectors
from infrastructure.doctor.fixers import FIXER_REGISTRY, build_plans_for_findings
from infrastructure.doctor.models import DoctorReport, TherapyLevel
from infrastructure.doctor.reporter import (
    EXIT_CRITICAL,
    EXIT_USAGE,
    compute_exit_code,
    render_report_json,
    render_report_text,
)
from infrastructure.doctor.safety import (
    DoctorSafetyError,
    DoctorState,
    load_journal,
    mutate,
    undo,
)
from infrastructure.doctor.scorecard import (
    DIMENSION_WEIGHTS,
    DIMENSIONS,
    compute_scorecard,
)


__all__ = ["build_parser", "main"]


logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="infrastructure.doctor",
        description=(
            "Diagnose and safely repair template repository state. "
            "Every mutation is backed up and journalled in .doctor/."
        ),
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root (default: current directory).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON to stdout instead of a human-readable table.",
    )

    sub = parser.add_subparsers(dest="command", required=False)

    sub_diag = sub.add_parser("diagnose", help="Run detectors and print findings.")
    sub_diag.set_defaults(command="diagnose")
    # ``diagnose`` has no extra args today but keeping the subparser
    # explicit lets us add flags (e.g. ``--detector``) without breaking
    # the signature.

    sub_fix = sub.add_parser("fix", help="Diagnose, then apply fixes.")
    sub_fix.add_argument("--apply", action="store_true", help="Apply fixes.")
    sub_fix.add_argument(
        "--plan",
        action="store_true",
        help="Print the fix plan without applying. Implies --no-apply.",
    )
    sub_fix.add_argument(
        "--aggressive",
        action="store_true",
        help="Allow radical-therapy fixes (still reversible via backup).",
    )
    sub_fix.add_argument(
        "--moderate",
        action="store_true",
        help="Allow moderate-therapy fixes (e.g. uv sync). Implied by --aggressive.",
    )
    sub_fix.add_argument(
        "--select",
        default="",
        help="Comma-separated finding codes to fix (default: all).",
    )
    sub_fix.add_argument(
        "--fix-id",
        default="",
        help="Comma-separated fix ids to apply (default: all available).",
    )

    sub_undo = sub.add_parser("undo", help="Reverse a previously applied fix.")
    sub_undo.add_argument(
        "--action-id",
        default="",
        help="Specific action_id to undo (see `history`).",
    )
    sub_undo.add_argument(
        "--last",
        action="store_true",
        help="Undo the most recent applied, reversible action.",
    )

    sub.add_parser("history", help="Print the action journal.")

    sub.add_parser(
        "capabilities",
        help="Print JSON describing every detector and fixer.",
    )

    sub.add_parser("robot-docs", help="Stable-text manual for agentic callers.")

    sub.add_parser("schema", help="Print this CLI's parameter schema as JSON and exit.")

    return parser


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


def _emit_report(report: DoctorReport, *, as_json: bool) -> None:
    if as_json:
        sys.stdout.write(render_report_json(report) + "\n")
    else:
        sys.stdout.write(render_report_text(report) + "\n")


def _build_report(
    repo_root: Path,
    *,
    applied: list | None = None,
    skipped: list | None = None,
    failed: list | None = None,
) -> DoctorReport:
    findings = run_detectors(repo_root)
    overall, dims = compute_scorecard(findings)
    return DoctorReport(
        findings=findings,
        applied=applied or [],
        skipped=skipped or [],
        failed=failed or [],
        overall_score=overall,
        dimension_scores=dims,
        exit_code=compute_exit_code(findings),
    )


def cmd_diagnose(args: argparse.Namespace) -> int:
    report = _build_report(args.repo_root)
    _emit_report(report, as_json=args.json)
    return report.exit_code


def cmd_fix(args: argparse.Namespace) -> int:
    state = DoctorState(args.repo_root)
    state.ensure()

    findings = run_detectors(args.repo_root)

    therapy = TherapyLevel.CONSERVATIVE
    if args.moderate or args.aggressive:
        therapy = TherapyLevel.MODERATE
    if args.aggressive:
        therapy = TherapyLevel.RADICAL

    selected_codes = frozenset(c.strip() for c in args.select.split(",") if c.strip()) if args.select else None
    selected_fix_ids = frozenset(f.strip() for f in args.fix_id.split(",") if f.strip()) if args.fix_id else None

    plans = build_plans_for_findings(
        findings,
        state,
        max_therapy=therapy,
        selected_codes=selected_codes,
        selected_fix_ids=selected_fix_ids,
    )

    applied = []
    skipped = []
    failed = []

    if args.plan or not args.apply:
        # Plan-only: surface what would happen, don't touch anything.
        skipped = list(plans)
    else:
        for plan in plans:
            try:
                record = mutate(plan, state)
            except DoctorSafetyError as exc:
                logger.error("Safety refusal: %s", exc)
                # Fabricate a failure record so the report carries it.
                # We deliberately do not append to the journal here —
                # the chokepoint only journals attempts it could
                # safely begin (snapshots + handler dispatch). Pre-
                # snapshot safety refusals never touched the FS.
                continue
            if record.applied:
                applied.append(record)
            else:
                failed.append(record)

    # Re-run detectors to capture the post-fix state.
    post_findings = run_detectors(args.repo_root)
    overall, dims = compute_scorecard(post_findings)
    report = DoctorReport(
        findings=post_findings,
        applied=applied,
        skipped=skipped,
        failed=failed,
        overall_score=overall,
        dimension_scores=dims,
        exit_code=compute_exit_code(post_findings),
    )
    _emit_report(report, as_json=args.json)
    return report.exit_code


def cmd_undo(args: argparse.Namespace) -> int:
    state = DoctorState(args.repo_root)
    records = load_journal(state)
    target = None
    if args.action_id:
        for r in records:
            if r.action_id == args.action_id:
                target = r
                break
        if target is None:
            sys.stderr.write(f"No action with id={args.action_id}\n")
            return EXIT_USAGE
    elif args.last:
        for r in reversed(records):
            if r.applied and r.reversible and not r.fix_id.startswith("undo:"):
                target = r
                break
        if target is None:
            sys.stderr.write("No reversible action to undo.\n")
            return EXIT_USAGE
    else:
        sys.stderr.write("Specify --action-id or --last.\n")
        return EXIT_USAGE

    try:
        undo_record = undo(target, state)
    except DoctorSafetyError as exc:
        sys.stderr.write(f"Undo refused: {exc}\n")
        return EXIT_CRITICAL

    if args.json:
        sys.stdout.write(json.dumps(undo_record.to_jsonable(), indent=2, sort_keys=True) + "\n")
    else:
        sys.stdout.write(f"Undid {target.action_id} ({target.fix_id}); new action id {undo_record.action_id}\n")
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    state = DoctorState(args.repo_root)
    records = load_journal(state)
    if args.json:
        sys.stdout.write(json.dumps([r.to_jsonable() for r in records], indent=2, sort_keys=True) + "\n")
    else:
        for r in records:
            status = "OK " if r.applied else "ERR"
            sys.stdout.write(f"{r.timestamp_utc}  {status}  {r.action_id}  {r.fix_id}  ({r.therapy})  {r.title}\n")
            if r.error:
                sys.stdout.write(f"    error: {r.error}\n")
    return 0


def cmd_capabilities(args: argparse.Namespace) -> int:
    payload = {
        "version": "1.0",
        "detectors": [
            {"name": d.__name__, "doc": (d.__doc__ or "").strip().splitlines()[0] if d.__doc__ else ""}
            for d in DETECTORS
        ],
        "fixers": [
            {
                "fix_id": fid,
                "doc": (builder.__doc__ or "").strip().splitlines()[0] if builder.__doc__ else "",
            }
            for fid, builder in FIXER_REGISTRY.items()
        ],
        "therapy_levels": [t.label for t in TherapyLevel],
        "dimensions": DIMENSIONS,
        "dimension_weights": DIMENSION_WEIGHTS,
        "exit_codes": {
            "healthy": 0,
            "warn": 1,
            "error": 2,
            "critical": 3,
            "usage": 64,
        },
    }
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return 0


def cmd_robot_docs(args: argparse.Namespace) -> int:
    sys.stdout.write(_ROBOT_DOCS)
    return 0


def cmd_schema(args: argparse.Namespace) -> int:
    """Print this CLI's parameter schema as JSON and exit 0."""
    return emit_schema(build_parser())


_ROBOT_DOCS = """\
infrastructure.doctor — robot-readable usage manual
====================================================

This document is stable across versions; an agent may parse it.

USAGE
  python -m infrastructure.doctor [--repo-root PATH] [--json] <command> [args]

COMMANDS
  diagnose                  Run detectors. Print findings + score.
  fix --apply               Diagnose then apply conservative fixes.
  fix --apply --moderate    Also apply moderate-therapy fixes (e.g. uv sync).
  fix --apply --aggressive  Also apply radical-therapy fixes (orphan removal).
  fix --plan                Show fix plan without applying.
  undo --last               Reverse the most recent reversible action.
  undo --action-id ID       Reverse a specific action from the journal.
  history                   Print the journal (.doctor/actions.jsonl).
  capabilities              JSON manifest of detectors / fixers / dimensions.
  robot-docs                This document.

EXIT CODES
  0  healthy            (no findings worse than INFO)
  1  warnings present
  2  one or more errors
  3  critical findings present
  64 usage error (BSD EX_USAGE)

CONTRACT
  - Every fix is backed up under .doctor/backups/<action_id>/.
  - Every fix is recorded in .doctor/actions.jsonl (append-only).
  - "undo --last" restores the most recent reversible action byte-for-byte
    (SHA-256 verified). Non-reversible fixes are flagged in the JSON output
    via "reversible": false; the agent must decide whether to proceed.
  - The doctor refuses to mutate paths outside the repo or inside .doctor/.

INSPECTION
  --json on any command emits a JSON document on stdout. Schema is stable;
  fields added over time will not change meaning.
"""


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------


_DISPATCH = {
    "diagnose": cmd_diagnose,
    "fix": cmd_fix,
    "undo": cmd_undo,
    "history": cmd_history,
    "capabilities": cmd_capabilities,
    "robot-docs": cmd_robot_docs,
    "schema": cmd_schema,
}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    cmd = args.command or "diagnose"
    handler = _DISPATCH.get(cmd)
    if handler is None:  # pragma: no cover — argparse already constrains
        parser.print_help(sys.stderr)
        return EXIT_USAGE
    return handler(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
