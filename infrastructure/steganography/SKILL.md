---
name: infrastructure-steganography
description: Skill for the steganography infrastructure module providing QR code generation with dynamic mailto links, hash manifests, metadata payloads, and document-wide overlay processing. Use this module to insert opt-in cryptographic and steganographic provenance data onto PDFs.
---

# Steganography Infrastructure Module

The `steganography` module applies cryptographic hash manifests, text overlays, and interactive metadata objects (like `mailto` QR barcodes) directly to PDF post-rendering.

## Core Processor (`core.py`)

The primary orchestrator of steganography operations. It handles config extraction, hashing, alpha-text watermarking, and barcodes.

```python
from infrastructure.steganography import SteganographyConfig, SteganographyProcessor
from pathlib import Path

processor = SteganographyProcessor(SteganographyConfig(enabled=True, overlay_mode="text"))
final_pdf = processor.process(
    Path("output.pdf"),
    author_emails=["test@example.com"],
)
```

## Barcodes (`barcodes.py`)

Responsible for generating dense Error-Correction Q-Level QR codes and Code128 barcode strips.

```python
from infrastructure.steganography.barcodes import create_barcode_strip_overlay
overlay_pdf_bytes = create_barcode_strip_overlay(
    page_width=612, page_height=792,
    qr_data="https://doi.org/...", code128_data="paper-id-001",
)
```

## Setup & Hashing (`hashing.py`)

Provides deterministic SHA-256 and SHA-512 manifest exports alongside standard PDF payloads.

```python
from infrastructure.steganography.hashing import compute_file_hashes, write_hash_manifest
hashes = compute_file_hashes(Path("file.pdf"))
write_hash_manifest(Path("file.pdf"), hashes)
```

## Overlays (`overlays.py`)

For applying visual steganographic traits like diagonally rendered strings across every page.

```python
from infrastructure.steganography.overlays import create_watermark_overlay
overlay_bytes = create_watermark_overlay(page_width=612, page_height=792, text="CONFIDENTIAL", opacity=0.08)
```

## Documentation Signposting
>
> **Master Documentation**: For comprehensive details regarding the framework structure, refer directly to the central docs hub:
>
> - 📚 **Core**: [docs/README.md](../../docs/README.md), [docs/AGENTS.md](../../docs/AGENTS.md), [docs/documentation-index.md](../../docs/documentation-index.md)
> - 🏛️ **Architecture**: [docs/architecture/](../../docs/architecture/), [docs/core/](../../docs/core/), [docs/modules/](../../docs/modules/)
> - 🔒 **Security & Audit**: [docs/security/](../../docs/security/), [docs/audit/](../../docs/audit/), [docs/best-practices/](../../docs/best-practices/)
> - 🛠️ **Usage & Ops**: [docs/usage/](../../docs/usage/), [docs/operational/](../../docs/operational/), [docs/development/](../../docs/development/), [docs/guides/](../../docs/guides/), [docs/prompts/](../../docs/prompts/), [docs/reference/](../../docs/reference/)

## Documentation Hub
For detailed documentation on the entire system, refer to the central documentation hub:
- **Core**: [docs/README.md](../../docs/README.md), [docs/AGENTS.md](../../docs/AGENTS.md), [docs/documentation-index.md](../../docs/documentation-index.md)
- **Architecture**: [docs/architecture/](../../docs/architecture/), [docs/core/](../../docs/core/), [docs/modules/](../../docs/modules/)
- **Security & Audit**: [docs/security/](../../docs/security/), [docs/audit/](../../docs/audit/), [docs/best-practices/](../../docs/best-practices/)
- **Usage & Ops**: [docs/usage/](../../docs/usage/), [docs/operational/](../../docs/operational/), [docs/development/](../../docs/development/), [docs/guides/](../../docs/guides/), [docs/prompts/](../../docs/prompts/), [docs/reference/](../../docs/reference/)
