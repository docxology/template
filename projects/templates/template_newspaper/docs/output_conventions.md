# Output Conventions

All generated artifacts live under `output/` and are safe to delete; they are
fully regenerable from `content/` + `src/`. Never edit them by hand.

| Path | Produced by | Contents |
|------|-------------|----------|
| `output/pdf/the-triplicate.pdf` | `20_render_newspaper.py` | the 12-page newspaper (primary artifact) |
| `output/figures/*.png` | `10_generate_figures.py` | halftone scenes + charts referenced by pages |
| `output/data/render_report.json` | `20_render_newspaper.py` | `{page_count, all_pages_fit, oversets}` |
| `output/reports/render_summary.txt` | `20_render_newspaper.py` | human-readable render summary |
| `output/pdf/<manuscript>.pdf` | Stage-03 infra renderer | descriptive manuscript PDF |

`output_basename` in `content/edition.yaml` controls the newspaper filename.

The render report is the machine-checkable contract: a CI gate should assert
`page_count == 12` and `all_pages_fit == true`.
