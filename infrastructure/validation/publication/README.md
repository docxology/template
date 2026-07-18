# Publication audit

`infrastructure.validation.publication` is the shared umbrella gate for public
exemplar readiness. It calls existing validators, normalizes their findings,
and emits deterministic JSON or Markdown for CI and human review.

Use `--project` for one qualified project or `--all-public` for the explicit
public roster. `--rendered` adds output, artifact-manifest, evidence-report,
and figure-registry checks.
