# References {#sec:references}

The bibliography lives in [`manuscript/references.bib`](references.bib) and is
read by Pandoc during PDF rendering. Every `[@key]` citation in the manuscript is
resolved against that file, so the reference list below is generated from the
cited entries rather than maintained by hand.

To validate that `references.bib` is syntactically clean and has the required
fields per entry type, run from the repository root:

```bash
uv run python -m infrastructure.reference.citation.cli validate \
    projects/templates/template_registered_report/manuscript/references.bib --strict
```
