# References {#sec:references}

Bibliography lives in [`manuscript/references.bib`](references.bib) and is read by Pandoc during PDF render. The build pipeline invokes Pandoc with `--natbib`, so every `[@key]` citation in the manuscript is rewritten to the appropriate `\cite{}`/`\citep{}`/`\citet{}` LaTeX command and resolved against the bib file.

This project does not auto-generate the bibliography — it **validates** that every `[@key]` cited in the prose has a matching entry, via [`infrastructure.reference.citation.parse_bibfile`](../../../../infrastructure/reference/citation/SKILL.md). The check policy is configured under `bibliography:` in [`config.yaml`](config.yaml).

To validate that `references.bib` is syntactically clean:

```bash
uv run python -m infrastructure.reference.citation.cli validate \
    projects/template_prose_project/manuscript/references.bib --strict
```
