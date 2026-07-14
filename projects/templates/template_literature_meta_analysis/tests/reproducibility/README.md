# Reproducibility Tests (`tests/reproducibility/`)

Test suite for verifying workflow-graph construction, content/structural
reproducibility scoring, prompt construction, and LLM extraction/pipeline
orchestration without relying on an active network connection.

## Focus Areas

- Dependency-reference resolution into directed edges vs. dangling-reference
  counting.
- Content score (`Rc`) renormalization and structural score (`Rs`) fixed
  convex combination, hand-checked against literal fixtures.
- Composite score (`R = sqrt(Rc * Rs)`) no-compensation and zero-division
  safety.
- Incremental extraction resume, fulltext-availability gating, and
  unparseable-PDF vs. no-fulltext distinction in the pipeline summary.

## Running the Tests

```bash
# General run
uv run pytest tests/reproducibility/ -v

# Target the LLM extraction + pipeline-orchestration suites
uv run pytest tests/reproducibility/test_reproducibility_extraction.py tests/reproducibility/test_runner.py -v
```

See **[AGENTS.md](AGENTS.md)** for detailed module logic verification
protocols and data-mocking guidelines.
