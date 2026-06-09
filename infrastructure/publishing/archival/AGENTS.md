# `infrastructure/publishing/archival/`

Folder-level routing doc for Stage 11 multi-target archival publication. Implementation
lives in the sibling module [`../archival.py`](../archival.py) (opt-in; not in the
default pipeline DAG).

## Purpose

Mirror an executable bundle or publication artifact to independent archival targets
so no single provider policy change erases the deposit. Supported providers (when
credentials are present):

| Provider | Module symbol | Credential env |
| --- | --- | --- |
| Zenodo | `ZenodoProvider` | `ZENODO_API_TOKEN` |
| IPFS (Pinata) | `IPFSPinataProvider` | `PINATA_JWT` |
| IPFS (Web3.Storage) | `IPFSWeb3StorageProvider` | `WEB3_STORAGE_TOKEN` |
| Software Heritage | `SoftwareHeritageProvider` | (anonymous save-code-now) |

## Entry points

```bash
# Dry-run (default — no network deposits)
uv run python scripts/09_archive_publication.py --project {name}

# Real deposits (requires credentials)
uv run python scripts/09_archive_publication.py \
  --project {name} \
  --providers zenodo software_heritage ipfs_pinata \
  --commit
```

CLI wrapper: [`../archival_cli.py`](../archival_cli.py).

## Public API

```python
from infrastructure.publishing.archival import (
    ArchivalRun,
    ArchivalReceipt,
    archive_publication,
    load_credentials,
)
```

`dry_run=True` is the default at every layer — accidental imports cannot trigger
real deposits.

## Design and credentials

- Threat scenarios and provider rationale:
  [`docs/maintenance/archival-targets.md`](../../../docs/maintenance/archival-targets.md)
- Stage 11 contract:
  [`docs/maintenance/stage-10-executable-bundle.md`](../../../docs/maintenance/stage-10-executable-bundle.md)
  (bundle) + archival stage in [`infrastructure/core/pipeline/pipeline.yaml`](../../core/pipeline/pipeline.yaml)
- Tokens: environment variables first; fallback
  `~/.config/template-archival/credentials.json` (never logged)

## Tests

```bash
uv run pytest tests/infra_tests/publishing/test_archival.py -q
```

## See also

- [`../AGENTS.md`](../AGENTS.md) — publishing module overview
- [`../zenodo/AGENTS.md`](../zenodo/AGENTS.md) — rich-metadata Zenodo path (distinct from archival mirror)
