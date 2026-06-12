# Thermo-nuclear code quality audit — scoped v2 (2026-06-11)

Scoped maintainability snapshot on HEAD `2b11c5f3`. Rubric:
thermo-nuclear-code-quality-review skill. Prior baseline:
[`thermo-nuclear-code-quality-2026-06-11.md`](thermo-nuclear-code-quality-2026-06-11.md)
+ [`thermo-nuclear-code-quality-2026-06-11-staged-closeout.md`](thermo-nuclear-code-quality-2026-06-11-staged-closeout.md).

**Scope:** `docs/`, `infrastructure/`, `tests/` only. **Excluded:** root `scripts/`
(except gate commands), `projects/` exemplars (covered by prior full-repo audit),
disposable `output/` trees.

**Verdict:** **Approve** — Waves F–O complete; unified health **11/11 PASS** (2026-06-11 close-out).

---

## Remediation wave log (v2 follow-on)

| Wave | Scope | Status |
| --- | --- | --- |
| F | Split `test_integrity.py` + `llm/test_validation.py` before 950-line cliff | **Done** — cores **502** / **440** LOC; peers `test_integrity_edge_cases.py` **462**, `test_validation_repetition.py` **532** |
| G | Extract drift check families from `project/drift/checks.py` | **Done** — `checks_exemplar.py` **558**; barrel **57** LOC; leaves `checks_docs_counts.py` **80**, `checks_boundary.py` **95** |
| H | Docs policy: `_generated/README.md` COUNTS contract; mermaid lint recovery | **Done** — multiline stadium→rect sweep (**65** files, **0** stadium nodes remain); `_MMDC_BATCH_SIZE` 20→10; total budget **135s** |
| I | P2 infra split / registry cleanup | **Done** — removed dead `check_repo_docs_hardcoded_counts` import from `registry.py` |
| J | Gate recovery (mypy + ruff) | **Done** — `QualityReportLike` protocol fields; CI-scope ruff clean |
| K | Mermaid lint (TN-2026-54 / TN-2026-70) | **Done** — see Wave H |
| L | Multi-project report → `reporting/` | **Done** — `reporting/multi_project_report.py` **261** LOC; `core/pipeline/multi_project.py` re-exports via `__all__` |
| M | `_link_normalize.py` from `link_extract` | **Done** — `_link_normalize.py` **96** LOC; `link_extract.py` **446** LOC |
| N | Integrity manifest vs completeness split | **Done** — `manifest.py` **132**, `completeness.py` **179**; facade `checks.py` **298** LOC |
| O | Close-out (AGENTS P1, COUNTS, gates, this report) | **Done** |

---

## Phase 1 gate baseline (measured 2026-06-11 close-out)

| Gate | Command | Result |
| --- | --- | --- |
| Module line count | `uv run python scripts/gates/module_line_count_check.py` | **PASS** |
| Unified health | `uv run python -m infrastructure.core.health` | **PASS** (11/11) |
| Docs lint | `uv run python scripts/lint_docs.py --quiet` | **PASS** (~84–108s; 135s mermaid total budget; 0 stadium nodes) |
| COUNTS sync | `uv run python scripts/generate_counts.py --check` | **PASS** |
| No mocks | `uv run python scripts/verify_no_mocks.py` | **PASS** |
| Mypy (CI scope) | `uv run python -m infrastructure.project.public_scope source-paths \| xargs uv run mypy` | **PASS** (823 files) |
| Targeted pytest (split modules) | see checklist below | **284 passed** (1 slow e2e deselected) |
| Drift unit tests | `tests/infra_tests/test_check_template_drift.py` (excl. slow e2e) | **32 passed** |

### Post-closeout LOC (infrastructure leaves + test cores)

