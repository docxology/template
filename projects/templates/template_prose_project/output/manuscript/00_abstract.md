# Abstract {#sec:abstract}

This paper documents `template_prose_project`, the prose-focused exemplar of the [Research Project Template](https://github.com/docxology/template). It pairs the template's two-layer architecture with the [prose analysis infrastructure](https://github.com/docxology/template/tree/main/infrastructure/prose) (readability metrics, structural outline, editorial quality flags) and the [reference validation infrastructure](https://github.com/docxology/template/tree/main/infrastructure/reference) (BibTeX validation), demonstrating that **rigorous editorial review can be expressed as a configurable, deterministic pipeline** with no novel domain algorithm of its own.

A single `manuscript/config.yaml` defines target grade-level bands, citation-density floors, structural rules (every section has an H1, no heading levels skipped), and bibliography-consistency policy. The pipeline reads the manuscript, runs the prose analysers, cross-checks every `[@key]` citation against `manuscript/references.bib`, evaluates the configured checks, and writes a deterministic markdown review report alongside three figures (per-file word counts, readability metrics, citation density) and a JSON `manuscript_report.json` suitable for CI artefacts.

**Run snapshot.** The current configuration analyses 8 file(s) totalling 1745 words across 86 sentence(s) and 64 paragraph(s). Average Flesch-Kincaid grade level is 15.97; average Gunning Fog index is 16.73; the manuscript references 6 unique citation key(s); the longest section is 416 words and the shortest is 17. These numbers are auto-substituted by `scripts/z_generate_manuscript_variables.py` after every run, so the abstract tracks the JSON outputs in `output/`.

The contribution is methodological and architectural: a *generic, reusable* prose-quality module (`infrastructure/prose/`) that any project in the template can opt into, plus a *minimal, configurable* exemplar (`projects/templates/template_prose_project/`) that wires it to the bibliography and the manuscript pipeline.

**Keywords:** prose analysis, readability, editorial review, reproducible manuscript review, scientific infrastructure
