# Methods: Outline and chapter routing

Handbook chapters follow a **fixed template** (`HANDBOOK_TEMPLATE` in `src/outline.py`). Each chapter lists one or more `theme_ids`; evidence items whose `theme` matches are attached during synthesis.

Ordering is lexicographic by `section_id` after discovery in the manuscript directory; numeric prefixes (`04_`, `05_`, …) keep print and PDF alignment with the conceptual flow: landscape through recommendations. The template lists eight sections (`04_landscape` … `11_recommendations`); manuscript files `12_`–`14_` extend the bound volume with maintenance guidance, stakeholder notes, and schema appendix without altering the core scoring template unless `HANDBOOK_TEMPLATE` is edited in code.

**One-to-many routing.** A single theme id may feed multiple sections if the template repeats it, but in this exemplar each operational theme maps to its namesake chapter. Recommendations-themed evidence rolls into `11_recommendations`; risks-themed evidence into `10_risks`. That keeps reviewer mental models simple: the YAML `theme` field is the bucket name reviewers already use in workshops.

**Stability for tests and diffs.** The template can later be parameterized per area (e.g., coastal zones inserting hazard chapters) while keeping the same synthesis interface. For this exemplar, the outline is static so tests assert stable section counts, deterministic score keys, and reproducible `area_outline.json`. Any pull request that changes `HANDBOOK_TEMPLATE` should update tests, fixture expectations, and manuscript headings together.

**Manuscript discovery.** Rendering combines numbered section files, optional `S01_`–style supplemental markdown, then glossary and references buckets per `infrastructure.rendering.manuscript_discovery`. Authors should keep `section_id` strings in code, JSON, and filenames aligned so cross-links and gap reports do not drift.
