# PDF Steganography

The template utilizes a multi-layer steganographic approach to assert provenance.

## Core Features

### 1. Alpha-Channel Overlays

Configurable text strings (such as "CONFIDENTIAL", "DRAFT", or the Author Name) can be diagonally overlaid across every page of the manuscript.

By default, the `overlay_opacity` is set to `0.08` (8% visibility). At this setting, the text is minimally intrusive to human readers but profoundly disrupts naive OCR scanners and automated data-scraping neural networks unless they deploy advanced de-noising algorithms.

### 2. Dynamic `mailto:` Author QR Codes

If `barcodes_enabled` is true, the `SteganographyProcessor` will automatically extract the `authors` array from your `projects/<name>/manuscript/config.yaml`.

If it finds `email` keys for the authors, the processor dynamically generates an actionable `mailto:` URI bridging all authors together in the `to` field, and embeds it as a High Error-Correction (Q Level) QR code on every page margin.

### 3. Invisible Metadata Injection

The processor bypasses the visual later completely to rewrite the PDF metadata dictionaries (XMP and standard PDF info keys), unconditionally branding the `Author`, `Subject`, and specific identifiers (like a `Doc-ID` tracking UUID) into the file internals.

## Configuration

Steganography is controlled by `infrastructure/config/secure_config.yaml`.
If you delete this file, the pipeline will fallback to conservative hard-coded defaults (Text overlay: CONFIDENTIAL, Opacity: 8%, Hash and Metadata enabled, QR barcodes enabled).

```yaml
steganography:
  # Mode: text, qr, or none
  overlay_mode: text
  
  # The text to display
  overlay_text: 'PROVENANCE PROTECTED'
  
  # 0.0 to 1.0 (0.08 is recommended for disruption without visual clutter)
  overlay_opacity: 0.08
  
  # RGB values (e.g. Red is [255, 0, 0])
  overlay_color_rgb: [128, 128, 128]
  
  # Generate and append margin QR code emails
  barcodes_enabled: true
  
  # Inject cryptographic SHA manifests
  hashing_enabled: true
```

## Deterministic mode

By default the steganography overlay embeds a fresh wall-clock timestamp on
every run, so two consecutive `secure_run.sh` invocations against the same
inputs produce *different* PDF bytes — useful as a tamper-evident marker
but inconvenient for reproducibility audits and content-addressable
storage.

Setting **`STEGANOGRAPHY_DETERMINISTIC=1`** (or passing `--deterministic`
to `secure_run.sh`) pins every timestamp inside the steganography
pipeline to the latest commit's strict-ISO8601 committer date, retrieved
via `git log -1 --format=%cI`. The same env var also derives the
`Doc-ID` from a SHA-256 of that timestamp instead of `secrets.token_hex`,
so two consecutive runs against the same `HEAD` produce **byte-identical**
`*_steganography.pdf` files.

```bash
# Reproducible build — byte-identical PDFs across consecutive runs
STEGANOGRAPHY_DETERMINISTIC=1 ./secure_run.sh --pipeline --project template_code_project
./secure_run.sh --deterministic --pipeline --project template_code_project
```

Trade-offs:

* **Reproducibility ↑** — supports SLSA-style provenance, content-hash
  pinning, and bitwise diffing across CI runs.
* **Tamper signal ↓** — the embedded timestamp no longer reflects when
  the PDF was actually rendered; combine with the
  `*.hashes.json` manifest if you need both properties.
* **Fallback** — when `git` is missing or the working tree is not a
  repository, the helper logs a warning and falls back to wall-clock
  time. Builds therefore never *fail* because of deterministic mode;
  they simply stop being byte-identical.

The single source of truth is
[`infrastructure.steganography.config.resolve_build_timestamp`](../../infrastructure/steganography/config.py).
Every overlay, footer, barcode payload, XMP packet, and hash manifest
calls into it.
