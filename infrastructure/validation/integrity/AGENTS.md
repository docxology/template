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
- `link_skip_policy.py` - `should_validate_path` plus `PATH_SKIP_SUBSTRINGS` / `PATH_SKIP_KEYWORDS` tables that exclude template/placeholder/example paths from filesystem checks
- `completeness.py` - build-artifact and output-tree completeness checks (`validate_build_artifacts`, `check_file_permissions`, `verify_output_completeness`) with `TypedDict` results
- `manifest.py` - integrity manifest create/save/load/verify (`create_integrity_manifest`, `save_integrity_manifest`, `load_integrity_manifest`, `verify_integrity_against_manifest`) using per-file hashes

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
