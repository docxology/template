# DEEP_PASS_2026-08-21b — Second-Pass Assessment (same-day follow-up)

Context: an earlier same-day deep pass exists at `DEEP_PASS_2026-08-21.md`
(commit `48efcd3e2`). This file is a separate, independent re-assessment
executed after additional commits landed on `main` (`1efa2f118` and others).
All measurements below were executed live in this checkout on 2026-08-21.

## Executive summary

Repository health remains **strong**. Every enforced gate I ran came back clean:

| Gate | Command | Measured result |
| --- | --- | --- |
| Ruff (full public lint surface) | `public_scope lint-paths` + `ruff check` | All checks passed |
| mypy (1559 source files) | `public_scope source-paths` + `mypy` | Success: no issues |
| No-mocks lexical gate | `scripts/audit/verify_no_mocks.py` | Exit 0 |
| No-mocks semantic inventory | `--inventory --max-dependency-replacements 0` | Status: clear, dependency_replacement: 0 (411 ops classified) |
| Template drift (strict) | `scripts/audit/check_template_drift.py --strict` | no drift detected |
| Docs linter | `scripts/audit/lint_docs.py` | exit 0 (two advisory mmdc 30s per-block timeouts on large `.github/README.md` diagrams; total-timeout guard fired correctly) |
| Skills manifests | `infrastructure.skills check` / `check-all-exports` | ok / 0 violations |
| Lockfile freshness | `uv lock --check` | Resolved 189 packages, in sync |
| Confidentiality guards | `scripts/audit/check_tracked_all.py` | projects/fonds/rules/tools all clean |
| Tracked-secrets scan | `scripts/audit/check_tracked_secrets.py` | no credentials found (exit 0) |
| Generated-artifact guard | `scripts/audit/check_tracked_generated_artifacts.py` | clean |
| Bandit (`bandit.yaml`) | over `infrastructure/`, `scripts/` | zero High/Medium findings |
| Core+benchmark test suites | `pytest tests/infra_tests/core tests/infra_tests/benchmark -q` | **1853 passed, 18 deselected** (~4–5 min), verified twice |
| Autoresearch suite | `pytest tests/infra_tests/autoresearch/test_autoresearch.py -q` | 24 passed x4 runs |

## Fixed (Minor)

**m-fix-1 — Load-flaky pipeline test vs global 10s pytest-timeout**
(`tests/infra_tests/core/pipeline/test_artifact_finalization.py:101`)
- Evidence: full infra lane
  (`stage_01_test.py --infra-only --infra-scope full`) failed once with exactly
  1 failure: `test_validation_seals_aggregate_before_core_and_full_downstream_stages[True]`
  hit the repo-wide 10-second `timeout = 10` default (pyproject.toml:266). The
  test executes a real 10-stage `PipelineExecutor` pipeline: ~5s idle but
  ~25–30s under concurrent load. Sibling suites already carry explicit markers
  (`tests/infra_tests/core/test_test_runner.py:31`,
  `test_multi_project.py:187`) for the same reason; this parametrized test did not.
- Fix: added `@pytest.mark.timeout(120)` above the test (matches sibling policy).
- Verification: `pytest tests/infra_tests/core/pipeline/test_artifact_finalization.py -q --timeout 10`
  -> 3 passed; ruff clean; mypy clean; full core suite rerun green (1853 passed).

## Deferred / advisory

- **Module line-count warnings** (unchanged from first pass):
  `infrastructure/validation/output/pipeline.py` (810),
  `infrastructure/validation/rendered_snapshot.py` (800),
  `projects/templates/template_active_inference/src/orchestration/full_verification.py` (929),
  `infrastructure/rendering/slide_deck.py` (842). All under warn>=800/fail>=950
  with expiring ratchets. Splitting is Major-scoped polish, not debt.
- **Docs-lint mermaid block timeouts**: `.github/README.md:534` and `:608` hit
  mmdc's 30s per-block timeout locally under load (exit still 0; CI's dedicated
  docs-lint job provisions pinned mmdc + chrome-headless-shell). Advisory only.
- **Local-only mirror-shape state** (first pass m2): unchanged local workspace
  condition, not tracked content; belongs to the workspace owner.
- **Dirty tree on arrival/dispatch**: extensive unrelated modifications
  (rendering helpers + their tests, health/matrix modules, provenance JSON,
  CHANGELOG, uv.lock, etc.) belong to another writer and were left untouched,
  per mission hard rules.

## Major (scoped, NOT implemented per mission)

**J1 — Oversized validation/rendering module split** (carried from first pass)
- Scope: `infrastructure/validation/output/pipeline.py` (~810 lines),
  `infrastructure/validation/rendered_snapshot.py` (~800 lines),
  `infrastructure/rendering/slide_deck.py` (~842 lines).
- Approach: extract stage-level helpers into siblings behind stable public APIs;
  keep `__all__` frozen (pinned by `check-all-exports`); migrate tests with the code.
- Effort: 2–3 days including gate reruns (`health`, drift, line-count ratchet).
- Risks: dotted diagnostic-ID stability (`validation/content/diagnostic_codes.py`);
  downstream `jq` filters; byte-determinism contracts (PPTX ZIP normalization,
  EPUB identity) must not shift.
- Acceptance: all gates green; modules <800 lines; no public-API rename;
  regression tier (`tests/regression/`) passes.

## Deliverable checklist

- [x] This report at repo root with classified findings + scoping
- [x] Minor fix implemented and verified (m-fix-1)
- [x] Path-scoped commit of my own files only (this report + the one-line test patch)
- [ ] No push (per mission hard rules)
