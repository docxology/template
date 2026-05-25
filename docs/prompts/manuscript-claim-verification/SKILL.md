---
name: template-manuscript-claim-verification
description: |
  Triple-pass verification of every manuscript claim against code, data, refs, and renderer;
  repair prose while staying renderable. USE WHEN pre-submission, pre-Zenodo, pre-arXiv,
  abstract numbers disagree with CSV, citations do not support sentences, or user asks to
  triple-check / verify every claim — even without docs/prompts. Not for casual PDF summary.
metadata:
  version: "1.0.0"
  last_updated: "2026-05-25"
  status: active
  data_access_level: verified_only
  task_type: open-ended
  modes:
    - claim-inventory
    - pre-submission
  related_skills:
    - template-reproducibility-audit
    - template-validation-quality
---

# Manuscript claim verification

## Natural invoke

- "Triple-check every claim in my manuscript before arXiv"
- "Abstract numbers don't match optimization_results.csv"
- "Verify citations actually support what the prose says"

## Inputs to confirm

- **Project** — [`docs/_generated/active_projects.md`](../../_generated/active_projects.md).
- **Manuscript style** — Pandoc-crossref vs registry tokens (see cross-ref skill).

## Workflow

Build a **claim inventory** first (numbered, file:line, class: number, comparison, citation, cross-ref, method, figure reading).

**Pass 1 — Source traceability:** For each claim, locate backing artifact (generated variable, `src/` + test, `output/` file, bib key, cross-ref key). Tag BACKED / WEAK / UNBACKED.

**Pass 2 — Independent recomputation:** Regenerate from clean; re-run validation CLI. Reconciliation table: stated | recomputed | tolerance | PASS/FAIL. UNREPRODUCIBLE = FAIL.

**Pass 3 — Methodological adversary:** Independent review axis — overstated claims, citation mismatch, figure/caption issues, abstract not earned by results. Tag OVERSTATED / UNSUPPORTED / MISLEADING.

**Improve (not just report):** Tighten claims; use generated-variable mechanism; fix citations/cross-refs; keep renderable format (`[@key]`, `@fig:` OR `[[…]]` per project — never raw `\cite{}`/`\ref{}`). Update `projects/<n>/AGENTS.md` and README.md. Never hand-edit `output/`.

## Deliverables

- Claim inventory table: id | file:line | class | pass1 | pass2 | pass3 | action
- Edits with before/after snippets
- Commands + exit status
- Residual unresolved claims listed explicitly
- **FINAL GATE:** PASS only if every claim BACKED, numerics reconciled, zero UNREPRODUCIBLE, zero unresolved MISMATCH/MISLEADING

## Verification commands

```bash
uv sync
uv run python scripts/execute_pipeline.py --project <project> --core-only
uv run pytest projects/<project>/tests/ --cov=projects/<project>/src --cov-fail-under=90 -q
uv run python -m infrastructure.validation.cli prerender projects/<project>/manuscript --repo-root .
uv run python -m infrastructure.reference.citation validate projects/<project>/manuscript/references.bib
uv run python -m infrastructure.validation.cli markdown projects/<project>/manuscript --repo-root . --strict
uv run python -m infrastructure.validation.cli links --repo-root .
uv run python -m infrastructure.validation.cli pdf output/<project>/pdf/
uv run python -m infrastructure.validation.cli integrity output/<project>/
uv run python -m infrastructure.prose.cli report projects/<project>/manuscript
```

## When NOT to use

- **Output stability between runs only** → [reproducibility-audit](../reproducibility-audit/SKILL.md)
- **Registry token audit only** → [manuscript-cross-references](../manuscript-cross-references/SKILL.md)
