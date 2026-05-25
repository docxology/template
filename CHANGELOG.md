# Changelog

All notable changes to this **template repository** (Layer 1 infrastructure, root
orchestration, CI, and repository-level docs) are documented here. This file does
not describe individual workspaces under `projects/` (many checkouts omit,
gitignore, or treat those trees as confidential); where entries mention
`projects/`, they refer to **generic layout and tooling** defined by the template,
not to the contents of any specific workspace.

## [Unreleased]

### Changed

- **Entry-point docs** — Expanded [`.cursorrules`](.cursorrules) (now tracked),
  [`README.md`](README.md), [`CLAUDE.md`](CLAUDE.md), and [`AGENTS.md`](AGENTS.md)
  with clearer roles, pre-commit/CI commands, `_generated/` ground truth, and an
  **For assistants** section in `AGENTS.md`. Removed `.cursorrules` from
  [`.gitignore`](.gitignore).

- **Bandit** — `bandit.yaml` now sets `exclude_dirs` for `projects_archive`,
  `projects_in_progress`, `.venv`, and `site-packages` so pre-push/CICD scans
  authored code only (local per-project virtualenvs no longer trigger
  multi-minute runs). CI, pre-commit, and docs use the same config via `-c
  bandit.yaml` without a separate `--exclude` CLI list.

### Added

- **Interactive simulation dashboards** — new project-agnostic infrastructure
  module ``infrastructure.reporting.interactive_dashboard`` (``InteractiveDashboard``,
  ``Panel``, ``Control``, ``Invariant``) builds self-contained Plotly HTML
  dashboards with multiple linked views, live controls, and plaintext-validatable
  numerical invariants. Zero new Python dependencies (Plotly via CDN). Companion
  ``invariants.txt`` + ``summary.txt`` + ``payload.json`` artefacts let CI / agents
  validate without a browser. Eight invariant kinds: ``equal``, ``le``, ``ge``,
  ``in_range``, ``monotone_increasing``, ``monotone_decreasing``, ``finite``,
  ``nonneg``, ``array_close``.
- **Per-project ``build_dashboard.py`` scripts** — every active exemplar under
  ``projects/`` now ships a CLI-configurable interactive dashboard:
  - ``actinf_policy_entanglement_lean`` — 6 panels, 3 live controls, 47
    invariants (Ising MI, free energy, optimal λ, phase classifier, marginal
    entropy, Theorem 4.1 decomposition witness, coupling-pays verdict,
    Theorem 6.4 e-geodesic affine slope).
  - ``template_code_project`` — 5 panels, 2 live controls, 22 invariants
    (gradient finite-difference agreement, monotone descent for stable α,
    closed-form-minimum agreement, trajectory monotonicity).
  - ``what_is_cogsec`` — 5 panels, 2 live controls, 11 corpus invariants
    (schema, uniqueness, year range, decade buckets, category coverage).
  - ``template_search_project`` — 5 panels, 11 search-coverage invariants
    (DOI/abstract/year coverage floors, keyword distribution, year plausibility).
- **CLI override layer for ``simulate_pymdp.py``** — every ``simulation.hyperparameters``
  knob (K, γ, coupling λ, sweep grid, rollout, observations, seed) is now a
  CLI flag while preserving bit-exact backwards compatibility.
- **CLI on ``parameter_sweep.py``** — λ grid, utilities, phase thresholds, and
  Schmidt tolerance are now overridable.
- **Numerical invariants modules** — ``src/lean/invariants.py``
  (actinf), ``src/invariants.py`` (template_code),
  ``src/analysis/corpus_invariants.py`` (what_is_cogsec),
  ``src/search_invariants.py`` (template_search_project) provide pure-compute
  invariant builders that drive both the dashboard and the test suite.
- **Comprehensive infrastructure tests** — ``tests/infra_tests/reporting/``
  ``test_interactive_dashboard.py`` adds 62 tests covering every Invariant
  kind (pass + fail paths), every Control kind, JSON/numpy serialisation,
  HTML+JSON round-trip, plaintext rendering, and JS syntax of every
  ``Panel.update_fn`` (when ``node`` is available).

### Fixed

- **Pytest orchestration:** ``pipeline_test_runner`` and
  ``infrastructure.core.test_runner.run_per_project_pytest`` now emit one
  combined ``-m`` expression (including ``not bench`` by default), aligned
  with ``pyproject.toml`` addopts for subprocess invocations that would
  otherwise collect benchmark tests under the global timeout.

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
