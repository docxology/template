# Changelog

All notable changes to this **template repository** (Layer 1 infrastructure, root
orchestration, CI, and repository-level docs) are documented here. This file does
not describe individual workspaces under `projects/` (many checkouts omit,
gitignore, or treat those trees as confidential); where entries mention
`projects/`, they refer to **generic layout and tooling** defined by the template,
not to the contents of any specific workspace.

## [Unreleased]

### Changed

- 🎨 **Generated-report web design + unified design system (WEBDESIGN-EXTEND-1)** —
  modernized the base HTML report/dashboard template and extracted the design
  tokens into a shared `html_templates.shared_css()` (single source of truth: CSS
  custom properties + `prefers-color-scheme` dark mode, WCAG-AA status contrast,
  fluid `clamp` type, tabular-numeric sticky tables, mobile breakpoint). All four
  generated HTML surfaces — base report, pipeline report (`pipeline_html.py`),
  interactive dashboard (`_interactive_html.py`), and the web renderer
  (`web_renderer.py`) — now anchor to the shared `--brand-1` token + a
  `prefers-color-scheme` block. Template contracts + deterministic output preserved.
- ⚡ **Fast doc link-audit (LINKCHECK-PERF-1)** — `link_audit_core.py` now prunes
  excluded/gitignored directories with `os.walk` *before* descending (no longer
  materializes `.git/`/`.venv/`/`node_modules/`) and reads each markdown file once
  instead of twice: ~15–28× faster discovery on the live checkout, same broken-link
  set. Adds a timed regression test.

### Fixed

- 📐 **TeX Live 2026 beamer compatibility (TEXLIVE-2026-BEAMER-1)** —
  `latex_utils.compile_latex` now downgrades the benign `! Illegal parameter number
  in definition of \reserved@a` kernel warning to a logged warning **when a valid
  PDF is produced**, instead of raising `CompilationError` on the non-zero exit.
  Genuine failures (missing/invalid PDF, any other error) still raise. Fixes beamer
  rendering under TeX Live 2026 while preserving fail-hard semantics.

## [3.4.0] — 2026-06-12

Comprehensive multi-pass review-and-improvement of `infrastructure/`, `docs/`,
`scripts/`, and the public exemplars (RedTeam + FirstPrinciples + SystemsThinking
lenses), the thermo-nuclear v2 remediation, and the post-`v3.3.1` backlog
closeout. All gates green; no mocks; tests added with each change.

### Added

- 🧭 **Reproducible run matrix (`run.config`)** — `scripts/run_matrix.py` +
  `infrastructure/core/pipeline/run_matrix.py`: a deterministic project × stage
  matrix runner (resolves projects, orders stages canonically), the
  version-controllable alternative to the interactive menu. `run.config.example.yaml`
  shipped; the user's `run.config` is git-ignored.
- ⏱️ **`SOURCE_DATE_EPOCH` determinism** — `infrastructure/core/determinism.py`
  threads a reproducible build timestamp through xelatex `/CreationDate`,
  manuscript `GENERATION_TIMESTAMP`, and data `generated_at` (opt-in via
  `TEMPLATE_DETERMINISTIC`/`SOURCE_DATE_EPOCH`; no-op otherwise) for byte-stable outputs.
- 🔢 **Generated `COUNTS.md` + CI `--check`** — `scripts/generate_counts.py` +
  `infrastructure/documentation/counts_doc.py` derive the canonical counts from
  the live tree, closing the long-standing doc-drift loop (`canonical_facts.md`
  was the one `_generated/` file with no generator). Renamed `canonical_facts.md`→`COUNTS.md`.
- 🚪 **Opt-in methods-plan gate** — `scripts/gates/methods_plan_check.py` enforces
  the previously-unenforced methods publication contract.
- 🔬 **Deep research dispatch** (`infrastructure/search/deep_research`) — opt-in,
  paid multi-provider deep-research CLI; fail-fast provider validation + bounded
  wait (`max_wait_seconds`/`DeepResearchWaitTimeout`) + `cancel`.
- 🔐 **Kmyth TPM adapter + NSA `kmyth` submodule** on the steganography surface.

