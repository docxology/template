# Literature Retrieval Tests Architecture

## Overview

Tests within this directory correspond to the external API clients and the centralized corpus deduplication mechanism built in `src/literature/`. This directory makes extensive use of the `pytest-httpserver` fixture to simulate the arXiv Atom API, Semantic Scholar Graph API, OpenAlex, Crossref, and PubMed-style responses.

## Key Validation Targets

- **`test_models.py`**: Tests pure dataclass serialization and type constraint validations for Authors, References, and Papers.
- **`test_corpus.py`**: Exceedingly critical logic governing cross-source deduplication. The tests assemble arrays of mathematically identical papers injected with conflicting DOI, generic title case variations, and overlapping OpenAlex/arXiv IDs to confirm the canonical ID priority queue cleanly drops duplicates.
- **`test_arxiv_client.py`**: Proxies an Atom HTTP payload to verify XML parsing cleanly unrolls `<entry>` nodes into instantiated `Paper` datatypes.
- **`test_semantic_scholar.py`**: Asserts correct traversal of the REST response payload, including citation traversal edge cases where the `references` key is absent.
- **`test_search_runner.py`**: Unit tests for relevance filtering, resume/clear corpus, YAML config merge, and duplicate accounting.
- **`test_search_runner_httpserver.py`**: End-to-end `run_literature_search` against local HTTP stubs via injectable `*_base_url` kwargs.
- **`test_fulltext_assessment.py`**: PDF URL coverage and malformed URL handling in full-text assessment reports.

See the directory `README.md` for execution instructions.
