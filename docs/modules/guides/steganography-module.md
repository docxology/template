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
- **AES-256 PDF Encryption**: Optional PDF password protection when `pdf_password` is configured
- **Kmyth/TPM Sidecars**: Optional `.ski` sidecars for selected artifacts through the bundled Kmyth git submodule or a system install
- **Fully Optional**: The module does nothing unless explicitly enabled through secure-run defaults, project config, or API configuration

---

## Usage Examples

### Quick Start (All Techniques Enabled)

```python
from infrastructure.steganography import embed_steganography
from pathlib import Path

# Apply all steganographic techniques to a PDF
output = embed_steganography(
    Path("output/template_code_project/pdf/combined.pdf"),
    title="My Research Paper",
    authors=["Alice Smith", "Bob Jones"],
    keywords=["active inference", "free energy"],
)
# Writes: output/template_code_project/pdf/combined_steganography.pdf
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
from infrastructure.steganography.barcode_generators import generate_qr_code

qr_png_bytes = generate_qr_code(
    data="mailto:alice@example.com?subject=Research+Inquiry",
)
```

### Document Hashing

```python
from infrastructure.steganography.hashing import compute_file_hashes, write_hash_manifest
from pathlib import Path

hashes = compute_file_hashes(Path("paper.pdf"))
# Returns dict with sha256 and sha512 digests
manifest_path = write_hash_manifest(Path("paper.pdf"), hashes)
```

### Text Overlay (Low-Level)

```python
from infrastructure.steganography.overlays import create_watermark_overlay

# Generate a single-page watermark overlay as PDF bytes
wm_bytes = create_watermark_overlay(
    page_width=612, page_height=792,
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
  kmyth_enabled: false
  kmyth_required: false
  kmyth_binary_dir: null
  kmyth_source_dir: null
  kmyth_pcrs: [0, 2, 7]
  kmyth_cipher: null
  kmyth_seal_artifacts: [hash_manifest]
  kmyth_output_suffix: ".ski"
  kmyth_overwrite: true
  kmyth_timeout_seconds: 120
```

### Via `SteganographyConfig`

| Attribute | Type | Default | Description |
|---|---|---|---|
| `enabled` | `bool` | `False` | Master switch for all processing |
| `overlays_enabled` | `bool` | `True` | Diagonal watermark text overlays |
| `barcodes_enabled` | `bool` | `True` | QR / Code128 barcode strips |
| `metadata_enabled` | `bool` | `True` | XMP and PDF Info injection |
| `hashing_enabled` | `bool` | `True` | SHA-256/SHA-512 hash computation |
| `encryption_enabled` | `bool` | `False` | Enable PDF password protection when `pdf_password` is set |
| `overlay_mode` | `str` | `"text"` | Overlay content: `text`, `qr`, or `none` |
| `overlay_opacity` | `float` | `0.08` | Alpha channel (0.0 invisible to 1.0 solid) |
| `pdf_password` | `str \| None` | `None` | Password for PDF-level encryption |
| `pdf_encryption_algorithm` | `str` | `"AES-256"` | PDF encryption algorithm passed to `pypdf` |
| `output_suffix` | `str` | `"_steganography"` | Suffix appended to output filename |
| `manifest_enabled` | `bool` | `True` | Write JSON hash manifest sidecar |
| `kmyth_enabled` | `bool` | `False` | Seal selected artifacts through Kmyth/TPM |
| `kmyth_required` | `bool` | `False` | Fail when Kmyth is unavailable or sealing fails |
| `kmyth_binary_dir` | `str \| None` | `None` | Optional directory containing `kmyth-seal` and `kmyth-unseal` |
| `kmyth_source_dir` | `str \| None` | `None` | Optional Kmyth checkout path override |
| `kmyth_pcrs` | `list[int]` | `[]` | Optional TPM PCR indexes passed to `kmyth-seal` |
| `kmyth_cipher` | `str \| None` | `None` | Optional cipher string passed to `kmyth-seal` |
| `kmyth_seal_artifacts` | `list[str]` | `["hash_manifest"]` | Supported values: `hash_manifest`, `pdf` |
| `kmyth_output_suffix` | `str` | `".ski"` | Suffix for sealed sidecars |
| `kmyth_overwrite` | `bool` | `True` | Replace existing Kmyth sidecars |
| `kmyth_timeout_seconds` | `int` | `120` | Timeout for each `kmyth-seal` invocation |

### Factory Methods

```python
# All techniques enabled (used by embed_steganography default; PDF password
# encryption still requires pdf_password)
config = SteganographyConfig.all_enabled()

# From a parsed YAML dictionary (unknown keys silently ignored)
config = SteganographyConfig.from_dict(yaml_data["steganography"])
```

---

## CLI Integration

```bash
# Run steganography via the secure menu
./secure_run.sh --project template_code_project

# Steganography only (skip pipeline)
./secure_run.sh --steganography-only --project template_code_project

# Validate optional Kmyth tooling without rendering or sealing PDFs
./secure_run.sh --validate-kmyth --project template_code_project
```

Kmyth is a git submodule, not a Python package. Initialize and build it before
turning on `kmyth_enabled`:

```bash
git submodule update --init --recursive infrastructure/steganography/kmyth
make -C infrastructure/steganography/kmyth
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
7. **Seal** configured artifacts with Kmyth/TPM (if enabled)

Output is written as `<input_stem>_steganography.pdf` alongside the original.

---

## Related Documentation

- [Rendering Module](rendering-module.md) -- PDF generation that precedes steganography
- [Modules Guide](../modules-guide.md) -- Overview of all infrastructure modules
- [PDF Validation](../pdf-validation.md) -- Validating generated PDFs