### Changed

- 🏷️ **Exemplar-support tier** — `infrastructure/sia` and `infrastructure/scientific`
  tagged as Layer-1-but-exemplar-only in their docs and the module roster.
- 🔀 **Validation ↔ autoresearch decoupling** — the generic validation layer no
  longer special-cases the domain-specific autoresearch module.
- 🗂️ **`scripts/` reorg** — operator tooling grouped under `scripts/maintenance/`
  (numbered pipeline stages + gates kept at root).
- 🧩 **Output-validation + reporting modularization**; benchmark test rename.

### Removed

- 🧹 **Dead modules deleted** (zero production importers, re-verified): `core/menu.py`,
  `validation/cli/markdown.py`, `rendering/poster_renderer.py`, and
  `scientific/{templates,documentation,validation}.py`.

### Fixed

- 🔒 **Confidentiality guard** — `projects/*.md` wildcard replaced with an explicit
  nav-doc allowlist so a stray top-level markdown can't be tracked.
- 🧪 **No-mocks enforcer** — rewritten as AST + comment/string-stripped scan,
  closing trailing-comment / `mock_`-prefix / `from unittest import mock` bypasses.
- 📦 **Repro bundle (REPRO-VERIFY-1)** — output paths rebased onto the project tree
  so `verify` actually hashes artifacts and fails closed on declared-but-absent outputs.
- 🧷 **Evidence-graph claims (EVIDENCE-CLAIM-1)** — `output/data/*claims*.json` glob
  so the autoresearch exemplar's ledger is ingested as claim nodes + `supports` edges.
- 🧰 Default-project selection (qualified names), `--stage clean` mismatch,
  book-length `book.title` metadata, markdown-CLI repo-root, arXiv old-style IDs,
  and Ollama tests using the discovered model instead of a hard-coded `gemma3:4b`.
- 📦 **Correction to [3.3.1] "Public-exemplar outputs tracked"** — tracked
  `output/` render proofs were removed on 2026-06-08; the repo ships no committed
  `output/` artifacts. Supersedes the 3.3.1 "outputs tracked" claim below.

## [3.3.1] — 2026-06-07

### Fixed

- 📄 **DOCX output completion** — Pandoc DOCX rendering now embeds figures and
  resolves cross-references (`infrastructure/rendering/pipeline.py`).
- 🔢 **Generated-count reconciliation** — `docs/_generated/COUNTS.md`
  project-scope collection count refreshed to 216 after test additions.

### Changed

- 📦 **Public-exemplar outputs tracked** — refreshed rendered `output/` artifacts
  for the public template exemplars are committed alongside the source so the
  repository ships reproducible, inspectable deliverables.

## [3.3.0] — 2026-06-07

### Added

- 🔎 **Reference-existence verification** (`infrastructure/reference/verification`) —
  deterministic anti-hallucination gate that resolves each cited reference against
  Crossref → OpenAlex / arXiv, classifying it `ok` / `mismatch` / `fabricated` /
  `unverifiable` / `unchecked` / `anachronism`. Offline-first with a persistent
  SQLite cache; live resolution is opt-in. CLI: `python -m infrastructure.reference.verification verify <bib>`.
- ✍️ **AI-writing fingerprint detector** (`infrastructure/validation/content/ai_writing.py`,
  `validation.cli prose-quality`) — flags AI-typical phrasing, em-dash density, and
  low sentence-length burstiness. Both distilled clean-room from Academic Research
  Skills ideas (CC-BY-NC-4.0); no code vendored.
- 🕸️ **Evidence graph** (`infrastructure/reporting/evidence_graph.py`) — typed
  producer/consumer/validator/claim/artifact graph assembled from the real stage DAG,
  with a query API and byte-stable JSON (EVIDENCE-GRAPH-1).
- 📦 **Reproduction bundle** (`infrastructure/publishing/repro_bundle.py`,
  `scripts/10_repro_bundle.py`) — deterministic repro manifest (lockfile, artifact
  hashes, canonical-facts pointer, repro command) plus a fail-closed verifier (REPRO-BUNDLE-1).
