# 🚀 Repo TO-DO — active backlog

> **DESIGN ETHOS**
> Modular · Intelligent · Functional · Logged · Tested · Documented.
> Real methods only — never mocks or fakes.
> Every release ships with all tests green and all docs accurate (no
> legacy mentions).

This file tracks **only** the live backlog. Historical release notes are
in [`CHANGELOG.md`](CHANGELOG.md). Numbers below come from a live audit
run when this file was last edited.

---

## ✅ Live state snapshot

| Gate | Value | Source |
| --- | --- | --- |
| `pyproject.toml` version | `3.0.0` | `pyproject.toml#[project].version` |
| `mypy --strict infrastructure/` | **0 errors / 327 files** | `uv run mypy --strict infrastructure/` |
| `ruff check` (infra + canonical project src) | **clean** | `uvx ruff check infrastructure/ projects/template_code_project/src/` |
| `ruff format --check` | **325/325 already formatted** | `uvx ruff format --check infrastructure/ projects/template_code_project/src/` |
| Bandit `-ll` (with `bandit.yaml` allow-list) | **HIGH 0 · MEDIUM 0 · LOW 0** | `uv run bandit -r -ll -c bandit.yaml infrastructure/ scripts/ --exclude projects_archive,projects_in_progress` |
| Bandit strict-LOW pass | **0 unsuppressed** | `uv run bandit -c bandit.yaml -r --severity-level low …` |
| `pip-audit` CI gate | **blocking** (allow-list: `.github/pip-audit-ignore.txt`) | `.github/workflows/ci.yml#security` |
| Zero-Mock Policy (`scripts/verify_no_mocks.py`) | **clean** | `uv run python scripts/verify_no_mocks.py` |
| `__all__` audit (`infrastructure.skills.check_all_exports`) | **0 violations** under live `infrastructure/` | `uv run python -m infrastructure.skills check-all-exports` |
| `docs-lint` (mermaid + cross-links + consistency) | **all 3 pass** | `uv run python scripts/lint_docs.py` |
| Stage-table generator | **idempotent** (5/5 docs in sync) | `uv run python scripts/generate_stage_table_doc.py` |
| API-reference generator | **idempotent** (15 packages) | `uv run python scripts/generate_api_reference_doc.py --check` |
| Architecture overview | **regenerable** (15 pkgs + 3 config dirs + active projects) | `uv run python scripts/generate_architecture_overview.py` |
| Unified `health` command | **10/10 gates PASS** | `uv run python -m infrastructure.core.health` |
| Pre-push hooks | `ruff-ci`, `mypy-ci`, `pre-push-quick`, `bandit-quick`, `skills-check`, `all-exports-check` | `.pre-commit-config.yaml` |
| Bench harness | **7 benches green** (opt-in via `-m bench`) | `tests/infra_tests/bench/` |
| Telemetry retention (`TELEMETRY_KEEP`, default 10) | wired into `TelemetryCollector._persist_report` | `infrastructure/core/telemetry/retention.py` |
| Steganography determinism (`STEGANOGRAPHY_DETERMINISTIC=1`) | byte-identical PDFs across runs | `infrastructure/steganography/config.py` |
| Multi-project parallel exec (`--parallel --max-workers=N`) | ~2.6× speedup on 3 synthetic projects | `scripts/execute_multi_project.py` |
| Coverage trend dashboard | regenerable via `--from-dir` / `--from-gh` | `scripts/generate_coverage_history.py` |
| Project-config schema-extension API | `register_project_schema_extension(name, schema)` | `infrastructure/core/config/schema.py` |
| `tests/infra_tests/` (no LLM, no bench) | **all pass** | `uv run pytest tests/infra_tests/ -q --ignore=tests/infra_tests/llm --timeout=60` |
| `infrastructure/` Python packages | **15** + 3 non-Python config dirs (`config/`, `docker/`, `logrotate.d/`) | `ls infrastructure/` |
| Docs subdirectories with both `AGENTS.md` + `README.md` | **26 / 26** | sweep |
| Infrastructure packages with `AGENTS.md` + `README.md` + `SKILL.md` | **15 / 15** | sweep |

