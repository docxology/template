# Thermo-nuclear code quality audit — 2026-05-29

Repo-wide maintainability review of public `template/` (Layer 1, public exemplars,
gates, branch delta). Rubric: thermo-nuclear-code-quality-review skill (cursor-team-kit).

**Scope:** `infrastructure/`, `scripts/`, `projects/templates/*` (PUBLIC_PROJECT_NAMES).
Excluded: local `projects/active/*` symlinks, disposable `output/` trees.

**Verdict:** **Remediation waves 1–12 complete (2026-05-29)** — blockers and TN-H/M items
addressed; full `template_autoresearch_project` package restructure deferred (fail-fast
hydration only).

---

## Remediation wave log (2026-05-29)

| Wave | Scope | Status |
| --- | --- | --- |
| 1 | Pytest union builder, `load_project_pyproject`, `coverage_policy`, fail-loud suite runner | **Done** |
| 2 | `markdown_strip.py`, `prerender.py` validation leaf | **Done** |
| 3 | `pdf_locator` dedupe, executive report collapse, drift AST | **Done** |
| 4 | Doctor read-only probes, drift registry, scoped pycache walk | **Done** |
| 5 | `literature/` backends package split + HTTP mixin | **Done** |
| 6 | `doctor/detectors/` package + registry | **Done** |
| 7 | `_dashboard_charts_{health,pipeline,outputs}.py` | **Done** |
| 8 | `symbols.py`, `_latex_log_parse.py`, config-driven citation | **Done** |
| 9 | `template_template.paths.locate_repo_root` | **Done** |
| 10 | `z_generate_manuscript_variables.py` fail-fast | **Partial** — full src package move deferred |
| 11 | `template_code_project` `dashboard.cli_main` | **Done** |
| 12 | TO-DO/audit sync, API reference regen, gates | **Done** |

## Phase 1 gate baseline (measured 2026-05-29 UTC)

| Gate | Command | Result |
| --- | --- | --- |
| Unified health | `uv run python -m infrastructure.core.health` | **PASS** (11/11) |
| Drift (strict) | `uv run python scripts/check_template_drift.py --strict` | **PASS** |
| Line count | `uv run python scripts/gates/module_line_count_check.py` | **PASS** (0 warn infra/scripts) |
| No mocks | `uv run python scripts/verify_no_mocks.py` | **PASS** |
| Docs lint | `uv run python scripts/lint_docs.py` | **PASS** |
| Mypy (CI scope) | `uv run python -m infrastructure.project.public_scope source-paths \| xargs uv run mypy` | **PASS** |
| Infra tests | `uv run pytest tests/infra_tests/ -q --ignore=tests/infra_tests/llm --timeout=120` | **PASS** (after canonical_facts refresh) |
| Public exemplars | `uv run python scripts/01_run_tests.py --project-only --all-projects --public-projects` | **PASS** (union ≥ 75%) |

### Blockers resolved in remediation wave

| Blocker | Cause | Fix |
| --- | --- | --- |
| `test_root_agents_is_public_repo_contract_not_personal_memory` | Root `AGENTS.md` contained `Learned User Preferences` / `Learned Workspace Facts` | Removed trailing personal-memory sections |
| Health `api-reference` gate | Stale `docs/reference/api-reference.md` | Regenerated via `scripts/generate_api_reference_doc.py --write` |
| Drift WARN `render_working_projects.py` | 354-line script with embedded audit logic | Extracted `infrastructure/project/working_render.py`; script now 113 LOC |
| Line-count WARN `architecture_viz.py` | 822-line exemplar module | Semantic split into `viz_palette.py` + four `figure_*.py` + thin orchestrator (max file 277 LOC) |
| `test_canonical_facts_infrastructure_python_count_matches_tree` | +1 infra `.py` from `working_render.py` | Updated `docs/_generated/canonical_facts.md` count **460** |

---

## 1. Structural regressions (branch delta)

### R1 — Pytest consolidation incomplete (Slice A, **high**)

`infrastructure/core/pytest_orchestration.py` growth is **directionally correct** but
Stage 01 and the union gate (`test_runner.run_per_project_pytest`) still use
**two pytest invocation models**. Union gate resolves coverage as flat
`projects/{name}/src` instead of qualified `projects/templates/{name}/src`.

**Remedy:** Single `build_pytest_argv(repo_root, project_root, …)` used by
`pipeline_test_runner`, `test_runner`, and CI union path.

### R2 — Coverage policy argued in three layers (Slice A, **high**)

`suite_runner` suppresses coverage plugin failures → `enforce_project_suite_guards`
re-forces → `pipeline_test_runner` re-mutates `exit_code`. Symptom patching.

**Remedy:** Make `--cov-fail-under` authoritative; delete guard compensation branches.

### R3 — Core imports reporting (Slice A, **medium**)

`pytest_orchestration` imports `check_cov_datafile_support` from `reporting`.

**Remedy:** Move probe to `core/coverage_policy.py` or pass `supported: bool` from callers.

**Branch delta verdict:** Approve direction of pytest consolidation; **do not**
mark slice done until `test_runner` shares the same builder.

---

## 2. Missed code-judo simplifications