- 📊 **Release-readiness dashboard** (`infrastructure/reporting/release_readiness.py`) —
  local, no-network report aggregating docs-lint, coverage/test facts, pipeline
  snapshots, evidence-graph status, and release metadata (DASHBOARD-1).
- 🧩 **Pipeline plugin stages** (`infrastructure/core/pipeline/plugins.py`) — schema-validated
  `projects/{name}/pipeline_plugins.yaml` adds DAG stages without core edits. Opt-in;
  default plan unchanged (PLUGIN-STAGES-1).
- ⏭️ **Incremental pipeline skipping** (`infrastructure/core/pipeline/incremental.py`,
  `IncrementalConfig`) — content-hash stage skipping with downstream invalidation and
  fail-safe (never skip when outputs absent). Opt-in, default-off (INCREMENTAL-PIPELINE-1).

### Changed

- ⚡ **Parallel infrastructure tests** — CI `test-infra` runs with `pytest-xdist -n auto`
  (~892s → ~585s per leg); suite verified parallel-safe.
- 🧬 **Dynamic CI project matrix** — `test-project` derives its matrix from
  `infrastructure.project.public_scope` via `fromJSON` (`detect-projects` job), so
  adding/retiring a `templates/` exemplar no longer edits the matrix literal (CI-MATRIX-DYNAMIC-1).
- 🔇 **Quieter terminal logging** — console handler floors at INFO (no DEBUG/spinner
  chrome on stdout) while the file handler retains timestamped DEBUG; per-file render
  internals demoted to DEBUG; default `-v` dropped from pytest `addopts` (LOG-CLEAN-1).
- 🧱 **Consolidated safe markdown reader** — `infrastructure/validation/docs/_io.py`
  hosts `read_markdown`; doc linters route their read-and-skip sites through it (READFILE-SAFE-1).
- 📚 **Documentation accuracy passes** — deep audit + fixes across `docs/` and every
  `infrastructure/*/{SKILL,README,AGENTS}.md`, correcting examples that cited
  methods/params/CLI flags/test paths that no longer exist; new deterministic infra is
  wired into the `docs/prompts` workflows.

## [3.2.0] — 2026-06-04

### Added

- 🧭 **Agentic-use workflow routing** — Added `template-agentic-use` as a
  first-party workflow for skill discovery, local routing, agent onboarding,
  contract/eval checks, and external-skill review without vendoring companion
  skills into the public repository.
- 🧪 **Skill eval coverage** — Extended the trigger eval set, eval harness
  configuration, mode registry, generated skill index, and editor skill
  manifest so requests such as "make template more agentic", "find relevant
  skills", and "improve agent routing" route through the new workflow.
- 🔍 **Public documentation audit** — Added advisory RedTeam-style helpers and
  a CLI for inventorying public Markdown, volatile project roster/count claims,
  verifier claims without nearby negative controls, and Python symbol
  docstring coverage across public CI source paths.
- 🧠 **Decision-memory contract** — Added a repository rule for WHY comments,
  ADRs, local agent memory, failure autopsies, selective ignorance, and negative
  controls, plus consistency checks that require key workflow docs and public
  exemplar AGENTS files to link back to that contract.
- 📚 **Active Inference scholarship traceability** — Added a source-backed
  scholarship matrix builder, scholarship track registration, manuscript
  scholarship sections, figure wiring, references, and tests for the
  `template_active_inference` exemplar.

### Changed

- 🧱 **Agent-facing docs** — Refreshed AGENTS/README guidance across root,
  docs, scripts, tests, infrastructure validation, public exemplars, and
  prompt workflows so agents can locate rules, public-scope boundaries, and
  decision-memory expectations without relying on stale path lore.
- 🚀 **Rendering and validation plumbing** — Tightened rendering pipeline
  behavior, documentation lint integration, accuracy checks, link extraction,
  and Active Inference output-check/gate surfaces to keep generated claims
  connected to source contracts.
- 🧾 **Release metadata** — Bumped the repository package and citation metadata
  to `3.2.0`.

### Fixed