| Module | LOC |
| --- | ---: |
| `reporting/multi_project_report.py` | 261 |
| `validation/integrity/checks.py` (facade) | 298 |
| `validation/integrity/manifest.py` | 132 |
| `validation/integrity/completeness.py` | 179 |
| `validation/integrity/_link_normalize.py` | 96 |
| `validation/integrity/link_extract.py` | 446 |
| `project/drift/checks.py` (barrel) | 57 |
| `project/drift/checks_exemplar.py` | 558 |
| `project/drift/checks_docs_counts.py` | 80 |
| `project/drift/checks_boundary.py` | 95 |
| `test_integrity.py` / `test_integrity_edge_cases.py` | 502 / 462 |
| `llm/test_validation.py` / `test_validation_repetition.py` | 440 / 532 |

---

## Findings

| ID | Severity | Area | Finding | Resolution |
| --- | --- | --- | --- | --- |
| TN-2026-53 | **High** | `project/drift/checks.py` (725 LOC) | Largest infra module; 14 `check_*` detectors in one file | **Closed** — exemplar leaf + thin barrel **57** LOC |
| TN-2026-54 | **High** | Mermaid lint (docs + exemplar) | `lint_docs` exit 124 on 120s budget — stadium/path-label diagrams | **Closed** — stadium→rect sweep + batch size 10 + 135s budget |
| TN-2026-55 | **High** | Unified health / CI scope | mypy fails on prose `QualityReportLike` protocol drift | **Closed** — `long_sentence_count`, `citation_density_per_1000` on Protocol |
| TN-2026-56 | **Medium** | `test_integrity.py` (950 LOC) | One line from 950 fail threshold | **Closed** — core **502** LOC |
| TN-2026-57 | **Medium** | `llm/test_validation.py` (940 LOC) | Same cliff | **Closed** — core **440** LOC |
| TN-2026-58 | **Medium** | P2 backlog (open) | `link_extract`, `integrity/checks`, `markdown_validator`, `rendering/pipeline` | **Partial** — link_normalize + integrity split **done**; markdown_validator + pipeline leaves deferred |
| TN-2026-59 | **Medium** | `core/pipeline/multi_project.py` | `format_multi_project_detailed_report()` in pipeline package | **Closed** — `reporting/multi_project_report.py` **261** LOC |
| TN-2026-60 | **Medium** | `validation/integrity/checks.py` (589 LOC) | Manifest + completeness mixed | **Closed** — `manifest.py` + `completeness.py`; facade **298** LOC |
| TN-2026-61 | **Medium** | `validation/content/markdown_validator.py` (610 LOC) | Five `validate_*` leaves inline | **Deferred** — next feature wave |
| TN-2026-62 | **Medium** | `project/drift/registry.py` | `check_repo_docs_hardcoded_counts` imported but never registered | **Wave I done** — dead import removed |
| TN-2026-64 | **Low** | `docs/_generated/README.md` | COUNTS row said **Maintained** vs auto-generated header | **Wave H done** — README aligned to **Generated** |
| TN-2026-63 | **Low** | Doc megas | Four human guides >800 LOC with no decomposition policy | Add docs P1 watch table or topic leaves |
| TN-2026-65 | **Low** | `rendering/render_all_cli.py` | `sys.path.insert` + CWD-relative `manuscript/` — P1 backlog | `--project` + `resolve_project_root` |
| TN-2026-66 | **Low** | `documentation/generate_glossary_cli.py` | Second `sys.path.insert` offender | Module entry or explicit PYTHONPATH in wrapper only |
| TN-2026-67 | **Low** | Emerging test cluster | `test_issue_categorizer.py` 894, `test_markdown_validator.py` 846, `test_publishing.py` 846 | Optional test line-count warn gate or proactive peer migration |
| TN-2026-68 | **Info** | `docs/_generated/COUNTS.md` | Exemplar coverage table dated 2026-06-11; infra count correct | `generate_counts.py --write` after exemplar changes |
| TN-2026-69 | **Info** | P1 watch modules | `publishing/archival.py` 669, `autoresearch/validation_checks.py` 661 | Monitor before next feature wave |
| TN-2026-70 | **Info** | `validation/docs/mermaid_lint.py` | 120s total budget masked slow diagrams across full tree | **Closed** — batch size 10; stadium→rect sweep; default total budget **135s** |

---

## Carry-forward: TN-2026-32 … TN-2026-52

