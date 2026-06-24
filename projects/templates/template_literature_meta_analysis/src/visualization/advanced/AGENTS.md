# `src/visualization/advanced/` — agent reference

| Module | Purpose |
| --- | --- |
| `embeddings.py` | PCA/SVD scatter, similarity heatmap, dendrogram of document embeddings |
| `word_cloud.py` | Term cloud from token weights (title parameterized by the search term) |
| `topics.py` | Topic–term bar charts and co-occurrence matrices |
| `labels.py` | Shared label-placement helpers for the advanced plots |

All functions are deterministic given their inputs (seeds fixed upstream) and write
PNGs via the headless matplotlib backend. No network, no I/O beyond the output path.
