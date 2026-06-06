# 🔒 Security Module

## Overview

The Research Project Template pipelines integrate optional cryptographic hashing, PDF steganography, and AES-256 PDF password protection capabilities. This module documentation explains how the secure-run path records provenance and creates protected companion PDFs. It does not implement a public-key signature scheme or reader tracking.

## Directory Structure

| File | Purpose |
|------|---------|
| [secure_execution.md](secure_execution.md) | Guide to the interactive orchestration environment `./secure_run.sh` |
| [steganography.md](steganography.md) | How the `SteganographyProcessor` overlays watermarks and dynamic `mailto:` QR codes |
| [hashing_and_manifests.md](hashing_and_manifests.md) | How cryptographic hashing ensures document provenance integrity |
| [literature-fetch-security.md](literature-fetch-security.md) | Trust boundaries, threat model, and hardening for `infrastructure/search/literature/` web fetching |

## Quick Start

Instead of using the default `./run.sh` pipeline menu, launch the pipeline using the secure orchestrator:

```bash
./secure_run.sh --project template_code_project
```

After the PDF rendering phase completes, secure-run reads `infrastructure/config/secure_config.yaml`, overlays any project `manuscript/config.yaml` `steganography:` settings, and executes the steganography pass on the selected project's finalized PDFs. Secured copies land in `<project>/output/pdf/` with the `_steganography.pdf` suffix along with cryptographic hash manifests (`.hashes.json`).
