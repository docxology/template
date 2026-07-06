#!/usr/bin/env python3
"""One-shot doc path migration: rewrite script references to subpackage paths.

Updates tracked documentation and config to prefer:
  scripts/audit/*, scripts/pipeline/stage_*, scripts/runner/*,
  scripts/docgen/*, scripts/publish/*, scripts/shell/*

Skips disposable trees (output/, project output/, caches).
"""

from __future__ import annotations

import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Longest paths first to avoid partial replacements.
REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("scripts/check_tracked_generated_artifacts.py", "scripts/audit/check_tracked_generated_artifacts.py"),
    ("scripts/check_tracked_projects.py", "scripts/audit/check_tracked_projects.py"),
    ("scripts/check_tracked_fonds.py", "scripts/audit/check_tracked_fonds.py"),
    ("scripts/check_tracked_rules.py", "scripts/audit/check_tracked_rules.py"),
    ("scripts/check_tracked_tools.py", "scripts/audit/check_tracked_tools.py"),
    ("scripts/check_tracked_all.py", "scripts/audit/check_tracked_all.py"),
    ("scripts/check_template_drift.py", "scripts/audit/check_template_drift.py"),
    ("scripts/audit_documentation.py", "scripts/audit/audit_documentation.py"),
    ("scripts/audit_filepaths.py", "scripts/audit/audit_filepaths.py"),
    ("scripts/verify_no_mocks.py", "scripts/audit/verify_no_mocks.py"),
    ("scripts/lint_docs.py", "scripts/audit/lint_docs.py"),
    ("scripts/copy_exemplar.py", "scripts/audit/copy_exemplar.py"),
    ("scripts/07_generate_executive_report.py", "scripts/pipeline/stage_07_executive_report.py"),
    ("scripts/12_metadata_package.py", "scripts/pipeline/stage_12_metadata.py"),
    ("scripts/11_ebook_generation.py", "scripts/pipeline/stage_11_ebook.py"),
    ("scripts/06_llm_review.py", "scripts/pipeline/stage_06_llm_review.py"),
    ("scripts/05_copy_outputs.py", "scripts/pipeline/stage_05_copy.py"),
    ("scripts/04_validate_output.py", "scripts/pipeline/stage_04_validate.py"),
    ("scripts/03_render_pdf.py", "scripts/pipeline/stage_03_render.py"),
    ("scripts/02_run_analysis.py", "scripts/pipeline/stage_02_analysis.py"),
    ("scripts/01_run_tests.py", "scripts/pipeline/stage_01_test.py"),
    ("scripts/00_setup_environment.py", "scripts/pipeline/stage_00_setup.py"),
    ("scripts/10_research_workflow.py", "scripts/pipeline/stage_10_research_workflow.py"),
    ("scripts/09_provenance_record.py", "scripts/pipeline/stage_09_provenance_record.py"),
    ("scripts/08_connector_search.py", "scripts/pipeline/stage_08_connector_search.py"),
    ("scripts/publish_project_release.py", "scripts/publish/publish_project_release.py"),
    ("scripts/08_executable_bundle.py", "scripts/runner/bundle_executable.py"),
    ("scripts/09_archive_publication.py", "scripts/runner/archive_publication.py"),
    ("scripts/10_repro_bundle.py", "scripts/runner/repro_bundle.py"),
    ("scripts/execute_multi_project.py", "scripts/runner/execute_multi_project.py"),
    ("scripts/execute_pipeline.py", "scripts/runner/execute_pipeline.py"),
    ("scripts/run_matrix.py", "scripts/runner/run_matrix.py"),
    ("scripts/generate_publication_records_doc.py", "scripts/docgen/publication_records.py"),
    ("scripts/generate_exemplar_roster_doc.py", "scripts/docgen/exemplar_roster.py"),
    ("scripts/generate_architecture_overview.py", "scripts/docgen/architecture_overview.py"),
    ("scripts/generate_coverage_history.py", "scripts/docgen/coverage_history.py"),
    ("scripts/generate_api_reference_doc.py", "scripts/docgen/api_reference.py"),
    ("scripts/generate_active_projects_doc.py", "scripts/docgen/active_projects.py"),
    ("scripts/generate_stage_table_doc.py", "scripts/docgen/stage_table.py"),
    ("scripts/generate_counts.py", "scripts/docgen/counts.py"),
    ("scripts/shell_bootstrap.sh", "scripts/shell/shell_bootstrap.sh"),
    ("scripts/backup-weekly.sh", "scripts/shell/backup-weekly.sh"),
    ("scripts/backup-daily.sh", "scripts/shell/backup-daily.sh"),
    ("scripts/backup-full.sh", "scripts/shell/backup-full.sh"),
    ("scripts/restore-test.sh", "scripts/shell/restore-test.sh"),
    ("scripts/health-check.sh", "scripts/shell/health-check.sh"),
    ("scripts/bash_utils.sh", "scripts/shell/bash_utils.sh"),
    ("scripts/ci_local.sh", "scripts/shell/ci_local.sh"),
)

SKIP_DIR_NAMES = frozenset(
    {
        ".git",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "node_modules",
    }
)

SKIP_PATH_PARTS = frozenset({"output"})

TEXT_SUFFIXES = frozenset(
    {
        ".md",
        ".yaml",
        ".yml",
        ".py",
        ".sh",
        ".toml",
        ".json",
        ".txt",
        ".cursorrules",
    }
)


def _should_skip(path: Path) -> bool:
    rel = path.relative_to(REPO_ROOT)
    if any(part in SKIP_PATH_PARTS for part in rel.parts):
        return True
    if any(part in SKIP_DIR_NAMES for part in rel.parts):
        return True
    if rel == Path("scripts/maintenance/migrate_doc_script_paths.py"):
        return True
    return False


def _iter_targets() -> list[Path]:
    files: list[Path] = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if _should_skip(path):
            continue
        if path.suffix not in TEXT_SUFFIXES and path.name not in {".cursorrules"}:
            continue
        files.append(path)
    return sorted(files)


def migrate_file(path: Path, *, dry_run: bool) -> int:
    original = path.read_text(encoding="utf-8")
    updated = original
    for old, new in REPLACEMENTS:
        updated = updated.replace(old, new)
    if updated == original:
        return 0
    if not dry_run:
        path.write_text(updated, encoding="utf-8")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Report files that would change.")
    args = parser.parse_args(argv)

    changed = 0
    for path in _iter_targets():
        if migrate_file(path, dry_run=args.dry_run):
            changed += 1
            print(path.relative_to(REPO_ROOT))
    print(f"{'Would update' if args.dry_run else 'Updated'} {changed} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
