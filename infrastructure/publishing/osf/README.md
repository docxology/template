# OSF (Open Science Framework) adapter

Create an OSF node (project) and deposit a manuscript / reproducibility bundle
into its storage. Useful for open-science data sharing and preregistration-style
publication alongside Zenodo.

## Methods

OSF deliberately separates **metadata** (`api.osf.io`) from **file I/O**
(`files.osf.io`, the Waterbutler service). The adapter mirrors that split with
raw `requests`, so both bases are configurable for hermetic `pytest-httpserver`
testing:

1. **Create node** (only when `node_id` is not supplied) —
   `POST {api_base}/nodes/` with a JSON:API body:

   ```json
   {"data": {"type": "nodes",
             "attributes": {"title": "...", "category": "project", "public": true}}}
   ```

   Response `data.id` is the 5-char node GUID (e.g. `ab12c`).

2. **Upload each file** — `PUT {files_base}/resources/{node_id}/providers/{provider}/?kind=file&name=<name>`
   (Waterbutler), raw bytes as the body. Default provider is `osfstorage`.

The public node URL is `https://osf.io/{node_id}/`.

## Usage

```python
from pathlib import Path
from infrastructure.publishing.osf import OSFAdapter, OSFConfig

# New public node from a title:
adapter = OSFAdapter(OSFConfig(title="My Paper", category="project", public=True))
print(adapter.publish(Path("output/bundle"), dry_run=True).extra)   # safe preview

# Real deposit (token from OSF_TOKEN, or pass token=...):
result = adapter.publish(Path("output/bundle"), dry_run=False)
print(result.status, result.node_id, result.url)

# Deposit into an existing node (skips creation):
OSFAdapter(OSFConfig(node_id="ab12c", token="...")).publish(Path("bundle"), dry_run=False)
```

## Credentials

- `OSF_TOKEN`, a personal access token from
  <https://osf.io/settings/tokens> with `osf.full_write` scope. Keep it in the
  repo-root `.env` (gitignored) or the environment — never committed.

## Contract

- `dry_run=True` is the default and never touches the network.
- Never raises on credential/HTTP failure — inspect `OSFResult.status`
  (`"ok"` / `"error"` / `"dry-run"`) and `.error`. A partial upload (some files
  failed) yields `status="error"` with the count in `.error`.
- Token resolved from config first, then `OSF_TOKEN`.

## Known limitations / follow-ups

- **Flat upload:** directory bundles are uploaded by basename into the storage
  root; nested OSF folder creation (Waterbutler `kind=folder`) is a follow-up.
- **Registrations / DOIs:** OSF can mint DOIs on *registrations* (frozen
  snapshots). This adapter creates editable nodes; turning a node into a
  registration with a DOI is a documented future step.
- **Components:** sub-components (child nodes) are not created; everything lands
  on a single node.
