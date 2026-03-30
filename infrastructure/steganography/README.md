# Steganography Module

Optional infrastructure module for secure PDF post-processing. Produces a
second `*_steganography.pdf` alongside every normal PDF output, augmented
with layered security and steganographic techniques.

## Module Structure

| File | Purpose |
|------|---------|
| `__init__.py` | Public API: `SteganographyProcessor`, `SteganographyConfig`, `process_pdf` |
| `config.py` | `SteganographyConfig` dataclass with per-technique toggles |
| `core.py` | `SteganographyProcessor` orchestrator class |
| `overlays.py` | Diagonal watermark + footer + invisible text overlays (reportlab) |
| `barcodes.py` | QR code, Code128, barcode strip generation |
| `metadata.py` | PDF Info dictionary + XMP metadata injection (pypdf) |
| `hashing.py` | SHA-256/512/BLAKE2b computation, JSON manifest sidecar |
| `encryption.py` | AES-256-GCM payload encryption, PDF password protection |

## Dependencies

All dependencies are lazily imported — the module loads without error even
when they are absent:

- `pypdf` — PDF reading/writing/merging
- `reportlab` — overlay canvas generation
- `qrcode[pil]` — QR code generation
- `python-barcode` — Code128 barcode generation
- `cryptography` — AES-256 encryption (optional, only for encryption feature)

Install all with: `pip install pypdf reportlab qrcode[pil] python-barcode`

## Configuration

Add a `steganography:` section to your project's `manuscript/config.yaml`:

```yaml
steganography:
  enabled: true
  overlays: true
  barcodes: true
  metadata: true
  hashing: true
  encryption: false        # Requires 'cryptography' package
  overlay_text: "CONFIDENTIAL"
  overlay_opacity: 0.08
```

## Usage

### CLI (recommended)

```bash
# Full pipeline + steganography
./secure_run.sh

# Specific project
./secure_run.sh --project code_project

# Post-process existing PDFs only (skip pipeline)
./secure_run.sh --steganography-only
```

### Python API

```python
from infrastructure.steganography import process_pdf, SteganographyConfig
from pathlib import Path

# Quick — all techniques enabled
process_pdf(Path("paper.pdf"))

# Configurable
config = SteganographyConfig(
    enabled=True,
    overlays_enabled=True,
    barcodes_enabled=True,
    metadata_enabled=True,
    hashing_enabled=True,
    encryption_enabled=False,
)
process_pdf(Path("paper.pdf"), config=config, title="My Paper")
```

## Techniques

### Watermark Overlays

- Diagonal semi-transparent text across every page
- Configurable text, opacity, and colour
- Page footer with document ID, page number, and short hash

### Invisible Text

- Render-mode-3 text (invisible ink) on first page
- Embeds document ID, title, and hash — survives text extraction

### Barcodes

- **QR code** on bottom-left of every page (document hash + title + timestamp)
- **Code128** linear barcode text with page-level document ID
- All barcodes rendered via reportlab canvas

### Metadata Injection

- PDF Info dictionary population (Title, Author, custom `/Hash_SHA256` keys)
- XMP Dublin Core metadata packet with custom steganography namespace
- Creator/Producer fields identify the steganography module

### Hashing

- SHA-256 and SHA-512 of the original PDF content
- Hash values embedded in barcodes, metadata, and footer overlays
- JSON sidecar manifest (`*.hashes.json`) for external verification

### Encryption (optional)

- AES-256-GCM encrypted metadata payloads
- HMAC-SHA256 digital fingerprinting
- PDF-level password protection via pypdf

## Architecture

```
Input PDF ──→ [Hashing] ──→ [Overlays+Barcodes] ──→ [Metadata] ──→ [Encryption] ──→ Output PDF
                 │                                                         │
                 └── .hashes.json manifest ────────────────────────────────┘
```

The module follows the thin orchestrator pattern: `SteganographyProcessor.process()`
chains each technique in sequence, each operating on the working PDF copy.
The original input PDF is never modified.
