# `infrastructure/publishing/zenodo/`

Zenodo [REST Deposit API](https://developers.zenodo.org/) client and publish workflow.

## Module graph

| File | Role |
| --- | --- |
| `config.py` | `ZenodoConfig` — sandbox/production/base_url |
| `models.py` | `DepositionResult` — deposition id + bucket URL + reserved/concept DOI fields; `PublishResult` — DOI + deposition id |
| `client.py` | `ZenodoClient` — create, upload, publish, resolve DOI, new version |
| `publish.py` | `publish_to_zenodo()`, `publish_new_version_to_zenodo()`, `reserve_zenodo_deposition()`, `publish_reserved_deposition_to_zenodo()`, `patch_deposition_description()` |

## Public API

```python
from infrastructure.publishing.zenodo import (
    ZenodoClient,
    ZenodoConfig,
    DepositionResult,
    PublishResult,
    publish_to_zenodo,
    publish_new_version_to_zenodo,
    reserve_zenodo_deposition,
    publish_reserved_deposition_to_zenodo,
    patch_deposition_description,
)
```

Reserve-first orchestration (write concept/version DOI to config, re-render, upload) lives in
[`release_workflow_zenodo.py`](../release_workflow_zenodo.py); see
[`docs/guides/publishing-guide.md`](../../../docs/guides/publishing-guide.md).

### `DepositionResult.from_zenodo_body`

```python
DepositionResult.from_zenodo_body(body: dict[str, Any]) -> DepositionResult
```

Parses Zenodo deposition JSON (`metadata.prereserve_doi`, `conceptrecid`, `conceptdoi`) into a typed result. Used by `ZenodoClient.create_deposition` and `create_new_version`.

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

### `reserve_zenodo_deposition`

```python
reserve_zenodo_deposition(
    metadata: PublicationMetadata,
    access_token: str,
    sandbox: bool = True,
    *,
    base_url: str | None = None,
) -> DepositionResult
```

Creates a draft with `prereserve_doi=True` and returns reserved version/concept DOI fields.

### `publish_reserved_deposition_to_zenodo`

```python
publish_reserved_deposition_to_zenodo(
    metadata: PublicationMetadata,
    file_paths: list[Path],
    access_token: str,
    deposition: DepositionResult,
    sandbox: bool = True,
    *,
    base_url: str | None = None,
) -> PublishResult
```

Uploads to an existing reserved draft and publishes. Used by [`release_workflow_zenodo.py`](../release_workflow_zenodo.py) after config write-back and re-render.

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
