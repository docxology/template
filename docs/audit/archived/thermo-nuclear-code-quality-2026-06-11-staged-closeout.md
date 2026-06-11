# Thermo-nuclear code quality audit — staged-deletion close-out (2026-06-11)

Scoped remediation after incomplete staged deletions (menu, markdown CLI, poster wrapper).
Rubric: thermo-nuclear-code-quality-review skill. Prior baseline:
[`thermo-nuclear-code-quality-2026-06-11.md`](thermo-nuclear-code-quality-2026-06-11.md).

**Scope:** `infrastructure/`, `tests/`, `docs/`, `.github/`.

**Verdict:** **Approve-with-remediation — Phases 1–4 applied.**

---

## Remediation log

| Phase | Scope | Status |
| --- | --- | --- |
| 1a | Stale SKILL/AGENTS/README refs (`cli.markdown`, poster tests) | **Done** |
| 1b | Poster formal deprecation (`poster_dir`, rendering docs) | **Done** |
| 1c | Markdown CLI + menu test parity | **Done** |
| 2 | Validation CLI unify (`python -m infrastructure.validation.cli`; legacy `pdf.py` shim) | **Done** |
| 3 | Split 1k+ test cores into peers | **Done** |
| 4 | AGENTS decomposition → `References/` stubs | **Done** |

---

## Post-remediation counts

| Metric | Value |
| --- | ---: |
| `test_pdf_renderer.py` | **705** (already under 1k) |
| `test_discovery.py` | **526** (+ `test_discovery_nested.py` 517) |
| `test_llm_review.py` | **464** (+ `test_llm_review_validation.py` 568) |
| `test_repo_scanner.py` | **597** (+ `test_repo_scanner_workflows.py` 424) |
| `test_check_links.py` | **566** (+ `test_check_links_extended.py` 434) |
| `infrastructure/rendering/AGENTS.md` | **394** |
| `infrastructure/validation/AGENTS.md` | **404** |
| `infrastructure/core/AGENTS.md` | **551** |

---

## Gate baseline (measured 2026-06-11)

| Gate | Result |
| --- | --- |
| Module line count | **PASS** |
| No mocks | **PASS** |
| Mypy (CI scope) | **PASS** |
| Targeted pytest (remediation modules) | **PASS** |
| Docs lint (`lint_docs.py --quiet`) | **Flaky** — mermaid `mmdc` 120s budget timeout on unrelated `infrastructure/llm/core/AGENTS.md` diagram (environmental; broken-link and doc-pair issues from this pass resolved) |

---

## Related documents

- [`thermo-nuclear-code-quality-2026-06-11.md`](thermo-nuclear-code-quality-2026-06-11.md) — prior main close-out
- [`infrastructure/AGENTS.md`](../../../infrastructure/AGENTS.md) — P1 watch table
