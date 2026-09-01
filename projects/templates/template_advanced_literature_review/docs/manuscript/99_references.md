# References

The bibliography is generated automatically during PDF compilation from `references.bib`.
Every citation key used in the manuscript has a matching bibliography entry, and the
checked-in bibliography contains only sources required by the manuscript sections.
Pandoc's `--natbib` flag injects `\usepackage{natbib}` and
`\bibliographystyle{plainnat}`, so neither directive appears in this section or in
`preamble.md`.

\bibliography{references}

<!--
References management notes:

* Entries are maintained in `references.bib` (BibTeX format).
* Each entry must include `title`, `author` (or `editor`), and `year`.
* DOIs are preferred over URLs where available.
* When adding a new citation, run the integrity sweep documented in `AGENTS.md`
  to confirm a 1:1 match between cited keys and bibliography entries.
-->
