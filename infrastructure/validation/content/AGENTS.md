# infrastructure/validation/content/ - Content Validation Documentation

## Purpose

Validators for content artifacts (PDFs, markdown sources, figures) that travel
through the rendering pipeline. These are pre-render checks; they fail fast
on classes of issues that would otherwise surface only as silent
LaTeX/pandoc warnings.

## Files

- `pdf_validator.py` - PDF text and structure validation
- `markdown_validator.py` - markdown structure validation, including
  Pandoc-pitfall and citation-key checks
- `figure_validator.py` - figure validation
- `diagnostic_codes.py` - stable, dotted IDs (`MarkdownCode`, `BibtexCode`)
  attached to every `DiagnosticEvent` emitted by `markdown_validator`

## `markdown_validator.py` — public API

| Function | Severity returned | Purpose |
|---|---|---|
| `find_markdown_files(dir)` | — | Sorted list of `*.md` under `dir`. |
| `collect_symbols(paths)` | — | Set of `\label{}` and `{#anchor}` names. |
| `validate_images(paths, root)` | ERROR | Referenced images resolve on disk. |
| `validate_refs(paths, root, labels, anchors)` | ERROR / WARNING | `\eqref` and `(#anchor)` resolve; bare URLs / non-informative link text. |
| `validate_math(paths, root)` | WARNING / ERROR | Bans `$$`/`\[`/`\]`; equation labels present and unique. |
| `validate_pandoc_pitfalls(paths, root)` | WARNING | Bare `\|word\|` in prose and `\|` inside Markdown table cells (Pandoc converts both to `\mid`). |
| `validate_citations(paths, root, bib_file=None)` | ERROR | Every `[@key]` resolves in `references.bib`. |
| `validate_markdown(dir, root, strict=False)` | aggregate | Runs all of the above. |

`AGENTS.md`, `README.md` and `preamble.md` are skipped by
`validate_pandoc_pitfalls` and `validate_citations` since they are not
combined into the rendered manuscript.

## Diagnostic codes

Every `DiagnosticEvent` emitted by `markdown_validator` carries a stable
`code` field (in addition to its free-form `message` and the coarse
`category` grouping). Codes are defined in
[`diagnostic_codes.py`](diagnostic_codes.py) and survive JSON round-trips
in `diagnostics.json`, so downstream tooling can filter or suppress
specific findings without parsing prose.

| Code                                  | Severity | Emitted by                         | What it means                                              |
|---------------------------------------|----------|------------------------------------|------------------------------------------------------------|
| `MARKDOWN.IMG_MISSING`                | ERROR    | `validate_images`                  | `![alt](path)` target not found on disk                    |
| `MARKDOWN.REF_EQUATION_MISSING`       | ERROR    | `validate_refs`                    | `\eqref{label}` has no matching `\label{}`                 |
| `MARKDOWN.LINK_ANCHOR_MISSING`        | ERROR    | `validate_refs`                    | `(#anchor)` has no matching heading or label               |
| `MARKDOWN.LINK_BARE_URL`              | WARNING  | `validate_refs`                    | Bare URL outside a Markdown link                           |
| `MARKDOWN.LINK_BAD_TEXT`              | WARNING  | `validate_refs`                    | Link text is the URL itself or otherwise non-informative   |
| `MARKDOWN.MATH_DOLLAR_DISPLAY`        | WARNING  | `validate_math`                    | `$$ ... $$` display math (use `equation` env)              |
| `MARKDOWN.MATH_BRACKET_DISPLAY`       | WARNING  | `validate_math`                    | `\[ ... \]` display math (use `equation` env)              |
| `MARKDOWN.MATH_LABEL_MISSING`         | WARNING  | `validate_math`                    | `equation` block without `\label{}`                        |
| `MARKDOWN.MATH_LABEL_DUPLICATE`       | ERROR    | `validate_math`                    | Same `\label{}` used twice                                 |
| `MARKDOWN.PANDOC_BARE_PIPE`           | WARNING  | `validate_pandoc_pitfalls`         | Bare `\|word\|` in prose -> Pandoc `\mid`                  |
| `MARKDOWN.PANDOC_TABLE_ESCAPED_PIPE`  | WARNING  | `validate_pandoc_pitfalls`         | `\|` in a Markdown table cell -> Pandoc `\mid`             |
| `BIBTEX.UNDEFINED_KEY`                | ERROR    | `validate_citations`               | `[@key]` not present in `references.bib`                   |

Filter examples:

```bash
# All bare-pipe pitfalls across every project's diagnostics report
rg 'MARKDOWN\.PANDOC_BARE_PIPE' projects/*/output/reports/

# Just the unresolved citations, JSON-flavoured
jq '.events[] | select(.code=="BIBTEX.UNDEFINED_KEY")' \
    projects/fep_lean/output/reports/diagnostics.json
```

Adding a new code is non-breaking; **changing** an existing code is a
breaking change for downstream filters and must be released with notice.

## Why the pitfall / citation checks exist

* `Bare |word|` and `\|` inside table cells become `\mid` after Pandoc
  conversion. Without an explicit math font, `\mid` falls back through
  the lmroman text font (no U+2223) and produces *Missing character*
  warnings + `U+FFFD` glyphs in the PDF. The lint catches the source
  pattern; the renderer fix-up (`infrastructure/rendering/_pdf_unicode_remap.py`
  and `ensure_setmathfont`) handles glyphs that escape the lint.
* Undefined `[@key]` citations only surface as *Citation undefined*
  warnings during the natbib pass at the end of a 60-second LaTeX
  compile. The audit catches them in milliseconds against
  `references.bib` before any LaTeX runs.

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
- [`../../rendering/AGENTS.md`](../../rendering/AGENTS.md) — `ensure_setmathfont`
  and `remap_prose_unicode` partner with these checks.
