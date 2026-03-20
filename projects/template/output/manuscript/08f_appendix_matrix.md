\newpage

## Appendix: Comparative Tool Matrix {#appendix-matrix}

**Symbol key** (applies to all cells): **Y** = full native support  ·  **~** = partial or plugin-based  ·  **N** = absent.
See also [Figure 4](#comparative-feature-analysis) for a colour-coded heatmap rendering of this table.

\begin{table}[h]
\caption{Comparative feature matrix (14 capabilities $\times$ 10 tools). Y~=~full native support, \textasciitilde~=~partial or plugin-based, N~=~absent.}
\label{tab:comparative-matrix}
\end{table}

| Capability | `template/` | Snakemake 9 | Nextflow 25 | CWL 1.2 | Quarto 1 | Jupyter Book 2 | R Markdown | DVC 3 | Overleaf (2025) | OpenAI Prism |
|------------------|:-----------:|:----------:|:----------:|:-------:|:--------:|:------------:|:----------:|:-----:|:-------------:|:------------:|
| Pipeline orchestration | Y | Y | Y | Y | ~ | N | N | Y | N | N |
| Manuscript rendering | Y | N | N | N | Y | Y | Y | N | Y | Y |
| Testing enforcement | Y | N | N | N | N | N | N | N | N | N |
| Coverage thresholds | Y | N | N | N | N | N | N | N | N | N |
| Cryptographic provenance | Y | N | ~¹ | N | N | N | N | ~² | N | N |
| Steganographic watermarking | Y | N | N | N | N | N | N | N | N | N |
| Multi-project management | Y | N | N | N | N | N | N | N | ~ | ~ |
| AI-agent documentation | Y | N | N | N | N | N | N | N | ~ | ~ |
| Agentic skill protocol (SKILL.md / MCP) | Y | N | N | N | N | N | N | N | N | N |
| Interactive TUI | Y | N | N | N | N | N | N | N | N | N |
| Zero-mock policy | Y | N | N | N | N | N | N | N | N | N |
| Container support | N | Y | Y | Y | N | N | N | N | N | N |
| Distributed execution | N | Y | Y | Y | N | N | N | ~³ | N | N |
| Multi-language (R/Julia) | N | Y | N | Y | Y | Y | Y | Y | N | N |

¹ Nextflow 25.04.0 introduced data-lineage provenance tracking (build-level, not document-level).
² DVC provides content-addressed versioning for data artifacts via its object store.
³ DVC integrates with remote storage (S3, GCS, Azure) but does not natively orchestrate distributed compute.
⁴ Overleaf and OpenAI Prism are collaborative cloud LaTeX/AI writing environments; their AI features (GPT-5.2 for Prism, Overleaf Labs AI for Overleaf) are partial/early-stage as of 2025–2026.
