# Publication audit

`infrastructure.validation.publication` is the shared umbrella gate for public
exemplar readiness. It calls existing validators, normalizes their findings,
and emits deterministic JSON or Markdown for CI and human review.

Use `--project` for a qualified project. When `--project` is omitted, every
project in `infrastructure.project.public_scope.PUBLIC_PROJECT_NAMES` is
audited. `--rendered` adds output, artifact-manifest, evidence-report, and
figure-registry checks.
