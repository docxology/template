# `manuscript/` — Illegal States, Unrepresentable

The markdown source for this exemplar's paper: a strongly-typed, decentralized
ant-robot colony simulation used to argue, honestly and with a citable
evidence trail, what `mypy --strict` proves versus what remains a runtime
discipline. `infrastructure/rendering/pdf_renderer.py` compiles these files
(plus `config.yaml`, `preamble.md`, `references.bib`) into the combined PDF
under `output/templates/template_formal/pdf/`.

Unlike several sibling exemplars (e.g. `template_code_project/manuscript/`),
this manuscript's content carries **no `{{VARIABLE}}` token-substitution
layer** — `grep -rn '{{' manuscript/0[0-9]_*.md manuscript/99_references.md`
returns nothing (this file and `AGENTS.md` are excluded from that check since
they describe the token convention in prose and legitimately contain the
literal string). Every number in the prose
(coverage percentages, `p`-values, state counts) is hand-written and pinned
against a specific test assertion or a specific run's captured output; see
`ISA.md`'s `## Verification` section for the exact commands each number
traces back to. There is no `z_generate_manuscript_variables.py` here and no
`output/manuscript/` substituted-copy step — `stage_03_render.py` renders
these files directly.

## File inventory

| File | Section | Role |
| --- | --- | --- |
| `00_abstract.md` | Abstract (`{#sec:abstract}`) | One-paragraph summary of the typed surface, the decentralization claim, and the honest mypy-vs-runtime scoping. |
| `01_introduction.md` | Introduction (`{#sec:introduction}`) | Why ant robots; frames the decentralized-multiagent research gap this exemplar fills. |
| `02_type_architecture.md` | Type Architecture (`{#sec:type-architecture}`) | Module layout of the typed surface — `Result`, `NewType` IDs, session types, affine handles. |
| `03_storage_as_functor.md` | Storage as a Functor (`{#sec:storage-functor}`) | Frames `storage/schema.py`'s agent-local SQLite schema as a functor `Schema -> Set`. |
| `04_active_inference.md` | The Active Inference Framing of the Decision Loop (`{#sec:active-inference}`) | Reads `agent/agent.py`'s `Agent.decide` as an expected-free-energy minimization (Friston 2005). |
| `05_results_discussion.md` | Results and Discussion (`{#sec:results-discussion}`) | The evidentiary core — mypy-as-oracle proof-of-detection, fault-injected negative controls, colony convergence statistics, eight pre-registered analyses across three experiment families, the formal side-spec status, and threats to the claims. By far the largest file; read its own headings before editing (`grep -n '^##' 05_results_discussion.md`). |
| `99_references.md` | References (`{#sec:references}`) | Explains the Pandoc/`natbib` bibliography wiring; the actual entries live in `references.bib`. |
| `config.yaml` | — | Real, committed paper metadata (title, authors, DOI placeholders, render-format toggles, steganography profile). Loaded via `yaml.safe_load` by `infrastructure/rendering/_pdf_combined_renderer.py`. |
| `config.yaml.example` | — | Fill-in-the-blank template for a new project copying this exemplar; diff it against `config.yaml` to see exactly which fields are project-specific. |
| `preamble.md` | — | LaTeX packages injected before Pandoc compilation — `algorithm2e` for session-type pseudocode, `fontspec`/`unicode-math` with a JuliaMono/Latin-Modern-Math fallback path for the Greek/math glyphs the code listings and equations use. |
| `references.bib` | — | 13 BibTeX entries (Wadler, Pierce, Fong, Spivak, Milner, Honda, Jung/RustBelt, Gao, Google's "eliminating classes of bugs," Ehresmann & Vanbremeersch, Friston, Ongaro/Raft) grounding the type-theory and Active-Inference claims in real literature, not marketing copy. |

Only two figures are referenced in the whole manuscript — both in
`05_results_discussion.md`, both pointing at
`../output/figures/*.png` written by `scripts/pipeline/stage_02_analysis.py`
(`{#fig:demo-convergence}`, `{#fig:convergence-tick-distribution}`). There is
no per-figure generator inventory table here because the figure count is
this small and stable; if you add a third figure, add its row to this table.

## Render pipeline

```
scripts/pipeline/stage_02_analysis.py   # runs projects/templates/template_formal/scripts/pipeline/stage_02_analysis.py
                                         #   -> writes output/figures/*.png + output/data/*.json
scripts/pipeline/stage_03_render.py     # Pandoc: manuscript/*.md + config.yaml + preamble.md + references.bib
                                         #   -> output/templates/template_formal/pdf/*_combined.pdf
scripts/pipeline/stage_04_validate.py   # infrastructure.validation: PDF structure + markdown lint
```

Run the whole chain for this project alone with the core pipeline (no LLM
stages, since `llm.reviews.enabled`/`llm.translations.enabled` are both
`false` in `config.yaml`):

```bash
uv run python scripts/runner/execute_pipeline.py --project templates/template_formal --core-only
open output/templates/template_formal/pdf/template_formal_combined.pdf
```

Validate the markdown source directly (fast, no PDF compile):

```bash
uv run python -m infrastructure.validation.cli markdown projects/templates/template_formal/manuscript/
```

## See also

- [`AGENTS.md`](AGENTS.md) — editing rules for this directory
- [`../../../docs/guides/manuscript-semantics.md`](../../../../docs/guides/manuscript-semantics.md) — repository-wide manuscript semantics
- [`../AGENTS.md`](../AGENTS.md) — project-level layer contract
- [`../formal/README.md`](../formal/README.md) — the optional formal side-spec `05_results_discussion.md` §"The optional formal side-spec: shipped, not cut" reports on
