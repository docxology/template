# Metadata pipeline family

Stage orchestration, export builders, and config-driven publication metadata
for the publishing pipeline.

```python
from infrastructure.publishing.metadata import metadata_stage, metadata_export

metadata_stage.run_metadata_package(...)
metadata_export.write_metadata_files(config, out_dir)
```

The flat `metadata_*.py` module paths remain as silent backwards-compat shims,
and the historical aggregate symbols (`extract_publication_metadata`,
`calculate_metadata_complexity_score`, ...) still resolve from
`infrastructure.publishing.metadata` itself. See [`AGENTS.md`](AGENTS.md).
