# Archival publishing

Multi-target mirror for long-horizon redundancy (Stage 11). See [`archival.py`](../archival.py) and [`docs/maintenance/archival-targets.md`](../../../docs/maintenance/archival-targets.md).

## Entry points

| Symbol | Module | Role |
| --- | --- | --- |
| `archive_publication` | `archival.py` | Orchestrate deposits across providers |
| `load_credentials` | `archival.py` | Env + `~/.config/template-archival/credentials.json` |
| `main` | `archival_cli.py` | CLI wrapper (dry-run unless `--commit`) |

## Providers

| Provider class | Credential | Notes |
| --- | --- | --- |
| `ZenodoProvider` | `ZENODO_API_TOKEN` | Delegates to shared `ZenodoClient`; empty deposition metadata (bundle mirror) |
| `SoftwareHeritageProvider` | none | save-code-now API |
| `IPFSPinataProvider` | `PINATA_JWT` | Pinata pinning |
| `IPFSWeb3StorageProvider` | `WEB3_STORAGE_TOKEN` | Web3.Storage pinning |

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

## Related

- [`../executable_bundle.py`](../executable_bundle.py) — `bundle_project()` for Stage 10
- [`../zenodo/`](../zenodo/) — canonical Zenodo HTTP client used by `ZenodoProvider`