- 🔐 **Public-scope drift risk** — Added explicit audit paths for hard-coded
  public exemplar rosters/counts and for verifier prose that claims enforcement
  without naming a known-wrong fixture or negative-control path.
- 🧰 **Agent memory ergonomics** — Expanded core agent-memory tests and docs so
  local-only memory remains useful for agents while staying out of committed
  public repository state.
- ✅ **Scholarship/manuscript consistency** — Connected Active Inference
  scholarship references, manuscript sections, sheaf track metadata, claim
  ledger entries, visualizations, and tests so literature anchors are checked
  as part of the exemplar's public source surface.

## [3.1.0] — 2026-05-30

### Added

- **SIA public exemplar** — Added `projects/templates/template_sia/` plus
  `infrastructure.sia`, project contracts, tests, docs, generated module guide,
  and CLI validation for the `mini_classify` task.
- **Active Inference semantic sheaf hardening** — Added semantic gluing,
  dependency-graph, evidence-crosswalk, policy-comparison, graph-world, and
  animation coverage so the exemplar now carries machine-checkable manuscript
  and output contracts beyond static prose.
- **Folder-doc and stale-path guardrails** — Extended documentation consistency
  checks so public exemplar docs, generated facts, and folder-level
  `AGENTS.md`/`README.md` pairs are checked across all six public templates.
- **Interactive simulation dashboard groundwork** — Kept the project-agnostic
  dashboard and invariant infrastructure in the release train, including
  plaintext-validatable dashboard artefacts and real-data tests.

### Changed

- **Public project signposting** — Migrated long-lived documentation,
  generated indexes, workflow docs, archived audit notes, and skill-eval
  fixtures from stale `projects/template_*` paths to canonical
  `projects/templates/template_*` paths.
- **Generated facts and skills** — Refreshed `docs/_generated/active_projects.md`,
  `COUNTS.md`, `publication_records.md`, the architecture overview,
  API reference, skill manifest, and skill index from live repository state.
- **Release metadata** — Bumped the repository package and citation metadata to
  `3.1.0`.
- **Entry-point docs** — Tightened `README.md`, `CLAUDE.md`, `AGENTS.md`,
  `.github/README.md`, and workflow docs around public scope, pipeline stages,
  coverage gates, release behavior, and private-project boundaries.

### Fixed

- **Multi-project coverage corruption** — Project pytest subprocesses now pin
  `coverage` to the workspace version before appending into `.coverage.project`,
  preventing mixed project virtualenvs from corrupting the shared SQLite trace.
- **Documentation lint blind spots** — Unqualified public exemplar links are no
  longer suppressed as intentionally local, and ghost-path checks now treat
  `projects/template_*` as stale public paths.
- **Public source gates** — Narrowed broad exception handling and fixed type
  issues in the code and Active Inference exemplars so Ruff and mypy remain
  clean across public source paths.
- **Generated output stability** — Normalized PNG writes atomically and made
  simulation logging recreate missing parent directories after fresh-output
  cleanup.

## [0.7.2] — 2026-05-05

### CI / GitHub

- **pip-audit (blocking):** CI parses `.github/pip-audit-ignore.txt` into `--ignore-vuln` flags, retries up to three times on failure, and fails the job on remaining findings. Root **`tool.uv.override-dependencies`** adds **`pip>=26.1.1`** so the lock does not pin a vulnerable pip pulled in via **pip-audit** → **pip-api**.
- **Bandit:** CI invokes **`bandit -c bandit.yaml`** over the same configured roots as before (`infrastructure/`, `scripts/`, optional `projects/` tree per workflow excludes). **`bandit-quick`** pre-push hook matches that scope.
- **Manual CI dispatch:** Removed unused `workflow_dispatch.inputs.project` from **`ci.yml`**.
- **Release workflow:** Set **`generate_release_notes: false`** so the git-log **`body_path`** is not duplicated by GitHub auto-notes.
- **Dependency bumps (security):** `black`, `cryptography`, `pillow`, `pygments`, `pypdf`, `pytest`, `requests`, `werkzeug` refreshed in **`uv.lock`** to satisfy pip-audit.
- **Docs:** `.github/AGENTS.md`, `.github/README.md`, `.github/workflows/{AGENTS,README}.md`, stale-issue parity (`do-not-close` on issues), PR template CI parity, issue-template fork note.

