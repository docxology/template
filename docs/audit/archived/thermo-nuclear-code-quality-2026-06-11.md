# Thermo-nuclear code quality audit — 2026-06-11

Full-repo maintainability snapshot on clean `main` (post `2c155117`). Rubric:
thermo-nuclear-code-quality-review skill. Prior baseline:
[`thermo-nuclear-code-quality-2026-06-08.md`](thermo-nuclear-code-quality-2026-06-08.md).

**Scope:** `infrastructure/`, `scripts/`, `tests/`, `docs/`, `.github/`, public
exemplars under `projects/templates/`. **Excluded:** disposable `output/` trees
(except doc-link fixes), local `projects/working|archive` symlinks.

**Verdict:** **Approve-with-remediation — Waves A–D applied in this close-out.**

---

## Remediation wave log (2026-06-11)

| Wave | Scope | Status |
| --- | --- | --- |
| A | Gate recovery: api-reference regen, canonical_facts refresh, fixtures mermaid simplify, disposable output link fix, stage-table targets | **Done** |
| B | Discovery correctness: `link_extract._get_actual_project_names` → `discover_projects()`; `find_manuscript_directory` → `resolve_project_root` | **Done** |
| C | P1 split: `evidence_registry_collectors.py` extract (orchestrator 453 LOC) | **Done** |
| D | Test decomposition: `test_resolve_project_root.py`, `test_llm_review_integration.py`; repo_scanner `__main__` at EOF; docs/AGENTS CI parity | **Done** (partial — 3 test megas still >1k LOC; carry-forward) |
| E | Carry-forward P2: `link_skip_policy.py`, `build_pandoc_metadata()`; test splits/dedupes | **Done** (2026-06-11 second pass) |

---

## Phase 1 gate baseline (measured 2026-06-11 post-remediation)

| Gate | Command | Result |
| --- | --- | --- |
| Module line count | `uv run python scripts/gates/module_line_count_check.py` | **PASS** |
| Unified health | `uv run python -m infrastructure.core.health` | **PASS** (post Wave A) |
| Docs lint | `uv run python scripts/lint_docs.py --quiet` | **PASS** (post fixtures mermaid fix) |
| No mocks | `uv run python scripts/verify_no_mocks.py` | **PASS** |
| Drift (strict) | `uv run python scripts/check_template_drift.py --strict` | **PASS** |
| Mypy (CI scope) | `uv run python -m infrastructure.project.public_scope source-paths \| xargs uv run mypy` | **PASS** |
| API reference | `uv run python scripts/generate_api_reference_doc.py --check` | **PASS** (post `--write`) |
| Evidence + links | `uv run pytest tests/infra_tests/validation/test_evidence_registry.py tests/infra_tests/validation/test_check_links.py::TestGetActualProjectNames -q` | **PASS** |

### Live counts (post carry-forward pass, 2026-06-11)

| Metric | Value |
| --- | ---: |
| Infrastructure `.py` files | **554** (+`link_skip_policy.py`) |
| Importable infrastructure packages | **20** |
| Top infra module by LOC | `validation/integrity/link_extract.py` **543** |
| Link skip policy leaf | `validation/integrity/link_skip_policy.py` **144** |
| Evidence registry facade | `validation/evidence_registry.py` **453** |
| Evidence collectors leaf | `validation/evidence_registry_collectors.py` **307** |
| `test_check_links.py` (core) | **1000** (+ `test_link_path_validation.py` 242, `test_link_audit_workflows.py` 435) |
| `test_pdf_renderer.py` | **1197** (duplicate tail removed) |
| `test_discovery.py` | **1043** (+ `test_project_metadata.py` 225) |
| `test_repo_scanner.py` | **1021** (duplicate scanner classes removed) |
| Line-count gate | **PASS** — no module ≥800 LOC in `infrastructure/` + `scripts/` |
| Unified health | **PASS** — 11/11 gates |

---

## Findings

