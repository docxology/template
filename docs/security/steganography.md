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