| ID | Status | Note |
| --- | --- | --- |
| TN-2026-32 | **Closed** | `discover_projects()` in link extract |
| TN-2026-33 | **Closed → regressed** | Fixtures fixed; new mermaid timeout → **TN-2026-54** |
| TN-2026-34 | **Closed** | Disposable output link |
| TN-2026-35 | **Closed** | `test_check_links.py` **569** LOC |
| TN-2026-36 | **Closed** | Evidence registry split |
| TN-2026-37 | **Partial** | `link_skip_policy` done; `_link_normalize.py` open → **TN-2026-58** |
| TN-2026-38 | **Partial** | `build_pandoc_metadata()` done; pipeline leaves open → **TN-2026-58** |
| TN-2026-39 | **Closed** | `resolve_project_root` in markdown CLI |
| TN-2026-40 | **Partial** | Counts refreshed; README drift → **TN-2026-64** |
| TN-2026-41 | **Partial** | Table refreshed; `drift/checks.py` missing → **TN-2026-53** |
| TN-2026-42–46 | **Closed** | api-reference, .github parity, stage-table |
| TN-2026-47–50 | **Closed** | Test megas decomposed (705–569 LOC cores) |
| TN-2026-51 | **Carry** | `archival.py` watch → **TN-2026-69** |
| TN-2026-52 | **Closed** | No infra ≥800; watch shifted to `drift/checks` **725** |

---

## Modularity and legibility

**Strengths**

- June 11 test megamonolith wave landed — four former >1k cores now 569–705 LOC with peer files; pattern is repeatable for Wave F.
- Facade+leaf discipline is consistent (`evidence_registry` / collectors, `link_extract` / `link_skip_policy`).
- Ground-truth docs infrastructure (`COUNTS.md` auto-generation, drift hardcoded-count scan) keeps prose from inventing statistics.

**Top code-judo opportunities**

1. **`drift/checks.py` detector package** — reframe 725-line monolith as family leaves + thin barrel (mirrors `validation_checks.py`).
2. **Reporting owns multi-project UX** — move `format_multi_project_detailed_report` from pipeline to `reporting/`.
3. **Markdown validator leaf package** — five `validate_*` functions into `content/validator_*.py` so `prerender.py` imports thin leaves only.

**Residual watch (optional P3)**

- Four infra test cores still 846–950 LOC without a test line-count gate.
- Open P2 splits in `infrastructure/AGENTS.md` L103–117.
- Four human doc guides >800 LOC without decomposition policy.

---

## Main-push gate checklist

```bash
uv sync
uv run python scripts/gates/module_line_count_check.py
uv run python scripts/verify_no_mocks.py
uv run python scripts/lint_docs.py --quiet
uv run python scripts/generate_counts.py --check
uv run pytest tests/infra_tests/validation/test_integrity.py \
  tests/infra_tests/validation/test_integrity_edge_cases.py \
  tests/infra_tests/llm/test_validation.py \
  tests/infra_tests/llm/test_validation_repetition.py \
  tests/infra_tests/test_check_template_drift.py \
  tests/infra_tests/core/test_multi_project_detailed_report.py \
  tests/infra_tests/validation/test_link_path_validation.py -q
uv run pytest tests/infra_tests/validation/test_evidence_registry.py \
  tests/infra_tests/validation/test_link_path_validation.py \
  tests/infra_tests/project/test_resolve_project_root.py \
  tests/infra_tests/project/test_project_metadata.py -q
uv run python -m infrastructure.project.public_scope source-paths | xargs uv run mypy
uv run python -m infrastructure.core.health
```

---

## Related documents

- [`thermo-nuclear-code-quality-2026-06-11.md`](thermo-nuclear-code-quality-2026-06-11.md) — prior full-repo close-out
- [`thermo-nuclear-code-quality-2026-06-11-staged-closeout.md`](thermo-nuclear-code-quality-2026-06-11-staged-closeout.md) — test mega splits
- [`infrastructure/AGENTS.md`](../../../infrastructure/AGENTS.md) — P1 quality backlog
- [`docs/_generated/COUNTS.md`](../../_generated/COUNTS.md) — live counts
- [`docs/audit/README.md`](../README.md) — live linter index
