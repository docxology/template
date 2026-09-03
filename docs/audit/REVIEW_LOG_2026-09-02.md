# Review log — 2026-09-02 infrastructure deep pass

Single-lane session (no sibling fleet lanes). Preflight: branch `main`, working
tree clean before edits, no pushes performed. Scope requested by the owner:
deep review and improvement of core infrastructure methods and documentation
across the public template surface.

## Method

Three parallel read-only scout passes (infrastructure methods/core/validation/
provenance; all 24 `projects/templates/template_*` exemplars; entry docs +
docs tree vs. live code), followed by author verification of every finding
against the live tree before any edit. Findings that did not survive
verification were discarded (see false-positive note).

## Ground truth at session start

- `check_template_drift.py --strict`, `check_backlog.py --strict` (33 IDs),
  `check_claim_bindings.py`, `check_public_template_contract.py --strict`
  (24 exemplars, 0 findings), `check_tracked_all.py`,
  `check_tracked_generated_artifacts.py`, `check_tracked_secrets.py`,
  `exemplar_roster.py --check` (24), `api_reference.py --check` (25 packages),
  `stage_table.py` (0 drift): all green.
- `infrastructure.core.health`: exit 1 — its **only** failing gate was
  `counts` (stale coverage provenance), pre-existing on `main`.
- `counts.py --check`: FAIL — **all 24** exemplar source hashes stale against
  `docs/_generated/coverage_snapshot.json` (systematic inventory-state drift
  from the 2026-08-31 provenance refresh, which ran in a checkout carrying
  untracked per-exemplar trees; this clean checkout hashes differently).
  Remediation launched this session: full `counts.py --verify-coverage --write`
  re-measurement (all 24 exemplars, unimpeded), then
  `counts.py --refresh-coverage-provenance --write`. Status recorded below.

## Code fixes (TDD: failing tests first, same change)

1. `infrastructure/methods` — fail-per-project aggregate audit
   (`METHODS.PLAN_BUILD_FAILED`, `plan: null` in `MethodsProjectAudit`),
   plan-less-aware Markdown roster render. Tests:
   `test_audit_methods_projects_continues_past_unbuildable_projects`,
   `test_cli_all_public_markdown_survives_unbuildable_projects`.
2. `infrastructure/core/config/loader.py` — `published`/`other` lifecycle
   parents recognized (docstring was already promising them). Tests:
   `TestFindConfigFile::test_infer_project_name_covers_published_and_other_parents`,
   `test_find_config_file_under_published_lifecycle_parent`.
3. `infrastructure/core/pipeline/dag.py` — shared `_definition_from_entry()`,
   `ValueError` with source context for missing stage names, `from_dict()`
   validated identically to `from_yaml()`. Four new parse-failure tests.
4. `infrastructure/core/health.py` — `OSError` guard in `_repository_state()`.
   Test uses a real environmental fault (PATH without a git binary), no mocks.
5. `infrastructure/provenance/validation.py` — self-loop no longer
   double-reported as `PROV_CYCLE_DETECTED`; strengthened
   `test_self_loop_detected`.
6. `infrastructure/project/drift/checks_exemplar.py` — `.agents/` skill
   catalog added to `must_exist` (documented canonical surface,
   `projects/templates/AGENTS.md` lines 19–21). Scaffold + two positive
   controls added; all 24 live exemplars pass.

## Documentation fixes

- README.md:451 and `docs/repurposing-architectures.md`: stale "16-stage"
  claims corrected to 17 (matches `pipeline.yaml` and README's own generated
  stage table); the repurposing row's scope corrected to "env setup through
  archival publication".
- `scripts/pipeline/SKILL.md`: stages 00–13 (stage_13_docxplus.py exists) and
  trigger regex `stage_1[0-3]`; `docs/_generated/skills_index.md` and
  `.cursor/skill_manifest.json` regenerated (`infrastructure.skills check` +
  `check-contracts` green after regeneration).
- `infrastructure/project/public_template_contract.py` docstring now states
  its minimal scope and cross-references the drift-gate file contract.

## Coverage-measurement regression found and fixed (pre-existing on main)

The launched `counts.py --verify-coverage --write` run failed for
`template_active_inference`: "coverage support destination already exists:
projects/templates/template_active_inference/manuscript/SYNTAX.md". Root
cause traced to the 2026-08-31 commits `437589bae` + `50b293dd4`: the
support-closure spec for SYNTAX.md is redundant (the disposable workspace
already copies the full project tree, which contains the file; the file is
already bound to coverage provenance through the project-tree source hash),
and its repointed destination lands inside the pre-copied project tree, so
the fail-closed copy check always aborts. The closure-equality test's
expected-target list also carried a `docs/guides/manuscript-semantics.md`
duplicate that the live outward-link scan does not produce. Fix: remove the
spec, correct the expected list to the live scan, retire the dead
`_repo_root_anchor` shim. Verified live: all three
`test_counts_doc.py::test_active_coverage_*` tests pass (8.8s / 15.3s);
ruff + mypy clean. The full re-measurement then proceeded past Active.

## Coverage-provenance remediation outcome (completed this session)

After the support-spec fix, the full unimpeded re-measurement completed
(`counts.py --verify-coverage --write`, ~54 min wall on this volume,
exit 0): 22/24 exemplars reproduced their recorded percentages exactly;
2 drifted and were re-recorded through the fail-closed complete-snapshot
rewrite — `template_active_inference` 91.89 % → 91.87 % (the
`formal_interop` derivation fix from commit `025640371`) and
`template_textbook` 96.08 % → 96.36 % (source changed since the
2026-08-16 snapshot date). `counts.py --refresh-coverage-provenance
--write` then re-recorded all 24 source hashes against this clean
checkout and rewrote `docs/_generated/COUNTS.md`. Final state:
`counts.py --check` → "COUNTS.md: OK (in sync with live tree)"; the
`infrastructure.core.health` `counts` gate's session-start failure is
resolved. Machine note: `template_active_inference/.venv` had decayed
(shims pointed at a pre-move checkout path under
`projects/outside_of_hum/template/`), breaking two
`test_counts_doc.py` tests locally; recreated from `uv.lock` via
`uv sync --extra dev` (pytest 9.0.3), tests green afterwards.

## False positive caught during verification

`docs/prompts/methods-orchestration/SKILL.md` "modes: audit, plan, repair" was
flagged as promising CLI verbs that do not exist. Reading the skill body
shows `repair` is an agent workflow step ("repair source layers" — editing
files), not a CLI subcommand, and every verification command listed is real.
No change made; recorded here so a future lane does not "fix" it.

## Deferred with reason

- `AGENT-ERG-COUNTS-PROVENANCE-MED-1` class remediation: the full 24-exemplar
  coverage re-measurement is long-running on this volume; it was launched
  unimpeded and the follow-up (`--refresh-coverage-provenance --write`, then
  `counts.py --check`) must run only after it completes. See the coverage
  receipt in this log once finished.
