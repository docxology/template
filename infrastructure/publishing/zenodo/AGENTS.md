# `infrastructure/publishing/zenodo/`

Zenodo [REST Deposit API](https://developers.zenodo.org/) client and publish workflow.

## Module graph

| File | Role |
| --- | --- |
| `config.py` | `ZenodoConfig` — sandbox/production/base_url |
| `models.py` | `DepositionResult` — deposition id + bucket URL; `PublishResult` — DOI + deposition id |
| `client.py` | `ZenodoClient` — create, upload, publish, resolve DOI, new version |
| `publish.py` | `publish_to_zenodo()`, `publish_new_version_to_zenodo()` |

## Public API

```python
from infrastructure.publishing.zenodo import (
    ZenodoClient,
    ZenodoConfig,
    DepositionResult,
    PublishResult,
    publish_to_zenodo,
    publish_new_version_to_zenodo,
)
```

### `ZenodoClient`

- `create_deposition(metadata: dict | None = None) -> DepositionResult`
- `upload_file(bucket_url: str, file_path: Path, *, object_key: str | None = None) -> None`
- `publish(deposition_id: str) -> str` — returns DOI
- `resolve_deposition_id_from_doi(doi: str) -> str`
- `create_new_version(deposition_id: str) -> DepositionResult`
- `get_deposition(deposition_id: str) -> dict`
- `delete_deposition_file(deposition_id: str, file_id: str) -> None`
- `clear_deposition_files(deposition_id: str) -> list[str]` — removes inherited draft files before new-version upload
- `update_deposition_metadata(deposition_id: str, metadata: dict) -> None`

Uploads target `deposition.links.bucket` from the create response (not the deposition id).

### `publish_to_zenodo`

```python
publish_to_zenodo(
    metadata: PublicationMetadata,
    file_paths: list[Path],
    access_token: str,
    sandbox: bool = True,
    *,
    base_url: str | None = None,
) -> PublishResult
```

### `publish_new_version_to_zenodo`

```python
publish_new_version_to_zenodo(
    metadata: PublicationMetadata,
    file_paths: list[Path],
    access_token: str,
    existing_doi: str,
    sandbox: bool = True,
    *,
    base_url: str | None = None,
) -> PublishResult
```

Clears inherited files on the new-version draft before upload so published records do not retain superseded PDF names.

## Environment variables

| Variable | Use |
| --- | --- |
| `ZENODO_TOKEN` | Default token for CLI / scripts |
| `ZENODO_PROD_TOKEN` | Production token (CLI fallback) |
| `ZENODO_SANDBOX_TOKEN` | Sandbox token (CredentialManager) |
| `ZENODO_API_TOKEN` | Archival provider credential name |

## Tests

```bash
uv run pytest tests/infra_tests/publishing/test_zenodo_client.py tests/infra_tests/publishing/test_api.py -v
```

## See also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
- [`../archival.py`](../archival.py) — `ZenodoProvider` delegates to `ZenodoClient`
