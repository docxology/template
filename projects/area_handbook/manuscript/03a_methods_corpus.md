# Methods: Corpus model

The **area corpus** is a YAML (or JSON) document with:

- **Identity** — `area_id`, `area_label`, and semantic `version`.
- **Themes** — Stable identifiers used to route evidence into handbook chapters; each theme includes human-readable `label` and `description` for glossaries and reviewer orientation.
- **Evidence** — Atomic statements with `theme`, `weight` in $[0,1]$, `source_label`, and `reviewed_at`.

Validation rejects unknown themes, out-of-range or non-finite weights, blank text fields, **duplicate** `themes[].id` or `evidence[].id` values, and missing keys so corrupt files fail fast at load time. The loader lives in `src/corpus_io.py` and is covered by dedicated tests (including JSON and YAML entry points).

**Weights as bounded signals.** Each evidence `weight` is a single scalar in $[0,1]$. It is not a probability distribution across rows; it is a reviewer-assigned strength or credibility hint. During synthesis, `section_coverage_score()` sums weights for all evidence whose `theme` matches a section’s `theme_ids`, then caps the sum at $1.0$. That cap prevents stacking many low-confidence rows into an artificially “certain” chapter score.

**Provenance is intentionally lightweight.** The field `source_label` names the document, export, or system row that justified the statement—e.g., “Regional GIS Compendium 2024” or “DOT condition database export”—without embedding a full citation graph in the corpus. Bibliographic detail remains in `references.bib` for the manuscript narrative layer. `reviewed_at` uses ISO-8601 dates so freshness checks sort lexicographically and render cleanly in Markdown tables.

**Riverbend shape.** The fixture declares eight themes (landscape through recommendations) and seventeen evidence rows. Every theme receives at least one row, which yields an empty `themes_without_evidence` list in metrics—a deliberate “happy path” for teaching the pipeline. Sparse corpora in tests demonstrate the opposite: empty `themes_without_evidence` is not guaranteed when teams add themes before evidence arrives.
