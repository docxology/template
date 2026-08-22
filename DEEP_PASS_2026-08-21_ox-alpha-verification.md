# Deep-Pass Session Report — ox-alpha (independent verification session, 2026-08-21)

Scope: full-repository deep assessment + improvement pass per
`~/HermesWorkspace/instituteos_deep_pass/brief.md`. This session ran
concurrently with several other deep-pass sessions in the same checkout
(canonical backlog `DEEP_PASS_2026-08-21.md`; sibling reports `_dr-pai.md`,
`_dr-pai-session.md`, `_ox-alpha.md`, and a staged `_ox-alpha-session2.md`).
All measurements below are from this session's own runs.

## Executive summary

Repository health is strong and consistent with the prior session
reports: static gates clean, security posture active, docs generated from
source with drift checks, confidentiality guards green. This session's
independent gate battery surfaced one real formatting regression (two newly
added test files failing `ruff format --check`), verified its resolution,
and measured three gates (bandit, docs-lint mermaid, counts) that exceed the
unified-health 300 s default ceiling on this machine under concurrent load.
No correctness or security defects were found that prior sessions had not
already fixed and committed.

## Measured gates (this session, fresh runs)

| Gate | Command | Result |
| --- | --- | --- |
| Ruff lint | `public_scope lint-paths` -> `ruff check` | All checks passed |
| Ruff format | same paths -> `ruff format --check` | Clean after fix (see F1); 2879 files formatted |
| Mypy | via `infrastructure.core.health` | Success: no issues in 1559 source files |
| Bandit | `bandit -c bandit.yaml -r -ll infrastructure scripts projects/templates -f json` | 0 findings (JSON, ~12-min run; see F3) |
| No-mocks | `verify_no_mocks.py` | PASS, 1188 files, 25 test roots |
| Confidentiality | `check_tracked_all.py` | projects/fonds/rules/tools: clean |
| Tracked secrets | `check_tracked_secrets.py` | No high-confidence credentials |
| Generated artifacts | `check_tracked_generated_artifacts.py` | Clean |
| Template drift | `check_template_drift.py --strict` | No drift |
| Backlog contract | `check_backlog.py` | 0 errors, 0 warnings |
| Docs cross-links | `lint_docs.py --links-only` | 0 broken |
| Docs consistency | `lint_docs.py --consistency-only` | 0 issues |
| Docs mermaid | `lint_docs.py --mermaid-only` | Flaky under load — see F4 |
| Counts | `scripts/docgen/counts.py` | Regenerated cleanly (~47 min under load; see F3) |
| Targeted tests | `pytest tests/infra_tests/project/test_workspace_branches.py tests/infra_tests/rendering/test_pipeline_summary_branches.py -q --no-cov` | 25 passed in 10.20 s |
| Unified health | `python -m infrastructure.core.health --json --quiet` | 3 gate timeouts under load (see F3) |

## Findings

### F1 — Minor — ruff-format failures in two new test files — FIXED (verified in HEAD)

- Evidence: `tests/infra_tests/project/test_workspace_branches.py`,
  `tests/infra_tests/rendering/test_pipeline_summary_branches.py` flagged by
  `ruff format --check` in this session's unified-health run.
- Status: fixed and verified. This session ran `ruff format` on both;
  the concurrent session's commit `1efa2f118` landed already-formatted
  copies, so HEAD and the working tree both pass
  (`ruff format --check` -> clean; the 25 tests in both files pass in 10.20 s).
- Note: the same unified-health run also flagged
  `infrastructure/rendering/_pdf_latex_helpers.py` for reformatting; that was
  pre-existing uncommitted work owned by a concurrent session and was
  subsequently committed by it (`cb1db305b`). Not modified by this session.

### F2 — Medium — unmanaged local entries under `projects/<lifecycle>/` — SCOPED (not actionable here)

- Evidence: `check_mirror_symlinks.py` reports
  `projects/active/project` (real dir), `projects/working/Untitled`
  (regular file), `projects/working/ap3` (real dir).
- Assessment: all three are gitignored private-sidecar content from other
  live sessions (`git ls-files projects/active projects/working` -> 0
  tracked). `check_tracked_all.py` stays green, so the confidentiality
  invariant holds. Moving another session's in-flight work would violate the
  brief's hard rule against touching others' uncommitted work.
- Scoping: after concurrent sessions wind down, run
  `mv projects/<lifecycle>/<name> <private-root>/<lifecycle>/<name>` then
  `uv run python -m infrastructure.orchestration link-projects`. Effort:
  minutes. Risk: low, but only when no session is actively using those trees.
  Acceptance: `check_mirror_symlinks.py` exits clean with the same tracked
  set.

### F3 — Medium — unified-health 300 s gate ceiling too small for bandit/counts on loaded machines — SCOPED

- Evidence: this session's `infrastructure.core.health` run timed out
  bandit, docs-lint, and counts at 300 s each. Measured standalone runtimes
  on this machine (macOS, concurrent deep-pass sessions running):
  bandit JSON scan approx. 12 min; `counts.py` approx. 47 min; full mermaid
  lint exceeded 300 s (268 blocks). CI runners are faster and the docs-lint
  ceiling was already raised to 900 s by commit `e03ddb9e7`.
- Scoping: raise the per-gate ceilings for bandit and counts in
  `infrastructure/core/health.py` (or make ceilings config-scaled), or mark
  those two gates advisory-under-load. Effort: 1–2 h including tests.
  Risks: masking genuine hangs if ceilings are set too generously; keep
  CI-timeout parity checks. Acceptance: unified health passes end-to-end on
  a loaded workstation with no timeout failures, and a deliberately slow
  gate still trips its ceiling in tests.

### F4 — Low — mermaid lint is flaky under machine load — SCOPED (already mitigated upstream)

- Evidence: one `--mermaid-only --quiet` run reported 3 mmdc timeouts
  (`.github/README.md:442,534,608`, exit 124 at 30 s/block); an immediate
  rerun reported 0 failures over 268 blocks. Prior sessions reached the same
  conclusion (commit `8b8deda8c`: "mermaid failures confirmed as load
  flakes").
- Scoping: optional retry-once-on-timeout in the mermaid linter, or a
  per-block timeout scaled to block size. Effort: about 1 h. Risk: low.
  Acceptance: 10 consecutive full mermaid lint runs under heavy load report
  0 false failures.

### F5 — Process — high-concurrency deep-pass sessions share one checkout — noted

- Evidence: 5+ `deep-pass:` commit trains in the reflog today, staged
  sibling report `DEEP_PASS_2026-08-21_ox-alpha-session2.md` (not committed
  by this session — it belongs to another agent), and a dirty tree whose
  modified set changed three times during this session.
- Assessment: path-scoped-commit discipline held (no cross-session
  overwrites observed in this session's files), but the canonical
  `DEEP_PASS_2026-08-21.md` was overwritten and restored repeatedly.
- Recommendation: future fleet dispatches should give each agent its own
  worktree (`git worktree add`) or assign disjoint report filenames up
  front.

## Deliverable checklist

- [x] This report at repo root with classified findings + scoping
- [x] Minor fixes implemented and verified (F1 — resolved in HEAD, 25/25 tests pass)
- [x] Path-scoped local commit of this report file only (other sessions' staged/dirty files untouched)
- [ ] No push (per brief)
