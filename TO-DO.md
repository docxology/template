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
| Bandit `-ll` (with `bandit.yaml` allow-list) | **HIGH 0 · MEDIUM 0 · LOW 0** | `uv run bandit -r -ll -c bandit.yaml infrastructure/ scripts/ projects/ --exclude projects_archive,projects_in_progress` |
| Bandit strict-LOW pass | **0 unsuppressed** | `uv run bandit -c bandit.yaml -r --severity-level low …` |
| `pip-audit` CI gate | **blocking** (allow-list: `.github/pip-audit-ignore.txt`; retries in CI) | `.github/workflows/ci.yml` → job `security` |
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

* **DOC-MERMAID-1 — Pre-existing Mermaid diagrams.**

  **Problem:** 26 `%% noqa: docs-lint — pre-existing diagram…` comments
  suppress mermaid validation on blocks that fail the repo parser/renderer.

  **Inventory (18 files, one PR-sized pass per file or small cluster):**

  | Area | Files |
  | --- | --- |
  | Root / system | [`AGENTS.md`](AGENTS.md) (2), [`infrastructure/AGENTS.md`](infrastructure/AGENTS.md), [`infrastructure/README.md`](infrastructure/README.md) |
  | Docs hub | [`docs/PAI.md`](docs/PAI.md), [`docs/RUN_GUIDE.md`](docs/RUN_GUIDE.md), [`docs/core/workflow.md`](docs/core/workflow.md), [`docs/core/literature-data-flow.md`](docs/core/literature-data-flow.md), [`docs/usage/examples.md`](docs/usage/examples.md), [`docs/architecture/decision-tree.md`](docs/architecture/decision-tree.md), [`docs/architecture/two-layer-architecture.md`](docs/architecture/two-layer-architecture.md) (4), [`docs/reference/copypasta-diagrams.md`](docs/reference/copypasta-diagrams.md) (2) |
  | GitHub docs | [`projects/template_search_project/AGENTS.md`](projects/template_search_project/AGENTS.md), [`.github/README.md`](.github/README.md) |
  | Infrastructure READMEs | [`infrastructure/documentation/README.md`](infrastructure/documentation/README.md), [`infrastructure/project/README.md`](infrastructure/project/README.md), [`infrastructure/rendering/README.md`](infrastructure/rendering/README.md) (3), [`infrastructure/scientific/README.md`](infrastructure/scientific/README.md), [`infrastructure/validation/README.md`](infrastructure/validation/README.md) (3) |

  **In scope:** Fix or replace diagrams so each block parses cleanly; delete
  the corresponding `%% noqa` line. Prefer valid Mermaid; use ASCII or static
  lists only when the graph is not expressible without lint hacks.

  **Out of scope:** Rewriting prose unrelated to the diagram; changing
  [`docs/development/roadmap.md`](docs/development/roadmap.md) MED4 wording
  (that label is the **shipped docs-lint CI job**, not this backlog — see
  [`CHANGELOG.md`](CHANGELOG.md)).

  **Acceptance:** `rg '%% noqa: docs-lint' --glob '*.md'` returns no matches;
  then `uv run python scripts/lint_docs.py` passes (all three checks).

  **Incremental check:** After each diagram fix, the two commands above should
  still pass (no new `noqa` lines).

_Shipped note — m2 (Steganography deterministic mode):_
`infrastructure.steganography.config.resolve_build_timestamp`,
`STEGANOGRAPHY_DETERMINISTIC=1` (or `secure_run.sh --deterministic`),
`tests/infra_tests/steganography/test_deterministic_mode.py`.

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

## 🔍 Tracked — scoped backlog (not scheduled)

Items here have a **default deferral** until someone picks them up; each row
states effort, why it matters, and the smallest next step.

