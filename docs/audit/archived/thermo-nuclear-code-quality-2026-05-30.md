# Thermo-nuclear code quality audit — 2026-05-30

Repo-wide maintainability review scoped to the **SIA harness branch delta**
(`infrastructure/sia/`, `projects/templates/template_sia/`, wiring in
`public_scope`, drift, release, rendering). Rubric: thermo-nuclear-code-quality-review
skill (cursor-team-kit).

**Scope:** `infrastructure/`, `docs/` signposting, `projects/templates/*` (PUBLIC_PROJECT_NAMES).
Excluded: local `projects/active/*` symlinks, disposable `output/` trees,
`templates/template_autoscientists` (LOCAL_ONLY_TEMPLATE_NAMES).

**Verdict:** **Conditional approve — remediation waves A–B complete (2026-05-30).**
SIA package decomposed; docs contract restored; full gate checklist green.
P1 carry-forward (`_pdf_latex_helpers` title-page split) unchanged from 2026-05-29.

---

## Remediation wave log (2026-05-30)

| Wave | Scope | Status |
| --- | --- | --- |
| A | Docs contract: canonical_facts, API reference, SKILL hub, sia module guide, AGENTS signatures, publication records, doc-pairs for template_sia | **Done** |
| B | SIA code: `EvaluationResult.to_dict` key order, live LLM wiring, lazy `live_llm` import, drift docstrings, `LOCAL_ONLY_TEMPLATE_NAMES`, linking test | **Done** |
| C | P1 `_pdf_latex_helpers` title-page split | **Deferred** — ~791 LOC; no new logic in branch |

---

## Phase 1 gate baseline (measured 2026-05-30 UTC)

| Gate | Command | Result |
| --- | --- | --- |
| Unified health | `uv run python -m infrastructure.core.health` | **PASS** (11/11) |
| Drift (strict) | `uv run python scripts/check_template_drift.py --strict` | **WARN** — pre-existing `template_code_project` blanket-except noqa |
| Line count | `uv run python scripts/gates/module_line_count_check.py` | **PASS** (0 infra/scripts WARN) |
| No mocks | `uv run python scripts/verify_no_mocks.py` | **PASS** |
| Docs lint | `uv run python scripts/lint_docs.py` | **PASS** |
| Mypy (CI scope) | `uv run python -m infrastructure.project.public_scope source-paths \| xargs uv run mypy` | **PASS** |
| SIA infra tests | `uv run pytest tests/infra_tests/sia/ -q --timeout=120` | **PASS** (19 tests) |
| Infra tests | `uv run pytest tests/infra_tests/ -q --ignore=tests/infra_tests/llm --timeout=120` | **PASS** (5885+) |
| Public exemplars | `uv run python scripts/01_run_tests.py --project-only --all-projects --public-projects` | **PASS** (union ≥ 75%; template_sia ≥ 90%) |

### Live counts (post-remediation)

| Metric | Value |
| --- | ---: |
| Infrastructure `.py` files | **492** |
| Importable infrastructure packages | **20** (includes `sia`) |
| Public exemplars | **6** (`template_sia` added) |

---

## Branch-delta findings (SIA + modified infra)

