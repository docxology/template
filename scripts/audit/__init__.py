"""Audit and quality-gate scripts.

Thin orchestrators for documentation, file-path, mock-usage, drift, and
tracked-resource audits.  None of these run in the default ``./run.sh``
pipeline — invoke them directly when needed.

Modules:

    lint_docs                        – documentation lint runner
    audit_documentation              – advisory RedTeam docs audit
    verify_no_mocks                  – mock-usage checker
    audit_filepaths                  – repository filepath audit
    check_template_drift             – exemplar doc/code drift check
    check_tracked_projects           – confidentiality guard
    check_tracked_fonds              – fonds resource-pool git guard
    check_tracked_rules              – rules resource-pool git guard
    check_tracked_tools              – tools resource-pool git guard
    check_tracked_all                – all-resource git guard (umbrella)
    check_tracked_generated_artifacts– generated-artifact git-index hygiene
    copy_exemplar                    – copy/update a canonical exemplar
"""

__all__ = [
    "lint_docs",
    "audit_documentation",
    "verify_no_mocks",
    "audit_filepaths",
    "check_template_drift",
    "check_tracked_projects",
    "check_tracked_fonds",
    "check_tracked_rules",
    "check_tracked_tools",
    "check_tracked_all",
    "check_tracked_generated_artifacts",
    "copy_exemplar",
]
