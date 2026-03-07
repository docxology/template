# Methods

The *Docxology Template* architecture is bifurcated into a globally shared `infrastructure/` layer and project-specific `projects/` silos. This "Two-Layer Architecture" allows for massive scaling across heterogeneous research domains (e.g., from cognitive diagrams to code optimization) while maintaining a singular source of truth for build logic.

## The 7-Stage Pipeline

Our primary methodology involves a sequential, staged orchestrator that manages the transition between code and prose:

1. **Stage 00 (Sanitization)**: Environment validation and dependency syncing.
2. **Stage 01 (Verification)**: Full execution of `tests/infra_tests` and `projects/<name>/tests`.
3. **Stage 02 (Extraction)**: Triggering analysis scripts in `projects/<name>/scripts/` to generate `data/` and `figures/`.
4. **Stage 03 (Rendering)**: Sequential Pandoc and XeLaTeX invocation to compile Markdown sections into a unified PDF.
5. **Stage 04 (Security)**: Application of SHA-256/512 hashing and Alpha-Channel steganographic text/QR overlays.
6. **Stage 05 (Validation)**: Structural PDF checking for xref/trailer integrity.
7. **Stage 06 (Summarization)**: Generation of Executive Reports and LLM-aided reviews.

## High-Consistency Documentation

We utilize a "Triad Documentation" standard for all infrastructure components:

- `README.md`: High-level purpose and quick-start.
- `AGENTS.md`: Deep technical implementation details for AI collaborators.
- `SKILL.md`: Actionable patterns and API usage snippets.
