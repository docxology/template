# Analysis Tests Architecture

## Overview

Tests within this directory correspond to the data structures and algorithms implemented in `src/analysis/`. They validate the bibliometric logic, TF-IDF vectorization, NMF topic modeling, temporal progression metrics, and subfield keyword classification systems.

## Key Validation Targets

- **`test_citation_network.py`**: Verifies `networkx` DiGraph construction, recursive depth mapping, and community detection outputs against local synthetic citation matrices.
- **`test_subfield_classifier.py`**: Asserts deterministic routing of papers to Domain A, B, and C targets based tightly on standard text token overlap. Validates edge cases concerning word boundaries.
- **`test_subfield_registry.py`**: YAML keyword loading, invalid entry fallback, and pattern-cache rebuild via `configure_subfields`.
- **`test_pipeline_runner.py`**: Stage-02 orchestration writes the expected JSON/GML artifact bundle from a sample corpus; missing-year papers yield `temporal_analysis.json` with an `error` field.
- **`test_pipeline_helpers.py`**: Reference counting (`_count_paper_references` prefers non-empty `references`, falls back to `referenced_works`), subfield timeline, tokenize_documents.
- **`test_temporal_analysis.py`**: Confirms Cumulative Annual Growth Rate (CAGR) calculations, time bucket logic, and grouping.
- **`test_text_processing.py`**: Exhaustively verifies that stopwords are safely evicted, TF-IDF matrices represent correct matrix dimensions, and ultra-common terms (>95% document frequency when `n_docs >= 20`) are excluded from the vocabulary.
- **`test_topic_modeling.py`**: Ensures NMF decomposition correctly extracts $k$ distinct topics from synthetically biased feature spaces.

See the directory `README.md` for execution instructions.
