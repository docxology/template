# Prompt: Manuscript claim verification (triple-check)

## Purpose

A **copy-paste template** for a maximum-effort, triple-pass re-verification of
**every claim** a manuscript makes — numbers, citations, cross-references,
methods, figures, and data — against the code, data, references, and renderer
that are supposed to back them. The pass does not only *report*: it **improves**
the manuscript so claims match evidence, keeps the project's `AGENTS.md` and
`README.md` complete and accurate, and never breaks the renderable
Pandoc/registry format.

Use this when correctness matters more than speed: pre-submission, pre-release,
pre-Zenodo/arXiv, or whenever a manuscript and its code/data may have drifted.

Live counts and CI parity live in
[`../_generated/canonical_facts.md`](../_generated/canonical_facts.md) and
[`.github/AGENTS.md`](../../.github/AGENTS.md). The renderer contract (what
"renderable" means) is
[`../guides/manuscript-semantics.md`](../guides/manuscript-semantics.md).

## Copy-paste prompt

```
You are triple-checking EVERY claim in a manuscript with maximum effort and the
maximum set of relevant repository tools. Goal: prove or repair each claim, then
improve the manuscript without breaking its renderable format.

PROJECT: [name from docs/_generated/active_projects.md — do not assume]
MANUSCRIPT: projects/[name]/manuscript/
OUTPUTS:    output/[name]/        (regenerated, never hand-edited)

Definitions — a "claim" is any sentence asserting a fact: a number/statistic, a
comparison or improvement, a citation's content, a cross-reference target, a
methodological assertion ("we use X"), or a figure/table reading. Build a claim
inventory first (numbered list, file:line for each).

Run THREE ORTHOGONAL passes (different axes, not the same check three times).
Each pass must be able to fail a claim the previous pass passed. A claim that
cannot be reproduced/backed is FAIL — never a silent pass, never "skipped".

PASS 1 — SOURCE TRACEABILITY (does a backing artifact exist?)
  For each claim, locate the artifact that should back it:
    - computed number  -> a generated manuscript variable, not a hand-typed digit
    - code behaviour    -> a function in projects/<n>/src/ + a test that exercises it
    - dataset/result    -> a file under output/<n>/ produced by the pipeline
    - citation          -> a resolvable key in manuscript/references.bib
    - cross-reference   -> a defined @fig:/@tbl:/@eq:/@sec: or [[…]] registry key
  Tag each claim BACKED / WEAK / UNBACKED. List every UNBACKED/WEAK with file:line.

PASS 2 — INDEPENDENT RECOMPUTATION (numeric reconciliation)
  Regenerate, do not trust the prose. Re-run tests, regenerate manuscript
  variables and figures/data from a clean state, re-resolve every citation and
  cross-reference with the validation CLI. For every numeric claim record a
  reconciliation: stated value | recomputed value | tolerance | PASS/FAIL.
  Divergence beyond tolerance = MISMATCH. A claim whose artifact cannot be
  regenerated or re-derived is UNREPRODUCIBLE = FAIL (escalate, never pass it
  through). Numbers in prose not driven by a generated variable are a finding
  even when currently equal (they will drift).

PASS 3 — METHODOLOGICAL ADVERSARY + INDEPENDENT RED-TEAM
  Performed with deliberate independence — ideally a fresh reviewer/agent that
  does NOT see the author's stated conclusions, so the same blind spot is not
  repeated. Attack what survived on a different axis than Pass 1/2: unstated
  assumptions, sample/power, multiple-comparisons or selective ("p-hacked")
  reporting, sensitivity of the inference to reasonable alternative choices,
  citations that do not support the sentence that cites them, figure/caption/
  axis mismatches, and abstract/conclusion claims not earned by the results.
  Tag OVERSTATED / UNSUPPORTED / MISLEADING.

THEN — IMPROVE (not just report):
  - Tighten each flagged claim to exactly what the evidence supports; replace
    hand-typed computed numbers with the generated-variable mechanism the
    project already uses; fix broken citations and cross-references.
  - Keep the renderable format intact: citations stay [@key]; cross-refs stay
    @fig:/@tbl:/@eq:/@sec: OR registry [[…]] tokens per the project's style
    (see docs/guides/manuscript-semantics.md and, for token projects,
    docs/prompts/manuscript_cross_references.md). Never introduce raw \cite{} or
    \ref{}. Never edit files under output/.
  - Update projects/<n>/AGENTS.md and projects/<n>/README.md so they remain
    complete and accurate after the changes (new/removed scripts, regeneration
    command, claim->artifact map). Do not duplicate the active-project roster —
    link docs/_generated/active_projects.md.
  - Re-run the full validation set below; the manuscript must still render.

DELIVER:
  - Claim inventory table: id | file:line | class | pass1 | pass2 | pass3 | action
  - Every concrete edit (file + before/after snippet)
  - Exact commands run with raw exit status (no invented coverage numbers —
    cite pytest output or docs/_generated/canonical_facts.md)
  - Residual unresolved claims explicitly listed (do NOT claim "all verified"
    unless every claim is BACKED and MISMATCH-free with evidence shown)
  - FINAL GATE (one line): PASS only if every claim is BACKED, every numeric
    reconciliation within tolerance, zero UNREPRODUCIBLE, zero unresolved
    MISMATCH/MISLEADING. Otherwise FAIL and name the blocking claim ids.
```

