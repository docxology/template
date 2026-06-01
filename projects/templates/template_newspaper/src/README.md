# src/ — the newspaper engine

The `newspaper` package renders a structured edition to a PDF. Modules, in
dependency order:

| Module | Responsibility |
|--------|----------------|
| `geometry.py` | pure page/column arithmetic (no ReportLab) |
| `typography.py` | font registration + paragraph stylesheet (the only font namer) |
| `content.py` | typed content model + strict YAML loaders |
| `config.py` | strict render configuration |
| `figures.py` | halftone engravings (Pillow) + charts (Matplotlib) |
| `components.py` | flowables: story, drop cap, box, table, pull quote, figure |
| `furniture.py` | canvas drawing: nameplate, band, folio, rules, lead headline |
| `layout.py` | column-frame construction + content flow |
| `engine.py` | top-level render entry point |

Public API: `from newspaper import build_and_render, render_edition,
load_edition, load_newspaper_config`. See `../docs/architecture.md`.
