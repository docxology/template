---
name: Statistical & Metric Analysis
description: Orchestration for bibliometrics, topological network analysis, and hypothesis scoring.
---

# Instructions

You are interacting with the `src/analysis/` module of the Meta-Analysis project. This layer transforms raw literature and structured knowledge graph edges into quantifiable metrics.

## Agentic Interface (MCP Strategy)

1. **Deterministic Operations**: Always fix `random_seed=42` across any clustering, layout algorithms (e.g. UMAP/t-SNE if added), or network metrics (Louvain community detection) to ensure reproducible builds.
2. **Data Abstractions**: Rely on Pandas and NetworkX for scalable computation. Optimize grouping and aggregation passes to use vectorized functions.
3. **No-Mock Constraint**: Ensure tests use local fixtures (like sample graphs or dummy DataFrames) rather than mocking out computation passes. Mocking statistical layers masks data-typing and floating-point errors.
