# infrastructure/core/files/ - File Helper Documentation

## Purpose

The `infrastructure/core/files/` package contains file cleanup, inventory, and output management helpers.

## Files

- `operations.py` - symlink-confined recursive local-mirror copying and per-format counts, including DOCX and EPUB; Stage 5 separately validates and reports the stable/shippable publication subset
- `serialization.py` - shared JSON/YAML read + relative-path helpers (`read_json_object`, `load_yaml_mapping`, `relative_or_self`) reused across infrastructure
- `portability.py` - sanitizes machine-local home prefixes from text publication artifacts before hashing/copying
- `project_lock.py` - per-project POSIX advisory lock serializing pipeline/test runs on the same `output/` tree
- `secure_write.py` - symlink-confined atomic UTF-8 writes for security-sensitive evidence
- `cleanup.py` - output cleanup coordination
- `cleanup_helpers.py` - cleanup helpers
- `cleanup_root.py` - root output cleanup
- `coverage_cleanup.py` - coverage artifact cleanup
- `inventory.py` - file inventory collection
- `inventory_entry.py` - inventory entries
- `inventory_reports.py` - inventory reporting
- `pdf_locator.py` - locate generated PDFs for validation and copy stages

## Confined text writes

`atomic_write_text_confined(root, target, content, *, mode=0o644)` writes UTF-8
through exclusive temporary files and held directory descriptors. The default
permissions are unchanged; callers can request `0o600` for checkpoints or retain
an existing HTML file's mode. Symlink targets and escaped paths are rejected.

## `project_lock.py`

Cross-process lock keyed by resolved project path (lock file under system temp, outside
`output/` so Stage-0 Clean cannot delete it). Pipeline executor and project test runner
acquire via `project_output_lock(project_root)`; subprocess test stages inherit an env
marker so re-acquisition is a no-op against the parent holder.

- `project_output_lock(project_root: Path, *, timeout: float | None = None) -> Iterator[None]`

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
