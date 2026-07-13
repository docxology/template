# infrastructure/core/files/ - File Helper Documentation

## Purpose

The `infrastructure/core/files/` package contains file cleanup, inventory, and output management helpers.

## Files

- `operations.py` - file operations used by the pipeline
- `serialization.py` - shared JSON/YAML read + relative-path helpers (`read_json_object`, `load_yaml_mapping`, `relative_or_self`) reused across infrastructure
- `portability.py` - sanitizes machine-local home prefixes from text publication artifacts before hashing/copying
- `project_lock.py` - per-project POSIX advisory lock serializing pipeline/test runs on the same `output/` tree
- `cleanup.py` - output cleanup coordination
- `cleanup_helpers.py` - cleanup helpers
- `cleanup_root.py` - root output cleanup
- `coverage_cleanup.py` - coverage artifact cleanup
- `inventory.py` - file inventory collection
- `inventory_entry.py` - inventory entries
- `inventory_reports.py` - inventory reporting
- `pdf_locator.py` - locate generated PDFs for validation and copy stages

## `project_lock.py`

Cross-process lock keyed by resolved project path (lock file under system temp, outside
`output/` so Stage-0 Clean cannot delete it). Pipeline executor and project test runner
acquire via `project_output_lock(project_root)`; subprocess test stages inherit an env
marker so re-acquisition is a no-op against the parent holder.

- `project_output_lock(project_root: Path, *, timeout: float | None = None) -> Iterator[None]`

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
