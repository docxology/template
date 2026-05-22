# infrastructure/benchmark/ — Agent Guide

## Purpose

Maintain small benchmark harnesses that validate canonical template outputs using real files and deterministic scoring.

## Local rules

- Keep benchmark logic generic to the public template; do not reference confidential or rotating local-only projects.
- Exercise actual generated artifacts, manuscript Markdown, BibTeX, figures, and data files.
- Keep rubric dimensions explicit in manifests; do not infer hidden benchmark weights from prior runs.
- Preserve the No-Mocks Policy: no mock frameworks, no fake clients, and no monkeypatched external behavior.
- Keep runtime bounded so harnesses can run in local readiness checks.

## Validation

```bash
uv run pytest tests/infra_tests/bench/test_template_benchmark_harness.py -v
uv run python -m infrastructure.benchmark.template_harness --repo-root .
```

## See also

- [`README.md`](README.md)
- [`../validation/AGENTS.md`](../validation/AGENTS.md)
- [`../../tests/infra_tests/bench/AGENTS.md`](../../tests/infra_tests/bench/AGENTS.md)
