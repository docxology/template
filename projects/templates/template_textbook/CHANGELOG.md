# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/) and this project adheres to
[Semantic Versioning](https://semver.org/).

## [0.1.0] — 2026-06-03

Initial public release of **The Template Textbook** — a modular, fillable
scaffold for book-length technical works.

### Added

- **Data-driven manuscript** — `manuscript/config.yaml` is the single source of
  truth (Parts → chapters → labs → question banks → appendices). 4 Parts, 12
  chapters, 12 labs, 12 question banks.
- **Tested computational backbone** — `src/textbook/` (`models`, `config`, `toc`,
  `content`, `constants`) with the worked formalisms (logistic growth, saturating
  response, exponential decay, linear fit, descriptive statistics).
- **Content engine** — `content.scaffold_chapter` / `validate_chapter` generate
  and verify stub chapters against one structural contract.
- **Figure gallery** — `src/visualization/gallery.py` with 18 deterministic plot
  types; `src/visualization/plots.py` worked-model + per-chapter figures.
- **Mermaid diagrams** — 11 diagram kinds (flowchart, sequence, state, class, ER,
  gantt, pie, mindmap, timeline, quadrant, journey) from `diagram_specs.yaml`.
- **Format gallery + formalisms appendices** — worked examples of every content
  primitive (text, lists, callouts, tables, math, figures, diagrams, code,
  cross-references, citations, media) and every formal element (definitions,
  theorems with proofs, algorithms, derivations, equation systems).
- **Two finished exemplar chapters** (`first_principles`, `case_studies`) showing
  the stub→finished workflow; the other chapters ship as marked stubs.
- **Multi-format rendering** — combined PDF, HTML, EPUB, and DOCX.
- **Test suite** — no-mocks, ≥90% coverage; structural-integrity tests bind the
  manuscript to the engine contract.

[0.1.0]: https://github.com/docxology/template_textbook/releases/tag/v0.1.0
