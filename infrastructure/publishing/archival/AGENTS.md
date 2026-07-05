# `infrastructure/publishing/archival/`

Multi-target archival mirror for long-horizon redundancy (Stage 13). Deposits an
executable bundle or publication artifact to independent providers so no single
provider policy change erases the record.

The canonical implementation lives in this subpackage. Import from
`infrastructure.publishing.archival` in new and existing code.

## Public API

```python
from infrastructure.publishing.archival import (
    ArchivalReceipt,
    ArchivalRun,
    ArchivalCredentials,
    ArchivalError,
    DEFAULT_CREDENTIALS_PATH,
    archive_publication,
    load_credentials,
)
```

### `models.py`

| Symbol | Notes |
| --- | --- |
| `ArchivalReceipt` | Per-provider result: `provider`, `success`, `deposit_id`, `url`, `error` |
| `ArchivalRun` | Aggregated result for one call: list of `ArchivalReceipt` + `dry_run` flag |
| `ArchivalCredentials` | Token bag loaded from env or JSON file; never logged |
| `ArchivalError` | Raised on unrecoverable provider errors |
| `DEFAULT_CREDENTIALS_PATH` | `~/.config/template-archival/credentials.json` |

### `providers.py`

`ArchivalProvider` protocol — all four providers implement `.deposit(bundle_path, credentials, dry_run) -> ArchivalReceipt`:

| Class | Credential env | Notes |
| --- | --- | --- |
| `ZenodoProvider` | `ZENODO_API_TOKEN` | Delegates to shared `ZenodoClient`; bundle mirror (no rich metadata) |
| `IPFSPinataProvider` | `PINATA_JWT` | Pinata pinning API |
| `IPFSWeb3StorageProvider` | `WEB3_STORAGE_TOKEN` | Web3.Storage pinning |
| `SoftwareHeritageProvider` | none | save-code-now (anonymous) |

### `orchestrate.py`

| Symbol | Role |
| --- | --- |
| `archive_publication(bundle_path, providers, dry_run)` | Fan out deposits; collect `ArchivalRun` |
| `load_credentials()` | Env vars first; fallback to `DEFAULT_CREDENTIALS_PATH` |

`dry_run=True` is the default at every layer — accidental imports cannot trigger
real deposits.

## Entry points

```bash
# Dry-run (default)
uv run python scripts/09_archive_publication.py --project {name}

# Real deposits (requires credentials)
uv run python scripts/09_archive_publication.py \
  --project {name} \
  --providers zenodo software_heritage ipfs_pinata \
  --commit
```

CLI wrapper: [`../archival_cli.py`](../archival_cli.py).

## Files

| File | Purpose |
| --- | --- |
| `__init__.py` | Re-exports all public symbols |
| `models.py` | `ArchivalReceipt`, `ArchivalRun`, `ArchivalCredentials`, `ArchivalError` |
| `providers.py` | `ArchivalProvider` protocol + 4 provider classes |
| `orchestrate.py` | `archive_publication()`, `load_credentials()` |

## Tests

```bash
uv run pytest tests/infra_tests/publishing/test_archival.py -q
```

## See also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md) — publishing module overview
- [`../zenodo/AGENTS.md`](../zenodo/AGENTS.md) — rich-metadata Zenodo path (distinct from archival mirror)
- [`docs/maintenance/archival-targets.md`](../../../docs/maintenance/archival-targets.md) — threat scenarios and provider rationale
