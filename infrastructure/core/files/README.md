# infrastructure/core/files/ - File Helpers

File cleanup, inventory, and output-copying helpers for `infrastructure.core`.

Package exports retain their existing providers and resolve on first use through
the established SDK lazy-export pattern. Importing a leaf such as `secure_write`
does not initialize cleanup, inventory or copying; requested public providers
are cached for subsequent access.

## Files

- `operations.py` — symlink-confined recursive local-mirror copying with PDF,
  HTML, slides, DOCX, EPUB, figure, data, report, simulation, LLM, and log counts
- `serialization.py`
- `secure_write.py`
- `cleanup.py`
- `cleanup_helpers.py`
- `cleanup_root.py`
- `coverage_cleanup.py`
- `inventory.py`
- `inventory_entry.py`
- `inventory_reports.py`
- `pdf_locator.py`

## See Also

- [`AGENTS.md`](AGENTS.md)
- [`../README.md`](../README.md)
