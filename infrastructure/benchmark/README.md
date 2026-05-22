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
uv run python -m infrastructure.benchmark.template_harness \
  --repo-root . \
  --output-json /tmp/template_benchmark.json \
  --output-markdown /tmp/template_benchmark.md
```

The default manifest is resolved next to `template_harness.py`. Pass an explicit manifest path as the first positional argument to run another benchmark definition.
Manifests may attach a `rubric` block with weighted dimensions; scoring still
reports explicit per-check issues so failed dimensions are inspectable.

Generate the default manifest from canonical exemplar profiles:

```bash
uv run python -m infrastructure.benchmark.template_harness \
  --repo-root . \
  --write-default-manifest
```

## Design rules

- Use real project output files and manuscript sources.
- Keep checks deterministic and bounded for CI/local readiness sweeps.
- Do not use mocks or network services.
- Treat benchmark manifests as public-template checks only; do not encode local-only project paths.

## See also

- [`../validation/evidence_registry.py`](../validation/evidence_registry.py) — evidence grounding registry used by the harness.
- [`../../tests/infra_tests/bench/test_template_benchmark_harness.py`](../../tests/infra_tests/bench/test_template_benchmark_harness.py) — test coverage.
