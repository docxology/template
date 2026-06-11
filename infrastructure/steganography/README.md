# Steganography Module

Optional infrastructure module for secure PDF post-processing. Produces a
second `*_steganography.pdf` alongside every normal PDF output, augmented
with layered security and steganographic techniques.

## Module Structure

| File | Purpose |
|------|---------|
| `__init__.py` | Public API: `SteganographyProcessor`, `SteganographyConfig`, `embed_steganography`, `process_pdf`, `resolve_build_timestamp` |
| `config.py` | `SteganographyConfig` dataclass with per-technique toggles |
| `core.py` | `SteganographyProcessor` orchestrator class |
| `overlays.py` | Diagonal watermark + footer + invisible text overlays (reportlab) |
| `barcodes.py` | QR code, Code128, barcode strip generation |
| `barcode_generators.py` | Low-level barcode image generators |
| `barcode_payload.py` | Barcode payload encoding and structure |
| `metadata.py` | PDF Info dictionary + XMP metadata injection (pypdf) |
| `hashing.py` | SHA-256/512 (any `hashlib.new` algorithm) computation, JSON manifest sidecar |
| `encryption.py` | AES-256-GCM payload encryption, PDF password protection |
| `kmyth_adapter.py` | Optional Kmyth/TPM validation and `.ski` sidecar sealing |
| `kmyth/` | Git submodule: upstream NSA Kmyth C project |

## Dependencies

All dependencies are lazily imported — the module loads without error even
when they are absent:

- `pypdf` — PDF reading/writing/merging
- `reportlab` — overlay canvas generation
- `qrcode[pil]` — QR code generation
- `python-barcode` — Code128 barcode generation
- `cryptography` — AES-GCM payload helpers and encrypted metadata payloads

The root `uv sync` includes the `steganography` group by default for the maintained test gate. Minimal environments can still install it explicitly with `uv sync --group steganography`.

Optional Kmyth support is not a Python dependency. Initialize and build the
submodule only when TPM sealing is needed:

```bash
git submodule update --init --recursive infrastructure/steganography/kmyth
make -C infrastructure/steganography/kmyth
./secure_run.sh --validate-kmyth
```

## Configuration

Add a `steganography:` section to your project's `manuscript/config.yaml`:

```yaml
steganography:
  enabled: true
  overlays: true
  barcodes: true
  metadata: true
  hashing: true
  encryption: false
  pdf_encryption_algorithm: "AES-256"
  overlay_text: "CONFIDENTIAL"
  overlay_opacity: 0.08

  # Optional TPM sealing through the kmyth/ submodule or a system install.
  kmyth_enabled: false
  kmyth_required: false
  kmyth_pcrs: []                 # Example: [0, 2, 7]
  kmyth_seal_artifacts: [hash_manifest]  # Add "pdf" to seal the output PDF too.
```

## Usage

### CLI (recommended)

```bash
# Full pipeline + steganography (requires --project)
./secure_run.sh --project template_code_project

# Interactive path → secure subcommand (same orchestrator as ./run.sh)
./run.sh --secure-run

# Post-process existing PDFs only — all discovered projects if --project omitted
./secure_run.sh --steganography-only --project template_code_project
./secure_run.sh --steganography-only

# Validate optional Kmyth/TPM tooling without rendering or sealing PDFs
./secure_run.sh --validate-kmyth
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

- SHA-256 and SHA-512 of the rendered source PDF content
- Hash values embedded in barcodes, metadata, and footer overlays
- JSON sidecar manifest (`*.hashes.json`) for external verification

### Encryption (optional)

- AES-GCM encrypted metadata payloads
- HMAC-SHA256 digital fingerprinting
- PDF-level AES-256 password protection via pypdf

### Kmyth / TPM Sealing (optional)

- The upstream `NationalSecurityAgency/kmyth` repository is mounted as
  `infrastructure/steganography/kmyth`.
- `secure_run.sh --validate-kmyth` checks for `kmyth-seal` and
  `kmyth-unseal` in either `kmyth_binary_dir`, the submodule's `bin/`
  directory, or `PATH`.
- When `kmyth_enabled: true`, the processor writes `.ski` sidecars for the
  configured `kmyth_seal_artifacts` after the steganography PDF and hash
  manifest exist. By default only the hash manifest is sealed.
- Set `kmyth_required: true` to make missing Kmyth tools or TPM seal failures
  fatal. With the default `false`, secure-run logs a warning and continues.
- Kmyth `.ski` files are TPM-bound artifacts. Keep the upstream warning in
  mind: unsealing requires the same TPM and compatible PCR state.

## Deterministic mode

Setting `STEGANOGRAPHY_DETERMINISTIC=1` (or passing `--deterministic` to
`secure_run.sh`) pins every embedded timestamp to the latest commit's
strict-ISO8601 committer date and derives the `Doc-ID` from a SHA-256 of
that timestamp. Two consecutive runs against the same `HEAD` produce
**byte-identical** `*_steganography.pdf` files — useful for provenance
audits and content-addressable storage. Trade-off: the embedded
timestamp no longer reflects rendering time. Falls back to wall-clock
time (with a logger warning) if `git` is unavailable. See
[`docs/security/steganography.md`](../../docs/security/steganography.md#deterministic-mode).

## Architecture

```mermaid
flowchart LR
    IN[Input PDF] --> H[Hashing]
    H --> OB[Overlays + Barcodes]
    OB --> META[Metadata]
    META --> ENC[Encryption · optional]
    ENC --> OUT[Output PDF]
    H -.SHA-256/SHA-512 manifest.-> MAN[.hashes.json]
    META -.provenance payload.-> MAN

    classDef io fill:#0f766e,stroke:#0f172a,color:#fff
    classDef proc fill:#1e3a8a,stroke:#0f172a,color:#fff
    classDef art fill:#7c2d12,stroke:#0f172a,color:#fff
    class IN,OUT io
    class H,OB,META,ENC proc
    class MAN art
```

The module follows the thin orchestrator pattern: `SteganographyProcessor.process()`
chains each technique in sequence, each operating on the working PDF copy.
The original input PDF is never modified.
