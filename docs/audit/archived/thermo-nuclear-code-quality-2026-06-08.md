# Thermo-nuclear code quality audit — 2026-06-08

Repo-wide maintainability review scoped to **`infrastructure/`** and **`docs/`**
signposting, anchored on the v3.3.0 delta (evidence graph, incremental pipeline,
plugin stages, reference verification, advisory prose detector) and doc–code
contract drift from the 2026-06-02 close-out. Rubric: thermo-nuclear-code-quality-review
skill (Thermos plugin).

**Scope:** `infrastructure/`, `docs/` guides and AGENTS contracts, `docs/_generated/`
factual claims. **Excluded:** disposable `output/` trees (except doc-link fixes),
local `projects/working|archive` symlinks, exemplar `src/` unless docs falsely
document APIs.

**Verdict:** **Approve — Waves A–E remediation applied in this close-out.** Infra
line-count, mypy, drift, no-mocks, docs-lint, and unified health pass. Remaining
P1 watch: `validation/evidence_registry.py` (733 LOC) split deferred until next
registry feature wave.

---

## Remediation wave log (2026-06-08)

| Wave | Scope | Status |
| --- | --- | --- |
| A | Doc contract: P1 table, canonical_facts, manuscript-semantics, archival AGENTS, validation_spine link | **Done** |
| B | READFILE-SAFE-1: prose-quality CLI batch read via shared helper | **Done** |
| C | AGENTS completeness (reporting v3.3, pipeline plugins, ai_writing) | **Done** — TN-2026-23–25 |
| D | Evidence graph ↔ registry bridge, SUPPORTS edges | **Done** — TN-2026-27–28 |
| E | P1 split: `autoresearch/validation_checks.py` extract | **Done** — orchestrator **125 LOC** |

---

## Phase 1 gate baseline (measured 2026-06-08)

| Gate | Command | Result |
| --- | --- | --- |
| Module line count | `uv run python scripts/gates/module_line_count_check.py` | **PASS** — 0 infra/scripts WARN/FAIL (≥800) |
| Unified health | `uv run python -m infrastructure.core.health` | **PASS** (post Wave A) |
| Docs lint | `uv run python scripts/lint_docs.py --quiet` | **PASS** (post Wave A) |
| No mocks | `uv run python scripts/verify_no_mocks.py` | **PASS** |
| Drift (strict) | `uv run python scripts/check_template_drift.py --strict` | **PASS** |
| Mypy (CI scope) | `uv run python -m infrastructure.project.public_scope source-paths \| xargs uv run mypy` | **PASS** (793 source files) |
| Targeted v3.3 tests | `uv run pytest tests/infra_tests/reporting/test_evidence_graph.py tests/infra_tests/core/pipeline/test_incremental.py tests/infra_tests/core/pipeline/test_plugins.py tests/infra_tests/reference/verification/ -q` | **PASS** (96 tests) |
| Wave C–E bundle | `uv run pytest tests/infra_tests/reporting/test_evidence_graph.py tests/infra_tests/autoresearch/ tests/infra_tests/validation/test_evidence_registry.py -q` | **PASS** (58 tests) |
| Unified health (post Wave E) | `uv run python -m infrastructure.core.health` | **PASS** (11/11 gates) |

### Live counts (post-audit close-out)

| Metric | Value |
| --- | ---: |
| Infrastructure `.py` files | **532** |
| Importable infrastructure packages | **20** |
| Top infra module by LOC | `validation/evidence_registry.py` **733** |
| Second | `rendering/pipeline.py` **685** |
| Autoresearch validation facade | `autoresearch/validation.py` **125** (checks in `validation_checks.py` **660**) |
| Combined PDF facade | `_pdf_combined_renderer.py` **49** (re-export) |
| Dashboard charts facade | `_dashboard_charts.py` **43** (re-export) |
| Line-count gate | **PASS** — no module ≥800 LOC in `infrastructure/` + `scripts/` |

---

## Findings

