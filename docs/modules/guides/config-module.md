# Config Module

> **Repository-scoped configuration defaults**

**Location:** `infrastructure/config/`  
**Quick Reference:** [Modules Guide](../modules-guide.md) | [Configuration Guide](../../operational/config/configuration.md)

---

## Overview

`infrastructure/config/` is a **configuration directory**, not a Python package. It holds template and default configuration files consumed by infrastructure modules and shell scripts. No Python import is needed — files here are loaded by path.

---

## Files

| File | Purpose |
|------|---------|
| `.env.template` | Template listing all supported environment variables with descriptions. Copy to `.env` and fill in values. |
| `secure_config.yaml` | Default steganography, watermarking, and hashing settings used by `secure_run.sh`. Override individual keys in your project or pass a custom path to the steganography module. |
| `SKILL.md` | AI skill descriptor for this directory (MCP-aligned, consumed by `infrastructure.skills`). |
| `AGENTS.md` | Machine-readable directory guide for AI agents. |

---

## Usage

### Environment Variables

```bash
# One-time setup
cp infrastructure/config/.env.template .env
# Edit .env to set LOG_LEVEL, AUTHOR_NAME, PROJECT_TITLE, etc.
```

### Secure Configuration

```bash
# Run steganographic post-processing with default settings
./secure_run.sh --project code_project

# Override individual settings in your own YAML
./secure_run.sh --project code_project --config my_secure_config.yaml
```

**From Python** (via steganography module):

```python
from pathlib import Path
from infrastructure.steganography import apply_steganography

apply_steganography(
    pdf_path=Path("output/code_project/pdf/paper.pdf"),
    config_path=Path("infrastructure/config/secure_config.yaml"),
)
```

---

## Key Settings in `secure_config.yaml`

| Setting | Default | Effect |
|---------|---------|--------|
| `steganography.enabled` | `true` | Master switch for all post-processing |
| `steganography.overlay_mode` | `"text"` | Watermark type: `text`, `qr`, or `none` |
| `steganography.overlay_opacity` | `0.08` | Watermark transparency (0.0–1.0) |
| `steganography.hashing_enabled` | `true` | Compute SHA-256/512 integrity manifests |
| `steganography.encryption_enabled` | `false` | AES-256 PDF password protection |

---

## Related Documentation

- **[Configuration Guide](../../operational/config/configuration.md)** — Full environment variable reference
- **[Steganography Module](steganography-module.md)** — Python API for PDF post-processing
- **[Infrastructure AGENTS.md](../../../infrastructure/config/AGENTS.md)** — Machine-readable spec
