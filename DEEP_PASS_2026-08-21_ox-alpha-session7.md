# Deep Assessment + Improvement Pass — 2026-08-21 (ox-alpha session 7)

Independent deep pass executed per `~/HermesWorkspace/instituteos_deep_pass/brief.md`.
This repository was already carrying same-day deep-pass reports from parallel
sessions; this report records **this session's own measurements** and does not
duplicate or overwrite any prior report. All pre-existing dirty working-tree
files were left untouched.

## Executive summary

Repository health is **strong**. Every static gate measured in this pass came
back clean; the two failing surfaces (unified-health docs-lint/counts
constituents) were traced to environment/timing causes, not code defects —
with one real linter-scope defect found and fixed by this session (F1 below).

### Gates measured green this session

| Gate | Command | Measured result |
| --- | --- | --- |
| Ruff lint | `uv run ruff check .` | All checks passed |
| Mypy | `public_scope source-paths` → mypy | Success: no issues in 1559 source files |
| Bandit | `bandit -c bandit.yaml -r -ll infrastructure/ scripts/` | exit 0, no issues |
| Tracked secrets | `scripts/audit/check_tracked_secrets.py` | No high-confidence credentials |
| Confidentiality guards | `scripts/audit/check_tracked_all.py` | projects/fonds/rules/tools all clean |
| Generated artifacts | `check_tracked_generated_artifacts.py` | clean |
| Skills exports | `infrastructure.skills check` / `check-all-exports` | ok / 0 violations |
| Exemplar roster | `docgen/exemplar_roster.py --check` | OK (24 exemplars, doc+manifest in sync) |
| API reference | `docgen/api_reference.py --check` | up-to-date (25 packages) |
| Template drift | `check_template_drift.py --strict` | no drift detected |
| Module line count | `scripts/gates/module_line_count_check.py` | pass (3 WARN-only ratchets) |
| No-mocks inventory | `verify_no_mocks.py --inventory --max-dep-repl 0` | dependency_replacement: 0, Status: clear |
| Regression tier | `uv run pytest tests/regression/ -q` | 55 passed in 66s |
| Benchmarks | `pytest tests/infra_tests/benchmark -q` | 26 passed, 7 deselected in 15s |
| Runtime compat suite | `pytest tests/infra_tests/core/runtime/` | 7 passed in 22s |
| Docs cross-links | `lint_docs.py` | 0 broken links across 268 mermaid blocks + full tree |

### Test-suite status under local load

The full `tests/infra_tests/` suite could not complete in one process on this
loaded macOS/arm64 machine: pytest-timeout aborted twice at ~8 minutes, both
traces ending inside subprocess waits (`benchmark/test_analysis_pipeline_bench.py`
via the execution-boundary guardian cleanup, and a `python_compatibility` scan
read). Targeted re-runs of every implicated area passed cleanly: benchmarks 26/26,
core/runtime 7/7, regression 55/55. This corroborates prior sessions' guardian-stall
finding and is scoped as M2 (prior report); not re-scoped here.

## Findings

### Minor/Medium

- **F1 (Minor, FIXED) — consistency linter scans its own dated audit reports.**
  Evidence: `infrastructure/validation/docs/consistency/_shared.py:129-142`
  (`iter_long_lived_docs`) globs every root-level `*.md`, so dated
  `DEEP_PASS_YYYY-MM-DD*.md` assessment reports were scanned as long-lived docs;
  their point-in-time project references tripped the ghost-project gate
  (`lint_docs.py` reported `[ghost-project]` failures against root reports).
  Fix: root-level Markdown matching `^DEEP_PASS_\d{4}-\d{2}-\d{2}` is now
  excluded from the long-lived-doc surface (same rationale as the existing
  `docs/audit/` exclusion), with two new tests
  (`tests/infra_tests/validation/docs/consistency/test_ghost_paths.py`:
  dated report skipped, undated root doc still scanned).
  Verified: focused suite 62 passed; `lint_docs.py --consistency-only` →
  "0 issues"; ruff/mypy/drift/api-reference all still green.
- **F2 (Environment, NOT A CODE DEFECT) — mermaid lint timeouts are local-browser
  provisioning flake.** Repeated `lint_docs.py` runs failed with rotating
  per-block `mmdc timed out after 30s` (exit 124) on *different* files each run,
  while direct probes of the exact same blocks via
  `validate_blocks(find_mermaid_blocks([...]))` rendered 18/18 with zero failures
  in 7.1s, and single-file probes also passed. The resolver
  (`infrastructure/rendering/chrome.py`) correctly picks the puppeteer-cache
  headless shell; the intermittent stalls match the documented GUI-Chrome/
  batch-render hang mode in `docs/validation AGENTS.md`. No code change made;
  reruns pass. Deferred hardening idea folded into M-A below.
- **F3 (Known, pre-existing) — `counts.py --check` stale coverage provenance for
  template_active_inference.** Caused by concurrent-session edits to that
  exemplar's sources during this pass; provenance refresh belongs to whichever
  session lands those sources. Not mine to fix.
- **F4 (Hygiene) — ruff format would reformat one dirty file**
  (`infrastructure/rendering/_pdf_latex_helpers.py`), which belongs to a
  concurrent session; untouched per mission rules.

### Major (scoped only)

- **M-A — Mermaid lint timeout-budget resilience.** Per-file budget is 30s
  (`TEMPLATE_MERMAID_LINT_TIMEOUT`) with a 300s total ceiling; under load a
  single slow Chrome launch consumes the whole file budget and the total ceiling
  aborts mid-tree, so the gate's outcome depends on machine load rather than doc
  content. Approach: (a) retry once with a fresh user-data-dir before declaring a
  per-file timeout failure (the current code kills the process group but reuses
  the profile); (b) make the total ceiling scale with block count
  (e.g. `max(300, blocks × per_file)`); (c) emit a distinct diagnostic when the
  resolved browser is system GUI Chrome vs headless shell. Effort: 1 day.
  Risks: masking genuine render hangs — keep the fail-closed no-output check
  intact. Acceptance: lint_docs passes deterministically on a loaded machine
  across 5 consecutive runs; injected true syntax error still fails.
- **M-B — Full-infra-suite wall-time architecture on Python 3.14** (corroborated,
  previously scoped as M2 in `DEEP_PASS_2026-08-21_ox-alpha.md`; unchanged).
- **M-C — Oversized-module decompositions** (`rendered_snapshot.py` 800 lines,
  `full_verification.py` 929; expiring ratchets) — scoped in prior reports;
  unchanged.

## Files changed by this session

- `infrastructure/validation/docs/consistency/_shared.py` — F1 fix (dated-report exclusion)
- `tests/infra_tests/validation/docs/consistency/test_ghost_paths.py` — 2 new tests for F1
- `DEEP_PASS_2026-08-21_ox-alpha-session7.md` — this report

All other modified/untracked files belong to concurrent sessions and were not committed.
