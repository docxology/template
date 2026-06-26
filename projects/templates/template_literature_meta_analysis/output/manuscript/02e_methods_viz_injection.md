# Visualization and Manuscript Injection

## Figure Generation

Figures are rendered headlessly (matplotlib Agg backend) and deterministically from the
analysis artifacts: subfield distributions, the publication growth curve, the citation
network, topic-term bars, a term cloud, and embedding projections. All figures use a
colourblind-safe palette (Wong 2011, 8 colours) with high-contrast labels at $\geq 16$pt.
This run produced 18 figures at 300 DPI. The full figure set includes:

- **Field overview**: field summary and subfield distribution
  ((Figure field summary; Figure subfield distribution))
- **Temporal**: growth curve and subfield timeline ((Figure growth curve; Figure subfield timeline))
- **Citation network**: network layout and degree distribution
  ((Figure citation network; Figure degree distribution))
- **Hypothesis**: dashboard and evidence timeline ((Figure hypothesis dashboard))
- **Text analytics**: word cloud, topic-term bars, PCA embeddings, term heatmap,
  dendrogram, and co-occurrence matrix
  ((Figure word cloud; Figure topic term bars; Figure pca embeddings; Figure term heatmap; Figure dendrogram; Figure cooccurrence matrix))

Each figure is registered in `figure_registry.json` with its source data file, generation
parameters, and SHA-256 hash, binding the visual output to the exact pipeline run.

## Variable Injection

The manuscript itself is generated, not hand-maintained. A variable computation step
reads the configuration and the pipeline outputs and emits a flat table of named values;
an injection step substitutes each named placeholder in these Markdown sections with its
computed value before rendering. Because the substitution is total — an unresolved
placeholder is a hard error, not a silent gap — every number in the rendered document is
guaranteed to trace to a committed artifact. Re-running the pipeline after a
configuration change re-computes the values and re-targets the prose automatically.

The injection system computes variables from seven sources:

1. `manuscript/config.yaml` — search term, engine roster, subfield taxonomy, hypotheses
2. `corpus.jsonl` — corpus size
3. `temporal_analysis.json` — year range, CAGR, peak year, doubling time
4. `citation_network.json` — edges, nodes, density, communities, PageRank, hubs
5. `subfield_classification.json` — per-bucket counts and percentages
6. `assertion_summary.json` — assertion counts and directions
7. `hypothesis_scores.json` — per-hypothesis evidence scores
