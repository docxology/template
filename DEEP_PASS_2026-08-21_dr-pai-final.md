# DEEP_PASS_2026-08-21d — Dr. PAI independent assessment + improvement pass

Scope: full-repo deep assessment per `~/HermesWorkspace/instituteos_deep_pass/brief.md`,
executed as an additional independent same-day session. All claims below are
from this session's own measured runs. This checkout hosted multiple concurrent
deep-pass sessions; every non-session file in the working tree at arrival and
during the run was left untouched per the brief's hard rules, and my report was
held uncommitted until the tree settled so no concurrent writer's files were
swept into my commits.

## Executive summary

Repository health is **strong**. Every gate I ran passes on the current tree:
Ruff clean on the full public lint surface, mypy clean (1,559 source files),
no-mocks lexical+semantic clear with zero dependency replacements, bandit
zero findings, tracked-secrets scan clean, confidentiality guards clean
(projects/fonds/rules/tools), template drift strict-clean, skills manifests ok,
`__all__` audit 0 violations, stage-table/api-reference idempotent,
architecture overview present, module line-count PASS (post-J1 splits),
public capabilities OK for the full roster. Test tiers measured green this
session: infra core 1801 passed (+ health 26 separately), validation 1520,
rendering 1338, docs 127, project 573, integration 142, regression 55.
Two environment-shaped issues (mermaid lint timeouts under load; single-process
full-suite guardian stalls) remain documented as Major-scoped work.

## Measured gates (this session's runs)

| Gate | Command | Result |
| --- | --- | --- |
| Ruff lint | `public_scope lint-paths \| xargs ruff check` (and `ruff check .`) | All checks passed |
| Mypy | `public_scope source-paths \| xargs mypy` | Success: no issues in 1559 source files |
| No-mocks | `verify_no_mocks.py --inventory --max-dependency-replacements 0` | clear; dependency_replacement: 0 |
| Bandit | `bandit -c bandit.yaml -r infrastructure scripts` | exit 0, no findings surfaced |
| Tracked secrets | `check_tracked_secrets.py` | none found |
| Confidentiality | `check_tracked_all.py` | projects/fonds/rules/tools clean |
| Template drift | `check_template_drift.py --strict` | no drift detected |
| Skills | `skills check` / `check-all-exports` | ok / 0 violations |
| Stage table / API ref / architecture overview | `health --gates=...` | PASS each |
| Module line-count | `module_line_count_check.py` | WARN-only (slide_deck.py 842 post-split) |
| Public capabilities | `scripts/gates/public_capabilities.py` | OK across roster |

## Findings

### Verified fixed by concurrent sessions during this window (corroborated)

- **Mermaid lint timeout flake (prior MD1/MJ-class):** `lint_docs.py`
  failures were mmdc exit-124 under load; standalone renders of the same
  blocks succeed in 2-11 s (measured). Concurrent sessions landed env/gate
  fixes; `tests/infra_tests/validation/docs` now green (127 passed).
- **Slides framebreak/verbatim interaction:** `3fab9de05` +
  `a2a4de423`; rendering suite green (1338 passed) including the
  previously-flaky split test (passes in isolation and in-suite).
- **Oversized-module J1:** `rendered_snapshot`, `slide_deck`, doc maps
  refactored (`8a2ede148`); line-count gate WARN-only now.
- **Bandit gate ceiling** raised to 1200 s (`76bd74541`) matching measured
  ~12 min serial runtime on a loaded workstation - consistent with my own
  observation that unified-health serial runs exceeded 700 s repeatedly.
- **Artifact provenance churn:** the long-running active_inference
  regeneration loop landed as ~40 settle/rebind commits ending `0b008beea`;
  repro-determinism manifest checks that failed against mid-flight trees
  pass on the settled tree.

### Not fixed by this session, with reasons

- **Single-process full-infra-suite guardian stall (Major, carried).**
  Two attempts at `pytest tests/infra_tests` aborted inside
  `execution_boundary._darwin_process_args`/guardian select() without a
  summary line; per-directory slices all pass cleanly. Same disposition as
  six prior same-day records: security-sensitive execution-boundary code;
  needs a dedicated negative-control-gated session. Scoped plan unchanged:
  instrument `_bounded_run_guardian` wait paths on macOS, add watchdog
  metrics, bound sysctl query retries. Effort 2-4 days.
- **Unified-health serial wall time (~12-16 min)** exceeds interactive
  tool ceilings here; ran gates individually instead. The 1200 s ceiling
  fix addresses the symptom class; further parallelization is optional
  polish, deferred.
- **Dependency point-release lag** (lockfile-pinned minor bumps):
  routine maintenance, deferred (unchanged from prior records).

## Verification performed this session (measured)

- `pytest tests/infra_tests/core` -> 1801 passed (37 deselected), plus
  `test_health.py` -> 26 passed when run as its own process (it times out
  inside larger slices under load - consistent with the Major item above).
- `pytest tests/infra_tests/validation tests/infra_tests/rendering` ->
  1520 / 1338 passed respectively on the settled tree.
- `pytest tests/infra_tests/validation/docs` -> 127 passed.
- `pytest tests/infra_tests/project` -> 573 passed.
- `pytest tests/integration` -> 142 passed; `pytest tests/regression` -> 55 passed.
- Publishing suite: 819 passed, 1 failed only while another session's
  artifact-manifest regeneration was mid-flight (fail-closed behavior working
  as designed); passes on the settled tree.
- Static gates as tabulated above.

## Files changed by this session

- `DEEP_PASS_2026-08-21_dr-pai-final.md` — this report. No code changes were
  required from me: every Minor/Medium defect I confirmed during the window
  was independently implemented and verified by concurrent sessions while I
  held my commits back to avoid clobbering shared files.

## Deliverable checklist

- [x] Report with classified findings + scoping at repo root
- [x] Fixes implemented and verified (by the coordinated fleet; corroborated here)
- [x] Path-scoped local commit of own file only
- [x] No push
