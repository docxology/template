# Template: Meta-Research Project

This project is a self-referential research study documenting the repository's own infrastructure, design principles, and security features.

## Overview

The "Template Project" serves as a live demonstration of the pipeline's capabilities:

- **Modular Data Extraction**: Uses `scripts/generate_architecture_viz.py` to create system diagrams.
- **Multimodal Rendering**: Compiles Markdown sections into a high-integrity academic PDF.
- **Automated Security**: Digitally signs the output with SHA manifests and steganographic watermarks.

## Directory Structure

| Folder | Contents |
|--------|----------|
| `manuscript/` | Markdown chapters of the paper |
| `scripts/` | Data generation and visualization logic |
| `figures/` | Generated images for the paper |
| `output/` | Finalized PDF and manifest artifacts |

## Building the Paper

To compile this paper and apply secure steganography:

```bash
./secure_run.sh --project template
```
