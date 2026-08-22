# Deep Assessment + Improvement Pass — ox-alpha session 7 (2026-08-21)

Scope: full-repo deep assessment per `~/HermesWorkspace/instituteos_deep_pass/brief.md`,
executed as an additional independent same-day pass. Prior reports
(`DEEP_PASS_2026-08-21*.md`, seven files) were present at arrival; every claim
below is from this session's own runs, not taken from them.

## Executive summary

Repository health is **strong**, independently re-confirmed by this pass:
static gates clean (Ruff/mypy/no-mocks/bandit/secrets/drift/skills/roster),
security posture active, docs generated-from-source with drift checks,
regression tier fully green. One new Medium documentation defect was found and
fixed (Level-10 guide teaching a nonexistent `custom_projects/` layout). The
two red items (`counts.py --check` staleness, mirror-shape strays) are
concurrent-session working-tree state, matching prior passes' disposition.

## Measured gate state (this session's runs)

| Gate | Command | Result |
| --- | --- | --- |
| Ruff lint | `public_scope lint-paths \| xargs ruff check` | All checks passed |
| Mypy | `public_scope source-paths \| xargs mypy` | Success: no issues in 1559 source files |
| No-mocks inventory ceiling 0 | `verify_no_mocks.py --inventory --max-dependency-replacements 0` | clear; dependency_replacement: 0, env isolation 406 |
| Bandit | `bandit -c bandit.yaml -r infrastructure scripts` | 0 High / 0 Medium / 0 Low |
| Tracked secrets | `check_tracked_secrets.py` | none found |
| Confidentiality guards | `check_tracked_all.py` | projects/fonds/rules/tools clean |
| Generated artifacts | `check_tracked_generated_artifacts.py` | clean |
| Template drift | `check_template_drift.py --strict` | no drift detected |
| Skills | `skills check` / `check-all-exports` / `check-contracts` / `operations-check` | ok / 0 violations / ok / ok |
| Backlog contract | `check_backlog.py --strict` | 22 IDs, 0 errors/warnings |
| Public template contract | `check_public_template_contract.py --strict` | pass, 24 exemplars |
| Exemplar roster / API ref / status evidence / publication records | docgen checks | all in sync |
| Claim bindings | `check_claim_bindings.py` | bound=15, errors=[] |
| STATUS freshness | `status_freshness.py` | OK (max age 183 days) |
| Module line-count gate | `module_line_count_check.py` | WARN-only (pipeline.py 810, rendered_snapshot.py 800, full_verification.py 929) — matches prior F3 ratchet disposition |
| Public capabilities | `scripts/gates/public_capabilities.py` | OK for roster |
| Export smoke | `exemplar_export_smoke.py` | PASS for 24 exemplars |
| Methods plan (source mode) | `methods_plan_check.py --all-public --artifact-mode source` | OK, 24 projects |
| Security scan | `scripts/gates/security_scan.py` | SUCCESS, no blocking issues (safety not installed — optional) |
| Prerender validation | code_project manuscript prerender | no render-blocking pitfalls |
| Markdown validation | code_project + active_inference manuscripts | no issues |
| Regression tier | `pytest tests/regression -q --no-cov` | **55 passed** in 80s |
| Infra core tier | `pytest tests/infra_tests/core -q --no-cov` | **1826 passed, 1 failed** (flake, see F2), 11 deselected in 314s |
| Docs lint | `lint_docs.py --json` (~10 min) | cross-links 0 broken, consistency 0, doc-pairs 0; 8 mermaid blocks exit-124 via local mmdc 30s/block timeout (environment, matches prior passes) |
| Counts provenance | `counts.py --check` | STALE for template_active_inference — concurrent session's uncommitted output edits; disposition unchanged |

## Findings

### Fixed this pass