---

### 🧹 Wave-3 backlog: 6 items closed (m1–m3 minor, MED1–MED3 medium)

All forward-looking items in the v0.7.0 TO-DO are now shipped. Every
gate in the "Live state snapshot" table of `TO-DO.md` is green via
`uv run python -m infrastructure.core.health`.

### Minor

- **m1 — Telemetry retention.** New
  `infrastructure/core/telemetry/retention.py` (`rotate(reports_dir,
  keep=…)`); collector wires through `TELEMETRY_KEEP` env var (default
  10). Older `telemetry.json` files archive into
  `<reports_dir>/.history/telemetry-<unix_ts>.json` deterministically.
  10 real-data tests.
- **m2 — Steganography deterministic mode.** New
  `infrastructure.steganography.config.resolve_build_timestamp(...)`
  honors `STEGANOGRAPHY_DETERMINISTIC=1` (or
  `secure_run.sh --deterministic`) → reads `git log -1 --format=%cI`
  for the build timestamp, falls back to wall-clock with a warning.
  Wired through metadata, overlays, barcodes, hashing, encryption.
  Two consecutive `secure_run.sh` invocations now produce
  byte-identical output PDFs (verified end-to-end). 8 real-data tests.
- **m3 — Config schema-extension hook (per workspace root).** New
  `register_project_schema_extension(project_name, schema)`,
  `get_project_schema_extensions(project_name)`,
  `clear_project_schema_extensions()` in
  `infrastructure/core/config/schema.py`. Validator hook in
  `loader.py` infers the workspace segment from the config path (or accepts
  explicit `project_name=`). 12 real-data tests.

### Medium

- **MED1 — Multi-project parallel execution.** New
  `infrastructure/core/pipeline/multi_project_parallel.py` exposes
  `run_projects_in_parallel(...)`. CLI flags `--parallel` and
  `--max-workers=N` added to `scripts/execute_multi_project.py`
  (default remains serial — backwards compatible). Per-worker
  stdout/stderr is redirected via `os.dup2` into each workspace's
  `…/output/logs/pipeline.log` under the configured projects root (no
  parent-process interleaving). Observed wall-time improvement in fixture
  runs: serial vs parallel with multiple workers (~2–3× in synthetic
  multi-workspace tests). 8 tests.
- **MED2 — Unified `health` command.** New
  `infrastructure/core/health.py` with `GateResult`, `HealthReport`,
  `run_health_checks(...)`, and `python -m infrastructure.core.health`
  CLI. Runs 10 gates (mypy, ruff, ruff-format, bandit, no-mocks,
  all-exports, docs-lint, stage-table, api-reference,
  architecture-overview) and prints a colored status table. `--json`
  emits machine-readable output. New informational `health` CI job
  uploads `health-report.json` as an artefact. 14 tests.
- **MED3 — Coverage trend dashboard.** New
  `infrastructure/reporting/coverage_history.py` with
  `parse_coverage_xml`, `collect_history_from_dir`,
  `collect_history_via_gh`, `build_history_markdown`. Driver:
  `scripts/generate_coverage_history.py` (offline `--from-dir` and
  online `--from-gh` modes). Generated
  `docs/_generated/coverage_history.md` includes a 30-day rolling
  table + ASCII sparkline. CI uploads `coverage-history` artefact. 15
  tests using `defusedxml`.

### Quality gates (v0.7.1, all enforced — `uv run python -m infrastructure.core.health`)

| Gate | Status |
| ---- | ------ |
| `mypy --strict infrastructure/` | ✅ 0 errors / 327 files |
| `ruff check` | ✅ clean |
| `ruff format --check` | ✅ 325 already formatted |
| `bandit -ll -c bandit.yaml` | ✅ 0 HIGH / 0 MEDIUM / 0 LOW |
| `verify_no_mocks.py` | ✅ no mocks |
| `infrastructure.skills check_all_exports` | ✅ 0 violations |
| `scripts/lint_docs.py` | ✅ mermaid + links + consistency |
| Stage-table + API-reference + architecture generators | ✅ idempotent |
| `uv run pytest tests/infra_tests/` (no LLM, no bench) | ✅ all pass |