| ID | Severity | Area | Finding | Resolution |
| --- | --- | --- | --- | --- |
| TN-2026-14 | **High** | `template_active_inference/.../validation_spine/AGENTS.md` | docs-lint FAIL: link to disposable `output/templates/...` missing pre-pipeline | **Wave A** — project-local `../../output/` + RUN_GUIDE pointer |
| TN-2026-15 | **High** | `infrastructure/AGENTS.md` P1 table | Stale rows: combined renderer 861 LOC, unsplit backends/detectors/dashboard | **Wave A** — mark Done; add watch-list P1 candidates |
| TN-2026-16 | **Medium** | `docs/_generated/canonical_facts.md` | Still claims 861-line WARN on combined renderer | **Wave A** — refresh top-module sentence |
| TN-2026-17 | **Medium** | `manuscript-semantics.md`, citation SKILL, validation/cli AGENTS | Pandoc `--natbib` cited at facade line 225 | **Wave A** — retarget `_pdf_combined_pandoc.py` |
| TN-2026-18 | **Medium** | `infrastructure/publishing/archival/` | Missing folder-level AGENTS | **Wave A** — add `archival/AGENTS.md` |
| TN-2026-19 | **Medium** | `validation/evidence_registry.py` (733 LOC) | Approaching 800 gate; mixed parse/build/I/O | **Deferred** — next registry feature wave |
| TN-2026-20 | **Medium** | `autoresearch/validation.py` (763 LOC) | Largest infra module; absent from P1 table | **Wave E** — split to `validation_checks.py` |
| TN-2026-21 | **Medium** | `rendering/pipeline.py` (685 LOC) | P2 orchestration monolith | **Deferred** — P2 carry-forward |
| TN-2026-22 | **Medium** | `integrity/link_extract.py` (694 LOC) | P2 extract/normalize intertwined | **Deferred** — P2 carry-forward |
| TN-2026-23 | **Low** | `reporting/AGENTS.md` | Omits v3.3 `evidence_graph.py` | **Wave C** — mermaid + API table |
| TN-2026-24 | **Low** | `core/pipeline/AGENTS.md` | Omits `plugins.py` | **Wave C** — plugins section added |
| TN-2026-25 | **Low** | `validation/content/AGENTS.md` | Omits `ai_writing.py` | **Wave C** — documented |
| TN-2026-26 | **Low** | READFILE-SAFE-1 | Prose-quality CLI used raw `read_text` | **Wave B** — shared `read_markdown`; rendering bypasses deferred |
| TN-2026-27 | **Info** | `evidence_graph.py` | Claim nodes without SUPPORTS edges | **Wave D** — `_ingest_claims` SUPPORTS |
| TN-2026-28 | **Info** | evidence graph ↔ registry | Parallel evidence surfaces | **Wave D** — `_ingest_evidence_registry` bridge |
| TN-2026-29 | **Info** | `incremental.py`, `plugins.py` | Opt-in, typed, lazy-import boundaries | **Approve** |
| TN-2026-30 | **Info** | `reference/verification/` | Thin resolver split, offline honesty | **Approve** |
| TN-2026-31 | **Info** | `validation/content/ai_writing.py` | Advisory leaf, CLI-only | **Approve** |

---

## Modularity and legibility

**Strengths**

- May–June splits succeeded: `_pdf_combined_renderer.py` and `_dashboard_charts.py`
  are 49/43 LOC facades; literature backends and doctor detectors are packages.
- v3.3 pipeline extensions (`incremental.py`, `plugins.py`) default OFF with lazy
  executor imports — correct boundary hygiene.
- `reference/verification/` is a ship-quality leaf (58–332 LOC per module).

**Weaknesses (post-remediation)**

- Doc P1 table had hidden real approaching-800 risk until this audit refresh.
- `evidence_registry.py` still needs a split before the next feature wave on that
  surface (collect/models attempt reverted — monolith kept intact).

---

## Main-push gate checklist (infra/docs delta)

```bash
uv sync
uv run python scripts/gates/module_line_count_check.py
uv run python scripts/verify_no_mocks.py
uv run python scripts/lint_docs.py --quiet
uv run pytest tests/infra_tests/reporting/test_evidence_graph.py \
  tests/infra_tests/core/pipeline/test_incremental.py \
  tests/infra_tests/core/pipeline/test_plugins.py \
  tests/infra_tests/reference/verification/ -q
uv run python -m infrastructure.project.public_scope source-paths | xargs uv run mypy
```

---

## Related documents

- [`thermo-nuclear-code-quality-2026-06-02.md`](thermo-nuclear-code-quality-2026-06-02.md) — prior branch delta
- [`thermo-nuclear-code-quality-2026-05-29.md`](thermo-nuclear-code-quality-2026-05-29.md) — repo-wide baseline
- [`infrastructure/AGENTS.md`](../../../infrastructure/AGENTS.md) — P1 quality backlog
- [`docs/_generated/canonical_facts.md`](../../_generated/canonical_facts.md) — live counts
