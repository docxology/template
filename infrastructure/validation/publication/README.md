# Publication audit

`infrastructure.validation.publication` is the shared umbrella gate for public
exemplar readiness. It calls existing validators, normalizes their findings,
and emits deterministic JSON or Markdown for CI and human review.

Use `--project` for one qualified project or `--all-public` for the explicit
public roster. `--rendered` adds output, artifact-manifest, evidence-report,
figure-registry, resolved-placeholder, and rendered-provenance checks.

Each rendered provenance receipt is a deterministic, timestamp-free
co-snapshot of:

- shared stage implementation files;
- shippable project source and configuration;
- current artifact-manifest outputs; and
- explicit canonical source-to-render manuscript consumption.

The receipt is alternative release evidence for integrity-only
`current-output-snapshot` manifests. It never relabels those manifests as
per-stage lineage. Source manuscript placeholders are intentional authoring
inputs; only the canonical hydrated or combined rendered Markdown is required
to be token-free.

Stage 04 writes the receipt after validation succeeds. For already-green
tracked outputs, refresh it explicitly:

```bash
uv run python scripts/maintenance/refresh_rendered_provenance.py --all-public
```
