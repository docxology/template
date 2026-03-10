---
name: infrastructure-steganography
description: Skill for the steganography infrastructure module providing QR code generation with dynamic mailto links, invisible hashing payloads, and document-wide overlay processing. Use this module to insert secure cryptographic and steganographic data onto PDFs.
---

# Steganography Infrastructure Module

The `steganography` module applies cryptographically-secure hashing manifests, text overlaps, and interactive metadata objects (like 'mailto' QR barcodes) directly to PDF post-rendering.

## Core Processor (`core.py`)

The primary orchestrator of steganography operations. It handles config extraction, hashing, alpha-text watermarking, and barcodes.

```python
from infrastructure.steganography import SteganographyProcessor
from pathlib import Path

processor = SteganographyProcessor(
    pdf_path=Path("output.pdf"),
    project_config={"steganography": {"overlay_mode": "text"}},
    author_emails=["test@example.com"]
)
final_pdf = processor.process()
```

## Barcodes (`barcodes.py`)

Responsible for generating dense Error-Correction Q-Level QR codes linking to the author pipeline.

```python
from infrastructure.steganography.barcodes import QRGenerator
generator = QRGenerator()
image = generator.generate_mailto(emails=["a@b.com", "c@d.com"], subject="Research Request")
```

## Setup & Hashing (`hashing.py`)

Provides deterministic SHA-256 and SHA-512 manifest exports alongside standard PDF payloads.

```python
from infrastructure.steganography.hashing import DocumentHasher
hasher = DocumentHasher()
manifest = hasher.generate_manifest(Path("file.pdf"))
```

## Overlays (`overlays.py`)

For applying visual steganographic traits like diagonally rendered strings across every page.

```python
from infrastructure.steganography.overlays import create_text_overlay
pdf_with_watermark = create_text_overlay(width=612, height=792, text="CONFIDENTIAL", opacity=0.08)
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