---

## [0.7.0] — 2026-05-04

### 🧹 Reconciliation cycle: 14 backlog items closed (M1–M7 + MED1–MED7)

This cycle reconciles the live repo state with the gates the v3.0.0 row
had previously claimed but not actually shipped. Every claim in the
"Live state snapshot" table of `TO-DO.md` is verifiable from a single
command (linked in that table).

### Foundation (closed inline)

- **M1 — `mypy --strict` `__all__` re-export fix.** Added explicit
  `__all__` to `infrastructure/core/exceptions.py`,
  `infrastructure/core/runtime/environment.py`,
  `infrastructure/rendering/latex_package_validator.py`. Typed missing
  generic in `infrastructure/rendering/_pdf_pandoc_engine.py`. Result:
  `mypy --strict infrastructure/` → **0 errors / 323 files**.
- **M2 — `pip-audit` blocking gate.** Removed `continue-on-error: true`
  from the security job's `pip-audit` step in
  `.github/workflows/ci.yml`. Added per-CVE allow-list at
  `.github/pip-audit-ignore.txt` (empty by default). Documented in
  `.github/AGENTS.md`.
- **M3 — Bandit MEDIUMs closed.** `xml.etree.ElementTree` →
  `defusedxml.ElementTree` in `infrastructure/search/literature/{backends,fulltext}.py`;
  `# nosec B615` with rationale on the HF fixture script. Result:
  `bandit -ll` → **HIGH 0 · MEDIUM 0 · LOW 0** (with `bandit.yaml`).

### Wave 2 (parallel agents)

- **M4 — Bandit LOW triage.** Repo-wide allow-list in `bandit.yaml`
  with per-test-ID justifications. Both MEDIUM+ and strict-LOW CI
  passes invoke `-c bandit.yaml`. No genuine code fixes were necessary;
  every flagged pattern is either a research-context norm (`B311`,
  `B404`, `B607`) or a typed-only re-export (`B405`).
- **M5 — Pre-push parity.** New hooks `bandit-quick`, `skills-check`,
  `bandit-low` (manual), `all-exports-check` in
  `.pre-commit-config.yaml` mirror CI gates locally.
- **M6 — Architecture overview generator.** New
  `infrastructure/documentation/architecture_overview.py` +
  `scripts/generate_architecture_overview.py` produce
  `docs/_generated/architecture_overview.{mmd,svg}` from live infra and
  workspace-root discovery (layout only; no workspace contents).
- **M7 — Roadmap freshness.** Re-baselined
  `docs/development/coverage-gaps.md` and
  `docs/development/roadmap.md`; date-stamped audit reports;
  `docs/audit/archived/` scaffold added.
- **MED1 — Stage-table single source of truth.** New
  `infrastructure/documentation/stage_table.py` +
  `scripts/generate_stage_table_doc.py` inject a deterministic
  Markdown table from `infrastructure/core/pipeline/pipeline.yaml`
  into 5 docs via `<!-- BEGIN:STAGE_TABLE --> … <!-- END:STAGE_TABLE -->`
  markers.
- **MED2 — Workspace setup-hook polish.** Optional `setup_hook.yaml`
  manifest (required tools / env vars / timeout / skip_if_env);
  `PROJECT_SETUP_HOOK_DRY_RUN=1` mode; preflight-before-invoke;
  Windows portability documented.
- **MED3 — Per-workspace pytest driver.** New
  `infrastructure/core/test_runner.py` lifts the open-coded
  shell loop over discovered test directories out of
  `.github/workflows/ci.yml#test-project` into a tested infrastructure
  function. CI workflow now calls
  `scripts/01_run_tests.py --project-only --all-projects`.
