"""Quality gate: validate every chapter's structure and report fill progress.

Delegates to :func:`textbook.audit.run_manuscript_audit`. Strict by default:
missing declared files and orphan part markdown fail the gate. Pass
``--lenient`` to treat missing files as warnings only (structural problems still
fail).
"""

from __future__ import annotations

import argparse

from _bootstrap import PROJECT as PROJECT_DIR, ensure_project_paths

ensure_project_paths()


def main() -> int:
    from textbook.audit import format_audit_table, run_manuscript_audit
    from textbook.config import load_config

    parser = argparse.ArgumentParser(description="Audit template_textbook structure + progress")
    parser.add_argument(
        "--lenient",
        action="store_true",
        help="Do not fail on missing declared files (still fail on structural/orphan problems).",
    )
    args = parser.parse_args()

    config = load_config(PROJECT_DIR / "manuscript")
    report = run_manuscript_audit(PROJECT_DIR, config, require_present=not args.lenient)

    print(format_audit_table(report.rows, report.total_words, report.total_stubs))

    if report.problems:
        print(f"\n{len(report.problems)} problem(s):")
        for problem in report.problems:
            print(f"  ✗ {problem}")
        return 1
    print("\n[audit] all declared manuscript files present and structurally valid ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
