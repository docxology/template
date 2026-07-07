# Repo TO-DO - active backlog

> **Design ethos:** modular, intelligent, functional, logged, tested, and
> documented. Real methods only; never mocks or fakes. Every release ships with
> green tests and accurate docs.

This file tracks live work after the `v3.5.1` release (latest published release:
`v3.5.1`). Historical release detail belongs in
[`CHANGELOG.md`](CHANGELOG.md); generated counts and project rosters belong in
[`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md) and
[`docs/_generated/active_projects.md`](docs/_generated/active_projects.md).

---

## Live state snapshot

Rows below are refreshed independently — check each row's own as-of date, not
a single blanket date for the whole table. Re-run the commands in the
**Source** column before copying any number into prose; live counts belong in
[`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md), not hard-coded here.

| Gate or surface | Current value | Source |
| --- | --- | --- |
| Package version | `3.5.1` (as of 2026-06-27, not reverified) | `pyproject.toml#[project].version` |
| Latest published release | `v3.5.1` (GitHub release; tag exists locally) (as of 2026-06-27, not reverified) | `gh-axi release list --limit 10`, `git tag --list "v3.5*"` |
| Public source scope | `infrastructure` plus 18 public exemplar `src/` trees (as of 2026-07-07, EXEMPLAR-AUDIT-2026-07-07) | `uv run python -m infrastructure.project.public_scope source-paths` |
| Public exemplars | Link the generated roster; do not copy it here | [`docs/_generated/active_projects.md`](docs/_generated/active_projects.md) |
| Canonical generated facts | Importable infrastructure packages, infrastructure Python-module count, project-scope + publishing test collections, and per-exemplar coverage — all live-derived; do not hard-code here | [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md) (regenerate with `uv run python scripts/docgen/counts.py --write`) |
| Open GitHub PRs | 1 open: Dependabot PR #32 (`actions/checkout` 7.0.0) (as of 2026-06-27, not reverified) | `gh-axi pr list --limit 20` |
| Health gate status | `uv run python -m infrastructure.core.health`: 11/11 PASS (as of 2026-07-07, EXEMPLAR-AUDIT-2026-07-07 — was 9/11, docs-lint + api-reference FAIL, fixed this session) | `uv run python -m infrastructure.core.health` |
| Docs lint status | 0 findings (as of 2026-07-07, EXEMPLAR-AUDIT-2026-07-07 — the 2026-06-27 "active literature-meta-analysis / active-inference / publishing lanes" failures were resolved by an intervening session; not independently reverified against that specific claim, only that the gate is currently clean) | `uv run python -m infrastructure.core.health --gates=docs-lint`, or `uv run python scripts/audit/lint_docs.py --quiet` |
| Mermaid lint status | rolled into the docs-lint row above as of 2026-07-07 | `uv run python scripts/audit/lint_docs.py --mermaid-only --quiet --json` |
| Release verification baseline | `v3.5.1` is the latest GitHub release, but the current local tree is dirty; do not treat this snapshot as release readiness (as of 2026-06-27, not reverified) | `gh-axi release view v3.5.1`, `git status --short --branch` |

---

## Recently shipped

Keep this section short. Details live in release notes or archived audits.