- **MED4 — Documentation linter.** New
  `infrastructure/validation/docs/{mermaid_lint,cross_link_lint,consistency_lint}.py`
  + `scripts/lint_docs.py` + new `docs-lint` CI job. Detects
  parallelogram-syntax abuse, broken cross-links (with inline-code
  spans correctly excluded), and stale "N Python packages" claims.
- **MED5 — `__all__` audit.** New
  `infrastructure/skills/check_all_exports.py` (AST-based) flags
  any module that re-exports without an explicit `__all__`. 13
  modules got new `__all__` lists. CI gate + pre-push hook.
- **MED6 — Bench harness.** Opt-in `tests/infra_tests/bench/`
  (`-m bench`) measures `find_setup_hook` (~6 µs), no-op
  `run_project_setup_hook` (~10 µs), trivial-subprocess hook
  (~21 ms), and `run_analysis_pipeline` at N=1/5/25 (~30/150/737 ms).
  Informational CI step + `bench-results.json` artefact upload.
- **MED7 — API-reference auto-generation.** New
  `infrastructure/documentation/api_reference_gen.py` +
  `scripts/generate_api_reference_doc.py` walk every `__all__` and
  inject a generated symbol catalogue into
  `docs/reference/api-reference.md`. CI `--check` gate.

### Restored architecture

- `infrastructure/core/analysis_pipeline.py` (Stage-02 runner) was
  silently overwritten during parallel edits; restored, plus its
  7-test no-mocks suite, plus re-thinned `scripts/02_run_analysis.py`.

### Quality gates (v0.7.0, all enforced)

| Gate | Status |
| ---- | ------ |
| `ruff check` (E501 included) | ✅ enforced |
| `ruff format --check` | ✅ enforced |
| `mypy --strict infrastructure/` | ✅ 0 errors / 323 files |
| `bandit -ll -c bandit.yaml` | ✅ 0 HIGH / 0 MEDIUM / 0 LOW |
| `pip-audit` | ✅ blocking |
| `infrastructure.skills.check_all_exports` | ✅ 0 violations |
| `scripts/lint_docs.py` | ✅ 0 issues across mermaid + links + consistency |
| Stage-table & API-reference generators | ✅ idempotent |
| `uv run pytest tests/infra_tests/` (no LLM, no bench) | ✅ 5347 passed |

---

## [0.6.0] — 2026-03-10

### 🧹 Code Health: Desloppify Campaign (161 commits)

The largest code-quality improvement cycle since the template's inception. All
`infrastructure/` packages and repository-level scripts were subjected to
systematic blind review and remediation across 26 review rounds, eliminating
AI-generated debt, convention outliers, and structural issues; tracked exemplar
layouts were aligned where they share code with Layer 1.

### Fixes

- **Import hygiene**: Removed unused imports across 8+ files; separated `TYPE_CHECKING` guarded imports from runtime imports; eliminated `sys.path` mutations from CLI modules
- **Exception handling**: Narrowed broad `except Exception` / bare `except` clauses throughout `integrity.py`, `logging_utils`, `config_loader`, and `llm` modules; fixed silent `JSONDecodeError` swallowing; restored exception context with `raise ... from exc`
- **Dead code removal**: Deleted orphaned `coverage_reporter.py` (zero importers); removed stub/passthrough wrapper methods across 10+ modules; eliminated dead HTML-entities dict from `InputSanitizer`
- **Type annotations**: Modernised legacy `typing` imports (`List[x]` → `list[x]`, `Optional[x]` → `x | None`) across 30+ modules; added `TypedDict` returns for integrity results; annotated CLI re-exports
- **API surface**: Consolidated `OllamaClientConfig` env-read wrappers (ABS-001); merged duplicate `PerformanceMetrics` naming conflict; removed `ProjectLogger` pure-forwarder abstraction; eliminated `calculate_file_hash` re-export from publishing boundary
- **Bug fixes**: Fixed inverted `scan_errors` bool in doc scanner; fixed stall-detection dead branch in pipeline reporter; fixed `config_files` path bug in `config_cli`; fixed `clean_output_directory` return type; fixed broken accessor imports after `core.py` hub elimination
- **Structural**: Eliminated `infrastructure/core/core.py` hub (delegated `validate_markdown_cli` to canonical location); extracted `_build_stage_list` to remove stage-list duplication; moved `MultiProjectResult` to `TYPE_CHECKING` to break `reporting→core` circular dep
- **Logging**: Removed nosy debug logs from LLM and environment modules; downgraded verbose entry logs; added `get_logger` to logic modules lacking structured logging
- **docstrings**: Stripped AI-generated boilerplate docstring bloat from 40+ functions; removed restating comments; cleaned banner comments
- **Tests**: Fixed test name collisions; added deterministic tests for `validate_review_quality` and exception types; added integration tests to `testpaths`; removed orphan test files
- **Dependencies**: Removed `scipy` from infrastructure env check; resolved stale findings in `psutil` guards; moved `matplotlib` to optional dep group

