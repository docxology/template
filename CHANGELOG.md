# Changelog

All notable changes to the Research Project Template are documented here.

## [0.7.1] — 2026-05-04 (PM)

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
- **m3 — Project-metadata schema-extension hook.** New
  `register_project_schema_extension(project_name, schema)`,
  `get_project_schema_extensions(project_name)`,
  `clear_project_schema_extensions()` in
  `infrastructure/core/config/schema.py`. Validator hook in
  `loader.py` infers project name from the config path (or accepts
  explicit `project_name=`). 12 real-data tests.

### Medium

- **MED1 — Multi-project parallel execution.** New
  `infrastructure/core/pipeline/multi_project_parallel.py` exposes
  `run_projects_in_parallel(...)`. CLI flags `--parallel` and
  `--max-workers=N` added to `scripts/execute_multi_project.py`
  (default remains serial — backwards compatible). Per-worker
  stdout/stderr is redirected via `os.dup2` into
  `projects/<name>/output/logs/pipeline.log` (no parent-process
  interleaving). Observed wall-time: 6.0 s serial → 2.2 s parallel
  with 3 workers (~2.6× speedup) on 3 synthetic projects. 8 tests.
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
| `pytest tests/infra_tests/` (no LLM, no bench) | ✅ all pass |

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
  `docs/_generated/architecture_overview.{mmd,svg}` from live infra +
  project discovery.
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
- **MED2 — Project-setup-hook polish.** Optional `setup_hook.yaml`
  manifest (required tools / env vars / timeout / skip_if_env);
  `PROJECT_SETUP_HOOK_DRY_RUN=1` mode; preflight-before-invoke;
  Windows portability documented.
- **MED3 — Per-project pytest factor.** New
  `infrastructure/core/test_runner.py` lifts the open-coded
  `for d in projects/*/tests; do …` bash loop out of
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
  inject a 213-symbol catalogue into
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
| `pytest tests/infra_tests/` (no LLM, no bench) | ✅ 5347 passed |

---

## [0.6.0] — 2026-03-10

### 🧹 Code Health: Desloppify Campaign (161 commits)

The largest code-quality improvement cycle since the template's inception. Every infrastructure
package and project module was subjected to systematic blind review and remediation across
26 review rounds, eliminating all AI-generated debt, convention outliers, and structural issues.

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
- `ci.yml`: `pip-audit` now blocking; Bandit scans `infrastructure/ + scripts/ + projects/` at MEDIUM+

### Quality Gates (v3.0.0, all enforced in CI)

| Gate | Status |
| ---- | ------ |
| `ruff check` | Enforced (E501 included) |
| `ruff format --check` | Enforced |
| `mypy --strict` (validation, rendering) | Enforced |
| `mypy` (all 8 packages) | 0 errors |
| `bandit -ll` | 0 MEDIUM+ findings |
| `pip-audit` | Blocking gate |
| `pytest` (2,544 infra + 469 project) | All pass |

## [2.0.0] — 2026-02-18

### Added (v2.0.0)

- Two-Layer Architecture (Infrastructure + Projects)
- Build pipeline with thin orchestrator pattern
- Program-aware project discovery
- Executive reporting dashboard
- Standalone Project Paradigm with Graduation Pattern
