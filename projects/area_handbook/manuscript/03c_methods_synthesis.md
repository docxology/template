# Methods: Synthesis, gaps, and coverage scores

**Synthesis** (`src/synthesis.py`) maps each handbook section to the tuple of evidence items whose themes intersect the section's `theme_ids`. The **coverage score** is computed by `section_coverage_score()`: the sum of weights for that section, capped at $1.0$, so many weak items cannot masquerade as certainty.

Sections whose score is **strictly below** the configured gap threshold (default `DEFAULT_GAP_THRESHOLD = 0.35`) are listed in `gaps`. Callers may pass `synthesize(corpus, gap_threshold=…)` when a stricter or looser policy applies; the chosen value is stored on `SynthesisResult.gap_threshold` and echoed in JSON metrics via `build_metrics_report()` (`gap_threshold`, `gap_section_ids`, `gap_count`).

Figure \ref{fig:coverage} shows section-level scores for the Riverbend fixture. Figure \ref{fig:bytheme} shows how many evidence rows attach to each theme id in the same fixture. Figure \ref{fig:gapstatus} repeats the section ordering used in metrics export (sorted ids) and colors bars by membership in `gap_section_ids`, so readers can see which chapters would be flagged without rereading JSON.

![Riverbend fixture (version 2026.1): horizontal coverage score per handbook section (capped sum of matching evidence weights, range 0–1). Red dashed vertical line: current gap threshold from synthesis; sections strictly to the left would be listed in the JSON gaps array.](../output/figures/handbook_evidence_coverage.png){#fig:coverage width=85%}

Under the default threshold, the Riverbend exemplar places every outline section at or above the line (`gap_count` is zero in `handbook_report.json`), which is why the executive summary can describe a “fully covered” template run. The chart still documents the contract: any future corpus revision that drags a section left of the dashed line will surface automatically in the gap table from `build_gap_report_md()` and in pipeline metrics.

![Riverbend fixture: count of evidence rows per theme id after corpus validation (duplicate ids and invalid weights rejected at load). Bar height shows how many statements contribute to each thematic bucket used for section routing.](../output/figures/handbook_evidence_by_theme.png){#fig:bytheme width=80%}

The histogram is intentionally simple: it answers whether evidence volume is balanced across themes or concentrated in a few buckets. For Riverbend, economy, infrastructure, and recommendations each carry multiple rows, while every declared theme has at least one row (`themes_without_evidence` is empty). Editors use this view to spot missing thematic coverage before rewriting chapter prose.

![Same scores as the coverage chart, sorted by section id, with bars colored by gap status: coral = section id in gap_section_ids (score strictly below threshold); steel blue = at or above threshold. For this fixture under the default threshold, all sections are above the line (empty gap list), illustrating a fully covered outline.](../output/figures/handbook_section_gap_status.png){#fig:gapstatus width=85%}

When `gap_section_ids` is non-empty, coral bars identify exactly which sections require new evidence or threshold tuning before publication. The sort order matches `scores_by_section` keys in JSON, which keeps figure inspection aligned with diff review of `handbook_report.json`.

Markdown bodies for preview or annex publication are assembled in `src/handbook_md.py`: executive bullets, gap table, evidence-by-theme table, per-section evidence lists, and optional `build_toc_md()` for outline-only exports.