| ID | Finding | Preferred remedy |
| --- | --- | --- |
| J1 | Triple `pyproject.toml` readers in `pytest_orchestration` | `load_project_pyproject()` struct + accessors |
| J2 | Triple markdown-strip helpers in `markdown_validator.py` (Slice B) | `validation/content/markdown_strip.py` |
| J3 | Cross-ref validation duplicated in `markdown_validator` vs `integrity/checks.py` | Shared `validation/content/symbols.py` |
| J4 | `render_working_projects.py` audit helpers | **Done** → `infrastructure/project/working_render.py` |
| J5 | Hard-coded Friedman citation in `_pdf_latex_helpers.py:535` | Drive from `config.yaml` publication metadata |

---

## 3. Spaghetti / branching growth

| ID | Location | Issue |
| --- | --- | --- |
| B1 | `integrity/checks.py:130-140` | Unknown ref prefix flips all five cross-ref booleans |
| B2 | `suite_runner.py:202-298` | Coverage-conflict string matching + suppression loop |
| B3 | `link_extract.py:415` | Parent-name skip (`docs`, `infrastructure`) fragile |
| B4 | `markdown_validator.py:131-140` | Image search dirs from first path only in multi-dir batches |

---

## 4. Boundary / type-contract issues

| ID | Issue |
| --- | --- |
| T1 | Rendering imports full `markdown_validator` — missing `validation/content/prerender.py` leaf (Slice B) |
| T2 | `find_manuscript_directory` in validator assumes flat `projects/{name}/` |
| T3 | `link_extract._get_actual_project_names` lists all `projects/*` dirs, not `discover_projects()` |
| T4 | `TestSuiteResults` TypedDict abandoned — guards use `dict[str, Any]` |

---

## 5. File-size / decomposition

### Infrastructure + scripts (gate: warn ≥800, fail ≥950)

| Module | LOC (approx.) | Status |
| --- | ---: | --- |
| `rendering/_pdf_latex_helpers.py` | 765 | Largest; split title-page + log parse |
| `search/literature/backends.py` | 748 | P1: one backend per file |
| `doctor/detectors.py` | 739 | P1: detector registry package |
| `reporting/_dashboard_charts.py` | 735 | P1: chart families |
| `validation/content/markdown_validator.py` | 686 | P1: validator package |
| `publishing/archival.py` | 669 | P2: provider modules |
| `validation/integrity/link_extract.py` | 655 | P2: policy extraction |
| `validation/integrity/checks.py` | 651 | P2: manifest vs completeness split |
| `rendering/pipeline.py` | 610 | P2: manuscript source + combined exports |
| `project/drift/checks.py` | 575 | Monitor; registry pattern |

### Exemplar Layer 2 (remediated)

| Module | Before | After |
| --- | ---: | --- |
| `template_template/architecture_viz.py` | 822 WARN | 47 LOC orchestrator + figure modules (max 277) |
| `scripts/render_working_projects.py` | 354 drift WARN | 113 LOC thin orchestrator |

### Exemplar src modules approaching 600 LOC (watch list, Slice E)

`template_autoresearch_project`: `manuscript_tables_builders.py` (563),
`diagnostics_metrics.py` (567), `writers.py` (542), `security.py` (541) — under
infra gate but candidates for domain splits if they grow past 600.

All exemplar `scripts/` are **under 150 LOC** except local-only
`template_autoscientists` (not in PUBLIC_PROJECT_NAMES).

---

## 6. Modularity and legibility

**Strengths**

- Thin-orchestrator discipline holds for pipeline stage scripts (`01_run_tests.py` ~209 LOC).
- P0 composability pass left a documented P1 backlog in `infrastructure/AGENTS.md`.
- Public exemplar tests remain no-mock with real filesystem / subprocess paths.

**Weaknesses**

- Validation ↔ rendering coupling (no prerender leaf).
- Literature backends and doctor detectors remain monoliths.
- Union-gate pytest path diverges from Stage 01 path.

---

## 7. Main-push gate checklist

Run before merging to `main`:

```bash
uv sync
uv run python -m infrastructure.core.health
uv run python scripts/check_template_drift.py --strict
uv run python scripts/gates/module_line_count_check.py
uv run python scripts/verify_no_mocks.py
uv run python scripts/lint_docs.py
uv run python -m infrastructure.project.public_scope source-paths | xargs uv run mypy
uv run pytest tests/infra_tests/ -q --ignore=tests/infra_tests/llm --timeout=120
uv run python scripts/01_run_tests.py --project-only --all-projects --public-projects
```

**Do not stage** `output/` artifact deletions from local pipeline runs.

---

## Slice synthesis notes

| Slice | Coverage | Key outcome |
| --- | --- | --- |
| A — Core orchestration | Complete | Union pytest builder unified; coverage policy single owner |
| B — Validation/rendering | Complete | Prerender leaf, symbols core, log parse extraction |
| C — Search/doctor/publishing | Complete | P1 monolith splits landed (backends, detectors, charts) |
| D — Root scripts | Complete | Executive report + drift orchestrator tightened |
| E — Public exemplars | Complete | `architecture_viz` split; dashboard CLI boundary; autoresearch fail-fast |

---

## Related documents

- [`TO-DO.md`](../../../TO-DO.md) — Thermo-nuclear remediation tiers (2026-05-29)
- [`infrastructure/AGENTS.md`](../../../infrastructure/AGENTS.md) — P1 quality backlog (refined)
- [`docs/architecture/thin-orchestrator-summary.md`](../../architecture/thin-orchestrator-summary.md)
