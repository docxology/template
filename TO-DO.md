# Repo TO-DO - active backlog

> **Design ethos:** modular, intelligent, functional, logged, tested, and
> documented. Real methods only; never mocks or fakes. Every release ships with
> green tests and accurate docs.

This file tracks live work after the `v3.4.0` release (latest published release:
`v3.4.0`, tagged 2026-06-12). Historical release detail belongs in
[`CHANGELOG.md`](CHANGELOG.md); generated counts and project rosters belong in
[`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md) and
[`docs/_generated/active_projects.md`](docs/_generated/active_projects.md).

---

## Live state snapshot

Refreshed on **2026-06-13** on branch `codex/template-exemplar-forkability`
after the forkability and verifier-first roadmap pass. Re-run the
commands in the **Source** column before copying any number into prose; live
counts belong in [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md), not
hard-coded here.

| Gate or surface | Current value | Source |
| --- | --- | --- |
| Package version | `3.4.0` | `pyproject.toml#[project].version` |
| Latest published release | `v3.4.0` (tagged + GitHub release published 2026-06-12; CHANGELOG `[3.4.0]` body) | `gh release list`, `git tag` |
| Public source scope | `infrastructure` plus nine public exemplar `src/` trees | `uv run python -m infrastructure.project.public_scope source-paths` |
| Public exemplars | `template_active_inference`, `template_autoresearch_project`, `template_autoscientists`, `template_code_project`, `template_newspaper`, `template_prose_project`, `template_sia`, `template_template`, `template_textbook` | [`docs/_generated/active_projects.md`](docs/_generated/active_projects.md) |
| Canonical generated facts | Importable infrastructure packages, infrastructure Python-module count, project-scope + publishing test collections, and per-exemplar coverage — all live-derived; do not hard-code here | [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md) (regenerate with `uv run python scripts/generate_counts.py --write`) |
| Open GitHub PRs | 0 open | `/opt/homebrew/bin/gh-axi pr list` |
| Docs lint status | links-only, consistency-only, and doc-pairs all clean (re-verified 2026-06-13) | `uv run python scripts/lint_docs.py --links-only --quiet --json`, `--consistency-only`, `--doc-pairs-only` |
| Mermaid lint status | clean with chunked batch rendering under the default total budget | `uv run python scripts/lint_docs.py --mermaid-only --quiet --json` |
| Release verification baseline | drift `--strict`, COUNTS/skills/exports gates, tracked-project/generated-artifact guards, docs-lint (links/consistency), reporting+evidence+repro suites (877), and the LLM suite (1244, live Ollama) all green at the v3.4.0 commit | `v3.4.0` release + local command history |

---

## Recently shipped

Keep this section short. Details live in release notes or archived audits.

- **Coverage sweep (2026-06-26, `[Unreleased]`):** added 119 tests across 8
  infrastructure modules, closing the coverage gaps below 50% identified in the
  2026-06-26 sweep. Overall test count: 7780 collected (9 failures under
  investigation). Scripts audit identified 6 thin-orchestrator violations now
  tracked as `SCRIPTS-LOGIC-1` through `SCRIPTS-LOGIC-6`; 43 of 49 scripts are
  clean. Parity gaps logged as `INFRA-TEST-PARITY-1` (docker) and
  `INFRA-TEST-PARITY-2` (logrotate.d).
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
  bridge, autoresearch validation split. Approve — see
  [`docs/audit/archived/thermo-nuclear-code-quality-2026-06-08.md`](docs/audit/archived/thermo-nuclear-code-quality-2026-06-08.md).
- **Thermo-nuclear remediation waves:** 2026-05-29 and 2026-05-30 blockers and
  branch deltas are closed. See
  [`docs/audit/archived/thermo-nuclear-code-quality-2026-05-29.md`](docs/audit/archived/thermo-nuclear-code-quality-2026-05-29.md)
  and
  [`docs/audit/archived/thermo-nuclear-code-quality-2026-05-30.md`](docs/audit/archived/thermo-nuclear-code-quality-2026-05-30.md).

---

## Active backlog

### AI-GATE-PERF-2 — Reduce active-inference gate runtime after correctness

- **Problem:** `template_active_inference` gate tests still have one heavy
  explicit roadmap/sheaf write path; clean-state fixed-point and gate setup now
  avoid redundant regeneration, but the full project suite still needs a
  durations-driven pass.
- **Why it matters:** slow gates discourage local verification and make future
  semantic changes harder to review.
- **Blocker (2026-06-26):** The `template_active_inference` test suite currently
  has 47 collection errors due to a Python 3.14/3.12 binary incompatibility —
  the project venv was built for Python 3.14 but the main runner is Python 3.12.
  Running `--durations=20` locally is blocked until the project venv is rebuilt
  with the correct interpreter. **Fix:** run `uv sync` inside the
  `projects/templates/template_active_inference/` directory to rebuild the venv
  for the active Python version before attempting any perf profiling.
- **Smallest next step:** rebuild the project venv (prerequisite above), then
  complete the remaining project-local `MEDIUM-TEST-PERF-1` split with cheap
  source-only negative controls plus one end-to-end refresh characterization.
- **Acceptance check:** 47 collection errors are gone, focused mutation tests
  still catch the known failure classes, `--durations=20` shows fewer redundant
  artifact refreshes, and the manuscript gate still passes.
- **Out of scope:** weakening coverage, skipping pymdp-backed evidence, or
  dropping the end-to-end refresh characterization.

---

### SCRIPTS-LOGIC-1 — Move `_discover_packages` out of `generate_api_reference_doc.py`

- **Problem:** `scripts/generate_api_reference_doc.py` implements a
  non-trivial package-discovery algorithm inline (`_discover_packages`: glob,
  filter by name prefix, exclude underscore-prefixed dirs, return sorted). This
  reusable domain operation belongs in `infrastructure.documentation` (e.g.
  `infrastructure/documentation/api_reference_gen.py`), not in the orchestrator.
- **Why it matters:** thin-orchestrator policy — scripts coordinate, modules
  implement. Inline algorithms are untested and drift from infrastructure
  patterns.
- **Smallest next step:** extract `_discover_packages` into
  `infrastructure/documentation/api_reference_gen.py`, add a unit test, and
  update the script to import from there.
- **Acceptance check:** `scripts/generate_api_reference_doc.py` contains no
  discovery logic; the extracted function has a test under
  `tests/infra_tests/documentation/`; `uv run python scripts/generate_api_reference_doc.py`
  still produces the same output.
- **Out of scope:** changing the discovery semantics or adding new documentation
  targets.

---

### SCRIPTS-LOGIC-2 — Move `_stage_label` out of `06_llm_review.py`

- **Problem:** `scripts/06_llm_review.py` implements a non-trivial stage-label
  resolution algorithm inline (`_stage_label`): iterates candidate YAML paths,
  instantiates `PipelineDAG`, searches for a stage name by index, and formats a
  label string with fallback. It also hardcodes two candidate YAML path patterns.
  This pipeline metadata logic belongs in `infrastructure.core.pipeline` (e.g.
  a `stage_label()` helper on `PipelineDAG`).
- **Why it matters:** pipeline metadata resolution spread across scripts and
  infrastructure creates divergence risk; the algorithm should live next to the
  DAG it queries.
- **Smallest next step:** add a `stage_label(index: int) -> str` helper to
  `infrastructure/core/pipeline/` (or `PipelineDAG`), cover it with a test, and
  update `06_llm_review.py` to call it.
- **Acceptance check:** `06_llm_review.py` has no inline stage-resolution logic;
  the helper is tested under `tests/infra_tests/`; existing LLM review runs
  produce identical stage labels.
- **Out of scope:** changing the stage-label format or the fallback behavior.

---

### SCRIPTS-LOGIC-3 — Move `_scan_roots` out of `verify_no_mocks.py`

- **Problem:** `scripts/verify_no_mocks.py` implements a non-trivial scan-root
  resolution algorithm inline (`_scan_roots`): combines the repo-level `tests/`
  directory with per-project `tests/` directories via `public_project_infos`,
  applies existence filtering. This belongs in
  `infrastructure.validation.output.no_mock_enforcer` or
  `infrastructure.project.public_scope`.
- **Why it matters:** which test trees are in scope for the no-mocks policy is
  domain logic — it should be tested and co-located with the enforcer, not
  repeated inline in the script.
- **Smallest next step:** extract `_scan_roots` into the enforcer module, add a
  unit test, update the script to import it.
- **Acceptance check:** `verify_no_mocks.py` contains no root-resolution logic;
  extracted function is tested; `uv run python scripts/verify_no_mocks.py` still
  identifies the same test roots.
- **Out of scope:** changing which directories are in scope.

---

### SCRIPTS-LOGIC-4 — Move statistics formatting out of `audit_filepaths.py`

- **Problem:** `scripts/audit_filepaths.py` performs inline data-shaping in its
  statistics summary loop (lines 111–123): computes `total_issues`, iterates
  `scan_results.statistics.items()`, and formats per-category output with
  `category.replace('_', ' ').title()`. This belongs in
  `infrastructure.validation.repo.audit_orchestrator` as a
  `format_audit_summary()` helper.
- **Why it matters:** formatting logic in scripts cannot be tested independently
  and drifts from how other audit tools report statistics.
- **Smallest next step:** add `format_audit_summary(stats: dict) -> str` to the
  audit orchestrator, test it, and update the script to call it.
- **Acceptance check:** `audit_filepaths.py` summary loop is replaced by a
  single helper call; the helper is tested; output format is unchanged.
- **Out of scope:** changing the human-readable category names or summary
  structure.

---

### SCRIPTS-LOGIC-5 — Move `_DEFAULT_TARGETS` out of `generate_stage_table_doc.py`

- **Problem:** `scripts/generate_stage_table_doc.py` hardcodes seven specific
  repository file paths inline in `_DEFAULT_TARGETS` (lines 43–51). This
  canonical list of documentation targets is configuration data that belongs in
  `infrastructure.documentation.stage_table` (or a config file) so the single
  source of truth is co-located with the injection logic.
- **Why it matters:** adding a new doc target requires editing both the script
  and any prose that describes which docs receive stage tables — a split
  responsibility that will drift.
- **Smallest next step:** move `_DEFAULT_TARGETS` into
  `infrastructure/documentation/stage_table.py` as a module-level constant,
  update the script to import it, add a test that the list is non-empty and
  all paths are relative strings.
- **Acceptance check:** the script contains no hardcoded path list; the constant
  lives in the module; existing injection runs produce identical output.
- **Out of scope:** adding new documentation targets or changing the injection
  logic.

---

### SCRIPTS-LOGIC-6 — Refactor mini-test-runner in `00_setup_environment.py`

- **Problem:** `scripts/00_setup_environment.py` contains a mini-test-runner
  implemented inline (lines 80–97): a `checks` list-of-tuples dispatch table,
  a loop that collects boolean results, and a pass/fail aggregation
  (`all_passed`). Each individual check delegates to infrastructure, but the
  aggregation pattern could drift from how `infrastructure.core` reports failures
  elsewhere. Minor: `log_header('Setup Summary')` on line 90 omits the `logger`
  argument present on all other `log_header` calls in the file.
- **Why it matters:** consistency — setup reporting should follow the same
  aggregation path as all other pipeline stages.
- **Smallest next step:** extract the aggregation loop into a shared helper in
  `infrastructure.core` (or reuse an existing one), fix the missing `logger`
  argument, and update the script to call it.
- **Acceptance check:** `00_setup_environment.py` has no inline aggregation
  loop; all `log_header` calls include the `logger` argument; `./run.sh
  --pipeline` still prints a correct Setup Summary.
- **Out of scope:** changing which checks run during environment setup.

---

### INFRA-TEST-PARITY-1 — Add `tests/infra_tests/docker/` test directory

- **Problem:** `infrastructure/docker/` (Dockerfile, docker-compose.yml) has
  partial coverage only via `tests/infra_tests/rendering/test_dockerfile_gen.py`
  but no dedicated `tests/infra_tests/docker/` directory. The three-tree mirror
  convention expects a parallel test tree for each infrastructure package.
- **Why it matters:** docker build correctness is not explicitly gated; a drift
  in the Dockerfile or compose file would not be caught by a targeted suite.
- **Smallest next step:** create `tests/infra_tests/docker/__init__.py` and at
  least one test (`test_docker_config.py`) that validates the Dockerfile and
  docker-compose.yml exist, are non-empty, and pass a basic structural check
  (e.g. `FROM` line present, required services declared).
- **Acceptance check:** `tests/infra_tests/docker/` exists with at least one
  passing test; overall infra coverage is unchanged or improved.
- **Out of scope:** full Docker build smoke tests in CI (those belong in a
  separate job with Docker-in-Docker).

---

### INFRA-TEST-PARITY-2 — Add test coverage for `infrastructure/logrotate.d/`

- **Problem:** `infrastructure/logrotate.d/` contains only config files
  (AGENTS.md, README.md, a logrotate template) with zero test coverage anywhere
  in the test tree. The package has no `__init__.py` but ships infrastructure
  config that should be validated.
- **Why it matters:** a broken logrotate template would silently fail in
  production deployments; there is currently no gate to catch structural errors.
- **Smallest next step:** add a test (location: `tests/infra_tests/` or a new
  `tests/infra_tests/logrotate/`) that reads the template file, confirms it is
  non-empty, and validates that it contains the expected logrotate directives
  (e.g. rotation interval, compress flag).
- **Acceptance check:** at least one test covers the logrotate template; the
  test passes; CI `test-infra` job picks it up.
- **Out of scope:** testing actual logrotate binary execution or OS-level log
  rotation.

---

## Known divergences from `CHANGELOG.md`

As of 2026-06-12 there are **no known divergences**: `pyproject.toml`,
`CHANGELOG.md`, and the published tag all agree at **`3.4.0`** (the prior
"`v3.3.1` bumped but not released" gap was resolved by cutting `v3.4.0`, which
folds the dated `[3.3.1]` entry and all post-`3.3.1` work into one published
release). The docs-lint (links/consistency/doc-pairs), drift, and canonical-facts
gates are clean.

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
