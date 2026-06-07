# Results {#sec:results}

After running `scripts/run_prose_pipeline.py` with the bundled `manuscript/config.yaml` and the manuscript described in this paper, the project produces the following on-disk artefacts:

* `output/manuscript_report.json` — the raw `ManuscriptReport` JSON.
* `output/checks.json` — one `CheckResult` per configured check.
* `output/review_report.md` — the assembled markdown review report.
* `output/figures/section_word_counts.png` — per-file word counts.
* `output/figures/readability_metrics.png` — Flesch / Flesch-Kincaid / Gunning Fog per file.
* `output/figures/citation_density.png` — citations per 1000 words per file.
* `output/data/manuscript_variables.json` — substitution variables for the abstract.

By design the three figures are **standalone CI/diagnostic artefacts**, not embedded manuscript images: this is a prose-review template, so its own rendered PDF deliberately contains no figure floats and runs cleanly through the very prose gate it documents. A fork that wants figures inside the manuscript embeds them with `![caption](../output/figures/<name>.png){#fig:<label>}` in the usual way; see `docs/syntax_guide.md`.

Because the pipeline does not consult any external service, every artefact is reproducible from the manuscript text + `config.yaml` alone. A second run on the same inputs produces byte-identical JSON (modulo timestamp metadata in any caches the project later adds).

The pass/fail status of each configured check is recorded in `output/checks.json`. With the bundled configuration:

* **`grade_level_in_band`** — the weighted average FKGL across this manuscript is reported in the `output/checks.json` `details.value` field. The default band `10.0–18.0` is intentionally generous; tighten it for editorial review of public-facing material.
* **`citation_density_above_floor`** — citations per 1000 words must meet `prose.citation_density_min_per_1000`. The bundled config sets the floor to `0.0` (disabled) so the run is green out of the box; researchers should raise it to match the publication target.
* **`no_skipped_heading_levels`** — every file in this manuscript uses contiguous heading levels.
* **`every_file_has_h1`** — every prose file starts with an H1.
* **`bibliography_consistency`** — every `[@key]` in the prose resolves against `manuscript/references.bib`.

The figures in `output/figures/` are colour-blind-safe (Wong 2011 palette) [@wong2011points], 300 dpi, and PNG-only for archival stability. They are referenced in [@sec:pipeline_internals] where we walk through the on-disk artefact set in full.

The full pass/fail summary lands in `output/review_report.md`, which is itself a Markdown file rendered alongside the manuscript by Pandoc — i.e. the project reports on itself in the same compilation step that produces the manuscript PDF.
