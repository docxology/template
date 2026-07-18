# Sensitive ownership and private-project promotion

This page records the repository-side controls for sensitive template paths
and the boundary between private work and public or deployed scope.

## Sensitive ownership

The authoritative sensitive-area map is
[`../../.github/sensitive-ownership.yaml`](../../.github/sensitive-ownership.yaml).
Its generated rules are the final rule-bearing block in
[`../../.github/CODEOWNERS`](../../.github/CODEOWNERS). A sole-owner exception
is explicitly recorded for each current sensitive area because a second
maintainer is not presently available. That exception documents residual risk;
it does not waive the Regression Tier or the required sensitive-area review.

External GitHub branch protection must require:

- `Regression Tier (claim-binding pins)`;
- the normal lint, security, validation, documentation, performance, and
  per-project checks listed in [`.github/AGENTS.md`](../../.github/AGENTS.md);
- one approving review, with CODEOWNERS review requested for sensitive paths.

The external setting is not asserted as complete by repository files. Verify it
in GitHub repository settings before treating the release gate as closed.

## Private-project promotion attestation

Private work remains in the separate sidecar repository. Promotion into
`projects/active/`, a public exemplar set, or a deployment/archive transport
requires an operator to complete this attestation in the private project’s
change record:

```yaml
promotion:
  project: "<qualified private project name>"
  source_commit: "<immutable source revision>"
  identity_verified: false
  authorization_verified: false
  redaction_reviewed: false
  secrets_externalized: false
  routes_reviewed: false
  mcp_boundaries_reviewed: false
  export_tests_passed: false
  risk_acceptance: null
  reviewer: "<operator or independent reviewer>"
```

Every boolean must be `true`, or `risk_acceptance` must contain an explicit
owner, rationale, and expiry. Before promotion, run the confidentiality,
generated-artifact, publication-preflight, and export tests against the exact
source revision. This template intentionally does not implement private-project
authentication or move private credentials into public configuration.

See [`TO-DO.md`](../../TO-DO.md) for the remaining ownership, promotion, and
external branch-protection follow-up.