## Commands (reference)

Resolve `<project>` via
[`../_generated/active_projects.md`](../_generated/active_projects.md). Every
command below is a real repository entrypoint (verify any flag with `--help`).

```bash
uv sync

# Pass 2 — regenerate from clean state, then diff (provenance of every number/figure)
uv run python projects/<project>/scripts/z_generate_manuscript_variables.py
uv run python scripts/execute_pipeline.py --project <project> --core-only
git status --porcelain projects/<project> output/<project>   # what regeneration changed

# Pass 1/2 — code-backed claims
uv run python scripts/01_run_tests.py --project <project>
uv run pytest projects/<project>/tests/ \
  --cov=projects/<project>/src --cov-fail-under=90 -q

# Citations + cross-references (undefined-citation + pitfall gate)
uv run python -m infrastructure.validation.cli prerender \
  projects/<project>/manuscript --repo-root .
uv run python -m infrastructure.reference.citation validate \
  projects/<project>/manuscript/references.bib

# Markdown + links + rendered PDF + output integrity
uv run python -m infrastructure.validation.cli markdown \
  projects/<project>/manuscript --repo-root . --strict
uv run python -m infrastructure.validation.cli links --repo-root .
uv run python -m infrastructure.validation.cli pdf output/<project>/pdf/
uv run python -m infrastructure.validation.cli integrity output/<project>/

# Pass 3 — prose/editorial signal (readability, hedging, quality flags)
uv run python -m infrastructure.prose.cli report projects/<project>/manuscript
```

## Manuscript cross-reference note

- **Pandoc-crossref style**: `[@bibkey]`, `@fig:`, `@tbl:`, `@eq:`, `@sec:` per
  [`../guides/manuscript-semantics.md`](../guides/manuscript-semantics.md).
- **Registry token style**: `refs/labels.yaml` + `[[FIG:…]]` / `[[THMREF:…]]` —
  use [`manuscript_cross_references.md`](manuscript_cross_references.md) as the
  checklist. Repairs in PASS-3 must keep whichever style the project already
  uses; do not mix styles.

## Checklist

### Pre-flight

- [ ] Target project resolved from `_generated/active_projects.md`; `uv sync` clean.
- [ ] Claim inventory built (numbered, `file:line`, claim class).

### During review

- [ ] Pass 1 traceability tags assigned (BACKED/WEAK/UNBACKED).
- [ ] Pass 2 run from a regenerated clean state; MISMATCHes carry expected vs. stated.
- [ ] Pass 3 done with deliberate independence; OVERSTATED/UNSUPPORTED listed.
- [ ] Hand-typed computed numbers migrated to the generated-variable mechanism.
- [ ] Citations/cross-refs still resolve; renderer style unchanged; no raw `\cite{}`/`\ref{}`.
- [ ] No file under `output/` edited by hand.

### Reporting

- [ ] `projects/<n>/AGENTS.md` + `README.md` updated and complete; roster linked, not copied.
- [ ] Validation set re-run; PDF still renders; raw exit status recorded.
- [ ] Residual unresolved claims listed explicitly — no blanket "all verified".

## See also

- [`comprehensive_assessment.md`](comprehensive_assessment.md) — wider repo audit (structure + gates).
- [`validation_quality.md`](validation_quality.md) — validation-infrastructure-focused QA.
- [`reproducibility_audit.md`](reproducibility_audit.md) — determinism / regenerate-and-diff.
- [`manuscript_cross_references.md`](manuscript_cross_references.md) — registry/token cross-ref audit.
- [`README.md`](README.md) — prompt index.
