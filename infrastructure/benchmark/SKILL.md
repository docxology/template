---
name: infrastructure-benchmark
description: Deterministic benchmark harnesses for public template exemplars. Use when scoring generated project outputs against benchmark manifests, refreshing the default template smoke manifest, checking publication-readiness rubrics, or adding bounded no-network readiness checks for public template outputs.
---

# Benchmark Infrastructure

Use `infrastructure.benchmark` for small, deterministic readiness benchmarks over public template exemplar outputs. The module reads real files, applies explicit manifest checks and optional weighted rubrics, and emits JSON or Markdown score reports.

## Common Workflows

```bash
uv run python -m infrastructure.benchmark --repo-root .
uv run python -m infrastructure.benchmark \
  --repo-root . \
  --output-json /tmp/template_benchmark.json \
  --output-markdown /tmp/template_benchmark.md
uv run python -m infrastructure.benchmark \
  --repo-root . \
  --write-default-manifest
```

## Routing Rules

- Keep benchmark manifests scoped to public template exemplars and generated output contracts.
- Use real output files, manuscript sources, evidence registries, and artifact manifests.
- Do not add network calls, LLM calls, mocks, or private-project paths.
- Keep scoring dimensions explicit and exactly aligned with manifest checks so
  failed checks, weights, and partial scores remain inspectable.
- Treat the default manifest as a fail-closed sweep of the full public roster;
  never shrink it to make a readiness run green.

## Public Imports

- `BenchmarkManifest`
- `BenchmarkCheckResult`
- `BenchmarkScore`
- `RubricScore`
- `RubricSet`
- `load_benchmark_manifest`
- `run_benchmark_manifest`
- `score_project_against_manifest`
- `score_rubric`
- `scores_to_dict`
- `scores_to_markdown`
- `write_default_manifest`

Pair this skill with [`README.md`](README.md) and [`AGENTS.md`](AGENTS.md) for module rules and validation commands.
