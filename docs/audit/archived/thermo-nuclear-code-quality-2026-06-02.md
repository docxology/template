# Thermo-nuclear code quality audit — 2026-06-02

Repo-wide maintainability review scoped to **`infrastructure/`** and **`docs/`**
signposting, anchored on the working-tree delta (project output lock, reserve-DOI
release workflow, Mermaid batch lint, publishing docs). Rubric:
thermo-nuclear-code-quality-review skill (cursor-team-kit).

**Scope:** `infrastructure/`, `docs/` guides and AGENTS contracts.
**Excluded:** disposable `output/` trees, local `projects/active/*` symlinks.

**Verdict:** **Conditional approve — remediation waves A–D applied in this audit
close-out.** Reserve-first orchestration extracted; title-page split completed;
docs contract restored for `project_lock`, Mermaid env knobs, Zenodo reserve APIs,
and reserve-first strategy.

---

## Remediation wave log (2026-06-02)

| Wave | Scope | Status |
| --- | --- | --- |
| A | Docs: `core/files/AGENTS.md`, `core/AGENTS.md`, P1 table refresh in `infrastructure/AGENTS.md` | **Done** |
| B | Code: `release_workflow_zenodo.py` extract + `DepositionResult` typing | **Done** |
| C | Docs: `validation/docs/AGENTS.md` Mermaid env vars | **Done** |
| D | P1 `_pdf_latex_helpers.py` title-page split → `_pdf_title_page.py` | **Done** — `_pdf_latex_helpers.py` **236 LOC**, `_pdf_title_page.py` **542 LOC** |
| E | Code-judo + docs polish: `DepositionResult.from_zenodo_body`, zenodo/AGENTS, zenodo-doi-strategy, canonical_facts | **Done** |

---

## Phase 1 gate baseline (measured 2026-06-02 UTC)

| Gate | Command | Result |
| --- | --- | --- |
| Unified health | `uv run python -m infrastructure.core.health` | **FAIL** — mypy (template_active_inference src), ruff-format, module-line-count (exemplar src FAIL ≥950) |
| Line count (infra/scripts) | `uv run python scripts/gates/module_line_count_check.py` \| grep infrastructure | **PASS** — 0 infra/scripts WARN/FAIL |
| Line count (full gate) | same | **FAIL** — `template_active_inference` src files (pre-existing) |
| Docs lint | `uv run python scripts/lint_docs.py --quiet` | **PASS** |
| Drift (strict) | `uv run python scripts/check_template_drift.py --strict` | **FAIL** — 2 blanket-except errors in `template_active_inference` (pre-existing) |
| No mocks | `uv run python scripts/verify_no_mocks.py` | **PASS** |
| Mypy (CI scope) | `uv run python -m infrastructure.project.public_scope source-paths \| xargs uv run mypy` | **FAIL** — 14 errors in 6 `template_active_inference` src files (pre-existing) |
| Targeted delta tests | `uv run pytest tests/infra_tests/core/test_project_lock.py tests/infra_tests/publishing/test_release_workflow.py tests/infra_tests/validation/docs/test_mermaid_lint.py -q` | **PASS** (34 tests) |
| Rendering split tests | `uv run pytest tests/infra_tests/rendering/test_pdf_latex_helpers.py tests/infra_tests/rendering/test_pdf_renderer_combined.py -q` | **PASS** (67 tests) |

### Live counts (post-audit close-out)

| Metric | Value |
| --- | ---: |
| Infrastructure `.py` files | **495** (+3 vs 2026-05-30 canonical_facts **492**: `project_lock.py`, `release_workflow_zenodo.py`, `_pdf_title_page.py`) |
| Top infra module by LOC | `_pdf_combined_renderer.py` **861** (WARN) |
| Title-page module | `_pdf_title_page.py` **542** |
| Preamble/math helpers | `_pdf_latex_helpers.py` **236** (was 791 pre-split) |
| Release workflow | `release_workflow.py` **559** + `release_workflow_zenodo.py` **259** |
| Importable infrastructure packages | **20** (unchanged) |

---

## Branch-delta findings

