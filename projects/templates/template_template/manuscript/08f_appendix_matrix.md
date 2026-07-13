\newpage

## Appendix: Comparative Tool Matrix {#appendix-matrix}

**Symbol key** (applies to all cells): **Y** = full native support  ·  **~** = partial or plugin-based  ·  **N** = absent.
See also [Figure 4](04_results.md#comparative-feature-analysis) for a colour-coded heatmap rendering of this table.

\begin{table}[h]
\caption{Comparative feature matrix (14 capabilities $\times$ 10 tools). Y~=~full native support, \textasciitilde~=~partial or plugin-based, N~=~absent.}
\label{tab:comparative-matrix}
\end{table}

| Capability | `template/` | Snakemake | Nextflow | CWL | Quarto | Jupyter Book | R Markdown | DVC | Overleaf | OpenAI Prism |
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

¹ Nextflow lineage records operate at workflow scope rather than as a rendered-document citation graph.
² DVC provides content-addressed versioning for data artifacts via its object store.
³ DVC integrates with remote storage (S3, GCS, Azure) but does not natively orchestrate distributed compute.
This matrix is a versioned manuscript snapshot, not a continuously updated product survey. A future refresh should re-check every external capability against current primary documentation before changing a cell.
