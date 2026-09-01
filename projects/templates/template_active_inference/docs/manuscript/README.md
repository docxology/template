# Manuscript

The sheaf-composed manuscript for the multi-track exemplar.

- `00_abstract.md`, composed IMRAD sections, `17_conclusion.md`, and
  `99_references.md` — manuscript-facing section outputs.
- `sections/` — per-track section fragments (prose, formalism, gnn, ontology,
  simulation, visualization, pymdp, lean) that the sheaf composer glues together.
- `sheaf/` — manifest-indexed sheaf registry, section bindings, and coverage config
  controlling composition.
- `figures.yaml` and `output/figures/figure_registry.json` are the figure-label
  contract. `references.bib` is the bibliography.
- `config.yaml` — paper metadata, authors, render targets. `preamble.md` — LaTeX preamble.
