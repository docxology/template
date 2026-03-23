# Scripts

| Script | Output |
|--------|--------|
| `generate_layout_schematic.py` | `../output/figures/layout_schematic.png` |
| `generate_masthead.py` | `../output/figures/masthead.png` |
| `generate_section_banners.py` | `../output/figures/section_banner_*.png` (19 stems) |
| `report_manuscript_stats.py` | `../output/data/manuscript_stats.json` |
| `visualization_wordcount_bw.py` | `../output/figures/wordcount_bars_bw.png` (needs stats JSON first) |

Run via `python scripts/02_run_analysis.py --project traditional_newspaper` from repo root (sets `PROJECT_DIR`). Analysis discovers scripts in **sorted filename order**; the word-count chart script must run after `report_manuscript_stats.py` (`v` sorts after `r`).
