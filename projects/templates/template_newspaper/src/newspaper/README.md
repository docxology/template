# `template_newspaper/src/newspaper/`

The newspaper layout engine — *The Triplicate*. A small ReportLab pipeline that
turns a data-only edition (`content/`) into a print-ready PDF. Each module has
one responsibility; the analysis scripts in `scripts/` delegate here so the
render is testable without shell logic.

## Files

| File | Role |
| --- | --- |
| `__init__.py` | Package exports for the layout engine. |
| `geometry.py` | Page and column geometry — trim, margins, `ColumnGrid` (pure arithmetic, no rendering import). |
| `content.py` | Editorial content model (`Edition`, `Page`, `Story`, `Box`, `Figure`, `Block`) and strict YAML loaders. |
| `config.py` | Typed, strict access to the render configuration (trim, columns, rail, gutter). |
| `typography.py` | Font registration and the paragraph stylesheet. |
| `components.py` | Flowable builders — headline, byline, body, drop cap, pull quote, ruled box, table, figure. |
| `furniture.py` | Drawn (not flowed) elements — nameplate, section banner, folio, column rules, spanning headline. |
| `layout.py` | Page composition — build column frames and pour flowables; reports over-set pages. |
| `figures.py` | Figure generation — halftone "engravings" and grayscale newspaper charts. |
| `engine.py` | Top-level render — fonts, stylesheet, canvas, per-page render, PDF + render report. |

## See Also

- [`../../content/README.md`](../../content/README.md) — the edition this engine renders
- [`../../manuscript/02_engine_architecture.md`](../../manuscript/02_engine_architecture.md) — architecture and method
- [`AGENTS.md`](AGENTS.md) — source-layer editing rules
