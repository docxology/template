# Manuscript conventions (not part of the built PDF)

Authoring rules for Markdown under `manuscript/`. This file replaces the former `manuscript/SYNTAX.md`, which was incorrectly picked up as a supplemental section because its filename started with `S`.

- Citations: `[@khinchin1964continued]`; keys must exist in `manuscript/references.bib`.
- Equations: use `\begin{equation}` / `\label{eq:...}`; reference with `\ref{eq:...}`.
- Figures: `![caption text](../output/figures/name.png){#fig:label}`; reference with `\ref{fig:label}` in prose. The alt text becomes the LaTeX figure caption.

See `infrastructure/rendering` for Pandoc, natbib, and cross-reference details.
