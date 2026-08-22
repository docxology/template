# Deep-Pass Session Report — ox-alpha (independent session, 2026-08-21 ~20:00–21:10 PT)

Scope: full-repository deep assessment per `~/HermesWorkspace/instituteos_deep_pass/brief.md`.
Prior sessions' reports: canonical backlog `DEEP_PASS_2026-08-21.md` plus the
suffixed session files. This session independently re-measured gates and found
one new verified defect.

## State on arrival

- Branch `main`, HEAD `0db2afcbb` at session start; concurrent sessions were
  committing continuously during the pass (tip moved past `d1daa855c`).
- Tree dirty with other sessions' in-flight work (rendering helpers + tests,
  `template_active_inference/output/*` provenance JSONs, docs, integration
  tests). All left untouched per hard rules; none committed by this session.

## Gates measured this session (fresh runs)

| Gate | Command | Result |
| --- | --- | --- |
| Ruff lint | `ruff check infrastructure scripts tests` | PASS |
| Confidentiality guards | `check_tracked_all.py` | projects/fonds/rules/tools clean |
| No-mocks lexical | `verify_no_mocks.py` | PASS (1189 files) |
| Exemplar roster | `exemplar_roster.py --check` | OK (24 exemplars in sync) |
| Status evidence | `status_evidence.py --check` | OK |
| API reference | `api_reference.py --check` | up-to-date (25 packages) |
| `__all__` exports | `skills check-all-exports` | 0 violations |
| Generated artifacts | `check_tracked_generated_artifacts.py` | clean |
| Template drift (single exemplar, `--strict`) | `check_template_drift.py --project templates/template_code_project` | no drift detected |
| Filepath audit | `audit_filepaths.py` | 55 link issues, 100% classified green/known-exceptions, 0 red/yellow, exit 0 |
| Counts provenance | `counts.py --check` | STALE for template_active_inference — concurrent session's uncommitted exemplar changes; disposition unchanged (owner) |
| Pipeline smoke lane | `stage_01_test.py --infra-only --infra-scope pipeline-smoke` | exit 1: "No infrastructure coverage percentage found" + "Multiple manuscript configs found" — harness-level, under concurrent load; consistent with prior sessions' M2 scoping |
| Reporting suite | `pytest tests/infra_tests/reporting -q --no-cov` (file-by-file) | 543 passed across all files except one flake below |
| Core CLI / pipeline / rendering / doc-pair / integration run.sh | targeted `pytest` runs | 23 / 18 / 95 (slides+latex helpers) / 8 / 12 passed |
| git_hook_smoke + regression tiers | (prior sessions) | confirmed landed fixes |

## New finding this session — FIXED

**F-new (Minor, test flake) — over-tight wall-clock assert in
`test_stream_timeout_kills_descendants`.**

- Evidence: `tests/infra_tests/reporting/test_suite_runner.py:165`
  `assert elapsed < 2.0` fails reproducibly under machine load (3/3 runs,
  elapsed 3.76–9.39s) while passing 5/5 on an idle machine (1.07–1.77s).
- Root-cause measurement: the functional contract (exit 124, "timed out" in
  stderr, descendant killed before its natural 5s exit, marker absent) holds in
  every run. The elapsed time is dominated by real, intended cleanup work —
  the bounded-run guardian handshake plus repeated `KERN_PROCARGS2`
  process-table scans — measured ~1.0–1.8s idle and ~3.7s loaded via isolated
  probes of `_complete_bounded_run_cleanup`. The 2.0s ceiling pins an absolute
  wall clock on load-sensitive work rather than the actual contract.
- Fix: relaxed to `assert elapsed < 5.0` — still proves the kill lands well
  before the workload's natural 5s exit (the invariant that matters), with a
  comment explaining why. Verified: 35/35 passed in
  `tests/infra_tests/reporting/test_suite_runner.py`, ruff clean.
- Commit: `46b343480` (path-scoped, this file only).

## Dispositions adopted (re-verified, unchanged)

- Counts-provenance staleness, mirror-shape strays: concurrent-session/owner
  state, not fixed by design (hard rules).
- Majors M1–M3 / MJ1–MJ2 in the canonical backlog and cross-check report:
  adopted by reference after re-reading the underlying code paths
  (`_bounded_run_guardian.py`, `counts.py`, line-count gate output).
- Advisory: `audit_filepaths.py` report omits per-issue detail for green flags
  (JSON has empty `green_flags` unless `--verbose`); cosmetic, noted for a
  future report-format pass.

## Deliverable checklist

- [x] Classified findings with evidence (this file + canonical backlog)
- [x] Minor fix implemented and verified by real runs
- [x] Path-scoped local commits of my files only
- [x] No push
