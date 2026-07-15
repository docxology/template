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

## Increment 3 — Adversarial review, hardening, and first real end-to-end run (2026-07-13)

**Trigger:** user asked for a fresh adversarial read of the increment-1 and
increment-2 work, not a re-confirmation that tests pass. "Don't just re-run
the existing tests and call it done."

**What was found and fixed:**

1. **BUG (critical): wrong system prompt sent to LLM.** `call_ollama()` in
   `knowledge_graph/llm_client.py` hardcoded `knowledge_graph.llm_prompts._
   SYSTEM_PROMPT` as the system prompt for every LLM call. The
   reproducibility module's `extraction.py` called `call_ollama(prompt,
   config)` without passing its own system prompt (from `reproducibility/
   prompts.py`, which describes the workflow-graph schema, node types, and
   JSON format). Result: the LLM received a system prompt about
   hypothesis-support assertions — a completely different task — and
   emitted nodes with empty `node_type=""` that the validation layer
   silently dropped, producing zero-node graphs. Tests did not catch this
   because pytest-httpserver returns canned responses regardless of what
   is sent to it. Fixed by adding an optional `system_prompt` parameter to
   `call_ollama()` (keyword-only, defaults to `None` → falls back to the
   knowledge-graph prompt for backward compatibility) and passing
   `reproducibility.prompts._SYSTEM_PROMPT` from `extraction.py`. Added a
   test (`test_extract_workflow_nodes_sends_reproducibility_system_prompt`)
   that inspects the actual HTTP request body to verify the correct system
   prompt is sent.

2. **BUG (moderate): `weak_component_coverage` (rc5) could exceed 1.0.**
   A hand-built `WorkflowGraph` whose edges reference `node_id`s not in
   `graph.nodes` (phantom endpoints) would inflate the component size
   beyond `len(graph.nodes)`, producing a result > 1.0 — violating the
   documented `[0.0, 1.0]` contract. `build_workflow_graph` prevents this
   in the normal pipeline (dangling references are counted, not turned
   into edges), but hand-built test fixtures and any future direct-edge
   construction bypass it. Fixed by filtering phantom-edge endpoints before
   building the undirected adjacency. Added a test
   (`test_phantom_edge_endpoints_do_not_inflate_rc5`).

3. **Documentation gap: cycle handling undocumented.** `build_workflow_graph`
   does not prevent cycles (A depends on B, B depends on A) or self-loops.
   All scoring functions handle cycles correctly (BFS `visited` sets,
   degree functions are inherently cycle-safe), but this was never
   documented. Added a "Cycle handling" section to `models.py`'s module
   docstring and a corresponding invariant in `AGENTS.md`. Added tests
   (`test_two_node_cycle_scores_without_infinite_loop`,
   `test_self_referencing_node_scores_without_error`).

4. **Coverage gaps closed.** extraction.py was at 95.58% (uncovered:
   non-numeric `reproducibility_rating` coercion, `output_path` resume
   from file). Added tests
   (`test_extract_workflow_nodes_coerces_non_numeric_rating`,
   `test_extract_workflow_graphs_llm_resumes_from_output_path`).
   extraction.py is now at 100.00%.

5. **Upstream issues #2 and #3 remain unanswered.** Both GitHub issues
   against the ARA paper's repo (AndresLaverdeMarin/agentic_reproducibility_
   assessment) remain OPEN with zero comments. The implementation's
   interpretation (rc3 counts method+experiment references only; rc4
   normalizes by |sources|*|sinks|) matches the interpretation described
   in those issues. No code change needed; the issues are documented as
   deliberate modeling choices in `scoring.py`'s module docstring.

6. **First-ever real end-to-end run.** Ran
   `scripts/10_reproducibility_assessment.py` against two real papers'
   fulltext with Ollama gemma3:4b. Before the system-prompt fix: 0 nodes
   per paper (all dropped for empty `node_type`). After the fix: 9 and 8
   workflow nodes respectively, with correct node-type classification,
   quote verification rate of 1.0, and reasonable composite scores (0.87
   and 0.95). This is the first time this module has ever run against real
   data — all prior testing was via pytest-httpserver stubs.

**Verification:**
- `pytest tests/` → 1106 passed (up from 1099), coverage 96.41% (up from
  96.29%).
- `ruff check --no-cache` on all modified files → clean.
- `mypy --no-incremental` on all modified files → clean.
- End-to-end: `scripts/10_reproducibility_assessment.py` against real
  Ollama + real fulltext → 2 papers, 17 nodes total, 14 edges, 0
  dangling references, quote_verification_rate=1.0.

## Increment 4 — Comprehensive meta-analysis exemplar improvement (2026-07-13)

**Trigger:** user asked to "comprehensively review and improve the
meta-analysis exemplar, ensure it makes full best use of the real methods."

**What was found and fixed:**

1. **Pipeline stage gap: `10_reproducibility_assessment.py` missing from
   config.yaml.** The script existed and passed tests, but was not listed
   in `analysis.scripts` (so it never ran in the default pipeline) nor
   in `pipeline_stages` (so it was invisible in the declared DAG). Added
   to both lists.

2. **Pipeline stage gap: no fulltext download script.**
   `literature.fulltext_download.download_and_extract_fulltext()` — the
   function that resolves OA PDFs via Unpaywall, downloads them, and
   extracts plaintext + figures — had zero callers from any script. The
   reproducibility runner reads `.txt` files but nothing produced them.
   Created `scripts/11_fulltext_download.py` (thin orchestrator) as the
   bridge between the corpus and the reproducibility assessment. Added
   to `analysis.scripts` and `pipeline_stages` in config.yaml.

3. **Config documentation: output tree stale.** `src/config.py`'s
   module docstring listed output/ artifacts but was missing
   `fulltext_extraction.json`, `workflow_graphs.jsonl`,
   `reproducibility_scores.json`, `reproducibility_summary.json`, and
   the `fulltext/` directory. Updated.

4. **Scripts AGENTS.md: architecture tree and script table stale.**
   Missing `10_reproducibility_assessment.py` and `11_fulltext_download.py`
   from the architecture tree, the script I/O table, and the default
   run-order description. Updated all three.

**What was verified as already correct (no change needed):**
- All 7 manuscript variable extractors are registered and functional.
- 03c_results_text_analytics.md already uses all text-analytics variables
  (NUM_EMBEDDING_CLUSTERS, TOP_ENTITIES_TABLE, TOP_KEYPHRASES_TABLE,
  TOP_SIMILAR_PAIRS_TABLE, NUM_TOPICS, TOPIC_TABLE, etc.).
- The "missing variables" identified in the initial audit (A1_COUNT,
  H1_SCORE, TOP_HUBS_TABLE, etc.) are either dynamically generated by
  extractors (hypothesis scores use f-strings keyed by hypothesis ID) or
  only referenced in AGENTS.md/README.md as examples, not in actual
  manuscript sections.
- 11 computed-but-unused variables (CORPUS_SIZE_LATEX, CITATION_EDGES_RAW,
  etc.) are intentional alternate-format aliases kept for future use.

**Verification:**
- `pytest tests/` → 1106 passed, coverage 96.39%.
- `ruff check --no-cache` on all modified files → clean.
- `mypy --no-incremental` on new script → clean.

## Increment 5 — Deep improvement of all literature methods (2026-07-13)

**Trigger:** user asked to "deeply improve all the literature sure methods as
demonstrated in the bibliography and full text methods of example project."

**Reference standard** (from `bibliography.py` and `fulltext_download.py`):
- Comprehensive module docstrings explaining WHY, not just WHAT
- Self-contained with no external dependencies that fail to resolve
- Graceful degradation (degrade-to-None/degrade-to-[] on errors)
- Atomic file writes (temp-file + rename)
- Multi-dimensional assessment (not just one metric)
- Injectable base URLs for testability
- Retry with exponential backoff
- Clear separation of concerns

**What was improved:**

1. **`evaluation.py`** — Was 78 lines with no module docstring and a stale
   7-engine `_SOURCE_KEYS` list (missing europepmc and biorxiv). Now has a
   comprehensive docstring, 9-engine `_SOURCE_KEYS` list, type-annotated
   `claim_verdicts` handling (supports dicts and dataclasses), and graceful
   degradation for missing fields.

2. **`fulltext_assessment.py`** — Was 70 lines with no module docstring.
   Now has a comprehensive docstring explaining the pure-vs-realized
   assessment split, adds `pmid` to `identifier_coverage` (was missing),
   and documents the five assessment dimensions.

3. **`query_router.py`** — Had no module docstring. Now has a comprehensive
   docstring explaining the routing logic, the stateless classifier
   contract, and why all nine engines appear in every source-order tuple.

4. **`models.py`** — Added `keywords` field (with serialization/deserialization),
   `referenced_works` property alias (matching OpenAlex/S2 field name),
   improved preprint detection (added "europepmc" to `_PREPRINT_HINTS`),
   and updated `metadata_completeness` to count the new `keywords` field.

5. **`corpus.py`** — Added atomic save (temp-file + rename, matching the
   convention in `reproducibility.models.append_workflow_graphs` and
   `fulltext_download.download_fulltext`), added `summary()` method for
   quick corpus diagnostics, and improved the module docstring to document
   the two-tiered deduplication strategy.

**Verification:**
- `pytest tests/` → 1106 passed, coverage 96.37%.
- `ruff check --no-cache` on all modified files → clean.
- `mypy --no-incremental` on all modified files → clean.
