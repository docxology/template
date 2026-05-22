# Steganography Module — Agent Documentation

## Overview

The `infrastructure/steganography` module provides optional, configurable
steganographic augmentation of PDF outputs. It post-processes existing PDFs
to produce a second `*_steganography.pdf` that embeds security overlays,
barcodes, metadata, hash values, and optional encryption.

## Key Classes

### `SteganographyConfig` (`config.py`)

Dataclass with boolean toggles for each technique. Factory methods:

- `from_dict(data)` — parse from YAML config section
- `all_enabled()` — return a config with everything on

### `resolve_build_timestamp(*, deterministic=None, repo_root=None)` (`config.py`)

Single source of truth for the build timestamp embedded in overlays,
footers, barcode payloads, XMP packets, and hash manifests.

* `deterministic=True` (or `STEGANOGRAPHY_DETERMINISTIC=1` in the
  environment with `deterministic=None`) — returns
  `git log -1 --format=%cI` from `repo_root` (defaults to `Path.cwd()`).
  Same `HEAD` ⇒ same timestamp ⇒ byte-identical
  `*_steganography.pdf` across runs.
* Otherwise — current UTC wall-clock time as `YYYY-MM-DDTHH:MM:SSZ`.
* Missing `git` or non-zero exit ⇒ logs a single warning and falls back
  to wall-clock time. **Trade-off:** deterministic mode trades a fresh
  per-run timestamp for reproducibility — combine with the
  `*.hashes.json` manifest when both are needed.

### `SteganographyProcessor` (`core.py`)

Orchestrator. Call `process(input_pdf, output_pdf, title, authors, keywords)`.
Chains: hashing → overlays → barcodes → metadata → encryption → manifest.

## File Map

| File | Responsibility |
|------|---------------|
| `config.py` | `SteganographyConfig` dataclass |
| `core.py` | `SteganographyProcessor` orchestrator |
| `overlays.py` | Watermark, footer, invisible text (reportlab) |
| `barcodes.py` | QR, Code128, barcode strips (public API) |
| `barcode_generators.py` | Low-level barcode image generators |
| `barcode_payload.py` | Barcode payload encoding and structure |
| `metadata.py` | PDF Info + XMP injection (pypdf) |
| `hashing.py` | SHA-256/512, manifest JSON |
| `encryption.py` | AES-GCM payload helpers, HMAC, AES-256 PDF password protection |

## Integration Points

- **`infrastructure/__init__.py`** — lazy import under try/except
- **`infrastructure/core/config_loader.py`** — `SteganographyConfigYAML` TypedDict in `ManuscriptConfig`
- **`secure_run.sh`** — shell entry; `uv sync --group steganography`, then `python -m infrastructure.orchestration secure` ([`run_secure_pipeline`](../orchestration/secure_run.py)); pipeline DAG matches `./run.sh` via Python, not a `./run.sh` subprocess
- **`infrastructure/config/secure_config.yaml`** — repository secure-run defaults
- **`config.yaml`** — project `manuscript/config.yaml` `steganography:` section with per-technique booleans and overrides

## Dependencies

All lazily imported: `pypdf`, `reportlab`, `qrcode[pil]`, `python-barcode`, `cryptography`.

## Testing

```bash
uv run pytest tests/infra_tests/steganography/ -v
```
