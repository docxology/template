---
description: Architectural specifications for the Blake Bimetallism manuscript parsing layer
---

# 🤖 AGENTS.md - Manuscript Subsystem

## 🎯 Subsystem Overview

The `manuscript/` directory operates entirely on a Zero-Mock textual standard. It is strictly passive storage that is scraped, collated, and rendered by the `template/infrastructure/` layer.

## 🏗️ Technical Constraints

1. **Pandoc Compliance**: All markdown must be 100% compliant with Github-Flavored Markdown AND Pandoc extensions (namely `{#id}` header anchors, and `[@citation]` syntaxes).
2. **Auto-Numbering**: The files are NOT hardcoded with section numeric prefixes (e.g. `2.1`). The `--number-sections` LaTeX compiler handles enumeration at build time to prevent overlapping identifiers for inter-document anchor linking.
3. **Equation Blocks**: Formal mathematical models (such as Bimetallic Arbitrage $M - c < R < M + c$) must be bracketed securely within `\begin{equation} \label{eq:example} ... \end{equation}` blocks for the pdflatex engine.
4. **Configuration Pipeline**: `config.yaml` is the sole source of truth for the PDF layout renderer; any layout modification (like `margin=1in` geometry parameters) MUST map purely to the repository standard YAML parser.
