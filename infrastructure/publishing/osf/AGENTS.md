# OSF Publishing Adapter

## Purpose

Publishes manuscript and reproducibility bundles to Open Science Framework nodes
for open-science sharing alongside DOI and repository publication channels.

## Modules

| Module | Role |
| --- | --- |
| `models.py` | `OSFConfig`, `OSFResult` — frozen config/result dataclasses (node title/id, category, public flag, separate `api_base` + `files_base` Waterbutler endpoints, `storage_provider`); token defaults to `OSF_TOKEN`, and `OSFResult.ok` is `True` when `status == "ok"` |

## Contracts

- Keep `dry_run=True` as the safe default.
- Resolve tokens from explicit config first, then `OSF_TOKEN`; never log token
  values.
- Keep metadata calls and Waterbutler file uploads separately configurable so
  tests can use local HTTP servers.
- Return structured `OSFResult` values instead of raising on HTTP, credential,
  or partial-upload failures.
- Do not add DOI-registration behavior here; this adapter creates or updates
  editable OSF nodes.

## Verification

```bash
uv run pytest tests/infra_tests/publishing/test_osf_adapter.py
```

## Parent Docs

- Publishing module: [`../AGENTS.md`](../AGENTS.md)
- Adapter README: [`README.md`](README.md)
