# Project State Report — 2026-08-26

Session: standing check-and-improve dispatch starting ~11:11 PDT on a clean tree (`HEAD = f3388fdc0`). Multiple sibling sessions worked this same backlog row concurrently and heavily interleaved changes; this report states what was verified by THIS session, not inferred from others claims.

## State assessment

- Backlog contract gate green pre-work: `scripts/audit/check_backlog.py --strict` -> 25 backlog files, 24 stable IDs, 0 errors/warnings.
- Quick audit gates green pre-work: `counts.py --check`, `check_tracked_all.py`, tracked-generated-artifact guard, secrets scan.
- Only fully-local open row in TO-DO.md: `DOC-NEGCTRL-HARDEN-MED-1` (~70->33 advisory `gate-negative-control` findings at session start). All other rows container-bound or blocked-external.
- Transient environment flake observed once: `lint_docs.py` mmdc total timeout (exit 124) on `docs/architecture/two-layer-architecture.md:296`; passed on re-run — not a content defect.

## What this session did

1. Captured pre-edit baseline: 58 grep hits / 33 distinct `gate-negative-control` findings via `audit_documentation.py`.
2. Dispatched six scoped leaf agents to add truthful negative-control sentences per flagged doc site under `projects/templates/`, then ran a second repair round to fix mid-sentence splices and duplicated filler left by the first pass.
3. Independently verified cited fixtures exist by reading test sources (not trusting agent self-reports). Caught and removed one misattribution: quickstart cited an optimizer shape-mismatch test as the *coverage gate* negative control — committed as `914b9e9d9` after surviving two concurrent-writer rollbacks of the same fix.
4. Verified citation density against live tests: e.g. `test_validate_outputs_negative_si_invariants_fail`, `test_validate_formal_interop_flags_gnn_source_drift`, `test_review_gate_blocks_missing_roles_rejections_and_bad_review_records`, `test_run_manuscript_audit_flags_missing_chapter` all confirmed present in their cited files.

## Verification (run by this session on the post-repair tree)

- `audit_documentation.py`: gate-negative-control findings **33 -> 0**.
- `check_template_drift.py --strict`: no drift.
- `prerender` validation on edited manuscripts (code_project, autoresearch_project, eda_notebook): no render-blocking pitfalls.
- `lint_docs.py`: cross-links/consistency/doc-pairs clean; mermaid renders clean after re-run.
- Final acceptance re-run after last edit: gate-negative-control count still 0.

## Backlog disposition

- `DOC-NEGCTRL-HARDEN-MED-1`: closed (commit `5a265deb4` closed the row; evidence series includes parts 1-4 plus this session follow-up `914b9e9d9`). An earlier copy of this file on disk claimed a stand-down verification-only lane; that understates reality — this session both drove edits via subagents and committed the final correction.

## Remaining backlog (unchanged by scope)

- `EXECUTABLE-BUNDLE-MAJ-2/-MAJ-1`: sibling sessions landed self-contained payload + fail-closed compose services (`277f75f88`) with offline receipts; full hosted rehearsal remains external-blocked.
- `CLEAN-CHECKOUT-MAJ-1`, `ARCHIVAL-TRACKER-MIN-1`, `SECURITY-OWNERSHIP-1`, `SECURITY-PRIVATE-PROMOTION-1`: blocked-external as before.

## Known race warning

6+ agent sessions dispatched to this same repo simultaneously; commits raced on `projects/templates/template_active_inference/output/*` artifacts (JSON provenance regenerated repeatedly, occasionally wiping staged edits). Anyone auditing these commits should treat interleaved mid-session stage/unstage events as expected noise, not sabotage. Consider serializing future check-and-improve dispatches rather than fanning out across sessions.
