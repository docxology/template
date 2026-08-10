"""Quality gate: validate every chapter's structure and report fill progress.

Delegates to :func:`textbook.audit.run_manuscript_audit`. The default mode
validates scaffold structure while reporting allowed stub counts. Pass
``--require-complete`` to fail on any remaining audited-section stubs, or
``--lenient`` to treat missing files as warnings while drafting.
"""

from __future__ import annotations

import argparse

from _bootstrap import PROJECT as PROJECT_DIR, ensure_project_paths

ensure_project_paths()


def main() -> int:
    """CLI entry point."""
    from textbook.audit import format_audit_table, run_manuscript_audit
    from textbook.config import load_config

    parser = argparse.ArgumentParser(description="Audit template_textbook structure + progress")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--lenient",
        action="store_true",
        help="Do not fail on missing declared files (still fail on structural/orphan problems).",
    )
    mode.add_argument(
        "--require-complete",
        action="store_true",
        help="Fail when any audited unit intro or chapter still contains stub markers.",
    )
    parser.add_argument(
        "--check-generated",
        action="store_true",
        help="Also reject stale or missing generated Mermaid diagram artifacts.",
    )
    args = parser.parse_args()

    config = load_config(PROJECT_DIR / "manuscript")
    report = run_manuscript_audit(
        PROJECT_DIR,
        config,
        require_present=not args.lenient,
        require_complete=args.require_complete,
    )

    generated_problems: tuple[str, ...] = ()
    if args.check_generated:
        from mermaid.diagrams import load_specs
        from textbook.contracts import validate_diagram_inventory

        generated_problems = validate_diagram_inventory(load_specs(), PROJECT_DIR / "output" / "figures" / "mermaid")

    print(format_audit_table(report.rows, report.total_words, report.total_stubs))

    problems = (*report.problems, *generated_problems)
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for problem in problems:
            print(f"  ✗ {problem}")
        return 1
    if args.require_complete:
        print("\n[audit] all audited sections are structurally valid and contain zero stub markers ✓")
    elif report.total_stubs:
        print(
            "\n[audit] scaffold structure valid; "
            f"{report.total_stubs} stub markers remain (allowed in default mode; "
            "use --require-complete for a filled-manuscript gate) ✓"
        )
    else:
        print("\n[audit] all declared manuscript files present and structurally valid ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
