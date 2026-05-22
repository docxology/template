# Secure Research: PDF Watermarking and Provenance

> **Cryptographic integrity, steganographic watermarks, and tamper detection**

**Skill Level**: 11
**Quick Reference:** [Modules Guide](../modules/modules-guide.md) | [Steganography Module](../modules/guides/steganography-module.md) | [Security Docs](../security/)

---

## What This Does

The steganography module can add visible and invisible provenance layers to PDFs during explicit secure-run workflows:

- **Watermark overlay**: Semi-transparent text plus footer metadata
- **QR and barcode strip**: Document metadata, author contact links, and integrity payloads
- **SHA-256/SHA-512 hashes**: Cryptographic hashes of the rendered source PDF
- **PDF metadata**: XMP metadata injection (author, title, DOI)
- **Hash manifest**: `.hashes.json` file for independent verification
- **PDF encryption**: Optional AES-256 password protection when configured

The original PDF is preserved; a second `*_steganography.pdf` is created alongside it.

---

## Quick Start

The simplest way to use steganography is via `secure_run.sh`:

```bash
# Full pipeline + steganography
./secure_run.sh --project template_code_project

# Same orchestrator CLI from the main thin shell
./run.sh --secure-run

# Steganography only (on existing PDFs)
./secure_run.sh --steganography-only --project template_code_project
```

---

## Programmatic Usage

### Simple Embedding

```python
from infrastructure.steganography import embed_steganography
from pathlib import Path

# All techniques enabled with defaults
embed_steganography(Path("output/template_code_project/pdf/template_code_project_combined.pdf"))
# Creates: code_project_combined_steganography.pdf + .hashes.json
```

### Configurable Processing

```python
from infrastructure.steganography import SteganographyConfig, SteganographyProcessor
from pathlib import Path

# Custom configuration
config = SteganographyConfig(
    enabled=True,
    overlay_text="DRAFT",
    barcodes_enabled=True,
    encryption_enabled=False,
)

processor = SteganographyProcessor(config)
output = processor.process(
    Path("output/template_code_project/pdf/template_code_project_combined.pdf"),
    title="My Research Paper",
    authors=["Daniel Ari Friedman"],
)
print(f"Output: {output}")
```

### Hash Verification

```python
from infrastructure.steganography import process_pdf
from pathlib import Path

# Process and get hash manifest
result = process_pdf(Path("paper.pdf"))

# The .hashes.json manifest contains:
# {
#   "source_file": "paper.pdf",
#   "timestamp": "2026-01-15T10:30:00Z",
#   "hashes": {"sha256": "abc123...", "sha512": "def456..."},
#   "document_id": "...",
#   "git_commit": "a1b2c3d..." or null,
#   "git_commit_available": true
# }
```

---

## Configuration via config.yaml

```yaml
# In projects/{name}/manuscript/config.yaml
steganography:
  enabled: true
  overlays_enabled: true
  barcodes_enabled: true
  metadata_enabled: true
  hashing_enabled: true
  encryption_enabled: false
  pdf_encryption_algorithm: "AES-256"
```

---

## Processing Pipeline

When steganography runs, it applies techniques in this order:

1. **Hashing** — compute configured hashes of the rendered source PDF
2. **Document ID** — generate a build identifier
3. **Overlays and barcodes** — alpha-channel text, footer, QR, and Code128 overlays
4. **Metadata** — XMP and PDF Info dictionary injection
5. **Encryption** — optional AES-256 PDF password protection
6. **Hash manifest** — write `.hashes.json` alongside the source PDF

---

## Verifying Integrity

To verify a PDF hasn't been tampered with:

```bash
# Compare computed hash against manifest
uv run python -c "
import hashlib, json
from pathlib import Path

pdf = Path('output/template_code_project/pdf/code_project_combined.pdf')
manifest = Path('output/template_code_project/pdf/code_project_combined.hashes.json')

computed = hashlib.sha256(pdf.read_bytes()).hexdigest()
expected = json.loads(manifest.read_text())['hashes']['sha256']

print(f'Computed: {computed}')
print(f'Expected: {expected}')
print(f'Match: {computed == expected}')
"
```

---

## Troubleshooting

**Missing reportlab:**
```bash
uv sync --group rendering --group steganography
```

**QR code not appearing:**
- Ensure `barcodes_enabled: true` in config
- Check that the steganography dependency group is installed: `uv sync --group steganography`

**Steganography skipped silently:**
- Check that secure-run is being used, or that `steganography.enabled: true` is present in config
- Verify PDF exists at expected path before steganography runs

---

## Related Documentation

- **[Steganography Module Reference](../modules/guides/steganography-module.md)** — API details
- **[Publishing Guide](publishing-guide.md)** — DOI and citation workflow
- **[Security Documentation](../security/)** — Threat model and hashing details
- **[Infrastructure AGENTS.md](../../infrastructure/steganography/AGENTS.md)** — Machine-readable spec
