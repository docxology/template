# Public Template Design System

This shared design system applies to every public `template_*` exemplar in the
generated [`active_projects.md`](../../docs/_generated/active_projects.md) roster.
It governs generated manuscript, web, PDF, figure,
dashboard, slide, and evidence-review outputs. It is not an app-shell or
product UI system; child `AGENTS.md` files may narrow it for a specific
exemplar without contradicting the shared research-artifact posture.

## 1. Atmosphere & Identity

Public template outputs should feel like reproducible research artifacts:
calm, legible, source-aware, and ready for inspection. The signature is
traceable clarity: every page should make the artifact, evidence boundary,
status, and source path understandable without decorative branding.

## 2. Color

### Palette

| Role | Token | Usage |
| --- | --- | --- |
| Surface primary | `color-surface-primary` | Manuscript and report backgrounds |
| Surface muted | `color-surface-muted` | Tables, callouts, appendix bands |
| Text primary | `color-text-primary` | Body, headings, labels |
| Text secondary | `color-text-secondary` | Captions, provenance, secondary metadata |
| Evidence pass | `color-evidence-pass` | Validated or complete evidence |
| Evidence warning | `color-evidence-warning` | Optional, skipped, or incomplete stages |
| Evidence fail | `color-evidence-fail` | Failed validation or unsupported claims |
| Accent | `color-accent` | Links, focus rings, selected series |

### Rules

- Use high-contrast palettes that survive print, PDF compression, and browser
  screenshots.
- Reserve saturated color for semantic roles: pass, warning, fail, selection,
  figure grouping, or active evidence state.
- Never rely on color alone. Labels, legends, captions, or status text must
  carry the same meaning.

## 3. Typography

### Scale

| Level | Use |
| --- | --- |
| Title | Manuscript, newspaper, textbook, or report title |
| H1-H3 | Document hierarchy and major sections |
| Body | Long-form prose and explanatory text |
| Small | Captions, provenance, footnotes, table notes |
| Mono | Code, paths, identifiers, generated variables |

### Rules

- Favor long-form reading over marketing display type.
- Body and table text must remain large enough for a browser-QA screenshot to
  verify without zooming.
- Use mono text for paths, identifiers, code, and generated artifact names.

## 4. Spacing & Layout

### Base Unit

Use a 4px base unit for web surfaces and preserve comparable rhythm in PDF
outputs.

### Rules

- Keep margins, figure widths, tables, captions, and callouts consistent within
  one artifact.
- PDF and web variants should preserve reading order, figure numbering, and
  caption placement even when pagination or line breaks differ.
- Use whitespace to separate evidence units, not to create decorative gaps.

## 5. Components

Reusable research-output components include title blocks, abstracts, section
headings, theorem or claim boxes, evidence tables, figure panels, captions,
appendices, provenance notes, validation summaries, and dashboard panels.

Each component should expose enough context to stand alone in review: source,
status, units, sample size, version, generated path, or validation state when
relevant. Do not introduce reusable components that imply unavailable
interactivity in static PDF outputs.

## 6. Motion & Interaction

Generated outputs must remain useful without motion or JavaScript. Interactive
web artifacts are progressive enhancement: static content, captions, links, and
evidence remain visible before hydration or with scripts disabled.

Motion should only explain state changes, should respect reduced-motion
preferences, and must never be required to read or validate a claim.

## 7. Depth & Surface

Use flat document surfaces by default. Borders, muted fills, and restrained
shadows may separate dense tables, warnings, callouts, figure groups, or
dashboard panels. Avoid nested app-card styling in manuscripts. Depth should
clarify artifact structure and print cleanly in grayscale.

## Browser QA Expectations

Browser QA is required when a change affects generated HTML, browser-mediated
PDF layout, rendered figures, dashboards, or interactive evidence pages. Capture
desktop and mobile screenshots when practical. Verify that text does not
overlap, figures load, legends remain readable, links are visible, tables fit or
scroll intentionally, and the first viewport identifies the artifact being
reviewed.

`template_newspaper` may substitute PDF/page-raster inspection for web QA when
the changed surface is the ReportLab newspaper layout.

## Template-Specific Boundaries

`template_textbook` should inspect book-style HTML pages in addition to the
copied manuscript index when textbook-specific rendering changes.
`template_code_project` should inspect dashboard artifacts when they are
generated. `template_madlib` should preserve config-owned token injection and
claim-ledger evidence. `template_autoscientists` and `template_sia` should keep
fixture-backed default QA separate from optional live external paths.