| ID | Severity | Area | Finding | Resolution |
| --- | --- | --- | --- | --- |
| TN-2026-01 | **High** | `release_workflow.run_release_workflow` | Duplicated `reserve_doi_first` control flow. **H1 confirmed.** | **Wave B** — extracted `release_workflow_zenodo.py`. |
| TN-2026-02 | **Medium** | `release_workflow.py` | **704 LOC** pre-split (88% of 800 warn gate). **H2 confirmed.** | **Wave B** — zenodo phase moved; orchestrator **559 LOC**. |
| TN-2026-03 | **Medium** | `_reserve_zenodo_doi_pair` | Returned `Any \| None`. **H3 confirmed.** | **Wave B** — `DepositionResult \| None` throughout. |
| TN-2026-04 | **Low (approve)** | `core/files/project_lock.py` | 144 LOC, flock + env re-entrancy. **H4 confirmed.** | **Wave A** — AGENTS signposting. |
| TN-2026-05 | **Low (approve)** | `validation/docs/mermaid_lint.py` | Batch render + total timeout budget. **H5 confirmed.** | **Wave C** — env var table in AGENTS. |
| TN-2026-06 | **Info** | `rendering/_pdf_latex_helpers.py` | **791 LOC** monolith. **H6 carry-forward.** | **Wave D** — title-page → `_pdf_title_page.py`; helpers **236 LOC**. |
| TN-2026-07 | **Low** | Docs contract | AGENTS omitted `project_lock`. **H7 confirmed.** | **Wave A** + pipeline/reporting/core-module docs. |
| TN-2026-08 | **Low** | `web_renderer.py` | Temp `.web.tmp` + shared HTML-safe markdown. | **Approve** — bounded cleanup in `finally`. |
| TN-2026-09 | **Low** | `pipeline_test_runner` | `include_ollama_tests` aligns project gate with infra marker policy. | **Approve** — matches CI `--public-projects` default. |
| TN-2026-10 | **Low** | `docs/guides/publishing-guide.md` | `--reserve-doi-first`, concept/version split documented. | **Approve** — matches implementation + tests. |
| TN-2026-11 | **Out of scope** | Repo-wide gates | mypy/drift/line-count failures in `template_active_inference` src pre-date this delta. | Track in project backlog. |
| TN-2026-12 | **Low** | Zenodo parsing | `_deposition_result_from_body` duplicated in client. | **Wave E** — `DepositionResult.from_zenodo_body`. |
| TN-2026-13 | **Low** | `zenodo-doi-strategy.md` | No reserve-first operator flow. | **Wave E** — reserve-first section + cross-links. |

---

## Modularity and legibility

**Strengths**

- `project_output_lock` serializes same-project pipeline/test races without deadlocking subprocess test stage (env-marker re-entrancy).
- Reserve-first publishing closes the “PDF without DOI on cover” gap with HTTP-tested workflow.
- Mermaid lint batch path reduces subprocess churn under a repo-wide total timeout budget.
- Title-page generation is isolated in `_pdf_title_page.py`; `_pdf_latex_helpers.py` retains preamble/math concerns only.

**Weaknesses (post-remediation)**

- `_pdf_combined_renderer.py` remains the largest infra module (861 LOC WARN).
- `template_active_inference` exemplar src size/mypy debt is outside this audit scope but fails unified health.

---

## Main-push gate checklist (infra/docs delta)

```bash
uv sync
uv run python scripts/gates/module_line_count_check.py  # infra/scripts: expect 0 WARN
uv run python scripts/verify_no_mocks.py
uv run python scripts/lint_docs.py
uv run pytest tests/infra_tests/core/test_project_lock.py \
  tests/infra_tests/publishing/test_release_workflow.py \
  tests/infra_tests/publishing/test_zenodo_client.py \
  tests/infra_tests/validation/docs/test_mermaid_lint.py \
  tests/infra_tests/rendering/test_pdf_latex_helpers.py \
  tests/infra_tests/rendering/test_pdf_renderer_combined.py -q
uv run mypy infrastructure/rendering/_pdf_title_page.py \
  infrastructure/rendering/_pdf_latex_helpers.py \
  infrastructure/publishing/zenodo/models.py infrastructure/publishing/zenodo/client.py
```

Full-repo health/drift/mypy remain red on pre-existing `template_active_inference` surface — not introduced by this delta.

---

## Related documents

- [`thermo-nuclear-code-quality-2026-05-30.md`](thermo-nuclear-code-quality-2026-05-30.md) — prior SIA branch delta
- [`thermo-nuclear-code-quality-2026-05-29.md`](thermo-nuclear-code-quality-2026-05-29.md) — repo-wide baseline
- [`infrastructure/AGENTS.md`](../../../infrastructure/AGENTS.md) — P1 quality backlog
- [`docs/guides/publishing-guide.md`](../../guides/publishing-guide.md) — reserve-DOI operator guide
- [`docs/guides/zenodo-doi-strategy.md`](../../guides/zenodo-doi-strategy.md) — concept vs version DOI + reserve-first flow
