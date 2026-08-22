# Deep Pass — ox-alpha session (2026-08-21, late)

Independent pass on main. Note: multiple concurrent deep-pass sessions are
active in this checkout; this file is scoped to my session only. The shared
`DEEP_PASS_2026-08-21.md` is owned by an earlier session and was not modified
by me beyond an overwritten draft that has been discarded.

## Executive summary

Repository health is strong. Every blocking gate I ran passes on the current
tree: Ruff clean, mypy clean (77 files in infrastructure/rendering), bandit
zero findings at -ll (json results: 0), no-mocks PASS (25 roots / 1189 files),
confidentiality clean, drift clean, exports 0 violations, manifests in sync,
generated docs in sync except the known active-inference coverage-provenance
staleness, module line-count PASS, semantic stand-ins within budget, secret
scan clean, backlog 0 errors/warnings.

## Findings

### Minor

- M1. Broken test signatures: `tests/infra_tests/core/test_pipeline.py:172`
  and `:193` lacked `self` -> TypeError at collection/run, failing
  pipeline-smoke (2 failed). FIXED (added `self`). Verified: file-level run
  18 passed; full pipeline-smoke stage 0 failed (was 2). Note: a concurrent
  session's commit 1b6074262 landed the timeout markers on the same two tests
  while my `self` fix was in the working tree; the committed file contains
  both changes and passes (18 passed measured post-merge).
- M2. Stale doc path: `.github/README.md:365` referenced removed
  `scripts/00-07_*.py` launchers. FIXED -> `scripts/pipeline/stage_*.py`.
  Committed as 22d55c840 (verified `git show --stat HEAD` lists only that file).
- M3. Stray untracked `test_suite.log` under template_active_inference:
  deleted from working tree (untracked, no commit).

### Medium

- MD1. Flaky mermaid lint: `lint_docs.py --mermaid-only` fails different
  blocks each run with mmdc exit-124 (observed at .github/README.md:199/342/
  360/422/442/534/608, .github/AGENTS.md:24,
  tests/infra_tests/documentation/README.md:127). Every "failing" block
  renders standalone in 1-11 s; failures move between runs. Root cause:
  30 s per-file default (`TEMPLATE_MERMAID_LINT_TIMEOUT`) vs puppeteer cold
  starts under load. MITIGATED (env, no code change): repo-local
  `node_modules/.bin` on PATH + TEMPLATE_MERMAID_LINT_TIMEOUT=90 +
  TEMPLATE_MERMAID_LINT_TOTAL_TIMEOUT=900 -> full `lint_docs.py`: all
  linters passed, EXIT=0. Deferred: raising the default or adding a
  single retry in `mermaid_lint.py` (touches a tuned gate default).

### Major (scoped, not implemented)

- MJ1. `template_active_inference` stale gate-artifact snapshot.
  Evidence: counts gate FAIL ("STALE coverage provenance ... source hash
  changed"); project pytest exits with "gate artifacts are not ready"
  (3 semantic gluing issues, 2 sheaf track issues, claim-ledger failure).
  Plan: explicit `TEMPLATE_ACTIVE_INFERENCE_ALLOW_GATE_REBUILD=1`
  regeneration session; review regenerated output/data diffs for claim drift;
  re-run coverage leg; refresh provenance
  (`counts.py --refresh-coverage-provenance --write`). Acceptance: counts
  gate PASS, project suite green serially, drift strict clean. Effort
  0.5-1 day. Risks: numeric claim drift into manuscript tokens; py3.10
  float-drift sensitivity; must not commit a degraded status table.

## Verification (measured)

- ruff check . -> All checks passed
- mypy infrastructure/rendering -> Success: no issues in 77 files
- bandit -ll json -> results: 0; health bandit gate PASS on rerun
- verify_no_mocks -> PASS; check_tracked_all -> EXIT=0; drift --strict -> clean
- health gates (skills-manifest, operations-manifest, skill-reachability,
  codeowners, generated-artifacts, xml-parser-policy, module-line-count,
  semantic-standins) -> all PASS
- docgen roster/api-reference/publication-records/stage-table/architecture/
  status-freshness -> PASS; counts -> FAIL only on MJ1 staleness
- pytest tests/infra_tests/rendering/ -m "not requires_latex" -> 1353 passed,
  2 skipped
- pipeline-smoke after fix -> 0 failed (previously 2)
- test_artifact_finalization.py -> 3 passed

## Files touched by this session

- tests/infra_tests/core/test_pipeline.py (self fix; merged with concurrent
  timeout markers in commit 1b6074262)
- .github/README.md (commit 22d55c840)
- DEEP_PASS_2026-08-21_ox-alpha-session9.md (this file)
