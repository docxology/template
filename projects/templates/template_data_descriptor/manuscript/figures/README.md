# manuscript/figures - template_data_descriptor

Figure generation guide. All five figures embedded in the manuscript are produced
deterministically (fixed inputs, `MPLBACKEND=Agg`) from
`data/example_descriptor.json` and the fixture bytes by the thin script
[`scripts/generate_figures.py`](../../scripts/generate_figures.py), which calls
tested preparers in `src/data_descriptor/figures.py` and
`src/data_descriptor/verification.py`.

| Figure | Source preparer | Shows |
| --- | --- | --- |
| `schema_overview.png` | `schema_table_rows()` | Field data dictionary (type, nullability, unit, constraint). |
| `file_inventory.png` | `file_inventory_rows()` | Declared row counts per file. |
| `provenance_flow.png` | `provenance_steps()` | Ordered provenance chain and agents. |
| `quality_gate.png` | `severity_counts()` | Findings by severity: clean fixture vs. broken demo. |
| `checksum_verification.png` | `verify_descriptor_files()` | Declared vs. recomputed rows and checksum agreement. |

Regenerate with:

```bash
uv run python projects/templates/template_data_descriptor/scripts/generate_figures.py
```

The pipeline generates PNGs under `output/figures/` before rendering and records
its descriptor/check inputs under `output/data/`. Authored manuscript sources
remain unchanged. Regenerate outputs whenever the descriptor or fixtures change.
The historical PNGs in this source directory are retained for reference only;
current manuscript embeds use `../output/figures/<name>.png`.
