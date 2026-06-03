# Manuscript Syntax

This directory holds the **descriptive manuscript** about the engine, not the
newspaper edition. It follows the shared monorepo manuscript conventions:

- One Markdown file per section, numbered `NN_name.md`; files are concatenated
  in lexicographic order at render time.
- `00_abstract.md` first, `99_references.md` last.
- `config.yaml` carries paper metadata (title, authors, keywords).
- `references.bib` holds BibTeX entries; cite with `[@key]`.
- Standard Markdown: ATX headings (`#`, `##`), one `#` (H1) per section file.

The **newspaper edition** content is *not* here — it lives as YAML under
`../content/`. See `../docs/syntax_guide.md` for the edition content schema.
