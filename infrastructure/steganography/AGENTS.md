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

### `SteganographyProcessor` (`core.py`)

Orchestrator. Call `process(input_pdf, output_pdf, title, authors, keywords)`.
Chains: hashing → overlays → barcodes → metadata → encryption → manifest.

## File Map

| File | Responsibility |
|------|---------------|
| `config.py` | `SteganographyConfig` dataclass |
| `core.py` | `SteganographyProcessor` orchestrator |
| `overlays.py` | Watermark, footer, invisible text (reportlab) |
| `barcodes.py` | QR, Code128, barcode strips |
| `metadata.py` | PDF Info + XMP injection (pypdf) |
| `hashing.py` | SHA-256/512, manifest JSON |
| `encryption.py` | AES-256-GCM, HMAC, PDF password |

## Integration Points

- **`infrastructure/__init__.py`** — lazy import under try/except
- **`infrastructure/core/config/loader.py`** — loads `ManuscriptConfig` including `SteganographyConfigYAML` (`infrastructure/core/config/schema.py`)
- **`secure_run.sh`** — shell entry point wrapping `run.sh` + steganography post-processing
- **`config.yaml`** — `steganography:` section with per-technique booleans

## Dependencies

All lazily imported: `pypdf`, `reportlab`, `qrcode[pil]`, `python-barcode`, `cryptography` (optional).

## Testing

```bash
pytest tests/infra_tests/steganography/ -v
```
