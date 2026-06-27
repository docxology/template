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
| `README.md` | Directory overview clarifying this is a non-Python config dir; points `from infrastructure.config import ...` users to `infrastructure/core/config/`. |
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
./secure_run.sh --project template_code_project

# Override individual settings by editing infrastructure/config/secure_config.yaml,
# then re-run (the secure subcommand has no --config flag)
./secure_run.sh --project template_code_project

# Validate optional Kmyth/TPM sealing tools without rendering PDFs
./secure_run.sh --validate-kmyth
```

**From Python** (via steganography module):

```python
import yaml
from pathlib import Path
from infrastructure.steganography import embed_steganography, SteganographyConfig

raw = yaml.safe_load(Path("infrastructure/config/secure_config.yaml").read_text())
config = SteganographyConfig.from_dict(raw.get("steganography", {}))
embed_steganography(
    Path("output/template_code_project/pdf/paper.pdf"),
    config=config,
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
| `steganography.kmyth_enabled` | `false` | Seal configured artifacts through Kmyth/TPM |
| `steganography.kmyth_required` | `false` | Fail secure-run when Kmyth validation or sealing fails |
| `steganography.kmyth_binary_dir` | `null` | Optional directory containing `kmyth-seal` / `kmyth-unseal` |
| `steganography.kmyth_source_dir` | `null` | Optional Kmyth checkout override; defaults to `infrastructure/steganography/kmyth` |
| `steganography.kmyth_pcrs` | `[]` | PCR indexes passed to `kmyth-seal` |
| `steganography.kmyth_cipher` | `null` | Optional cipher passed to `kmyth-seal` |
| `steganography.kmyth_seal_artifacts` | `[hash_manifest]` | Artifacts to seal; supports `hash_manifest` and `pdf` |
| `steganography.kmyth_output_suffix` | `".ski"` | Suffix for sealed sidecars |
| `steganography.kmyth_overwrite` | `true` | Replace existing `.ski` outputs |
| `steganography.kmyth_timeout_seconds` | `120` | Timeout for each `kmyth-seal` invocation |

---

## Related Documentation

- **[Configuration Guide](../../operational/config/configuration.md)** — Full environment variable reference
- **[Steganography Module](steganography-module.md)** — Python API for PDF post-processing
- **[Infrastructure AGENTS.md](../../../infrastructure/config/AGENTS.md)** — Machine-readable spec
