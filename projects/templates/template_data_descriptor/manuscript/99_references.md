# References {#sec:references}

This exemplar draws on established data-publishing practice: the FAIR guiding
principles for reusable data [@wilkinson2016fair], datasheets-style structured
dataset documentation [@gebru2021datasheets], the W3C PROV data model for
provenance [@moreau2013prov], and the Frictionless Data Package container format
for machine-readable descriptors [@frictionless2023datapackage].

The bibliography lives in [`manuscript/references.bib`](references.bib) and is
read by Pandoc during PDF render; every `[@key]` citation in the manuscript is
resolved against that file. To validate that `references.bib` is syntactically
clean and complete:

```bash
uv run python -m infrastructure.reference.citation.cli validate \
    projects/templates/template_data_descriptor/manuscript/references.bib --strict
```
