# `manuscript/` — Agent Guide

**This directory did not have an `AGENTS.md` until now.** Every other
permanent exemplar's `manuscript/` carries one (`template_active_inference`,
`template_code_project`, `template_textbook`, …) — `template_formal`'s was a
real, tracked gap, not an intentional omission; this file closes it.

Repository-wide manuscript rules: [`../../../docs/guides/manuscript-semantics.md`](../../../../docs/guides/manuscript-semantics.md).
Project-level layer contract: [`../AGENTS.md`](../AGENTS.md).

## What makes this manuscript different from most siblings

- **No `{{VARIABLE}}` token layer.** `template_code_project/manuscript/`
  substitutes `{{RESULT_...}}` tokens computed from analysis output; this
  manuscript's own content files (`0[0-9]_*.md`, `99_references.md`) have
  none — `grep -rn '{{' 0[0-9]_*.md 99_references.md` must stay empty (this
  file and `README.md` are excluded from that check since they *describe*
  the token convention in prose and legitimately contain the literal string).
  Every number is
  written by hand and must be re-derived from a real command before you
  change it (see `ISA.md` → `## Verification` for the exact quoted commands
  each headline number in `05_results_discussion.md` traces to — coverage
  percentages, theorem/state counts, `p`-values).
- **No manuscript-injection copy step.** `stage_03_render.py` renders these
  files directly; there is no `output/manuscript/` substituted tree to check
  for unresolved tokens.
- **The evidentiary weight lives almost entirely in one file**,
  `05_results_discussion.md` (32KB, 12 `##`/`###` subsections). Read its own
  heading list (`grep -n '^##' 05_results_discussion.md`) before editing —
  do not assume section names from memory.

## Editing rules

1. **Never hand-adjust a quoted number without re-running the thing it
   quotes.** A coverage percentage, a theorem count, a TLC state count, or a
   `p`-value in this manuscript is load-bearing prose, not decoration — the
   `iid bootstrap CI on clustered samples` and `goodness-of-fit
   green-by-construction` failure classes documented in this repo's shared
   memory both trace back to a prose number that outran its source
   computation. If you touch a number, re-run the source (`lake build`,
   `java -jar tla2tools.jar ...`, `pytest --cov`, or the specific stats
   function in `src/template_formal/colony/stats.py`) and quote the fresh
   output.
2. **`99_references.md` describes the bibliography wiring; it does not hold
   the entries.** Add/edit citations in `references.bib`, not in
   `99_references.md`'s prose.
3. **Figure additions.** Only two figures exist
   (`{#fig:demo-convergence}`, `{#fig:convergence-tick-distribution}`), both
   written by `scripts/02_run_analysis.py` to `../output/figures/`. A new
   figure needs: a generator in `src/template_formal/colony/visualization.py`,
   a call site in `scripts/02_run_analysis.py`, a Pandoc image line with a
   `{#fig:label}` anchor in `05_results_discussion.md`, and a row added to
   `README.md`'s file inventory table here.
4. **`config.yaml` vs `config.yaml.example`.** `config.yaml` is the real,
   committed metadata for this exemplar (title, ORCID, DOI placeholders — all
   intentionally blank until a real Zenodo deposit exists). `.example` is the
   fill-in-the-blank copy for someone forking this template; keep both in
   sync structurally (same keys) when you add a new `config.yaml` field —
   diff them (`diff config.yaml config.yaml.example`) before committing either.
5. **`preamble.md`'s JuliaMono/Latin-Modern-Math block is environment-
   sensitive** (hardcoded TeX Live 2026 path). If a fresh clone's PDF render
   fails on a missing font, that block — not the manuscript prose — is the
   first thing to check; the file's own comments explain the fallback (comment
   out the `Path =` line, or the whole `\setmonofont`/`\setmathfont` block).

## Render / validate loop

```bash
# 1. Regenerate figures + data (writes ../output/figures, ../output/data)
uv run python projects/templates/template_formal/scripts/02_run_analysis.py

# 2. Validate markdown before spending a full PDF compile
uv run python -m infrastructure.validation.cli markdown projects/templates/template_formal/manuscript/

# 3. Render (from repo root)
uv run python scripts/pipeline/stage_03_render.py --project templates/template_formal

# 4. Validate the rendered PDF
uv run python -m infrastructure.validation.cli pdf output/templates/template_formal/pdf/template_formal_combined.pdf
```

Or run stages 2-4 together via the core pipeline:
`uv run python scripts/runner/execute_pipeline.py --project templates/template_formal --core-only`.

## See also

- [`README.md`](README.md) — file inventory and human quick-reference
- [`../AGENTS.md`](../AGENTS.md) — project layer contract (`src/` vs `scripts/` vs `formal/`)
- [`../formal/README.md`](../formal/README.md) — the side-spec `05_results_discussion.md` §"The optional formal side-spec: shipped, not cut" and §"Formal side-spec expansion" report on
- [`../../../docs/guides/manuscript-semantics.md`](../../../../docs/guides/manuscript-semantics.md) — repository-wide manuscript semantics
