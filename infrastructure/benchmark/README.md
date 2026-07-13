# Benchmark Infrastructure

`infrastructure.benchmark` contains small, deterministic benchmark harnesses for the public template exemplars. These checks score generated project outputs against declarative manifests without introducing external services or mocks.

## Files

| File | Purpose |
| --- | --- |
| `template_harness.py` | Loads benchmark manifests, scores exemplar outputs, and provides the CLI entry point. |
| `rubrics.py` | Weighted rubric models for publication-readiness checks. |
| `template_smoke_manifest.json` | Default smoke manifest for the canonical exemplar projects. |

## Usage

```bash
uv run python -m infrastructure.benchmark \
  --repo-root . \
  --output-json /tmp/template_benchmark.json \
  --output-markdown /tmp/template_benchmark.md
```

The default manifest is resolved next to `template_harness.py` and covers the
entire `PUBLIC_PROJECT_NAMES` roster. Pass an explicit manifest path as the
first positional argument to run another benchmark definition. Missing project
directories, validation reports, declared reproducibility artifacts, or
generated outputs fail closed.

Manifests may attach a `rubric` block with positive finite weights. Rubric
dimensions must exactly match the declared checks; the JSON report includes a
per-check pass state, score, weight, and issue list so partial scores remain
inspectable rather than being mistaken for readiness.

Generate the default manifest from canonical exemplar profiles:

```bash
uv run python -m infrastructure.benchmark \
  --repo-root . \
  --write-default-manifest
```

## Design rules

- Use real project output files and manuscript sources.
- Keep checks deterministic and bounded for CI/local readiness sweeps.
- Do not use mocks or network services.
- Treat benchmark manifests as public-template checks only; do not encode local-only project paths.
- Keep project and required-output paths relative and non-traversing.
- Treat every path-like `domain_profile.yaml` artifact expectation as required;
  fix stale declarations instead of accepting any one artifact as a bundle.

## See also

- [`../validation/evidence_registry.py`](../validation/evidence_registry.py) — evidence grounding registry used by the harness.
- [`../../tests/infra_tests/benchmark/test_template_benchmark_harness.py`](../../tests/infra_tests/benchmark/test_template_benchmark_harness.py) — test coverage.