| ID | Severity | Area | Finding | Resolution |
| --- | --- | --- | --- | --- |
| TN-2026-32 | **High** | `link_extract._get_actual_project_names` | Listed `projects/*` bucket dirs, not discoverable projects | **Wave B** — `discover_projects()` + qualified/bare names |
| TN-2026-33 | **High** | `tests/fixtures/AGENTS.md` mermaid | docs-lint exit 124 (120s budget); stadium path labels | **Wave A** — simplified rect-node diagram |
| TN-2026-34 | **High** | `template_code_project/.../03_results.md` | GitHub link to disposable `output/...csv` | **Wave A** — prose path + script reference |
| TN-2026-35 | **High** | `test_check_links.py` (1767 LOC) | 1k+ test monolith | **Wave E** — deduped Extended classes; split into path + workflow peers (core 1000 LOC) |
| TN-2026-36 | **Medium** | `evidence_registry.py` (733 LOC) | God-module approaching 800 gate | **Wave C** — collectors extract |
| TN-2026-37 | **Medium** | `link_extract.py` (694 LOC) | Inline path-skip policy table | **Wave E** — `link_skip_policy.py` (144 LOC); `link_extract` 543 LOC |
| TN-2026-38 | **Medium** | `rendering/pipeline.py` (685 LOC) | Duplicated DOCX metadata vs `_pdf_title_page` | **Wave E** — `build_pandoc_metadata()` shared helper |
| TN-2026-39 | **Medium** | `markdown_validator.find_manuscript_directory` | Flat `projects/{name}` only | **Wave B** — `resolve_project_root` |
| TN-2026-40 | **Medium** | `COUNTS.md` | Stale 533 count, wrong largest-module claim | **Wave A** — refreshed measured block |
| TN-2026-41 | **Medium** | `infrastructure/AGENTS.md` P1 table | Stale LOC rows; missing watch entries | **Wave D** — refreshed table |
| TN-2026-42 | **Medium** | api-reference health gate | Stale vs exports | **Wave A** — `--write` |
| TN-2026-43 | **Medium** | `.github/AGENTS.md` | 12 jobs documented; CI has 14 | **Wave D** — job table updated |
| TN-2026-44 | **Medium** | `.github/AGENTS.md` coverage | 75% union gate overstated for CI | **Wave D** — clarified local-only path |
| TN-2026-45 | **Low** | `.github/AGENTS.md` pre-push | 3 hooks documented; 5 implemented | **Wave D** — five-hook table |
| TN-2026-46 | **Low** | `generate_stage_table_doc.py` | Omitted `AGENTS.md` / `CLAUDE.md` targets | **Wave A** — added to `_DEFAULT_TARGETS` |
| TN-2026-47 | **Low** | `test_pdf_renderer.py` (1485 LOC) | Test megamonolith | **Wave E** — removed duplicate tail (1197 LOC); peer migration optional |
| TN-2026-48 | **Low** | `test_discovery.py` (1284 LOC post-split) | Still >1k after `resolve_project_root` extract | **Wave E** — `test_project_metadata.py` extracted (1043 LOC core) |
| TN-2026-49 | **Low** | `test_repo_scanner.py` | `__main__` mid-file; duplicate scanner classes | **Wave D+E** — `__main__` at EOF; removed duplicate `TestDataClasses`/`TestRepositoryScanner` block (1021 LOC) |
| TN-2026-50 | **Low** | `test_llm_review.py` (1032 LOC post-split) | Ollama + unit mixed | **Partial** — integration extracted |
| TN-2026-51 | **Info** | `publishing/archival.py` (669 LOC) | New watch candidate | **Wave D** — added to P1 watch table |
| TN-2026-52 | **Info** | Recent infra delta | No new ≥800 LOC modules | **Approve** |

---

## Modularity and legibility

**Strengths**

- Evidence registry split follows the autoresearch validation pattern (thin facade + collectors leaf).
- Discovery APIs now drive link validation and markdown CLI manuscript resolution.
- CI/documentation job inventory and pre-push parity aligned with `.pre-commit-config.yaml`.

**Residual watch (optional P3)**

- Four infra test cores still exceed 1k LOC (`test_check_links` 1000, `test_pdf_renderer` 1197, `test_discovery` 1043, `test_repo_scanner` 1021) — split peers exist for links/metadata; further migration to `test_pdf_*.py` peers is optional.
- `link_extract` URL/normalize helpers and `rendering/pipeline` manuscript-source split remain P2 in `infrastructure/AGENTS.md`.

---

## Main-push gate checklist

```bash
uv sync
uv run python scripts/gates/module_line_count_check.py
uv run python scripts/verify_no_mocks.py
uv run python scripts/lint_docs.py --quiet
uv run pytest tests/infra_tests/validation/test_evidence_registry.py \
  tests/infra_tests/validation/test_link_path_validation.py \
  tests/infra_tests/project/test_resolve_project_root.py \
  tests/infra_tests/project/test_project_metadata.py -q
uv run python -m infrastructure.project.public_scope source-paths | xargs uv run mypy
uv run python -m infrastructure.core.health
```

---

## Related documents

- [`thermo-nuclear-code-quality-2026-06-08.md`](thermo-nuclear-code-quality-2026-06-08.md) — prior close-out
- [`infrastructure/AGENTS.md`](../../../infrastructure/AGENTS.md) — P1 quality backlog
- [`docs/_generated/COUNTS.md`](../../_generated/COUNTS.md) — live counts
