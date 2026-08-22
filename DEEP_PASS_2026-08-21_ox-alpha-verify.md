# Deep Pass — 2026-08-21 (independent verification session)

Executed per `~/HermesWorkspace/instituteos_deep_pass/brief.md`. This checkout
was worked concurrently by several sibling deep-pass sessions; their commits and
dirty working-tree files were left untouched per the hard rules. This report
records only what THIS session itself ran and measured.

## Executive summary

Repository health is high. Every enforced gate this session executed passed.
No security findings. No new code defects found in this session's scope; the
one collection-level failure encountered was a sibling's mid-edit state, not a
committed defect. Findings below are classified per the brief.

## Gates verified (measured results)

| Gate | Command | Result |
| --- | --- | --- |
| Ruff | `uv run ruff check $(public_scope lint-paths)` | All checks passed |
| mypy | `uv run mypy $(public_scope source-paths)` | no issues in 1559 files |
| No-mocks lexical | `scripts/audit/verify_no_mocks.py` | PASS, 1189 files / 25 roots |
| No-mocks semantic inventory (ceiling 0) | `--inventory --max-dependency-replacements 0` | clear on quiet tree: dep_replacement 0, total 406 (see F1) |
| Bandit | `uv run bandit -c bandit.yaml -r infrastructure scripts` | 0 issues at all confidence levels |
| Tracked-resource guard | `scripts/audit/check_tracked_all.py` | projects/fonds/rules/tools all clean |
| Tracked secrets scan | `check_tracked_secrets.py` + direct `tracked_secret_findings()` call (25s) | [] |
| Mirror-symlink guard | `check_mirror_symlinks.py` | 3 unmanaged local entries reported (see F4) |
| Template drift | `check_template_drift.py --strict` | no drift |
| Skills contracts | `infrastructure.skills check`, `check-contracts`, `operations-check`, `check-all-exports` | all OK, 0 violations |
| Backlog / claim bindings / public template contract | `check_backlog.py`, `check_claim_bindings.py`, `check_public_template_contract.py` | pass (24 exemplars) |
| Docs lint | `lint_docs.py --json` | cross-links 0 broken, consistency 0, doc-pairs 0; 5 mmdc exit-124 timeouts under load (see F2) |
| Generated facts | `counts.py --check`, `exemplar_roster --check`, `api_reference --check`, `status_evidence --check`, `publication_records --check` | all OK at end of session |
| Public capabilities | `scripts/gates/public_capabilities.py` | OK for full roster |
| Status freshness | `scripts/gates/status_freshness.py` | OK (max age 183 days) |
| Infra tests core | `pytest tests/infra_tests/core/` (timeout=300) | **1827 passed**, 11 deselected (5m25s) |
| Infra pipeline slice | `pytest tests/infra_tests/core/pipeline/` | 219 passed |
| Project tests | `pytest tests/infra_tests/project/` | 573 passed |
| Rendering tests | `pytest tests/infra_tests/rendering/` (two runs) | run A: 1327 passed / 1 fail -> run B: **1328 passed**, 2 skipped (flake, see F3); framebreak slice passes in isolation |
| git_hook_smoke | `pytest tests/infra_tests/git_hook_smoke/` | 14 passed (with timeout=300) |
| Integration | `pytest tests/integration/` | 142 passed |
| Exemplar gate | `pytest projects/templates/template_code_project/tests` | 246 passed |

## Findings

### Minor

**F1. Apparent nondeterminism in `verify_no_mocks --inventory` under concurrent edits.**
Evidence: one early run reported `dependency_replacement: 2 / advisory_debt`
(FAIL against ceiling 0); repeated runs on the quiet tree report
`dependency_replacement: 0 / Status: clear`. The scanner is deterministic;
the anomalous reading coincided with sibling sessions editing public test
files mid-scan (`tests/infra_tests/project/test_workspace_branches.py`,
`tests/infra_tests/rendering/test_pipeline_summary_branches.py`). Not
reproducible after siblings committed. **Status: NO FIX REQUIRED** — tool is
correct; noted so future readers do not chase it. Suggested hardening for a
future pass: snapshot file mtimes/hashes during the scan and warn when the
tree mutates underneath it.

**F2. Mermaid lint timeouts under load (`lint_docs.py`).**
Evidence: lint JSON showed 5 of 268 blocks failing with `mmdc`
exit 124 (30s per-block cap) while sibling sessions saturated the machine:
`.github/workflows/AGENTS.md:45`, root `AGENTS.md:237/348/593/924`. On an
unloaded rerun the same blocks pass (sibling session also provisioned
chrome-headless-shell). **Status: NO FIX REQUIRED (transient)**. Optional
medium improvement scoped as M1.

**F3. One-shot rendering-suite flake.**
Evidence: run A failed 1 test that passed on `--lf` rerun and in the full run B
(1328 passed). The failing case correlated with the sibling-uncommitted edit to
`infrastructure/rendering/_slides_framebreaks.py` present during run A.
**Status: NOT THIS SESSION'S CHANGE; left uncommitted per rules.**

### Deferred (with reasons)

**F4. Unmanaged local entries under `projects/<lifecycle>/`**
(`projects/active/project`, `projects/working/ap3`, `projects/working/Untitled`)
fail `check_mirror_symlinks.py`. These are private/local content (gitignored,
verified via `git check-ignore -v`) belonging to other workstreams; moving them
to the sidecar is explicitly another actor's decision. **Deferred:** not this
session's files; documented remediation exists in the guard output
(`mv` to sidecar + `link-projects`).

**F5. Full `tests/infra_tests/` single-process suite exceeds practical wall
clock here** (~6.5 min for `core/` alone; rendering ~5 min; several suites
contain 25-55s real subprocess tests). Per-suite slices all pass. Repo-wide
timeout-policy revision risks masking real hangs and is maintainer-owned.
**Deferred as policy change.**

### Medium scoping (not implemented)

**M1. Make `lint_docs.py` mermaid rendering load-tolerant.**
Approach: add bounded retry (e.g. 2 attempts) or scale the per-block mmdc
timeout with detected system load before reporting exit 124; keep failures
actionable by listing retried blocks. Effort: ~0.5 day incl. tests.
Risk: low (advisory lane). Acceptance: 268/268 blocks render under artificial
load (parallel pytest) without false failures; negative control still fails on
a genuinely broken diagram.

### Major scoping

None identified. Architecture, confidentiality guards, secrets hygiene,
generated-facts contract, and test discipline are consistent and enforced.
The known large-surface items (repo-wide suite wall time on Python 3.14,
per-test timeout policy) are scoped above rather than treated as architectural.

## What this session did NOT change

All pre-existing dirty files (arrival set: `infrastructure/rendering/*` edits,
`template_active_inference/output/**`, sibling test files) and all sibling
commits were left untouched. COUNTS.md drifted stale mid-session and was
re-refreshed by a sibling producer run; final state passes `--check`.

## Deliverable checklist

- [x] This report at repo root with classified findings + verification evidence
- [x] Minor findings triaged: none required code changes from this session (all fixed upstream by producers/siblings or transient); deferrals reasoned above
- [x] Path-scoped local commit of only this file; no push
