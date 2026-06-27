# Archival publishing

Multi-target mirror for long-horizon redundancy (Stage 11). See
[`docs/maintenance/archival-targets.md`](../../../docs/maintenance/archival-targets.md)
for provider rationale and threat scenarios.

## Entry points

| Symbol | Module | Role |
| --- | --- | --- |
| `archive_publication` | `orchestrate.py` | Fan out deposits across providers |
| `load_credentials` | `orchestrate.py` | Env + `~/.config/template-archival/credentials.json` |
| `main` | `../archival_cli.py` | CLI wrapper (dry-run unless `--commit`) |

## Providers

| Class | Credential | Notes |
| --- | --- | --- |
| `ZenodoProvider` | `ZENODO_API_TOKEN` | Delegates to shared `ZenodoClient`; bundle mirror |
| `SoftwareHeritageProvider` | none | save-code-now API |
| `IPFSPinataProvider` | `PINATA_JWT` | Pinata pinning |
| `IPFSWeb3StorageProvider` | `WEB3_STORAGE_TOKEN` | Web3.Storage pinning |

## Usage

```python
from pathlib import Path
from infrastructure.publishing.archival import archive_publication, load_credentials

credentials = load_credentials()  # reads env vars / credentials.json

# Dry-run (default — no network deposits)
run = archive_publication(
    bundle_path=Path("output/my_project/executable_bundle"),
    providers=["zenodo", "software_heritage", "ipfs_pinata"],
    dry_run=True,
    credentials=credentials,
)
for receipt in run.receipts:
    print(receipt.provider, receipt.success, receipt.url)

# Real deposits
run = archive_publication(
    bundle_path=Path("output/my_project/executable_bundle"),
    providers=["zenodo", "software_heritage"],
    dry_run=False,
    credentials=credentials,
)
```

## CLI

```bash
# Dry-run (default)
uv run python -m infrastructure.publishing.archival_cli \
  --bundle output/<project>/executable_bundle \
  --providers zenodo

# Real deposit
uv run python -m infrastructure.publishing.archival_cli \
  --bundle output/<project>/executable_bundle \
  --providers zenodo software_heritage \
  --commit
```

Pipeline stage: `uv run python scripts/09_archive_publication.py --project <name>` (expects Stage 10 bundle).

## Backwards compatibility

`from infrastructure.publishing.archival import ...` continues to work via the flat
[`../archival.py`](../archival.py) re-export. Prefer importing from this subpackage
for new code.

## Related

- [`AGENTS.md`](AGENTS.md) — module internals, file list, provider protocol
- [`../executable_bundle.py`](../executable_bundle.py) — `bundle_project()` for Stage 10
- [`../zenodo/`](../zenodo/) — canonical Zenodo HTTP client used by `ZenodoProvider`