---

## 🟢 Minor (1–2 hours each)

_None active — m2 (Steganography deterministic mode) shipped via
`infrastructure.steganography.config.resolve_build_timestamp`,
`STEGANOGRAPHY_DETERMINISTIC=1` (or `secure_run.sh --deterministic`),
and `tests/infra_tests/steganography/test_deterministic_mode.py`._

---

## 🟡 Medium (½ – 2 days each)

_None active — MED1 (multi-project parallel execution) shipped via
`infrastructure/core/pipeline/multi_project_parallel.py` and the
`--parallel` / `--max-workers=N` CLI flags on `execute_multi_project.py`.
MED3 (coverage trend dashboard) shipped via
`infrastructure/reporting/coverage_history.py` +
`scripts/generate_coverage_history.py` (offline `--from-dir` and online
`--from-gh` modes), with an informational `coverage-history` artefact
uploaded by the `performance` job in `.github/workflows/ci.yml`._

---

## 🔍 Tracked, not yet scoped

* **Cross-project `tests/conftest.py` deduplication.** Two projects
  shipping `tests/conftest.py` collide in single-pass pytest; we work
  around it with one process per project. Long-term, give each project
  a unique conftest namespace.
* **Replace `defusedxml` with stdlib `xml.etree` + entity guards.** When
  the Python core security policy adds entity-resolution guards, drop
  the dep.
* **Project setup-hook Windows portability.** `setup_hook.sh` is
  POSIX-only; document Windows-only `setup_hook.py` more prominently
  and add a CI smoke check on Windows when a project ships either.

---

## ⚠️ Known divergences from `CHANGELOG.md`

The pre-2026-05 CHANGELOG entries v3.0.0 and v0.6.0 each claimed three
gates that were not actually shipped at the time:

| Past CHANGELOG claim | Closed by | Acceptance verified |
| --- | --- | --- |
| `pip-audit` blocking gate | this cycle (M2) | `.github/workflows/ci.yml#security` no longer has `continue-on-error: true`; allow-list at `.github/pip-audit-ignore.txt` |
| 0 MEDIUM Bandit findings | this cycle (M3) | `defusedxml` swap in `infrastructure/search/literature/{backends,fulltext}.py` + `# nosec B615` on the HF fixture script |
| `mypy --strict` for all infrastructure | this cycle (M1 + MED5) | Explicit `__all__` on every re-exporting module; `mypy --strict infrastructure/` → 0 errors / 323 files; `infrastructure.skills.check_all_exports` gates regression |

These are recorded here rather than by rewriting history. The current
`CHANGELOG.md` v0.7.0 row documents the actual remediation.

---

## Conventions

- Every release row in `CHANGELOG.md` corresponds to a `vX.Y.Z` git tag.
- Every TO-DO item has explicit acceptance criteria and a verifiable
  command in the **Acceptance** line.
- Numbers in the "Live state snapshot" table come from a live audit;
  re-baseline them — never copy stale values.
- **Bandit policy.** Repo-wide LOW-severity allow-list lives in
  [`bandit.yaml`](bandit.yaml) with per-test-ID justifications. CI runs
  both a MEDIUM+ pass and a strict LOW pass — both invoked with `-c
  bandit.yaml`. Any new LOW outside the allow-list must be either fixed
  or annotated inline with `# nosec <ID> reason: …`. See
  [`docs/rules/security.md`](docs/rules/security.md) and
  [`.github/AGENTS.md`](.github/AGENTS.md).
- **`__all__` policy.** Every re-exporting Python module under
  `infrastructure/` must define an explicit `__all__`; the
  `check-all-exports` CI gate enforces this. See
  [`docs/rules/api_design.md`](docs/rules/api_design.md).

## See also

- [`CHANGELOG.md`](CHANGELOG.md) — historical release notes
- [`docs/development/roadmap.md`](docs/development/roadmap.md) — longer-term direction
- [`.github/AGENTS.md`](.github/AGENTS.md) — CI gates and quality thresholds
- [`docs/audit/triple-check-report.md`](docs/audit/triple-check-report.md) — most recent integrity audit
