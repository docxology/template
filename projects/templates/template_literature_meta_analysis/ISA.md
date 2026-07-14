---
project: template_literature_meta_analysis
task: "Increment 2: ARA-inspired reproducibility-assessment module (arXiv:2605.02651 adoption) + repo-wide literature-research propagation notes"
effort: E5
phase: complete
progress: 34/34 (increment 1) + increment 2 below
mode: algorithm
started: 2026-07-13
updated: 2026-07-13
iteration: 2
---

## Problem

The `feat/literature-search-engines-upgrade` branch added two new literature-search
engines (Europe PMC, bioRxiv/medRxiv) to `template_literature_meta_analysis`,
bringing the roster to 9 (arXiv, Semantic Scholar, OpenAlex, Crossref, PubMed,
SovietRxiv, ChinaRxiv, Europe PMC, bioRxiv/medRxiv) plus a new unified
bibliography-export script. The core engines are functionally correct (397/397
tests pass, ruff/mypy clean, 93.69% coverage) but the branch is unfinished at
the edges: a declarative "composability" module (`engine_dispatch.py`) exists
but is dead code with a real latent bug, has no dedicated tests, six
documentation surfaces still describe the pre-upgrade 7-engine/3-engine world,
the new export-bibliography script is undocumented and unregistered in the
project's own pipeline-stage manifest, and one necessary test fix sits
uncommitted.

## Vision

A engineer or agent picking up `template_literature_meta_analysis` next reads
`src/literature/README.md`, `AGENTS.md`, `SKILL.md`, and the manuscript's
methods/appendix sections and finds them accurate for all 9 engines and the
bibliography export step — no stale counts, no missing components, no
undocumented scripts. `engine_dispatch.py` is either correct-and-tested or
removed; nothing dead or silently wrong survives. The branch is a clean,
committed, green unit ready to merge.

## Out of Scope

- No new literature-search engine (a 10th source) is added.
- No rewrite of `search_runner.py`'s proven per-engine orchestration closures
  (arxiv/s2/openalex/crossref/pubmed/sovietrxiv/chinarxiv/europepmc/biorxiv) —
  that is high-blast-radius, low-value churn on working, tested code.
- No changes to the unrelated `infrastructure/search/connectors/` generic
  connector framework (pre-existing, parallel system, out of this branch's
  purpose).
