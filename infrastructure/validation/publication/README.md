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

The default published audit also requires all stable artifacts and publication
receipts to be present and byte-clean in Git's index. Native Original and fresh
Current execution each audit the independently held pristine Source reference
before Core, retaining that actual report for readback. After Core, the explicit
`validate_current_rendered_provenance` API checks the complete actual derived
snapshot without comparing derived Output bytes to published Git blobs.

`build_current_publication_audit` retains every Source and rendered checker and
brackets them with genuine `NativeSourceContext` correspondence checks. Exact
authored Source, full Git/index, selected SDK, owner, reader and native execution
custody remain separate required predicates. Snapshot consistency alone cannot
establish native acceptance, and the CLI continues to use the strict published
audit. This separation permits legitimate native output differences without a
second render or an index mutation.