### Quality Gates (v0.6.0)

| Gate | Status |
| ---- | ------ |
| Desloppify blind reviews | **26 rounds completed** |
| Commits | **161** |
| Files changed | **948** |
| `ruff check` | ✅ Enforced |
| `mypy --strict` | ✅ 0 errors |
| `bandit -ll` | ✅ 0 MEDIUM+ findings |
| `pytest` | ✅ All pass |

---

## [3.0.0] — 2026-02-22

### 🎉 Production/Stable Release

Promoted from **Beta** to **Production/Stable** after completing comprehensive
quality gates across all 8 infrastructure packages (126 source files).

### Added (v3.0.0)

- **v2.12.0 — Ruff Format Enforcement**: Auto-formatted 280 files; `ruff format --check` blocking CI gate
- **v2.13.0 — mypy Strict Enforcement**: 140→0 errors in `validation/` (22 files) + `rendering/` (12 files); `disallow_untyped_defs = true` overrides
- **v2.14.0 — Security Hardening**: 7→0 MEDIUM Bandit findings (CWE-400, CWE-502, CWE-377); `pip-audit` blocking CI gate; Bandit `-ll` threshold
- **v2.15.0 — CI & Container Modernization**: Dockerfile `python:3.12` + `uv`; mypy pre-commit hook; docker-compose healthchecks
- **v2.16.0 — E501 Line Length Enforcement**: E501 removed from ruff ignore list; 342 code-line + 36 docstring per-file-ignores
- **v3.0.0 — Major Version Bump**: mypy strict for all 8 infrastructure packages (126 files, 0 errors); version 3.0.0; Production/Stable classifier

### Changed (v3.0.0)

- `pyproject.toml` version: `2.0.0` → `3.0.0`
- Classifier: `Development Status :: 4 - Beta` → `Development Status :: 5 - Production/Stable`
- Dockerfile: `python:3.11-slim` + `pip` → `python:3.12-slim` + `uv`
- docker-compose.yml: Removed deprecated `version` key; added Ollama healthcheck
- `.pre-commit-config.yaml`: Added mypy hook; ruff `v0.8.4` → `v0.9.7`; pre-commit-hooks `v4.6.0` → `v5.0.0`
- `ci.yml`: `pip-audit` now blocking; Bandit scans `infrastructure/`, `scripts/`, and (when present) the configured `projects/` roots at MEDIUM+

### Quality Gates (v3.0.0, all enforced in CI)

| Gate | Status |
| ---- | ------ |
| `ruff check` | Enforced (E501 included) |
| `ruff format --check` | Enforced |
| `mypy --strict` (validation, rendering) | Enforced |
| `mypy` (all 8 packages) | 0 errors |
| `bandit -ll` | 0 MEDIUM+ findings |
| `pip-audit` | Blocking gate |
| `pytest` (infra suite; workspace suites per CI matrix) | All pass |

## [2.0.0] — 2026-02-18

### Added (v2.0.0)

- Two-layer layout (shared infrastructure + optional per-workspace trees)
- Build pipeline with thin orchestrator pattern
- Program-aware discovery of workspace roots under the configured `projects/` layout
- Executive reporting dashboard (multi-workspace orchestration)
- Standalone workspace lifecycle pattern (promote / archive) for local trees
