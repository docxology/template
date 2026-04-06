# Steganography Module

> **Cryptographic PDF watermarking and secure document post-processing**

**Location:** `infrastructure/steganography/`
**Quick Reference:** [Modules Guide](../modules-guide.md) | [API Reference](../../reference/api-reference.md)

---

## Key Features

- **Diagonal Watermark Overlays**: Alpha-channel text rendered across every page with configurable opacity, color, font size, and repetition count
- **QR Code and Barcode Strips**: Error-correction Q-level QR codes and Code128 barcodes encoding document metadata, author mailto links, and hash digests
- **SHA-256/SHA-512 Hashing**: Cryptographic hash computation with JSON manifest sidecar output
- **PDF Metadata Injection**: XMP packets and PDF Info dictionary injection with embedded manifest attachments
- **AES-256 Encryption**: Optional PDF password protection via encrypted payloads
- **Fully Optional**: All dependencies are lazily imported; the module does nothing unless explicitly enabled in `config.yaml`

---

## Usage Examples

### Quick Start (All Techniques Enabled)

```python
from infrastructure.steganography import embed_steganography
from pathlib import Path

# Apply all steganographic techniques to a PDF
output = embed_steganography(
    Path("output/code_project/pdf/combined.pdf"),
    title="My Research Paper",
    authors=["Alice Smith", "Bob Jones"],
    keywords=["active inference", "free energy"],
)
# Writes: output/code_project/pdf/combined_steganography.pdf
```

### Configurable Processing

```python
from infrastructure.steganography import SteganographyConfig, SteganographyProcessor
from pathlib import Path

# Selective techniques: watermarks and metadata only, no encryption
config = SteganographyConfig(
    enabled=True,
    overlays_enabled=True,
    barcodes_enabled=False,
    metadata_enabled=True,
    hashing_enabled=True,
    encryption_enabled=False,
    overlay_text="DRAFT",
    overlay_opacity=0.05,
)

processor = SteganographyProcessor(config)
result = processor.process(
    Path("paper.pdf"),
    output_pdf=Path("paper_secure.pdf"),
    title="Draft Manuscript",
    authors=["Alice Smith"],
)
```

### QR Code Generation

```python
from infrastructure.steganography.barcodes import QRGenerator

generator = QRGenerator()
qr_image = generator.generate_mailto(
    emails=["alice@example.com", "bob@example.com"],
    subject="Research Inquiry",
)
```

### Document Hashing

```python
from infrastructure.steganography.hashing import DocumentHasher
from pathlib import Path

hasher = DocumentHasher()
manifest = hasher.generate_manifest(Path("paper.pdf"))
# Returns dict with sha256 and sha512 digests
```

### Text Overlay (Low-Level)

```python
from infrastructure.steganography.overlays import create_watermark_overlay

# Generate a single-page watermark overlay as PDF bytes
wm_bytes = create_watermark_overlay(
    width=612, height=792,
    text="CONFIDENTIAL",
    opacity=0.08,
    color_rgb=(128, 128, 128),
    font_size=60,
    repeat_count=5,
)
```

---

## Configuration

### Via `config.yaml`

Enable steganography in a project's `manuscript/config.yaml`:

```yaml
steganography:
  enabled: true
  overlays: true
  barcodes: true
  metadata: true
  hashing: true
  encryption: false
  overlay_text: "CONFIDENTIAL"
  overlay_opacity: 0.08
  overlay_mode: "text"   # 'text' | 'qr' | 'none'
```

### Via `SteganographyConfig`

| Attribute | Type | Default | Description |
|---|---|---|---|
| `enabled` | `bool` | `False` | Master switch for all processing |
| `overlays_enabled` | `bool` | `True` | Diagonal watermark text overlays |
| `barcodes_enabled` | `bool` | `True` | QR / Code128 barcode strips |
| `metadata_enabled` | `bool` | `True` | XMP and PDF Info injection |
| `hashing_enabled` | `bool` | `True` | SHA-256/SHA-512 hash computation |
| `encryption_enabled` | `bool` | `False` | AES-256 payload encryption |
| `overlay_mode` | `str` | `"text"` | Overlay content: `text`, `qr`, or `none` |
| `overlay_opacity` | `float` | `0.08` | Alpha channel (0.0 invisible to 1.0 solid) |
| `pdf_password` | `str \| None` | `None` | Password for PDF-level encryption |
| `output_suffix` | `str` | `"_steganography"` | Suffix appended to output filename |
| `manifest_enabled` | `bool` | `True` | Write JSON hash manifest sidecar |

### Factory Methods

```python
# All techniques enabled (used by embed_steganography default)
config = SteganographyConfig.all_enabled()

# From a parsed YAML dictionary (unknown keys silently ignored)
config = SteganographyConfig.from_dict(yaml_data["steganography"])
```

---

## CLI Integration

```bash
# Run steganography via the secure menu
./secure_run.sh --project code_project

# Steganography only (skip pipeline)
./secure_run.sh --steganography-only --project code_project
```

---

## Processing Pipeline

The `SteganographyProcessor.process()` method runs techniques in order:

1. **Hash** the original PDF (SHA-256, SHA-512)
2. **Generate** a unique document ID
3. **Apply** overlays (watermark text or tiled QR) and barcode strips to every page
4. **Inject** PDF metadata, XMP packet, and manifest attachment
5. **Encrypt** with PDF password (if enabled)
6. **Write** JSON hash manifest sidecar

Output is written as `<input_stem>_steganography.pdf` alongside the original.

---

## Related Documentation

- [Rendering Module](rendering-module.md) -- PDF generation that precedes steganography
- [Modules Guide](../modules-guide.md) -- Overview of all infrastructure modules
- [PDF Validation](../pdf-validation.md) -- Validating generated PDFs
