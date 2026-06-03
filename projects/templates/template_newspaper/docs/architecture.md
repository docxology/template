# Architecture

## The core idea: drawn furniture, flowed body

A newspaper page has two kinds of element:

1. **Furniture** — fixed elements at known coordinates: the nameplate, the
   section banner, the folio, the hairline rules between columns, and the
   spanning lead headline. These are *drawn* on the canvas.
2. **Body** — the prose, which must wrap and *flow* down one column and into the
   next, splitting paragraphs as needed.

The engine draws the furniture first. Crucially, the furniture functions
**return the y-coordinate at which the column grid may begin**, so the flowed
body always clears the masthead/headline above it. Then the body flows through
ReportLab `Frame`s via `Frame.addFromList`, which handles paragraph splitting
across columns. This split is what lets a headline span four columns sit above
body text that flows beneath it — something a pure document-template cannot do.

```
            ┌───────────────────────── content box ─────────────────────────┐
 furniture  │  N A M E P L A T E   (drawn)            folio line (drawn)     │
   (drawn)  │  ───────────────────────────────────────────────────────────  │
            │  KICKER / SPANNING LEAD HEADLINE / deck  (drawn → returns y₀)   │
 body grid  │ rail │ col1   │ col2   │ col3   │ col4   │   ← frames start y₀  │
  (flowed)  │ idx  │ flows… │ flows… │ flows… │ flows… │                      │
            │ wx   │        │        │        │        │                      │
            │      │  folio rule (drawn)                                      │
            └────────────────────────────────────────────────────────────────┘
```

## Module map

| Module | Responsibility | Imports ReportLab? |
|--------|----------------|:--:|
| `geometry` | page trim, margins, `ColumnGrid` math | no |
| `typography` | font registration, paragraph stylesheet | yes |
| `content` | typed model + strict YAML loaders | no |
| `config` | strict render settings | no |
| `figures` | halftone scenes (Pillow) + charts (Matplotlib) | no |
| `components` | flowables: story, drop cap, box, table, pull quote, figure | yes |
| `furniture` | canvas drawing: nameplate, band, folio, rules, lead | yes |
| `layout` | frame construction + content flow per page | yes |
| `engine` | render the whole edition → PDF + report | yes |

## The rail

When a page sets `rail_enabled`, the leftmost area becomes a fixed-width rail
(`config.rail_inches`, default 1.55″) drawn independently of the main grid, so
the main columns keep a readable ~1.95″ measure (4 main columns beside the
rail; full-width editorial pages run 4 columns at ~2.4″). The rail gets its own flowable
list (index, weather, refers); the main well gets the lead body and the rest.
`page.columns` counts **main** columns; the rail is extra.

## Flow and over-set

`layout._flow` walks the frames, calling `addFromList` on each until content is
exhausted. Anything left over after the last frame is counted as **over-set** —
copy that did not fit. `RenderResult.oversets` reports it per page;
`all_pages_fit` is the single boolean a caller checks. Over-set is a failure, not
a warning: it means a reader would lose copy.

## Why ReportLab

Pure Python, no system pre-press dependencies (unlike WeasyPrint's pango/cairo),
and exact control of frames and vector rules — the precise primitives a column
grid needs. Fonts are registered best-effort with a base-14 fallback so the same
code renders on any machine.
