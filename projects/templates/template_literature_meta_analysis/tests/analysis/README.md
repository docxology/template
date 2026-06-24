# Analysis Tests (`tests/analysis/`)

This directory tests the quantitative, text, and temporal analytic functions executing on top of the derived corpus.

## Focus Areas

- Keyword-based taxonomy mapping (Domain A/B/C)
- Citation network dynamics (PageRank/Centrality)
- Mathematical consistency in TF-IDF and NMF text topic modeling systems.

## Running the Tests

```bash
# Run all analysis tests
uv run pytest tests/analysis/ -v

# Check specific classifier edges
uv run pytest tests/analysis/test_subfield_classifier.py -v
```

See **[AGENTS.md](AGENTS.md)** for detailed module logic verification protocols.