| ID | Severity | Area | Finding | Resolution |
| --- | --- | --- | --- | --- |
| TN-1 | High | `loop_runner._live_feedback` | Ignored `RunConfig.llm_model`; top-level `live_llm` import pulled `requests` into fixture CI | Wired `generate_improvement_markdown`; **lazy import** inside `_live_feedback` only |
| TN-2 | High | `EvaluationResult.to_dict()` | `extra` could overwrite canonical keys | Canonical keys win; test added |
| TN-3 | Medium | `drift/checks.py` | Docstrings said `src/*.py`; implementation uses `rglob` | Docstrings updated to `src/**/*.py` |
| TN-4 | Medium | `public_scope.py` | Long LOCAL-ONLY essay in module body | **Fixed** — `docs/maintenance/local-only-template-exemplars.md` |
| TN-5 | Low | `loop_runner` dispatch | Meta/target/feedback duplication between fixture and live | Acceptable; function-pointer dispatch avoids spaghetti `if live` chains |
| TN-6 | Low | Dead type aliases | Unused `MetaFn` aliases | Removed |
| TN-7 | Low | CLI `validate` task-dir default | Argparse shim + cwd default | **Fixed** — `validate` defaults to `.`; epilog documents shorthand |
| TN-8 | — | `infrastructure/sia/` decomposition | Max module ~233 LOC (`loop_runner.py`) | **Approve** |
| TN-9 | P1 carry-forward | `_pdf_latex_helpers.py` | ~791 LOC; targeted `_latex_text` escape fix only | Monitor; title-page split deferred |
| TN-10 | — | `release_workflow.resolve_combined_pdf` | Qualified `templates/<name>` + dedupe | **Approve** — correct layer boundary |
| TN-11 | Medium | Docs discovery test | `template_autoscientists` on disk but not public | Added `LOCAL_ONLY_TEMPLATE_NAMES`; test excludes intentional local-only set |
| TN-12 | Medium | `template_sia` pytest | Missing repo-root `pythonpath`; LLM import at module load | Fixed `pyproject.toml` pythonpath; lazy `live_llm` import |

---

## Docs contract findings

| Gap | Fix |
| --- | --- |
| `canonical_facts.md` stale (459/19 packages) | Refreshed to **492** `.py`, **20** packages; `template_sia` in exemplar lists |
| `infrastructure/SKILL.md` module map | Added `sia/` row |
| Missing peer guide | Added `docs/modules/guides/sia-module.md`; indexed in modules AGENTS |
| `infrastructure/AGENTS.md` | Mermaid node + function signatures for SIA |
| `tests/infra_tests/AGENTS.md` | Added `sia/` covered area |
| `docs/reference/api-reference.md` | Regenerated (`--write`, 20 packages) |
| `publication_records.md` / `.github/README.md` | Regenerated with `template_sia` |
| `template_sia` doc-pairs | README/AGENTS pairs under manuscript, src, scripts, tests, tasks |
| `doc_pair_lint` fixture trees | Excluded `recorded_generations` from pair lint |

---

## Carry-forward P1 backlog (unchanged)

From [`infrastructure/AGENTS.md`](../../../infrastructure/AGENTS.md) — monitor, do not block SIA merge:

| Module | ~LOC | Note |
| --- | ---: | --- |
| `rendering/_pdf_latex_helpers.py` | 791 | Title-page extraction deferred |
| `project/drift/checks.py` | 580 | Registry pattern; nested `src/` now covered |
| Other P1 rows | — | See infrastructure AGENTS P1 table |

---

## Modularity and legibility

**Strengths**

- SIA harness uses small modules and function-pointer dispatch for fixture vs live paths.
- Fixture replay is default; Ollama/`requests` stay off the default CI import graph.
- Shared-path fixes (drift rglob, release PDF resolution, LaTeX author escape) are boundary-correct and tested.

**Weaknesses**

- `_pdf_latex_helpers.py` remains a P1 monolith.
- `public_scope.py` registry is lean; local-only policy lives in maintenance doc.

---

## Post-close-out verification (2026-05-30)

Six-exemplar doc sync (`projects/AGENTS.md`, `manuscript-semantics.md`, tests/_support, `MAINTAINERS.md`); TN-4 essay extraction; TN-7 SIA CLI cwd default; extended stale-count guard in `test_docs_discovery_consistency.py`. Health **11/11 PASS**; docs lint and targeted tests green.

## Main-push gate checklist

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

Strict drift may emit one pre-existing WARN on `template_code_project` blanket-except — not introduced by this branch.

---

## Related documents

- [`TO-DO.md`](../../../TO-DO.md) — Thermo-nuclear remediation tiers (2026-05-30 section)
- [`thermo-nuclear-code-quality-2026-05-29.md`](thermo-nuclear-code-quality-2026-05-29.md) — prior baseline
- [`infrastructure/sia/AGENTS.md`](../../../infrastructure/sia/AGENTS.md) — SIA module reference
- [`docs/modules/guides/sia-module.md`](../../modules/guides/sia-module.md) — peer module guide