| ID | Topic | Effort (rough) | Why | In scope (this item) | Out of scope | Next step |
| --- | --- | --- | --- | --- | --- | --- |
| **ARCH-CONFTEST-1** | Cross-project `tests/conftest.py` | Medium (½–2 days if pursued) | Multiple `conftest.py` trees in one pytest proc collide on `tests.conftest`. | Doc-only first: state the **one subprocess per project** contract in [`tests/AGENTS.md`](tests/AGENTS.md) and one allowed pattern (uniquely named `pytest_plugins` / shared import, no duplicate `tests.conftest`). Code later: optional thin helper if it does not change CI’s per-project pytest shape. | Switching CI to a single global pytest over all `projects/*/tests/` without `run_per_project_pytest`; silent `tests.conftest` collisions. | Read [`tests/AGENTS.md`](tests/AGENTS.md); add a short “Shared fixtures” subsection that names the collision failure mode and the allowed extension. |
| **DEP-DEFUSEDXML-1** | Replace `defusedxml` with hardened stdlib | Medium (1–3 days) | Drop third-party XML dep once stdlib usage is provably safe on supported Pythons. | Refactor [`infrastructure/reporting/coverage_history.py`](infrastructure/reporting/coverage_history.py), [`infrastructure/search/literature/fulltext.py`](infrastructure/search/literature/fulltext.py), [`infrastructure/search/literature/backends.py`](infrastructure/search/literature/backends.py); add regression tests on real sample XML. | Drive-by changes to unrelated parsers; blanket `# nosec B314`. | `rg defusedxml` for call sites; read CPython 3.10–3.12 notes on `xml.etree` (DTD/expansion/external entities) for the parse modes this repo uses. |
| **WIN-SETUPHOOK-1** | `setup_hook` Windows path | Small (mostly docs) | POSIX `setup_hook.sh` does not run on Windows; Python entry is required there. | Onboarding and CI stay aligned: [`docs/guides/new-project-setup.md`](docs/guides/new-project-setup.md) states Windows uses `setup_hook.py`; [`.github/workflows/ci.yml`](.github/workflows/ci.yml) `setup-hook-windows-smoke` still runs only when a matching `projects/**/scripts/setup_hook.py` exists. | Porting the shell hook to PowerShell; guaranteeing every Windows environment. | `rg setup_hook` after template changes; confirm the workflow `paths` / `if:` gates still match the doc. |

**Canonical test runner reminder (ARCH-CONFTEST-1):** one pytest subprocess
per `projects/<name>/tests/` via
`infrastructure.core.test_runner.run_per_project_pytest` and CI `test-project`.
A single pytest collecting multiple project trees with distinct `conftest.py`
files remains **unsupported**.

**Per-ID closure notes**

- **ARCH-CONFTEST-1 (doc track):** [`tests/AGENTS.md`](tests/AGENTS.md) states
  the per-project pytest rule, names the `tests.conftest` collision, and
  documents one sanctioned way to share fixtures without a second pytest
  collection root.

- **DEP-DEFUSEDXML-1:** Same inputs produce the same parsed structures as
  before; Bandit B314 clean without `# nosec` carpet-bombing; `defusedxml`
  removed from `pyproject.toml`; XML-related tests pass on real samples.

- **WIN-SETUPHOOK-1:** Doc and workflow both describe the Windows smoke job
  condition; no contradictory “POSIX-only” wording for people on Windows.

---

## ⚠️ Known divergences from `CHANGELOG.md`

_Previously_: older CHANGELOG rows claimed gates not yet wired; those items were closed in the v0.7.0 / v0.7.1 cycle. If you find a **new** drift between `CHANGELOG.md`, `TO-DO.md`, and `.github/workflows/ci.yml`, log it here and fix forward rather than rewriting shipped changelog entries.

| Past CHANGELOG claim | Closed by | Acceptance verified |
| --- | --- | --- |
| `pip-audit` blocking + ignore file | v0.7.2 | `.github/workflows/ci.yml` security job parses `.github/pip-audit-ignore.txt`; no `continue-on-error` on pip-audit |
| `pip>=26.1.1` override | v0.7.2 | `[tool.uv] override-dependencies` in root **`pyproject.toml`** |


---

## Conventions

- Every release row in `CHANGELOG.md` corresponds to a `vX.Y.Z` git tag.
- **Backlog IDs** (`DOC-MERMAID-1`, `ARCH-CONFTEST-1`, …) are stable; use
  them in commit messages or doc comments when touching related work so grep
  stays useful.
- Every TO-DO item has explicit acceptance criteria and a verifiable
  command in the **Acceptance** line (tracked-table items use **Per-ID closure
  notes** below the table).
- **Elevation:** when an item in **Tracked** gets an owner and schedule, move
  it to **Minor** or **Medium** with a target window; shrink **Tracked** to
  defer-only work.
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
