# Metadata pipeline family

Stage orchestration, export builders, and config-driven publication metadata
for the publishing pipeline.

```python
from infrastructure.publishing.metadata import metadata_stage, metadata_export

metadata_stage.run_metadata_package(...)
metadata_export.write_metadata_files(config, out_dir)
```

Import the nested `metadata.*` modules directly. The package exports
`extract_publication_metadata`, `calculate_metadata_complexity_score`, and the
other public metadata functions directly from their implementation modules.
See [`AGENTS.md`](AGENTS.md).
