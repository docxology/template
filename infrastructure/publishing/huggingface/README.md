# HuggingFace Hub adapter

Publish a manuscript / reproducibility bundle to a HuggingFace Hub repository
(model, dataset, or space). Datasets are the usual target for research
artifacts.

## Methods

The adapter is a thin orchestrator over two documented Hub REST endpoints, using
raw `requests` (no hard dependency on the `huggingface_hub` client library), so
it is fully unit-testable against `pytest-httpserver`:

1. **Create repo** — `POST {base}/api/repos/create`
   (idempotent: HTTP `409` "already exists" is treated as success).
2. **Commit files** — `POST {base}/api/{repo_type}s/{repo_id}/commit/{revision}`
   using the newline-delimited-JSON ("ndjson") commit protocol. Each file is
   base64-inlined as a regular (non-LFS) blob:

   ```
   {"key":"header","value":{"summary":"<commit message>","description":""}}
   {"key":"file","value":{"path":"paper.pdf","content":"<base64>","encoding":"base64"}}
   ```

### Git-LFS escalation (optional)

The raw inline path cannot satisfy the Hub's Git-LFS requirement for large or
binary blobs (e.g. PDFs), which the Hub rejects. Install the optional
`publishing` group (`uv sync --group publishing`, which adds `huggingface_hub`)
and the adapter automatically escalates to `HfApi.upload_file` (auto-LFS) against
the real Hub — both for files over the ~10 MB inline ceiling and as a fallback
when a raw commit fails. Without the client it stays dependency-free (small text
blobs inline; oversized files return a clear error). Custom `base_url` test
servers always use the raw path.

## Usage

```python
from pathlib import Path
from infrastructure.publishing.huggingface import HuggingFaceHubAdapter, HuggingFaceConfig, HFRepoType

adapter = HuggingFaceHubAdapter(
    HuggingFaceConfig(repo_id="docxology/my-paper", repo_type=HFRepoType.DATASET)
)

# Always-safe dry run (no network, lists files that would be uploaded):
print(adapter.publish(Path("output/bundle"), dry_run=True).uploaded)

# Real publish (token read from HUGGINGFACE_TOKEN / HF_TOKEN, or pass token=...):
result = adapter.publish(Path("output/bundle"), dry_run=False)
print(result.status, result.url, result.commit_url)
```

## Credentials

- `HUGGINGFACE_TOKEN` (preferred) or `HF_TOKEN`, a write-scoped access token
  from <https://huggingface.co/settings/tokens>. Keep it in the repo-root `.env`
  (gitignored) or the environment — never committed.

## Contract

- `dry_run=True` is the default at every layer and never touches the network.
- Never raises on credential/HTTP failure — inspect `HuggingFaceResult.status`
  (`"ok"` / `"error"` / `"dry-run"`) and `.error`.
- Token resolved from config first, then environment.

## Known limitations / follow-ups

- **Large files (> ~10 MB):** the inline commit path rejects blobs above
  `_INLINE_BYTE_CEILING`; those must be routed through Git-LFS
  (`preupload` + `lfs/batch` + multipart PUT). The adapter returns a clear
  `"error"` receipt naming the oversized files rather than failing opaquely.
- **Rich repo cards:** `README.md` / `dataset_infos.json` model-card metadata can
  be added as ordinary files in the bundle; structured card generation is a
  future enhancement.
