# References {#sec:references}

Bibliography lives in [`manuscript/references.bib`](references.bib) and is read by Pandoc during PDF render. The build pipeline invokes Pandoc with `--natbib`, so every `[@key]` citation in the manuscript is rewritten to the appropriate `\cite{}`/`\citep{}`/`\citet{}` LaTeX command and resolved against the bib file.

To validate that `references.bib` is syntactically clean and contains the required fields per entry type:

```bash
uv run python -m infrastructure.reference.citation.cli validate \
    projects/templates/template_autoscientists/manuscript/references.bib --strict
```
