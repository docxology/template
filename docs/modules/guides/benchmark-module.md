# Benchmark Module

> **Deterministic benchmark manifests for public template outputs.**

**Location:** `infrastructure/benchmark/`
**Quick Reference:** [Modules Guide](../modules-guide.md) | [API Reference](../../reference/api-reference.md) | [Code Review Checklist](../../development/code-review-checklist.md)

---

## Key Features

- **Manifest runner** - `run_benchmark_manifest()` loads explicit checks for public exemplar outputs.
- **Rubrics** - weighted rubric dimensions remain declared in manifests, not inferred from prior runs.
- **Report formats** - benchmark scores can be emitted as JSON or Markdown.
- **Default smoke manifest** - `template_smoke_manifest.json` covers canonical template exemplar readiness checks.
- **Bounded execution** - checks use real local files only; no network calls, LLM calls, mocks, or private-project paths.

---

## CLI

```bash
uv run python -m infrastructure.benchmark.template_harness --repo-root .
uv run python -m infrastructure.benchmark.template_harness \
  --repo-root . \
  --output-json /tmp/template_benchmark.json \
  --output-markdown /tmp/template_benchmark.md
uv run python -m infrastructure.benchmark.template_harness \
  --repo-root . \
  --write-default-manifest
```

---

## Public API

```python
from infrastructure.benchmark import (
    load_benchmark_manifest,
    run_benchmark_manifest,
    score_project_against_manifest,
    score_rubric,
    scores_to_dict,
    scores_to_markdown,
    write_default_manifest,
)
```

See `infrastructure/benchmark/__init__.py` for the authoritative export list.

---

## Review Criteria Mapping

The Benchmark module is reviewed primarily against criteria 3 (Functionality / SSOT - scoring logic lives in the module, not docs), 4 (Testability - tests use real files), and 8 (Reproducibility - manifest checks and rubric weights are explicit). See [Code Review Checklist](../../development/code-review-checklist.md).
