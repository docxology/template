# manuscript/figures - template_data_descriptor

Generated figures embedded in the manuscript. All five are produced
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

These PNGs are committed so the manuscript renders on a fresh checkout; they are
regenerated (not hand-edited) whenever the descriptor or fixtures change.
