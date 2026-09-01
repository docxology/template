# Abstract

We specify a reproducible advanced literature-review workflow for rapidly changing
domains in which a single query does not adequately represent methodological or
temporal variation. The exemplar is configured for exoplanet atmospheric composition
and separates foundation, James Webb Space Telescope, and molecular-detection phases.

The design is informed by systematic-review reporting practice [@page2021prisma], but
this repository release is a methods exemplar rather than a completed systematic review:
its default corpus is synthetic and its phase boundaries, search coverage, and domain
interpretation require review for any live application.

The pipeline combines multi-engine retrieval, canonical de-duplication, deterministic
screening, optional LLM-assisted classification, full-text assessment, bibliometrics,
knowledge-graph construction, visualization, reproducibility assessment, and export.
Each stage has a declared input, output, method reference, and definition of done in
`methods_pipeline.yaml`. The numbered scripts are thin adapters; reusable computation
is tested in `src/`.

The manuscript is generated from configuration and recorded artifacts. Offline runs use
a clearly labelled synthetic fixture corpus with reserved identifiers and generated
authors; they exercise pipeline behavior and are not evidence about {{SEARCH_TERM}}.
Live runs
must retain retrieval reports, source provenance, claim classifications, and the exact
configuration needed to interpret reported results.

The contribution is therefore infrastructural: it makes phase-aware search design,
evidence boundaries, accessibility metadata, and reproducibility checks explicit while
leaving domain claims subject to source-backed review.

**Keywords:** {{KEYWORDS_LIST}}