- **EXEMPLAR-AUDIT-2026-07-07 — deep repo review + all 18 public exemplars verified (2026-07-07, [Unreleased]):**
  parallel per-exemplar audit (docs sync, thin-orchestrator composability,
  manuscript config, CI wiring) across all 18 `projects/templates/*`, plus a
  repo-wide gate sweep. Fixed: (1) `infrastructure/validation/docs/consistency/import_resolution.py`
  had a real bug — a trailing comment containing its own `(...)` truncated
  multi-line import accumulation early, false-flagging `fonds/rules/tools/connectors`
  `SKILL.md` as "unparseable" (2 new regression tests added); (2) `infrastructure/provenance/SKILL.md`
  documented an entirely fictional API (`ProvenanceStore`, `ProvenanceEdge`,
  `ReviewRecord`, a config-driven `provenance:` block) — rewritten against the
  real `Provenance`/`ArtifactNode`/`RunNode`/`Edge` API and live-verified end
  to end; (3) **critical**: `scripts/pipeline/stage_10_research_workflow.py`
  raised `ImportError` on every invocation, including `--help` — it imported
  a `WORKFLOW_STAGES` symbol and called `ResearchWorkflow.describe()`/`.stage()`
  as classmethods, none of which exist on the real (instance-based, lowercase
  stage names) API; had zero test coverage despite `tests/infra_tests/research/AGENTS.md`
  claiming otherwise — fixed and given a full regression suite; (4) `infrastructure/research/{AGENTS,README,SKILL}.md`
  `WORKFLOW_STAGES`/`WorkflowConfig` import drift fixed, with the larger
  aspirational 7-stage-with-subagents design (vs. the simpler implemented one)
  flagged inline rather than invented away; (5) `template_autopoiesis` was
  missing the `.agents/skills/template-autopoiesis/SKILL.md` its own `TODO.md`
  claimed as done — created; (6) doc-overclaims fixed in `template_search_project/README.md`
  (paperclip source claimed to "degrade gracefully"; it fail-fasts by design)
  and `template_pools_rules_tools/README.md` (stale `src/`/`scripts/`/`tests/`
  structure tree); (7) `INDEX.md` (a HumOS-side nested-checkout bookkeeping
  file, not part of this repo's own content) gitignored — was untracked but
  not ignored, a public-repo hygiene risk, and a `docs-lint` false-positive.
  `./run.sh` health went FAIL (docs-lint + stale api-reference) → PASS 11/11.
  (8) **critical, CI-breaking:** `uv run pytest tests/regression/` — the
  claim-binding tier CI actually runs — could not even collect;
  `template_madlib`'s regression-pin loader assumed a bare-import `src/`
  layout that stopped being true when the module was split into files with
  real relative imports. Fixed via the same `spec_from_file_location`
  alias-exec pattern `_autoscientists_src` already uses; while fixing it,
  found and refreshed 3 stale `template_template` regression pins
  (14→16 pipeline stages, 16→18 exemplar roster, 23→28 modules — organic
  repo growth since the 2026-07-01 pin date). `tests/regression/`: 0
  collectible → 55 passed. See **EXEMPLAR-AUDIT-FOLLOWUP-1** below for
  two lower-risk composability findings deferred rather than risking a
  same-session refactor of exemplar business logic, plus 8 pre-existing
  `tests/infra_tests/` failures (stale hardcoded counts, same class as the
  pins above) noted but not fixed this session.
- **SECURITY-AUDIT-1 — pip-audit exemption re-baselined (2026-07-03, [Unreleased]):**
  added `PYSEC-2026-597` to `.github/pip-audit-ignore.txt` for `nltk 3.9.4`
  after `pip-audit` reported no fixed version. Acceptance evidence: exemption is
  documented inline in the ignore file, limited to the advisory ID, and should
  be removed when upstream publishes a fixed release.
- **REGRESSION-PIN-2 — regression tier expanded to all 15 exemplars (2026-07-01, [Unreleased]):**
  populated real, source-re-derived regression pins (following the
  `REGRESSION-PIN-1` `template_code_project` contract) for every public
  exemplar — `template_prose_project` (was a 9-line stub),
  `template_autoscientists`, `template_autoresearch_project`,
  `template_eda_notebook`, `template_gold_refinement`,
  `template_literature_meta_analysis`, `template_sia`, `template_template`,
  `template_methods_paper`, `template_active_inference`, `template_madlib`,
  `template_newspaper`, `template_search_project`, and `template_textbook` — 55
  tests collect and pass together (`uv run pytest tests/regression/`, verified
  from the main checkout, not just per-project). Along the way, found and fixed a
  real cross-project collision: every exemplar ships a top-level `src`
  package, so the original bare `sys.path.insert` + `from src.x import y`
  pattern let whichever test module collected first win `sys.modules['src']`,
  breaking every other project's collection. Standardized on loading each
  project's `src` under a project-unique alias via
  `importlib.util.spec_from_file_location`, extended with a project-scoped
  `sys.meta_path` finder for exemplars using absolute internal imports whose
  module names collide (`template_literature_meta_analysis`'s `analysis`
  package vs. `template_code_project`'s), and a `@pytest.mark.timeout(30)`
  override for `template_template`'s slow whole-repo-introspection test (see
  `docs/maintenance/regression-testing.md` for all three patterns). All 15
  public exemplars are now pinned; the tier is not yet wired into a CI job or
  pre-push hook (see [`docs/maintenance/review-remediation-2026-07.md`](docs/maintenance/review-remediation-2026-07.md), item R1).
- **Modularity + exemplar deepening (2026-06-28, [Unreleased]):** split the
  oversized `template_gold_refinement/src/figures.py` (1280 lines) into a
  `figures/` subpackage (`_common`, `graphs`, `charts`, `diagrams`, `registry`
  + facade `__init__` preserving the exact 25-name public API), clearing the
  module-line-count gate (every module < 800 lines; 291 exemplar tests green).
  Updated every `src/figures.py::` provenance/evidence/prose reference to the
  owning submodule and shipped the required `figures/` `AGENTS.md`+`README.md`
  doc pair. Removed the redundant flat `infrastructure/publishing/archival.py`
  shim (subpackage is sole source of truth; 589 publishing tests pass). Deepened
  `template_madlib` (doc accuracy + determinism tests), `template_template`
  (workspace-discovery tests), and `template_textbook` (atomic-write test);
  regenerated `COUNTS.md`, `api-reference.md`, and the exemplar roster
  manifest/doc. Full infra suite green (7863 passed).
- **SCRIPTS-LOGIC closeout (2026-06-28, [Unreleased]):** closed SCRIPTS-LOGIC-1 through
  SCRIPTS-LOGIC-6 — extracted six inline algorithms from scripts into tested infra modules:
  discover_infrastructure_packages (api_reference_gen.py), stage_label (pipeline/dag.py),
  scan_test_roots (no_mock_enforcer.py), format_audit_statistics (audit_orchestrator.py),
  DEFAULT_STAGE_TABLE_TARGETS constant (stage_table.py), aggregate_check_results plus
  log_header logger fix (setup_checks.py / 00_setup_environment.py). Each extraction is
  backed by unit tests; all 6 scripts remain behaviourally identical.
- **Coverage sweep (2026-06-26, `[Unreleased]`):** added 119 tests across 8
  infrastructure modules, closing the coverage gaps below 50% identified in the
  2026-06-26 sweep. Overall test count: 7780 collected (9 failures under
  investigation). Scripts audit identified 6 thin-orchestrator violations now
  tracked as `SCRIPTS-LOGIC-1` through `SCRIPTS-LOGIC-6`; 43 of 49 scripts are
  clean. Parity findings were later reconciled in
  [`docs/development/coverage-gaps.md`](docs/development/coverage-gaps.md):
  Docker already has partial coverage through the rendering tests and
  `logrotate.d` is a config directory with zero test coverage by design.
- **Modular publishing adapter suite (2026-06-26, `[Unreleased]`):** closed
  `PUB-PLATFORM-1`. Shipped `infrastructure/publishing/registry.py`
  (`PLATFORM_REGISTRY`, `PublishingTier`, `list_platforms()`, `get_platform()` —
  10 first-class + 2 documented targets); `infrastructure/publishing/pypi/`
  (`PyPIAdapter` with build/check/upload/verify, `PyPIConfig`, `PyPIResult`);
  `infrastructure/publishing/static_site/` (`GitHubPagesAdapter`,
  `CloudflarePagesAdapter`, `NetlifyAdapter`, per-family registry); and promoted
  `infrastructure/publishing/archival/` to a proper subpackage (`models.py`,
  `providers.py`, `orchestrate.py`). Pinned by 137 tests across
  `tests/infra_tests/publishing/test_pypi.py` (11), `test_static_site.py` (22),
  `test_archival_module.py` (57), `test_registry.py` (47).
- **AutoResearch reviewer-boundary closeout (2026-06-13, `[Unreleased]`):**
  closed `AR-REPORT-ERGONOMICS-1`, `AR-BENCHMARK-ERGONOMICS-1`, and
  `AR-SOURCE-LEDGER-2`. The loop now emits
  `output/data/autoresearch_evidence_overview.json`,
  `output/reports/autoresearch_evidence_overview.md`, and
  `output/data/benchmark_boundary.json`; the source-ledger contract validates
  ledger citekeys against BibTeX and manuscript citations, rejects invalid
  tiers/future dates, and prints offline age/tier summaries. Verified with
  `uv run pytest projects/templates/template_autoresearch_project/tests/ -q`
  (224 passed).
- **Template forkability + verifier roadmap pass (2026-06-13, `[Unreleased]`):**
  closed `TODO-REBASE-2` (live PR count is 0; active backlog restored instead of
  `_No open items_`), `REGRESSION-PIN-1` (the first real
  `template_code_project` regression pins now collect and pass with a mutation
  negative control), and `AI-VIZ-SPLIT-1` (`src/visualizations/figures.py`
  split into focused semantic and simulation modules while preserving the figure
  facade). `AI-SEMANTIC-FIXPOINT-1` is now closed: the shared fixed-point
  orchestrator drives manuscript variables, sheaf semantic outputs, and contract
  settlement; the selected fixed-point cluster passed 21 tests on 2026-06-13.
- **Generated-report web design (2026-06-12, `[Unreleased]`):** modernized the
  base HTML report/dashboard template (`infrastructure/reporting/html_templates.py`)
  with CSS design tokens, dark mode (`prefers-color-scheme`), WCAG-AA status
  contrast, fluid type, and a mobile breakpoint — template contract + deterministic
  output preserved (7 template + 875 reporting tests green).
- **Scoped-improvement sweep (2026-06-12, `[Unreleased]`):** closed all three
  freshly-scoped items. `WEBDESIGN-EXTEND-1` — extracted `html_templates.shared_css()`
  as the single design-token source; the pipeline report, interactive dashboard, and
  web renderer all now anchor to `--brand-1` + a `prefers-color-scheme` block (108
  tests). `LINKCHECK-PERF-1` — `link_audit_core` prunes excluded/gitignored dirs
  before descending + single-pass file reads (~15–28× faster; 303 link tests + a
  timed regression). `TEXLIVE-2026-BEAMER-1` — `latex_utils.compile_latex` tolerates
  the benign `\reserved@a` kernel warning when a valid PDF results (the beamer test
  now passes on TeX Live 2026; genuine failures still raise).

- **Backlog closeout + comprehensive review (2026-06-12):** closed `REPRO-VERIFY-1`
  (the repro bundle now fails closed on declared-but-absent outputs — a
  declared output absent at build rebases onto the project tree and `verify`
  returns `ok=False`; pinned by `tests/infra_tests/publishing/test_repro_bundle_absent_output.py`)
  and `EVIDENCE-CLAIM-1` (the claim-ledger candidate list gained an
  `output/data/*claims*.json` glob so the `template_autoresearch_project`
  exemplar's `autoresearch_claims.json` is ingested as claim nodes + `supports`
  edges; pinned by `test_ingest_claims_autoresearch_ledger_yields_nodes_and_supports`
  and `test_build_evidence_graph_ingests_real_autoresearch_ledger`). Shipped
  alongside a large multi-pass review (dead-code removal, `run.config` matrix
  runner, `SOURCE_DATE_EPOCH` determinism, the `canonical_facts.md`→`COUNTS.md`
  generator, exemplar-support-tier tagging, methods-plan gate, validation↔
  autoresearch decoupling, and an Ollama test-model fix). Full detail in
  [`CHANGELOG.md`](CHANGELOG.md).
- **Backlog sweep + RedTeam hardening (2026-06-08):** closed 6 backlog items —
  `PIPELINE-INCR-FLAG-1` (`--incremental` CLI flag on both entrypoints),
  `DASHBOARD-CLI-1` (release-readiness dashboard discoverable + subprocess test),
  `REPRO-MULTI-1` (`--all-public` multi-exemplar repro bundles),
  `PROSE-GATE-WIRE-1` (opt-in report-only prose gate in Stage 6, disabled =
  byte-identical), `SIA-HARNESS-2` (fixture/live separation tests + docs), and
  `LOG-SEP-CENTRAL-1` (33 banner literals routed through width constants + lint).
  Verified `TODO-REBASE-1`, `ARCH-CONFTEST-1`, and `AI-GATE-CACHE-1` already
  satisfied. A verifier-first RedTeam pass then fixed a real SIA fail-closed hole
  (`max_generations<1` returned a vacuous empty run) and closed five green-wash
  test gaps. Commits `33e5ca71`, `c8381d9a`. One out-of-scope finding logged as
  `REPRO-VERIFY-1`. `RELEASE-TAG-1` deferred (needs a clean tree + sign-off).
- **`v3.3.1` release train (2026-06-07):** completed Pandoc DOCX output (embed
  figures + resolve cross-references in `infrastructure/rendering/pipeline.py`),
  ran a deep per-exemplar quality pass across the eight tracked public templates,
  completed and cross-linked sidecar publication metadata for all nine public
  exemplars, and reconciled the generated project-scope collection count to 216.
  Full detail in [`CHANGELOG.md`](CHANGELOG.md).
- **`v3.3.0` release train (2026-06-07):** closed the three Medium backlog items
  (READFILE-SAFE-1, CI-MATRIX-DYNAMIC-1, LOG-CLEAN-1) and all five Major items
  (EVIDENCE-GRAPH-1, REPRO-BUNDLE-1, DASHBOARD-1, PLUGIN-STAGES-1,
  INCREMENTAL-PIPELINE-1) — the two pipeline-core features are opt-in/default-off.
  The shipped artifacts were re-verified on disk and under test on 2026-06-08
  (169 dedicated tests pass; no stubs). Full detail in
  [`CHANGELOG.md`](CHANGELOG.md). The genuine residual next-increments of these
  features are now tracked as new backlog items below (EVIDENCE-CLAIM-1,
  PIPELINE-INCR-FLAG-1, DASHBOARD-CLI-1, REPRO-MULTI-1, PROSE-GATE-WIRE-1).
- **Reference-existence + AI-writing infrastructure (2026-06-06):** new
  `infrastructure/reference/verification/` deterministic anti-hallucination gate
  (Crossref→OpenAlex/arXiv resolver, SQLite cache, offline-first) and
  `infrastructure/validation/content/ai_writing.py` AI-writing fingerprint
  detector (`validation.cli prose-quality`); wired into the `docs/prompts`
  workflows. Clean-room distillation of academic-research-skills ideas
  (CC-BY-NC-4.0); no code vendored.
- **Infra test parallelization (2026-06-06):** `pytest-xdist` + `-n auto` on the
  CI `test-infra` job cut each leg from ~892s to ~585s; suite verified
  parallel-safe; default `-v` dropped from `addopts`.
- **Docs accuracy sweep (2026-06-06):** audited `docs/` + every
  `infrastructure/*/{SKILL,README,AGENTS}.md`; corrected examples that cited
  methods/params/CLI flags/test paths that did not exist (every fixed command
  re-verified to resolve).
- **`v3.2.0` release train (2026-06-04):** DOCX/EPUB renderers + format toggles
  (FMT-BUNDLE-1), Active Inference validation spine v2 (AI-SPINE-V2),
  infrastructure coverage gaps rebaselined (COVERAGE-REBASE-1), GitHub
  supply-chain hardening (GH-PIN-1, GH-ACTIONLINT-1, GH-AUTOMERGE-1), and the
  XML parser policy (DEP-DEFUSEDXML-1). See [`CHANGELOG.md`](CHANGELOG.md).
- **`v3.1.0` release train:** SIA joined the public exemplar scope; Active
  Inference gained the first validation-spine tracks; docs signposting moved to
  `projects/templates/...`; public coverage orchestration was hardened. See
  [`CHANGELOG.md`](CHANGELOG.md).
- **Thermo-nuclear infra/docs audit (2026-06-08):** Waves A–E closed — doc contract,
  READFILE-SAFE-1 CLI, AGENTS v3.3 completeness, evidence-graph SUPPORTS/registry
  bridge, autoresearch validation split. The dated point-in-time audit snapshots
  were retired with the public `docs/audit/` archive; use git history for those
  reports.
- **Thermo-nuclear remediation waves:** 2026-05-29 and 2026-05-30 blockers and
  branch deltas are closed. Dated point-in-time reports were retired with the
  public audit archive.

---

## Active backlog

### EXEMPLAR-AUDIT-FOLLOWUP-1 — thin-orchestrator violations in two exemplars

- **Source:** EXEMPLAR-AUDIT-2026-07-07 (see "Recently shipped"), refuted-tested
  by a live re-probe agent — both confirmed real on HEAD `646bb15`.
- **`template_autoscientists/scripts/hermes_proposer.py` — FALSE POSITIVE,
  refuted 2026-07-07 on deeper investigation, no fix needed:** the original
  finding ("implements real business logic — prompt construction, live LLM
  query, JSON-reply parsing — directly in `scripts/`") missed that
  `src/agents.py`'s own module docstring documents this placement as
  intentional: `HermesProposer` lives in `scripts/hermes_proposer.py`
  specifically **so `src/` stays infrastructure-free** (no live-Ollama/LLM
  import in the deterministic, always-tested core); `src/__init__.py` lazily
  re-exports it via `__getattr__`. Both the original audit agent and its
  independent refutation agent missed this documented rationale — a live
  Gate-J example of a finding that looked real from the outside but wasn't,
  caught only by reading the sibling module's own docstring before acting.
- **`template_code_project/scripts/09_provenance_record.py`** (medium
  severity): reimplements a content-addressed DAG store inline instead of
  using `infrastructure.provenance.Provenance`, producing an incompatible
  on-disk schema from the repo's own provenance module. **Acceptance:**
  either (a) migrate the script to call `infrastructure.provenance.Provenance`
  directly (preferred — matches `scripts/pipeline/stage_09_provenance_record.py`'s
  pattern), or (b) if the inline schema is intentional (e.g. this exemplar
  predates the shared module), document why in the script's docstring and add
  a regression test pinning the on-disk schema so it can't silently drift
  further.
- Deferred rather than fixed same-session: `template_code_project`'s finding
  was fixed in iteration 8b (see "Recently shipped" below);
  `template_autoscientists`'s was refuted — `src/agents.py`'s own docstring
  documents `HermesProposer` living in `scripts/` as intentional (keeps
  `src/` infrastructure-free of live-Ollama deps). No further action needed.
- **New finding (iteration 8b, not fixed):** the "combined coverage gate"
  step of `uv run python scripts/pipeline/stage_01_test.py --project-only
  --all-projects --public-projects` (75% union-coverage floor) fails with
  `No source for code: '.../pytest-<N>/test_run_project_tests_fail_wh0/iso_project/src/__init__.py'`
  — reproducible from a clean checkout, unrelated to any of this session's
  edits. Root cause (not fully traced): `template_search_project/tests/test_analysis.py::test_run_project_tests_fail_when_pytest_errors`
  spawns a real `pytest` subprocess against a `tmp_path`-scoped isolated
  fixture project to test `run_project_tests()`; that subprocess appears to
  write coverage data into a file the parent's "combined coverage gate"
  later tries to combine, referencing a source path that no longer exists
  once `tmp_path` is torn down. All 18 projects' own per-project gates pass;
  only this aggregate union-coverage step is affected. Needs someone to trace
  `infrastructure.core.test_runner`'s combine step and confirm whether
  `COVERAGE_FILE`/`COV_CORE_DATAFILE` env vars are leaking into the
  subprocess, or scope the subprocess's coverage data file explicitly.
- **Fixed this session — CI-breaking, not just dormant:** `uv run pytest
  tests/regression/` (wired into `.github/workflows/ci.yml`, the claim-binding
  tier from R1) could not even **collect** on clean HEAD `646bb15` —
  `tests/regression/projects/template_madlib/tables/test_configuration_counts_claims.py`
  raised `ImportError: attempted relative import with no known parent
  package`. Root cause: its `_load_src_package()` loader assumed
  `template_madlib/src` used bare intra-package imports (`from config import
  ...`) and exec'd each submodule as a standalone top-level module — stale
  relative to the actual source, which has used ordinary relative imports
  (`from .config import ...`) throughout since the module was split into
  multiple files. Fixed by switching to the same `spec_from_file_location`
  alias-exec pattern `_autoscientists_src` already uses correctly. Also found
  (once collection succeeded) 3 stale regression pins in
  `tests/regression/pinned_values/template_template.json` — `pipeline_stages_declared`
  (14→16), `public_exemplar_roster_count` (16→18), `module_count` (23→28,
  outside its ±2 band) — legitimate organic repo growth since the 2026-07-01
  pin date, re-derived live and refreshed with `refreshed_on`/`refresh_reason`
  provenance fields (no prior precedent for a pin refresh in this repo; a
  convention worth adopting for future refreshes). `uv run pytest
  tests/regression/` now: 55 passed.
- **Also confirmed pre-existing (not introduced this session, verified via
  `git stash` against clean HEAD `646bb15`), part of the "tested" pillar gap,
  not fixed this session:** 8 `tests/infra_tests/` failures with stale
  hardcoded expectations — `test_single_stage.py::test_known_stage_key_is_mapped`
  expects a render script named `*03_render_pdf.py`, actual is
  `stage_03_render.py`; `test_mcp_server.py::TestInvokeCli::test_invokes_registered_cli`
  hardcodes `len(stages) == 14`, actual is 16; plus `test_stage_registry.py`
  (×2), `test_methods_orchestration.py` (×2),
  `test_mcp_server.py::TestServeLoop::test_real_subprocess_stdio`,
  `test_xml_parser_policy.py`, and
  `test_repro_determinism.py::test_every_public_exemplar_declares_output_artifact`
  (`template_autopoiesis`/`template_pools_rules_tools` repro manifests declare
  no present output-artifact). Same class of self-pinned-hardcoded-count
  drift as the `template_template` pins above; none investigated deeply
  enough this session to safely fix.

### REVIEW-2026-07-02 — Multi-lens review remediation backlog

- **Source:** a 9-dimension adversarial review at HEAD `890abb6a` (43 findings
  confirmed against HEAD, 3 refuted). The safe, bounded fixes shipped the same
  session (two CI-breaking CRITICALs cleared — 4 missing `data/README.md` +
  stale `exemplar_roster.md` — plus health-CLI, drift-gate-scoping, upload-script,
  CITATION.cff, and doc-drift fixes; `./run.sh` health went FAIL → PASS 11/11).
- **Open items (R1–R18)** with per-item acceptance lines live in
  [`docs/maintenance/review-remediation-2026-07.md`](docs/maintenance/review-remediation-2026-07.md).
  Highest leverage: **R1** (wire the 15-exemplar / 55-test regression tier into
  CI — it is currently unenforced), **R2** (scope skills discovery to tracked
  paths, mirroring the drift-gate fix already shipped), **R7** (operations
  catalog / MCP miss single-file CLIs).

### AI-GATE-PERF-2 — Reduce active-inference gate runtime after correctness

- **Problem:** `template_active_inference` gate tests had a heavy explicit
  roadmap/sheaf write path whose *first* invocation in a process took ~250s —
  well past the repo's real per-test timeout
  (`infrastructure.core.test_runner.DEFAULT_TIMEOUT = 120`).
- **Why it matters:** slow gates discourage local verification and make future
  semantic changes harder to review.
- **Blocker (2026-06-26, resolved 2026-07-01):** The `template_active_inference`
  test suite had 47 collection errors due to a Python 3.14/3.12 binary
  incompatibility — the project venv was built for Python 3.14 but the main
  runner is Python 3.12. Fixed by rebuilding the venv pinned to 3.12
  (`rm -rf .venv && UV_PYTHON=3.12 uv sync --extra dev` inside
  `projects/templates/template_active_inference/` — a bare `uv sync` alone
  re-resolves against the newest installed interpreter and also omits the
  `dev` extra that carries `pytest`, so both flags are required). Collection
  now succeeds cleanly: 493 tests collected, 0 errors.
- **Heavy-test root cause found and fixed (2026-07-01):** `ensure_gate_artifacts`
  memoizes its expensive bootstrap behind an `output/`-artifact signature cache
  that is genuinely fast (~0.01s) on every call after the first — but the
  first call alone measured ~250s. Whichever test ran first paid that cost
  inside its own 120s timeout window and got killed mid-bootstrap, so its
  cache marker never landed; the next test then retried the same
  never-completing bootstrap, cascading the failure across every test in
  `test_aggregate_forgery_controls.py` (all 7 timed out, not just one). Fixed
  with a `pytest_sessionstart` hook in `tests/conftest.py` that pre-warms the
  bootstrap once, before pytest-timeout's per-item timer starts (hooks aren't
  subject to the per-test timeout). The hook snapshots and restores the
  mutable `manuscript/**/*.md` sources around its own pre-warm call so it
  doesn't hydrate them before the existing `_restore_mutable_project_sources`
  fixture takes its "original" snapshot. Along the way, also fixed two
  independent O(N×M) redundant-file-read bottlenecks that compounded the cold
  start: `scholarship.py::_citation_sections` and
  `visualization_audit.py::_figure_reference_sections` each re-globbed and
  re-read every manuscript markdown file from scratch per citation
  key/figure id (~25 keys × ~138 files, ~7 rows × ~116 files); both now read
  the file set once per `build_*` call and reuse it across the loop.
  Full suite verified: `uv run pytest tests/ -q --timeout=120 -k "not long_running"`
  → 381 passed (112 deselected), ~12 minutes wall-clock, 0 failures.
- **Acceptance check met:** 47 collection errors are gone (0 errors, 493
  collected); `test_aggregate_forgery_controls.py`'s 7 tests all pass; the
  full non-long-running suite (381 tests) passes under the real 120s per-test
  timeout; manuscript source and `output/` stay git-clean after a full run.
- **Remaining:** the `--durations=20` profiling pass itself (to look for
  further redundant artifact refreshes beyond the two fixed here) and the
  project-local `MEDIUM-TEST-PERF-1` split (cheap source-only negative
  controls plus one end-to-end refresh characterization) are still open —
  this item closed the *correctness/timeout* blocker, not the full perf-tuning
  scope.
- **Out of scope:** weakening coverage, skipping pymdp-backed evidence, or
  dropping the end-to-end refresh characterization.

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

## See also

- [`CHANGELOG.md`](CHANGELOG.md) - historical release notes
- [`docs/development/roadmap.md`](docs/development/roadmap.md) - release
  direction and long-horizon themes
- [`docs/development/coverage-gaps.md`](docs/development/coverage-gaps.md) -
  measured infrastructure coverage gaps
- [`.github/AGENTS.md`](.github/AGENTS.md) - CI gates and local parity commands
