# data/fixtures - AGENTS.md

Public, synthetic fixture bytes only. If you edit a CSV here, recompute its
sha256 checksum and row count and update the matching entry in
`data/example_descriptor.json` — otherwise `verify_descriptor_files()` reports a
mismatch and the tests fail. Recompute with:

```bash
uv run python -c "from pathlib import Path; from data_descriptor import compute_file_digest, count_csv_rows; p=Path('projects/templates/template_data_descriptor/data/fixtures/measurements.csv'); print(compute_file_digest(p), count_csv_rows(p))"
```

Never place real restricted data here; represent it with descriptor metadata and
checksums instead.
