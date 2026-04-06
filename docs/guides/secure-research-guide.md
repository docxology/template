# Secure Research: PDF Watermarking and Provenance

> **Cryptographic integrity, steganographic watermarks, and tamper detection**

**Skill Level**: 11  
**Quick Reference:** [Modules Guide](../modules/modules-guide.md) | [Steganography Module](../modules/guides/steganography-module.md) | [Security Docs](../security/)

---

## What This Does

The steganography module adds invisible provenance layers to your PDFs:

- **Watermark overlay**: Semi-transparent text with build timestamp and commit hash
- **QR code**: Links to the repository, embedded in the PDF
- **SHA-256 hash**: Cryptographic fingerprint for tamper detection
- **PDF metadata**: XMP metadata injection (author, title, DOI)
- **Hash manifest**: `.hashes.json` file for independent verification

The original PDF is preserved; a second `*_steganography.pdf` is created alongside it.

---

## Quick Start

The simplest way to use steganography is via `secure_run.sh`:

```bash
# Full pipeline + steganography
./secure_run.sh --project code_project

# Steganography only (on existing PDFs)
./secure_run.sh --steganography-only --project code_project
```

---

## Programmatic Usage

### Simple Embedding

```python
from infrastructure.steganography import embed_steganography
from pathlib import Path

# All techniques enabled with defaults
embed_steganography(Path("output/code_project/pdf/code_project_combined.pdf"))
# Creates: code_project_combined_steganography.pdf + .hashes.json
```

### Configurable Processing

```python
from infrastructure.steganography import SteganographyConfig, SteganographyProcessor
from pathlib import Path

# Custom configuration
config = SteganographyConfig(
    enabled=True,
    watermark_text="DRAFT - {timestamp}",
    qr_enabled=True,
    encryption_enabled=False,  # Skip AES encryption
)

processor = SteganographyProcessor(config)
result = processor.process(
    pdf_path=Path("output/code_project/pdf/code_project_combined.pdf"),
    title="My Research Paper",
    author="Daniel Ari Friedman",
)
print(f"Output: {result.output_path}")
print(f"SHA-256: {result.sha256}")
```

### Hash Verification

```python
from infrastructure.steganography import process_pdf
from pathlib import Path

# Process and get hash manifest
result = process_pdf(Path("paper.pdf"))

# The .hashes.json manifest contains:
# {
#   "sha256": "abc123...",
#   "sha512": "def456...",
#   "timestamp": "2026-01-15T10:30:00Z",
#   "commit": "a1b2c3d"
# }
```

---

## Configuration via config.yaml

```yaml
# In projects/{name}/manuscript/config.yaml
steganography:
  enabled: true
  watermark: true
  qr_code: true
  encryption: false
  hash_algorithm: "sha256"
```

---

## Processing Pipeline

When steganography runs, it applies techniques in this order:

1. **Metadata injection** — XMP and PDF Info dictionary
2. **SHA-256 hashing** — Compute fingerprint of original PDF
3. **Watermark overlay** — Alpha-channel text on each page
4. **QR code injection** — Repository link encoded as QR
5. **Hash manifest** — Write `.hashes.json` alongside output
6. **Encryption** (optional) — AES-256 encrypted payload

---

## Verifying Integrity

To verify a PDF hasn't been tampered with:

```bash
# Compare computed hash against manifest
python3 -c "
import hashlib, json
from pathlib import Path

pdf = Path('output/code_project/pdf/code_project_combined_steganography.pdf')
manifest = Path('output/code_project/pdf/code_project_combined.hashes.json')

computed = hashlib.sha256(pdf.read_bytes()).hexdigest()
expected = json.loads(manifest.read_text())['sha256']

print(f'Computed: {computed}')
print(f'Expected: {expected}')
print(f'Match: {computed == expected}')
"
```

---

## Troubleshooting

**Missing reportlab:**
```bash
uv sync --group rendering  # Install optional PDF dependencies
```

**QR code not appearing:**
- Ensure `qr_enabled: true` in config
- Check that `qrcode` package is installed: `uv pip install qrcode`

**Steganography skipped silently:**
- Check that `steganography.enabled: true` in config.yaml
- Verify PDF exists at expected path before steganography runs

---

## Related Documentation

- **[Steganography Module Reference](../modules/guides/steganography-module.md)** — API details
- **[Publishing Guide](publishing-guide.md)** — DOI and citation workflow
- **[Security Documentation](../security/)** — Threat model and hashing details
- **[Infrastructure AGENTS.md](../../infrastructure/steganography/AGENTS.md)** — Machine-readable spec
