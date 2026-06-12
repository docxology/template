# audit/ - Audit Reports

Directory for audit reports and validation snapshots.

## Status

The historical audit reports that previously lived here have been moved
to [`archived/`](archived/) — each report is a point-in-time snapshot
whose file paths and line numbers refer to the tree as it was at
generation, and several pairs of reports disagreed by ~100+ broken-link
issues (artifact of being written months apart). Keeping them in the
top-level audit directory implied they were all current; archiving with
the report date suffixed makes the chronology explicit.

**For current drift status, use the live linters, not the snapshots:**

| Linter | Command | Surface |
|---|---|---|
| Repo-wide doc linter | `uv run python scripts/lint_docs.py` | mermaid block parsing, cross-link integrity, sibling-doc consistency, AGENTS.md/README.md pair presence (all mermaid blocks + every markdown link checked) |
| Documentation RedTeam audit | `uv run python scripts/audit_documentation.py --format markdown` | advisory inventory of public docs, generated-fact grounding, verifier negative-control claims, and Python `def` / `class` documentation coverage |
| Template drift checker | `uv run python scripts/check_template_drift.py` | 9 per-exemplar detectors + 2 repo-level checks (`repo_docs_hardcoded_counts`, thin-orchestrator script AST/line-count on root `scripts/` and `projects/*/scripts/`) |
| Documentation verification checks | `DocumentationScanner.run_verification_checks()` in `infrastructure/validation/docs/scanner.py` | Delegates to `run_verification_checks()` — `run_docs_lint`, `validate_markdown`, `verify_commands`, `detect_markdown_link_cycles()` — see [`infrastructure/validation/docs/AGENTS.md`](../../infrastructure/validation/docs/AGENTS.md) |
| Filepath audit (on-demand snapshot) | `uv run python scripts/audit_filepaths.py --output docs/audit/filepath-audit-report-$(date +%Y-%m-%d).md` | one-off broken-reference scan; archive the result rather than keep in top-level |

## Archived snapshots

See [`archived/`](archived/) — each filename ends in `-YYYY-MM-DD.md`
naming the generation date. Reports archived during the May 2026
hardening pass:

- `triple-check-report-2026-04-27.md` (15-pass deep review)
- `documentation-review-report-2026-05-04.md`
- `documentation-review-summary-2026-05-15.md`
- `filepath-audit-report-2026-05-16.md`
- `literature-modules-audit-2026-05-01.md` (`infrastructure/search/` + `infrastructure/reference/`)
- `thermo-nuclear-code-quality-2026-06-11-staged-closeout.md` (staged-deletion close-out — Phases 1–4)
- `thermo-nuclear-code-quality-2026-06-11.md` (full-repo snapshot — Waves A–D approve-with-remediation)
- `thermo-nuclear-code-quality-2026-06-08.md` (v3.3 infra/docs audit — Waves A–E approve)
- `thermo-nuclear-code-quality-2026-06-02.md` (reserve-DOI + title-page split close-out)

When generating a new snapshot, suffix the filename with the generation
date and archive it directly — don't park it at the top level where it
would imply currency.

## See Also

- [`archived/`](archived/) — historical snapshots
- [`../_generated/COUNTS.md`](../_generated/COUNTS.md) — live counts + coverage (canonical source of truth)
- [`../_generated/active_projects.md`](../_generated/active_projects.md) — current `projects/` roster
- [`../guides/fork-an-exemplar.md`](../guides/fork-an-exemplar.md) — fork-readiness entry
- [`../../scripts/lint_docs.py`](../../scripts/lint_docs.py) — the live linter; replaces stale audit reports
- [`../../scripts/check_template_drift.py`](../../scripts/check_template_drift.py) — exemplar drift checker
