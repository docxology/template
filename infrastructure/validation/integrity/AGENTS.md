# infrastructure/validation/integrity/ - Integrity Validation Documentation

## Purpose

The `infrastructure/validation/integrity/` package contains link validation and file integrity helpers.

## Files

- `checks.py` - integrity checks (`verify_output_integrity`, manifests, build artifacts)
- `link_extract.py` - link extraction, path/import validators, `LinkCheckResult` (no CLI)
- `check_links.py` - link audit CLI; re-exports `discover_markdown_files` from `content.discovery` and helpers from `link_extract`
- `link_audit_core.py` - `run_link_audit(repo_root)` loop (uses `discover_markdown_files(..., scope="link_audit")`)
- `link_policies.py` - skip policies for anchors and generated paths
- `link_validator.py` - `LinkValidator` path resolution helpers

## Markdown discovery

Link audits do **not** define their own enumerator. Use:

```python
from infrastructure.validation.content.discovery import discover_markdown_files

md_files = discover_markdown_files(repo_root, scope="link_audit")
```

Repo-wide doc scans use `scope="repo"`. Manuscript dirs use `scope="tree"`.

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
- [`../content/discovery.py`](../content/discovery.py)
