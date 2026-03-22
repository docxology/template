# Methods: Quality gates on the corpus file

Before synthesis runs, `src/corpus_io.py` rejects files that would silently corrupt metrics:

- **Unique ids** — Duplicate `themes[].id` or `evidence[].id` values raise `CorpusValidationError`.
- **Non-empty text fields** — Theme `label` and `description`, evidence `statement`, `source_label`, and `reviewed_at` must be non-blank after stripping.
- **Numeric weights** — Each `weight` must parse as a finite float in $[0, 1]$ (NaN and infinity are rejected).

These checks keep CI deterministic: the same YAML on disk always loads or always fails with an actionable message. Downstream `src/corpus_stats.py` then reports themes that have **zero** evidence rows, which is valid (reserved buckets) but visible in the executive summary Markdown.

**Operational implications.** Teams can run the project test suite locally before pushing corpus edits; failures point to line-level validation rather than cryptic PDF breaks later. The gates also protect multi-author editing: two contributors cannot both add `ev-001` without merge resolution—the second duplicate id triggers an exception at load.

**Cross-field consistency.** Every `evidence.theme` must reference an existing `themes[].id`. Typos therefore surface immediately (“economy” vs “economy_sector”) instead of producing silent empty matches during synthesis. Combined with the cap on section scores, these rules keep the handbook honest about what was reviewed and what was never supplied.

**Downstream consumers.** `handbook_report.json` carries `evidence_count`, `theme_count`, `gap_count`, and `themes_without_evidence`. Oversight bodies can treat non-zero `themes_without_evidence` or rising `gap_count` under a fixed threshold as signals to schedule evidence workshops—not as build failures, but as explicit visibility [@template2026].
