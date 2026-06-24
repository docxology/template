# Literature Tests (`tests/literature/`)

Test suite validating cross-database data retrieval parsing constraints and absolute deduplication uniqueness algorithms.

## Focus Areas

- Atom XML and REST JSON localized HTTP mocking targeting OpenAlex, arXiv, and Semantic Scholar via `pytest-httpserver`.
- Hard assertions confirming the correct processing of multi-tiered Canonical ID cascading.

## Running the Tests

```bash
uv run pytest tests/literature/ -v

# Specifically audit deduplication heuristics
uv run pytest tests/literature/test_corpus.py -v
```

See **[AGENTS.md](AGENTS.md)** for detailed module logic verification protocols concerning local HTTP serving boundaries over standard library mocking techniques.
