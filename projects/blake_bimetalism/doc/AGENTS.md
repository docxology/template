# 🤖 AGENTS.md - `projects/blake_bimetalism/doc/`

## 🎯 Directory Overview

This directory acts as the central Reference Hub for the `blake_bimetalism` manuscript architecture. Any autonomous agents modifying the primary manuscript or root pipeline MUST adhere to the index documented in `./doc/README.md`.

## 🏗️ Architecture Rules

### 1. Parity Between Documentation and Pipeline

- If a new chapter (e.g., `07_epilogue.md`) is added to the `manuscript/` directory, it MUST simultaneously be indexed in `doc/README.md`.
- Similarly, if any new Python programmatic charts are added to `src/viz/generators.py`, they MUST be logged under the **The `src/viz/` Programmatic Engine** block here.
- Documentation drift is strictly prohibited under the project's Zero-Mock governance structure.

### 2. Scholarly Verification

- Any historical claim (e.g., the 50% deflation from 1865-1896, or the 1965 Coinage Act) mentioned in `doc/` must perfectly mirror the verified BibTeX (`references.bib`) citations encoded in the main manuscript.
- Never stub or hallucinate historical metadata in this directory. If unsure, query `references.bib` or execute `mcp_perplexity-ask_perplexity_ask`.

### 3. Read-Only Context

- Agents should aggressively read `doc/README.md` to acquire the overall 18-file conceptual mapping before proposing structural edits to the manuscript itself.

### 4. Markdown Rendering & Caption Styling

- **Zero-Warning Pandoc Generation**: For images to properly render as LaTeX/Pandoc figures, the markdown image syntax (`![alt-text](path){#fig-id}`) MUST be placed on a standalone line, entirely isolated by blank lines above and below it.
- **No Hardcoded "Figure" Labels**: Pandoc automatically prefixes "Figure X: " to the caption text at compile time. Never include "Figure N:" inside the markdown `![alt-text]` brackets, or the PDF will double-render the label.
