# Repo TO-DO - active backlog

> **Design ethos:** modular, intelligent, functional, logged, tested, and
> documented. Real methods only; never mocks or fakes. Every release ships with
> green tests and accurate docs.

This file tracks **only upcoming, scoped work**. Shipped work and historical
detail live in [`CHANGELOG.md`](CHANGELOG.md); generated counts and project
rosters live in [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md) and
[`docs/_generated/active_projects.md`](docs/_generated/active_projects.md).

---

## Active backlog

### EXEMPLAR-AUDIT-FOLLOWUP-1 — aggregate union-coverage gate leak

- **Source:** EXEMPLAR-AUDIT-2026-07-07 (see `CHANGELOG.md` "2026-07-07").
- **Open finding (not fixed):** the "combined coverage gate" step of
  `uv run python scripts/pipeline/stage_01_test.py --project-only
  --all-projects --public-projects` (75% union-coverage floor) fails with
  `No source for code: '.../pytest-<N>/test_run_project_tests_fail_wh0/iso_project/src/__init__.py'`
  — reproducible from a clean checkout, unrelated to any of that session's
  edits. Root cause (not fully traced): `template_search_project/tests/test_analysis.py::test_run_project_tests_fail_when_pytest_errors`
  spawns a real `pytest` subprocess against a `tmp_path`-scoped isolated
  fixture project to test `run_project_tests()`; that subprocess appears to
  write coverage data into a file the parent's "combined coverage gate"
  later tries to combine, referencing a source path that no longer exists
  once `tmp_path` is torn down. All 18 projects' own per-project gates pass;
  only this aggregate union-coverage step is affected.
- **Acceptance:** trace `infrastructure.core.test_runner`'s combine step and
  confirm whether `COVERAGE_FILE`/`COV_CORE_DATAFILE` env vars are leaking
  into the subprocess, or scope the subprocess's coverage data file
  explicitly. Then re-run the aggregate command and confirm it exits 0.

### REVIEW-2026-07-02 — Multi-lens review remediation backlog

- **Source:** a 9-dimension adversarial review (43 findings confirmed
  against HEAD, 3 refuted). Safe bounded fixes shipped the same session.
- **Open items (R1–R18)** with per-item acceptance lines live in
  [`docs/maintenance/review-remediation-2026-07.md`](docs/maintenance/review-remediation-2026-07.md).
  Highest leverage: **R1** (wire the 15-exemplar / 55-test regression tier
  into CI — currently unenforced), **R2** (scope skills discovery to tracked
  paths, mirroring the drift-gate fix already shipped), **R7** (operations
  catalog / MCP miss single-file CLIs).

### AI-GATE-PERF-2 — Reduce active-inference gate runtime after correctness

- **Problem:** `template_active_inference` gate tests had a heavy explicit
  roadmap/sheaf write path whose *first* invocation in a process took ~250s.
- **Status:** correctness/timeout blocker closed (2026-07-01) — a
  `pytest_sessionstart` pre-warm hook fixed the cascade; two O(N×M) redundant
  file-read bottlenecks fixed. Full non-long-running suite passes under the
  real 120s per-test timeout.
- **Remaining (open):** the `--durations=20` profiling pass itself (to look
  for further redundant artifact refreshes beyond the two fixed) and the
  project-local `MEDIUM-TEST-PERF-1` split (cheap source-only negative
  controls plus one end-to-end refresh characterization) are still open. This
  item closed the *correctness/timeout* blocker, not the full perf-tuning
  scope.

---

## Known divergences from `CHANGELOG.md`

As of 2026-06-27, `pyproject.toml` and the latest GitHub release agree at
**`3.5.1`** / **`v3.5.1`**. `CHANGELOG.md` still carries current work under
`[Unreleased]` rather than a `3.5.x` heading; confirm release-note reconciliation
before claiming changelog parity. The docs-lint links/consistency/doc-pairs gates
were rerun for the contributor-strategy docs pass and reported unrelated active
lane failures; full release-readiness gates were not rerun against the dirty
local tree.

If a new drift appears between [`CHANGELOG.md`](CHANGELOG.md), `TO-DO.md`,
generated facts, or `.github/workflows/ci.yml`, fix forward and record the
current source of truth here instead of rewriting shipped changelog entries.

---

## Conventions

- Backlog IDs are stable. Use them in commit messages when closing related
  work; do not silently reuse retired IDs for new work.
- **ID scheme:** `<AREA>-<SLUG>-<N>`, where `AREA` names the surface — `GH`
  (GitHub workflows/CI), `ARCH` (architecture/test rules), `LOG` (logging), `AI`
  (Active Inference exemplar), `SIA` (SIA exemplar), `DEP` (dependencies), `FMT`
  (rendering formats), `PIPELINE`/`DASHBOARD`/`REPRO`/`PROSE`/`EVIDENCE`
  (shipped-capability follow-ups), `COVERAGE`/`READFILE`/`CI-MATRIX` (named
  gates/patterns), and `TODO` (backlog hygiene itself). `N` is a monotonic
  counter within that area+slug.
- Every active item must include a problem, why it matters, smallest next step,
  acceptance check, and out-of-scope boundary.
- Completion requires evidence from a command, file diff, or generated artifact;
  do not check off items from intention. Before retiring an item, confirm its
  artifact exists on disk (and under test) this session — never from a commit
  message alone.
- Re-baseline measured facts instead of copying old numbers from this file.
- Keep private or rotating project names out of public docs; link to
  [`docs/_generated/active_projects.md`](docs/_generated/active_projects.md)
  for public scope.
- Preserve the no-mocks testing policy, project coverage floors, and generated
  artifact guard when closing backlog items.
