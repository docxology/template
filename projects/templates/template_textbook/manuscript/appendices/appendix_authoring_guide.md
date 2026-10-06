# Appendix A — Authoring and Verification {#sec:appendix_authoring_guide}

<!-- chapter-metadata-badge -->
> Reference appendix · For authors and contributors.

A technical book needs a traceable path from an idea to an explanation, a computation, and a checked artifact. This appendix describes that path for this book. The canonical chapters are authored examples. The separate scaffolding API creates draft outlines for new work; generating an outline does not establish that a chapter is ready to teach.

## Declare the structure

The live structure uses `units:` in `config.yaml`. Each unit declares a directory, an introduction, and a list of chapter files. The chapter stem connects its source to its lab, question bank, and figure. For example, `part_II/dynamics_and_change.md` connects to `labs/part_II/lab_dynamics_and_change.md` and `questions/part_II/q_dynamics_and_change.md`. A renamed file requires all three entries and their section references to move together. Keep software release metadata separate from publication evidence; an intended version does not turn an old DOI into a new deposit.

The engine derives the table of contents from this configuration. Authors supply stable labels such as `{#sec:part_II_dynamics_and_change}`; rendering supplies display numbers. Do not write a second chapter roster in a script or assume that changing a display title changes the source filename.

## Create a draft without replacing authored work

From the project directory, `uv run python scripts/scaffold_chapter.py` creates only missing files. Its structural contract supplies headings, a learning blueprint, a labelled formalism, and companion locations. Fill each instructional element with a purpose, assumptions, an example, and an answer that a learner can inspect. Retain useful structure while replacing draft markers with authored material. Keep generation tests in temporary directories so tests never rewrite the canonical manuscript.

A chapter should answer a concrete question. Name its state, observations, units, model, and limits before choosing a computation. A lab should make a prediction before running code, show the resulting arithmetic, and discuss a failure case. A question bank should include answers with reasoning, rather than simply repeating definitions. A correct calculation under explicit assumptions is a useful result even when it does not establish a real-world claim.

## Bind prose to computation

Put reusable mathematics in `src/textbook/models.py`; scripts coordinate calls and file output. For a worked numerical example, independently derive a small exact case and assert it in runnable Python. For growth, the initial condition and carrying-capacity limit are separate checks. For decay, compare a half-life ratio with a direct exponential evaluation. For a fit, inspect residuals as well as the displayed slope.

Figures come from `src/visualization/plots.py`. Run `uv run python scripts/generate_figures.py` to generate deterministic plots from declared model parameters and the bundled instructional fixture. Explain the axes, units, and uncertainty convention in the caption and supply meaningful alt text. A fixed random seed can make an illustration reproducible; it cannot make simulated observations into empirical measurements.

Mermaid specifications live in `src/mermaid/diagram_specs.yaml`. Run `uv run python scripts/generate_diagrams.py` to produce diagram assets. Where a rendering backend is unavailable, a saved source specification preserves the diagram's content but is not evidence that a graphical artifact rendered successfully.

## Cite and cross-reference responsibly

Citations resolve to `references.bib`. Record publisher-verified authors, title, year, and DOI or URL; explain precisely why the source is useful. This book uses primary publications for model adequacy, scientific computing, communication, computation, dynamics, and reproducibility. A citation does not transfer every claim in a chapter to its source. Mathematical examples derived here should identify their assumptions and derivation.

Glossary links use the anchors declared in `GLOSSARY_ANCHORS` and authored in `glossary.md`. Figures, tables, equations, and sections use `[@fig:...]`, `[@tbl:...]`, `[@eq:...]`, and `[@sec:...]`. Keep labels unique. A section reference is preferable to a hand-written page number because pagination varies across PDF, HTML, and EPUB.

## Require content completion

Run `uv run python scripts/audit_textbook_quality.py --require-complete`. The completion mode requires every configured chapter, introduction, front-matter file, lab, question bank, and reference section to exist and contain no draft markers. Structural mode remains available for deliberate new outlines. Neither mode can infer scientific truth from the absence of markers.

Run the isolated project test suite after source changes. Its model cases, configuration controls, manuscript integrity checks, and runnable examples provide distinct evidence. Inspect the changed source and final artifacts as well. A passing test suite does not certify that every explanation is sufficient for every audience, and a render that finishes does not establish that its numeric claims match the source.

## Contributor checklist

Before accepting a chapter, verify its question, assumptions, numerical example, figure, citations, lab solution, and question answers. Preserve the source data and release history. Record the interpreter and commands used for local verification, identify missing rendering backends, and keep publication pending until the intended artifacts actually exist. This practice follows the reproducible computational workflow discussed by Sandve and colleagues [@sandve2013ten] and the tested software practices discussed by Wilson and colleagues [@wilson2014best].
