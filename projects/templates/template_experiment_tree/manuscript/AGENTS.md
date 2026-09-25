# `template_experiment_tree/manuscript/`

Agent guide for the manuscript directory. Companion to
[README.md](README.md); repo-wide policy lives in
[`../AGENTS.md`](../AGENTS.md).

## Policy

- **`config.yaml` is the single source of truth** for publication
  metadata and render settings. `config.yaml.example` is the fork
  template; edit `config.yaml`, not the example.
- **Sections are CommonMark Markdown.** The results/discussion bodies are
  not written here — they are token placeholders (`{{EXP_SECTIONS_*}}`)
  filled from the tree. Section slugs come from `flatten_sections` in
  `src/template_experiment_tree/report.py`.
- **`references.bib` is hand-curated and read-only** as far as this
  project is concerned: citations are validated, never auto-written.
- **No hand-typed numbers.** Any run-derived value must be an `{{EXP_*}}`
  token backed by tree state; a token without backing fails hydration.

## Editing checklist

- [ ] Added a section → start with `# Title` (H1), matching the numbered
  ordering (`00_abstract.md` … `04_discussion.md`).
- [ ] Added a token → ensure `render_variables` / `flatten_sections` in
  `src/template_experiment_tree/report.py` produces it; the generator
  fails closed otherwise.
- [ ] Answered or froze a node → re-run
  `scripts/z_generate_manuscript_variables.py` so `manuscript_variables.json`
  and every hydrated section reflect the new tree state.
- [ ] Changed `config.yaml` → do not hand-edit the generated publishing
  status block in `../README.md`; regenerate it instead.
- [ ] New claim → it must trace to an answered node in
  `output/data/experiment_tree.json`; frozen nodes may not be cited as
  results.

## See also

- [`config.yaml`](config.yaml) — metadata and render settings.
- [`../AGENTS.md`](../AGENTS.md) — invariants and ground-truth table.
- [`../README.md`](../README.md) — what this exemplar honestly shows.
