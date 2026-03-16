# 🔒 Security Module

## Overview

The Research Project Template pipelines natively integrate optional cryptographic hashing and PDF steganography capabilities. This module documentation explains how the pipeline signs and secures academic outputs against scraping, tampering, or misattribution.

## Directory Structure

| File | Purpose |
|------|---------|
| [secure_execution.md](secure_execution.md) | Guide to the interactive orchestration environment `./secure_run.sh` |
| [steganography.md](steganography.md) | How the `SteganographyProcessor` overlays watermarks and dynamic `mailto:` QR codes |
| [hashing_and_manifests.md](hashing_and_manifests.md) | How cryptographic hashing ensures document provenance integrity |

## Quick Start

Instead of using the default `./run.sh` pipeline menu, launch the pipeline using the secure orchestrator:

```bash
./secure_run.sh
```

complements your specified scientific orchestrations inside an augmented pipeline. After the PDF rendering phase completes, it automatically reads your `infrastructure/config/secure_config.yaml` and executes the steganographer across all your finalized manuscripts, dropping secured copies into `<project>/output/pdf/` labeled `_steganography.pdf` along with cryptographic manifests (`.hashes.json`).
