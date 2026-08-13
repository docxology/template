# Accessibility in Research Documentation

The template provides source-level checks and accessibility-oriented rendering
features. Those checks reduce common defects; they do **not** by themselves
establish WCAG conformance, PDF/UA conformance, or usability with assistive
technology. Release review must combine automated checks with inspection of the
rendered formats.

## Authoring contract

### Structure and navigation

- Use one meaningful H1 per manuscript section, followed by H2 and H3 without
  skipped levels.
- Use real Markdown lists and tables rather than visual alignment with spaces.
- Write descriptive link text that makes sense outside the surrounding sentence.
- Use the portable citation and cross-reference syntax in
  [`guides/manuscript-semantics.md`](guides/manuscript-semantics.md); do not
  encode structure through visual styling alone.

### Math and equations

- Use `$...$` for inline math and `$$...$$` for display math.
- Define symbols in prose and state the role of an equation; a rendered formula
  is not a substitute for an explanation.
- HTML output uses the repository's pinned MathJax path and adds accessibility
  annotations. Review the rendered speech/navigation behavior for the actual
  manuscript, especially for dense or custom notation.

### Figures, captions, and color

- A caption and alt text have different jobs. The caption interprets the figure
  and states data/statistical context; alt text conveys the visual structure,
  encodings, important trend, and information needed to follow the argument.
- Include axis meanings, units, group/panel identities, uncertainty encoding,
  sample or analysis scope, and any scale transform needed to interpret the
  display.
- Do not rely on color alone. Combine a colorblind-safe palette with labels,
  markers, line styles, patterns, or direct annotation, and verify contrast in
  the rendered artifact.
- Keep figure values, caption statistics, manuscript prose, and the figure
  registry bound to the same analysis output. Presence-only alt-text checks do
  not establish semantic adequacy.

## What the automated checks establish

| Check | Establishes | Does not establish |
| --- | --- | --- |
| `validation.cli markdown --strict` | Referenced image files, citations, labels/references, math delimiters, and known Pandoc pitfalls pass the source validator | Alt-text quality, heading semantics, color contrast, reading order, or rendered usability |
| `publication-audit --require-figure-accessibility` | Every referenced registered figure has a non-empty explicit `alt` or `metadata.alt_text` field, and registered generated files exist | Whether the text describes the figure well or whether unregistered decorative images are handled correctly |
| HTML renderer tests | Language metadata, a main landmark and skip link, MathJax hardening, responsive figures, and basic alt/caption post-processing are emitted by covered code paths | Whole-document WCAG conformance or screen-reader usability |
| PDF render/structural validation | The PDF was produced and passes the repository's structural checks; the LaTeX path requests tagged PDF/UA metadata when supported | A conforming tag tree, correct reading order, semantic tables/math, or PDF/UA certification |

Run the source and publication checks from the repository root, using a
qualified project name:

```bash
uv run python -m infrastructure.validation.cli markdown \
  projects/templates/template_code_project/manuscript --repo-root . --strict

uv run python -m infrastructure.validation.cli publication-audit \
  --project templates/template_code_project \
  --strict --require-figure-accessibility
```

Add `--rendered` to the publication audit only after regenerating the current
project outputs. That option checks rendered publication evidence; it still is
not a semantic accessibility certification.

## Rendered-artifact review

For every format intended for release:

1. Inspect the HTML with keyboard-only navigation, zoom/reflow, a screen reader,
   and a contrast checker. Verify focus order, skip navigation, headings, links,
   tables, math, and figure alternatives.
2. Inspect the PDF tag tree, reading order, headings, lists, tables, links,
   language, math, and figure alternatives with a PDF/UA-capable validator and
   assistive technology. Record the tool/version and any exceptions.
3. Inspect DOCX/EPUB semantics in their target readers rather than assuming the
   PDF or HTML result transfers unchanged.
4. Have a human reviewer compare each visualization with its caption, alt text,
   source data, and statistical claim.

`pdftotext` is useful as a text-extraction smoke test, but extracted text alone
cannot prove headings, tags, reading order, or PDF/UA conformance.

## Further reading

- [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/) — normative W3C web-content guidance.
- [PDF/UA-1 in a Nutshell](https://pdfa.org/resource/pdfua-in-a-nutshell/) — overview of the ISO accessibility requirements for PDF and conforming readers.
- [arXiv accessibility research report](https://info.arxiv.org/about/accessibility_research_report.html) — research-user needs and the case for accessible HTML alongside PDF/source.
