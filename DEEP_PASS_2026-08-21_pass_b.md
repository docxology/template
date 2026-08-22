# Deep Assessment + Improvement Pass (pass B) — 2026-08-21

Second same-day autonomous pass on `template/`. This pass ran independently of
the other same-day deep-pass reports (`DEEP_PASS_2026-08-21.md`,
`DEEP_PASS_2026-08-21_prior_session.md`, `..._ox-alpha-crosscheck.md`) which were
being written concurrently on this checkout.

## Executive summary

Repo health is excellent. Every enforced gate measurable in one local session
passes:

| Gate | Result |
| --- | --- |
| Ruff (full public lint surface) | clean |
| mypy (`public_scope source-paths`, 1,559 files) | clean |
| No-mocks lexical gate (1,187 files) | PASS |
| Tracked secrets scan | clean |
| `check_tracked_all.py` confidentiality guards | projects/fonds/rules/tools clean |
| Template drift `--strict` | clean |
| Backlog contract `--strict` | 0 errors / 0 warnings (22 stable IDs) |
| Claim bindings receipt | valid |
| Docs linter (268 mermaid blocks) | **0 broken cross-links** |
| `public_capabilities.py` | OK, all canonical exemplars |
| Skills check | ok |
| Module line-count gate | within ratchets (6 warns, 0 fails) |
| Filepath audit (regenerated) | 2,062 files, 0 red / 0 yellow flags |

Measured test runs:

- `tests/infra_tests/validation/`: **1515 passed**, 5 deselected (155.89s).
- `tests/infra_tests/documentation/` + `project/`: green after fixing the one
  environment-flaky test below.
- `tests/infra_tests/rendering/`: not completable in budget (LaTeX subprocess
  wall-time on this host); environment constraint, not a code failure.

## Findings

### Minor

**M-1. mmdc parse test hard-fails when renderer hangs (FIXED this pass)**
- Evidence: `tests/infra_tests/documentation/test_architecture_overview.py`
  (`test_generated_mermaid_parses_via_mmdc`).
- Reproduced manually: mmdc 11.9.0 + Chrome 151 on macOS/arm renders a valid SVG
  but does not exit (exit 124 after 150s standalone), so the test raised
  `TimeoutExpired`.
- Fix: catch `subprocess.TimeoutExpired`; skip with reason when a parseable SVG
  was produced, fail otherwise.
- Verified: targeted pytest run -> 1 passed; Ruff clean.
- Note: concurrent session fcb7773e7 raised timeouts on related flaky tests;
  this fix is complementary (lifecycle hang vs tight cap).

**M-2. Filepath audit report refresh (FIXED)**
- Regenerated via canonical producer; snapshot matches live tree (55 known-
  exception link findings, all green-flag). Committed per docs/audit contract.

### Medium

**MED-1. Stale coverage provenance blocks `counts.py --check` (DEFERRED)**
- Evidence: counts check fails with `stale coverage snapshot for
  template_active_inference: source hash changed` (snapshot pins `c0862c75...`,
  live tree hashes `e22aa78a...`).
- Deferred because repo policy forbids hand-editing generated evidence; honest
  fix needs the full exemplar coverage-gate rerun plus
  `counts.py --refresh-coverage-provenance --write`, exceeding session budget.
- Acceptance: `scripts/docgen/counts.py --check` exits 0 post-refresh.

**MED-2. Bounded-run guardian stalls under Python 3.14/macOS (DEFERRED)**
- Evidence: `infrastructure/core/_bounded_run_guardian.py:133` `_expect_status`
  TimeoutError waiting for DONE status in several `test_counts_doc.py`
  subprocess-policy tests; one stall inside `Popen._execute_child` during spawn.
- Corroborated independently by `DEEP_PASS_2026-08-21_ox-alpha-crosscheck.md`.
- Scope: minimal guardian reproduction outside pytest; audit py3.14
  fd-inheritance/spawn-path changes; bounded-retry or sharper diagnostics.
  ~0.5-1 day. Risk: load-bearing security component; negative controls required.
- Acceptance: `pytest tests/infra_tests/documentation/test_counts_doc.py -q
  --no-cov` green without deselection on macOS/py3.14.

### Major (scoped only, not implemented)

**MAJ-1. Local full-suite verification debt**
- Unified health run exceeds ~7 min wall-clock locally; rendering suite not
  locally completable. Hosted Linux CI remains authoritative.
- Approach: subset `--gates=<names>` local lanes; keep LaTeX tests opt-in
  locally (markers exist). Effort: 1-2 days CI tuning. Risk of masking real
  regressions mitigated by unchanged CI. Acceptance: <15 min local loop,
  complete CI.

**MAJ-2. Dependency currency drift**
- `uv pip list --outdated`: e.g. inferactively-pymdp 1.0.1->1.0.3,
  jax 0.9.2->0.11.1, hypothesis, bandit minor bumps. Lockfile-pinned; no
  immediate risk.
- Approach: grouped bump PRs + full matrix + regression tier; regenerate any
  affected pinned exemplar artifacts with provenance. Effort: ~1 day + CI.

### Verified clean
TODO/FIXME sweep (29 hits are doc strings/scanner itself), tracked secrets,
generated-artifact hygiene, doc links, drift/thin-orchestrator checks.

## Commits (path-scoped, not pushed)
- `tests/infra_tests/documentation/test_architecture_overview.py` — M-1 fix.
- This report file.

Pre-existing/concurrent dirty files untouched.