- **F1 (Medium, docs) — Level-10 guide teaches an architecture that does not
  exist here.** Evidence: `docs/guides/extending-and-automation.md:47-101`
  instructed `mkdir custom_projects/...`, referenced nonexistent
  `scripts/train_models.py` / `evaluate_models.py` /
  `generate_model_cards.py` and `templates/ml_template.tex`, and imported via
  `custom_projects.machine_learning.*`. In this repo new workspaces are clean
  copies of canonical exemplars into the private sidecar (`copy_exemplar.py`),
  synced into managed symlinks under `projects/<lifecycle>/` and guarded by
  `check_mirror_symlinks.py`; hand-built real dirs under `projects/` are a
  documented anti-pattern. Also fixed the sentence typo at line 7
  ("Template. for" → "Template, for").
  **Fix:** rewrote the "Extending the Template" section around
  `scripts/audit/copy_exemplar.py` (`--source/--dest/--new-name/--dry-run`,
  flags verified against `infrastructure/project/copy_exemplar.py:166-178`
  and exercised live with `--dry-run`: "Would copy 91 files") plus
  `link-projects --dry-run` (help verified) and qualified-lifecycle rendering;
  rewrote the build-script example to use real pipeline stage entry points
  (`stage_02_analysis/03_render/04_validate --project working/<name>`) and the
  one-project-per-pytest-process coverage rule.
  **Verified:** every command shown now resolves to a real entry point or
  module; dry-run of copy_exemplar executed successfully.

### Not fixed, with reasons

- **F2 (Minor, known flake) — `test_health.py::test_json_output_is_parseable`
  failed once** with `assert payload["repo_commit"] -> None`. Root cause
  already diagnosed by a prior pass (F5 in `DEEP_PASS_2026-08-21_prior_session.md`):
  health.py nulls repo_commit when the commit changes during the ~14 s run
  (infrastructure/core/health.py:573); concurrent deep-pass commits landed
  mid-run. Correct fail-closed behavior; reran the file's class slice → 23
  passed alongside test_cli.py. **Deferred as design-intended** (same
  reasoning as prior record).
- **F3 (Medium, external) — `counts.py --check` stale provenance +
  mirror-shape strays.** Working tree carries another live session's
  uncommitted `template_active_inference/output/*` regeneration and ~20 dirty
  files (CHANGELOG.md, infrastructure/core/*, uv.lock appeared mid-session).
  Per hard rules these are not mine to touch or commit; owner must land the
  regeneration then refresh provenance. Disposition unchanged from six prior
  records.
- **F4 (Advisory) — dependency point-release lag** (bandit, coverage,
  cyclonedx minor bumps; lockfile-pinned). Routine maintenance, deferred.

### Major (scoped only — carried from prior backlog, still accurate)

- **M1 Coverage-provenance automation coupling** (counts check should name the
  exact refresh command). 1–2 days. Acceptance: self-explanatory failure
  naming the rerun command.
- **M2 Test-suite runtime architecture on py3.14/macOS** (full single-process
  infra suite hit guardian/sysmon timeouts twice this pass too, before summary
  line — third-party corroboration of M2/MED-2). 2–4 days, security-sensitive
  execution-boundary code, negative controls required.
- **M3 Oversized-module decompositions** (rendered_snapshot.py 800,
  full_verification.py 929, pipeline.py 810 at WARN). 2–3 days each.

## Environment note

Two full-suite attempts aborted inside coverage/guardian internals (not
assertion failures) before printing a summary; the `tests/infra_tests/core`
slice completed cleanly and is reported above. Regression tier green. This is
the same host-specific pattern prior passes recorded under M2.

## Files changed by this pass

- `docs/guides/extending-and-automation.md` — F1 fix.
- `DEEP_PASS_2026-08-21_ox-alpha-session8.md` — this report (renamed after a
  filename collision with a parallel session's session-7 report; that report is
  restored verbatim at its original path).

All other dirty files belong to concurrent sessions and are intentionally not
committed. No push (per hard rules).

## Deliverable checklist

- [x] Report with classified findings + scoping at repo root
- [x] New medium finding implemented and verified (F1)
- [x] Path-scoped local commits of own files only
- [x] No push
