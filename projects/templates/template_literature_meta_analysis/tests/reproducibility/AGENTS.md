# Reproducibility Tests Architecture

## Overview

Tests within this directory target the workflow-graph data model, pure
scoring functions, prompt templates, and LLM-driven extraction/orchestration
implemented in `src/reproducibility/`. Ensure that no actual LLM outbound
requests are made during these tests; HTTP-boundary tests use
`pytest-httpserver` (a real local HTTP server), exactly like
`tests/knowledge_graph/test_llm_assess_paper.py`. Pure functions
(`models.py`, `scoring.py`, `prompts.py`) are tested with literal fixture
objects and zero I/O.

## Key Validation Targets

- **`test_reproducibility_models.py`**: Ensures `build_workflow_graph()` correctly resolves
  `depends_on` references into directed `WorkflowEdge`s and counts dangling
  references without raising. Verifies `to_dict()`/`from_dict()` round-trips,
  JSONL serialization/deserialization, `merge_workflow_graphs()`'s
  new-wins-on-`paper_id` dedup semantics, and `append_workflow_graphs()`'s
  atomicity (no `.jsonl.tmp` left behind).
- **`test_scoring.py`**: Hand-computes `content_score()` and
  `structural_score()` against literal `WorkflowGraph` fixtures to verify the
  weighted-average and convex-combination formulas exactly, including the
  renormalization-when-a-stage-is-absent behavior of `Rc` and the
  fixed-weight (never renormalized) behavior of `Rs`. Verifies
  `composite_score()`'s geometric-mean no-compensation property and that an
  empty graph never raises `ZeroDivisionError` or a `math.sqrt` domain
  error. Verifies `rc3` counts only `METHOD`/`EXPERIMENT` node references
  (never `SOURCE`) and `rc4` normalizes by `|sources| * |sinks|` (not set
  union size) — the two ambiguities this implementation resolves relative to
  the source paper (arXiv:2605.02651). Also covers `verify_source_quote()`'s
  exact-match fast path, fuzzy word-window matching, and threshold
  rejection.
- **`test_prompts.py`**: Checks the system prompt documents all four node
  types, the exact JSON schema keys, the mandatory-and-verbatim
  `source_quote` field, and the 1-4 rating scale; checks `build_prompt()`
  embeds the paper title and full text and requests a bare JSON array.
- **`test_reproducibility_extraction.py`**: LLM extraction via `pytest-httpserver` (real
  HTTP) plus manual-validation behavior — rejecting nodes with a missing
  `source_quote` or an invalid `node_type`, retry-then-`RuntimeError`
  exhaustion, and the incremental multi-paper driver's resume/skip-without-
  fulltext semantics.
- **`test_runner.py`**: End-to-end pipeline behavior — expected output
  artifacts, the `--clear-workflow-graphs` flag, the fulltext-disabled
  warning-and-degrade path, distinguishing an unparseable PDF
  (`n_skipped_unparseable_pdf`) from no fulltext at all
  (`n_skipped_no_fulltext`), config auto-load and override precedence, and
  skip-when-corpus-already-covered incremental resume.

See the directory `README.md` for execution instructions.