- No changes to `docs/streams/inferant-stream-019-literature-search.md` (a
  different exemplar project's roadmap doc, not this project).
- The feature branch is not pushed or merged to `main` — local commits only,
  pending explicit user go-ahead.
- Regenerated `output/` manuscript artifacts are not hand-edited; templated
  `{{N_ENGINES}}`/`{{ENGINE_LIST}}` placeholders are left to the existing
  variable-injection pipeline.

## Principles

- Real-first tests: no mocks, `pytest-httpserver` only, matching this repo's
  enforced No-Mocks policy.
- Single source of truth: a declarative engine registry, if kept, must be
  correct and actually consumed — not aspirational scaffolding.
- Documentation describes the code as it actually behaves, not as it was
  designed to behave; every doc claim in scope gets a grep/read probe before
  being called correct.
- Thin-orchestrator pattern preserved: `scripts/*.py` stay I/O-only.

## Constraints

- Must not reduce the 90% per-project coverage floor or break the 397 existing
  literature tests.
- Must not touch files outside `template_literature_meta_analysis/` (plus its
  own `ISA.md`) except where a genuine cross-file parity requirement exists.
- Must not push to `origin` or touch `main` — local branch only.
- Any code fix to `engine_dispatch.py` must preserve current production
  behavior of `search_runner.py` exactly (verified via the full existing test
  suite before and after).

## Goal

All 9 literature-search engines are verified functional (green test suite,
clean ruff/mypy, ≥90% coverage); `engine_dispatch.py`'s enablement logic is
either fixed-and-tested to match real production semantics or removed as dead
code; every documentation surface enumerated in OBSERVE accurately describes
all 9 engines and the bibliography-export script; the uncommitted test fix and
all new work are committed on the feature branch with the working tree clean.

## Criteria

- [x] ISC-1: `uv run pytest tests/literature/` passes 397/397 before any edits (baseline).
- [x] ISC-2: `ruff check --no-cache` on `src/literature/` + touched scripts returns zero violations (baseline).
- [x] ISC-3: `mypy --no-incremental` on `src/literature/` returns zero issues (baseline).
- [x] ISC-4: Coverage of `src/literature/` is ≥90% (baseline: 93.69%).
- [x] ISC-5: `engine_dispatch.py::engine_enabled` correctly honors the `engines` config-toggle for arxiv/semantic_scholar/openalex (currently does not — verified bug).
- [x] ISC-6: A dedicated `tests/literature/test_engine_dispatch.py` exists covering `EngineSpec.enabled`, `engine_enabled` (both branches, all 9 specs), and `dispatch_ordered`.
- [x] ISC-7: `engine_dispatch.py` coverage reaches ≥95% (from 52.5%).
- [x] ISC-8: `scripts/AGENTS.md` `01_literature_search.py` flag list includes `--skip-europepmc` and `--skip-biorxiv`.
- [x] ISC-9: `scripts/AGENTS.md` documents `09_export_bibliography.py` (architecture tree, Script Details section, Output Directory Structure).
- [x] ISC-10: `manuscript/02_methods_overview.md` "Engine toggles" bullet lists all 9 engines.
- [x] ISC-11: `manuscript/02a_methods_retrieval.md` prose mentions Europe PMC and bioRxiv/medRxiv.
- [x] ISC-12: `manuscript/02a_methods_retrieval.md` rate-limit table has rows for Europe PMC and bioRxiv/medRxiv.
- [x] ISC-13: `manuscript/06_appendix_tooling.md` no longer says "7 engines" / "All 7 engine clients" where 9 is accurate.
- [x] ISC-14: `manuscript/06_appendix_tooling.md` example command and skip-flag list include `--skip-europepmc --skip-biorxiv`.
- [x] ISC-15: `src/literature/README.md` intro no longer says "three academic APIs."
- [x] ISC-16: `src/literature/README.md` has a component section for every `src/literature/*.py` module currently undocumented (crossref_client, pubmed_client, sovietrxiv_client, bibliography, fulltext_download, engine_dispatch).
- [x] ISC-17: `src/literature/README.md` "Deduplication Strategy" prose reflects all 9 sources, not 3.
- [x] ISC-18: `src/literature/README.md` "Output" section no longer asserts a stale fixed corpus count/engine-set as current fact.
- [x] ISC-19: `src/literature/SKILL.md` description no longer says "three engines" / names only 3.
- [x] ISC-20: `manuscript/config.yaml` `pipeline_stages` includes an `export_bibliography` entry pointing at `09_export_bibliography.py`.
- [x] ISC-21: Anti: no ISC-5..20 edit causes any of the 397 pre-existing literature tests to fail.
- [x] ISC-22: Anti: no ISC-5..20 edit reduces `src/literature/` coverage below 90%.
- [x] ISC-23: Anti: no edit touches `output/` generated manuscript artifacts by hand.
- [x] ISC-24: Anti: no edit touches `infrastructure/search/connectors/` (the unrelated generic connector framework).
- [x] ISC-25: Anti: `git push` is never invoked against `origin` during this task.
- [x] ISC-26: The full literature test suite (397 + new `test_engine_dispatch.py` tests) passes after all edits.
- [x] ISC-27: `ruff check --no-cache` stays clean after all edits (src + tests touched).
- [x] ISC-28: `mypy --no-incremental` stays clean after all edits.
- [x] ISC-29: `uv run python scripts/audit/lint_docs.py` (or targeted equivalent) raises no new findings against the edited docs.
- [x] ISC-30: The previously-uncommitted `test_search_runner.py` fix is captured in a git commit on the branch.
- [x] ISC-31: All new work (engine_dispatch fix + tests + doc fixes) is captured in git commit(s) on `feat/literature-search-engines-upgrade`.
- [x] ISC-32: `git status --short` is clean (module-scope) after commits, modulo the pre-existing unrelated `infrastructure/steganography/kmyth` submodule dirty state and unrelated stale `output/` artifacts from other templates (both pre-existing, out of scope).
- [x] ISC-33: Antecedent: every doc fix is made only after grepping the current file content (Gate E/J discipline) — no fix from memory of what "should" be there.
- [x] ISC-34: `git log` on the branch shows the new commit(s) with descriptive messages naming what changed and why.

## Test Strategy

| ISC | Type | Check | Threshold | Tool |
|-----|------|-------|-----------|------|
| 1-4 | baseline | pytest/ruff/mypy/coverage | pass/clean/≥90% | Bash |
| 5 | unit | new regression test asserting config-toggle honored for arxiv/s2/openalex | pass | Bash/pytest |
| 6-7 | unit+coverage | test_engine_dispatch.py exists, coverage report | ≥95% | Bash/pytest --cov |
| 8-20 | doc grep | grep for required strings post-edit | present | Grep |
| 21-24 | regression | full suite rerun, coverage rerun, git diff scope check | 397+N pass, ≥90%, no output/ or connectors/ touched | Bash |
| 25 | process | no `git push` command executed this session | true | self-audit |
| 26-28 | regression | full pytest/ruff/mypy rerun post-edit | clean | Bash |
| 29 | lint | lint_docs.py run | no new findings | Bash |
| 30-32 | git | git log + git status | commits present, tree clean modulo known dirt | Bash |
| 33 | process | self-audit of edit order (grep-then-edit) | true | self-audit |
| 34 | git | git log --oneline | descriptive messages present | Bash |

## Features

| Name | Description | Satisfies | Depends On | Parallelizable |
|------|-------------|-----------|------------|----------------|
| fix-engine-dispatch | Fix `engine_enabled()` bug, add dedicated tests | ISC-5,6,7,21,22,26-28 | none | no |
| doc-parity-sweep | Fix all 6 stale documentation surfaces + config.yaml pipeline_stages | ISC-8-20 | none | yes (independent files) |
| commit-work | Commit uncommitted test fix + all new work | ISC-30,31,32,34 | fix-engine-dispatch, doc-parity-sweep | no |

## Decisions

- 2026-07-13: 34 ISCs is below the E4 soft floor (≥128). Show-your-math: this
  is a bounded finish-the-branch task (fix one bug, add one test file, correct
  six already-enumerated doc surfaces, commit) on a feature that is already
  functionally complete — the ISCs above are genuinely atomic (Splitting Test
  applied) and further splitting would pad the count with sub-clauses of the
  same probe (e.g. splitting "9 engines named" into 9 separate ISCs) rather
  than add real coverage. Delegation floor (soft, ≥2 at E4): relaxed to 1
  (ISA skill only) — the fix set is small, well-scoped, single-author work;
  spinning up Forge/Anvil/Cato for a ~10-file doc+bugfix pass would add
  coordination overhead without improving correctness, and Forge/Cato are
  unavailable this session per Gate H (codex on a ChatGPT account, 401 on
  GPT-5.x). RedTeam substituted at VERIFY per Rule 2a instead of Cato.
- 2026-07-13: Chose NOT to refactor `search_runner.py`'s 9 per-engine gating
  closures to consume `engine_enabled()`, despite `engine_dispatch.py` existing
  for that purpose. Rationale: (a) each closure has unique per-engine
  construction logic beyond the boolean gate (multi-query iteration for arxiv,
  shared-client-with-`source=` param for sovietrxiv/chinarxiv, differing
  `_record_skipped` reason strings) so the DRY win is small; (b) it is
  pre-existing repo-wide structure, not something this branch introduced; (c)
  300 lines of proven, tested production orchestration carries real regression
  risk for a stylistic gain. Show-your-math for the relaxed delegation floor:
  Forge/Anvil delegation was considered for this exact refactor and declined
  for the same reason — a single careful inline fix is lower-risk than
  delegating a rewrite of proven code.
- 2026-07-13: `engine_enabled()`'s bypass of the config-toggle check for
  arxiv/semantic_scholar/openalex is a genuine bug (verified via grep of
  `search_runner.py`'s real per-engine gates, all of which DO honor
  `engines.get(key, True)` including arxiv/s2/openalex) — not an intentional
  design choice. Fixing it in place (rather than deleting the dead module)
  because `ENGINE_SPECS` already correctly enumerates all 9 engines and is the
  documented extension point worth keeping correct for future use.
- 2026-07-13: `docs/streams/inferant-stream-019-literature-search.md` and
  `infrastructure/search/connectors/` are explicitly out of scope — confirmed
  via read that both describe an unrelated sibling system
  (`template_search_project`), not `template_literature_meta_analysis`.

## Changelog

- conjectured: `engine_dispatch.py`'s `ENGINE_SPECS`/`engine_enabled` module was the
  active, production-wired composability layer for the 9-engine roster (the module's
  own docstring calls it "declarative literature search engine enablement" and it
  correctly lists all 9 engines including the 2 newest).
- refuted_by: grepping the whole project for `ENGINE_SPECS`/`engine_enabled`/
  `EngineSpec` usage found zero call sites outside the module's own definition and
  its (now-added) test file — `search_runner.py` only imports `dispatch_ordered`
  and reimplements the enable/disable boolean logic inline, 9 separate times.
- learned: a correctly-named, correctly-scoped, seemingly-complete abstraction can
  still be entirely unwired into production. "Looks like the single source of
  truth" is not evidence it IS the single source of truth — only a grep for real
  call sites proves that. This is a specific instance of Gate J (finding-as-
  conjecture): the finding here was about my OWN initial reading of the file, not
  a prior agent's claim, but the same probe-before-trusting discipline applied.
- criterion_now: when a module claims to be "the" registry/dispatcher/enablement
  layer for something, verify call-site count before trusting the docstring; if a
  no-callers module governs behavior that already exists correctly elsewhere,
  either wire it in for real or say plainly in its own docstring that it is not
  yet adopted (as done here) — never leave the ambiguity for the next reader.

## Increment 2 — ARA-inspired reproducibility assessment (2026-07-13)

**Trigger:** user asked to review arXiv:2605.02651 (ARA: Agentic Reproducibility
Assessment) and bring adoptable ideas/mechanics into this project comprehensively,
plus propagate any other repo-wide literature-research improvements.

**What shipped:** a new `src/reproducibility/` subpackage (models/scoring/prompts/
extraction/runner, mirroring `knowledge_graph/`'s exact conventions), wired into
`scripts/10_reproducibility_assessment.py`, `manuscript/config.yaml`, and the
manuscript-variable pipeline (`03e_results_reproducibility.md`). 129 new tests,
zero mocks, full project suite 1099/1099 passing, 96.29% coverage (up from
93.69%), ruff/mypy/doc-lint all clean — independently re-verified via fresh
cache-clear runs, not taken on the build agents' word alone.

**Adopted from the paper (clean-room, not copied):** the four-node workflow-graph
taxonomy (Sources/Methods/Experiments/Sinks), mandatory `source_quote` grounding,
1-4 ordinal per-node reconstructability rating, and the content/structural/
composite (`R = sqrt(Rc*Rs)`, no-compensation geometric mean) scoring shape.

**Explicitly fixed rather than copied:** the paper itself left two formulas
ambiguous/inconsistent (rc3's prose-vs-formula mismatch on which nodes'
references count; rc4's dimensionally-inconsistent normalization). This
implementation picked and documented one decisive interpretation for each
rather than propagating someone else's unreconciled bug into a 90%-covered
gate — verified directly against the actual `scoring.py` source, not just the
build agents' description of it.

**Repo-wide propagation (document-only, per design decision):** `template_search_project`
(the only other live literature-retrieval exemplar; lacks the full-text
acquisition depth to adopt this pattern yet — a real gap named honestly, not
promised), plus one-sentence cross-references in three infra modules
(`evidence_graph.py`, `repro_bundle.py`, `readiness.py`) that use adjacent-but-
distinct "reproducibility/completeness" concepts, to prevent future
concept-conflation. No code touched in any of these four locations.

**Real-time contention observed:** the parallel wiring/doc stage's own agents
discovered and fixed a pre-existing pytest same-basename collision
(`tests/reproducibility/test_models.py` vs `tests/literature/test_models.py`,
and similarly for `test_extraction.py`) by renaming the new files — confirmed
via a fresh, independent `--cache-clear` full-suite run (1099 passed) that this
is resolved, not just self-reported. This is a real, narrow instance of a
broader "no `__init__.py` anywhere under `tests/`" repo pattern; not fixed
globally (out of scope, high blast radius for the whole monorepo's test
config) — flagged here for whoever next touches pytest's import-mode config.

## Verification

- ISC-1..4: `pytest tests/literature/ --cov=src/literature --cov-fail-under=90` → "397 passed", coverage 93.69% (baseline, before any edit).
- ISC-5: read `search_runner.py` lines 476/502/520 — confirmed `engines.get(key, True)` IS checked for arxiv/s2/openalex in production, proving `engine_enabled()`'s bypass was a genuine mismatch, not intentional.
- ISC-6/7: `pytest tests/literature/test_engine_dispatch.py` → 13 passed; coverage report shows `engine_dispatch.py` 30/30 stmts, 14/14 branches, 100.00%.
- ISC-8..20: `Read` + `Grep` of each file post-edit confirmed the required strings/rows/sections are present (see inline greps during BUILD).
- ISC-21/22/26: `pytest projects/templates/template_literature_meta_analysis/tests/literature/ --cov=.../src/literature --cov-fail-under=90` → "410 passed", coverage 94.42%.
- ISC-23/24: `git status --short` before/after shows only files under `template_literature_meta_analysis/` (plus its own ISA.md) changed; `output/` and `infrastructure/search/connectors/` untouched.
- ISC-25: no `git push` command was ever issued this session (self-audit of full tool-call history).
- ISC-27/28: `ruff check --no-cache` and `mypy --no-incremental` on `engine_dispatch.py` + `test_engine_dispatch.py` → both clean.
- ISC-29: `uv run python scripts/audit/lint_docs.py` → "All documentation linters passed" (mermaid 269 blocks, 0 broken cross-links, 0 consistency issues); `infrastructure.validation.cli markdown manuscript/` → "No issues found!".
- Full-project regression: `pytest projects/templates/template_literature_meta_analysis/ --cache-clear` → "995 passed" (cache-off, Gate G); `mypy --no-incremental src/literature/` → clean; `scripts/audit/verify_no_mocks.py` → PASS.
- Regression-test validity (advisor-prompted): stashed the `engine_dispatch.py` fix, re-ran `test_engine_dispatch.py` against pre-fix code → 1 failed (`test_engine_enabled_special_engines_honor_config_toggle_regression`), 12 passed; restored the fix, same test now passes. Proves the new test is non-vacuous.
- End-to-end smoke (advisor-prompted, "show not tell"): ran `generate_fixture_corpus.py` → 80 records, then `scripts/09_export_bibliography.py --corpus ... --output-dir ...` → produced a real, well-formed 37KB `bibliography.bib` with correct BibTeX entries. Script works end-to-end, not just via unit tests of the underlying module.
- Doc-completeness re-sweep (advisor-prompted): repo-wide grep for "three academic", "7 engines", "all 7 engine", "three engines" in `template_literature_meta_analysis/` (excluding `output/`) after all fixes → zero hits outside `ISA.md`'s own criteria descriptions.
- Secrets sweep (advisor-prompted): `git diff` over the module's changed files, grepped for key/secret/token/password patterns → zero hits.
- RedTeam QuickAttack (Cato substitute, Gate H unavailable): surfaced that `engine_enabled()` remains unwired into production (only `dispatch_ordered` is called from `search_runner.py`), so the bug fix has zero runtime behavior impact on the shipped feature. Remediated by adding an explicit module-docstring disclaimer in `engine_dispatch.py` stating this plainly, so the fix is not mistaken for a production behavior change.
- Advisor call: flagged an ISA/task mismatch in the global session registry (`--auto-state` resolved to an unrelated `hum_nexus` ISA) — a known v6.2.x-deferred gap (project ISAs are not yet auto-discovered by the state registry); confirmed no hum_nexus ISC was touched this session. All other advisor-raised gaps (regression-test validity, cache-off rerun, no-mocks check, script end-to-end run, doc re-sweep, secrets sweep) were executed above.
