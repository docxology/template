---
name: template-manuscript-claim-verification
description: |
  Triple-pass verification of every manuscript claim against code, data, refs, and renderer;
  repair prose while staying renderable. USE WHEN pre-submission, pre-Zenodo, pre-arXiv,
  abstract numbers disagree with CSV, citations do not support sentences, or user asks to
  triple-check / verify every claim — even without docs/prompts. Not for casual PDF summary.
metadata:
  version: "1.1.0"
  last_updated: "2026-06-06"
  status: active
  data_access_level: verified_only
  task_type: open-ended
  modes:
    - claim-inventory
    - pre-submission
    - reference-existence
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

**Pass 1 — Source traceability:** For each claim, locate backing artifact (generated variable, `src/` + test, `output/` file, bib key, cross-ref key). Tag BACKED / WEAK / UNBACKED. The canonical deterministic check for binding manuscript numbers/citations to registered evidence is `infrastructure.validation.cli evidence <project> --fail-on-issues` — run it as the machine gate for BACKED claims.

**Pass 2 — Independent recomputation:** Regenerate from clean; re-run validation CLI. Reconciliation table: stated | recomputed | tolerance | PASS/FAIL. UNREPRODUCIBLE = FAIL.

**Pass 3 — Methodological adversary:** Independent review axis — overstated claims, citation mismatch, figure/caption issues, abstract not earned by results. Tag OVERSTATED / UNSUPPORTED / MISLEADING.

**Pass 4 — Reference existence (anti-hallucination):** Resolve every cited reference against Crossref / OpenAlex / arXiv with the deterministic verification gate. Tag each `ok` / `mismatch` / `fabricated` / `unverifiable` / `unchecked` / `anachronism`. `fabricated`, `mismatch`, and `anachronism` are **blocking**. `unchecked` (offline + uncached) is an honest non-pass — re-run with `--live` to resolve, never treat it as clean. Distilled from the ARS hallucination taxonomy; runs fully offline against the SQLite cache once seeded.

**Improve (not just report):** Tighten claims; use generated-variable mechanism; fix citations/cross-refs; keep renderable format (`[@key]`, `@fig:` OR `[[…]]` per project — never raw `\cite{}`/`\ref{}`). Update `projects/<n>/AGENTS.md` and README.md. Never hand-edit `output/`.

## Deliverables

- Claim inventory table: id | file:line | class | pass1 | pass2 | pass3 | action
- Edits with before/after snippets
- Commands + exit status
- Residual unresolved claims listed explicitly
- **FINAL GATE:** PASS only if every claim BACKED, numerics reconciled, zero UNREPRODUCIBLE, zero unresolved MISMATCH/MISLEADING, and zero blocking reference verdicts (no `fabricated`/`mismatch`/`anachronism`; `unchecked` resolved via a `--live` pass)

## Verification commands

```bash
uv sync
uv run python scripts/runner/execute_pipeline.py --project <project> --core-only
uv run pytest projects/<project>/tests/ --cov=projects/<project>/src --cov-fail-under=90 -q
uv run python -m infrastructure.validation.cli prerender projects/<project>/manuscript --repo-root .
uv run python -m infrastructure.validation.cli evidence projects/<project> --manuscript-dir projects/<project>/manuscript --fail-on-issues
uv run python -m infrastructure.reference.citation validate projects/<project>/manuscript/references.bib
uv run python -m infrastructure.reference.verification verify projects/<project>/manuscript/references.bib --live --as-of-year <year> --fail-on-issues
uv run python -m infrastructure.validation.cli markdown projects/<project>/manuscript --repo-root . --strict
uv run python -m infrastructure.validation.cli links --repo-root .
uv run python -m infrastructure.validation.cli pdf output/<project>/pdf/
uv run python -m infrastructure.validation.cli integrity output/<project>/
uv run python -m infrastructure.validation.cli prose-quality projects/<project>/manuscript
uv run python -m infrastructure.prose.cli report projects/<project>/manuscript
```

The reference-existence gate is offline-first: drop `--live` to verify against the
cached resolutions only (CI-safe), and keep `--live` for the seeding pass that
populates the cache. `prose-quality` is advisory — add `--fail-on-flags` to gate.

## When NOT to use

- **Output stability between runs only** → [reproducibility-audit](../reproducibility-audit/SKILL.md)
- **Registry token audit only** → [manuscript-cross-references](../manuscript-cross-references/SKILL.md)
