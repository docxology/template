# Supplement: Worked example — reading Riverbend end to end

This note walks a reviewer from fixture file to rendered artifacts without running commands, highlighting how ids line up across layers.

**1. Load and validate.** `src/corpus_io.load_corpus` reads `riverbend_area.yaml`, checks ids, weights, and theme membership, and builds an `AreaCorpus` object. Failure modes include duplicate `ev-001` or a `weight` of `nan`.

**2. Outline.** `build_handbook_outline` returns `HANDBOOK_TEMPLATE`: eight sections from `04_landscape` through `11_recommendations`, each with `theme_ids` that pick up matching evidence.

**3. Synthesis.** `synthesize` attaches evidence to sections, sums weights with a cap of $1.0$, compares each score to `DEFAULT_GAP_THRESHOLD` (0.35), and fills `gaps` with ids strictly below threshold. Riverbend under defaults yields an empty gap tuple because every section clears the bar.

**4. Metrics JSON.** `build_metrics_report` flattens scores, gap lists, theme histograms, and descriptive stats. A CI job can assert `evidence_count == 17` and `themes_without_evidence == []` for this fixture.

**5. Markdown bodies.** `build_full_handbook_body` emits section headings, evidence lists, and tables suitable for annex publication; `handbook_toc.md` mirrors outline depth.

**6. Figures.** `02_generate_handbook_figure.py` plots scores, theme counts, and gap-colored bars, then registers `fig:coverage`, `fig:bytheme`, and `fig:gapstatus` in `figure_registry.json` so `validate_figure_registry` passes during output validation.

**7. Manuscript.** Numbered markdown sections plus this supplemental file combine through manuscript discovery; Pandoc assigns figure numbers from attributes `{#fig:...}` while preserving `\ref{...}` in PDF.

**Traceability spot check.** If prose cites “47 priority bridges,” the reviewer should find `ev-007` with that statement and DOT export provenance. If not, the narrative drifted from the corpus [@gray2005].
