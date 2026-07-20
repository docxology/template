# Sensitive ownership and private-project promotion

This page records the repository-side controls for sensitive template paths
and the boundary between private work and public or deployed scope.

## Sensitive ownership

The authoritative sensitive-area map is
[`../../.github/sensitive-ownership.yaml`](../../.github/sensitive-ownership.yaml).
Its generated rules are the final rule-bearing block in
[`../../.github/CODEOWNERS`](../../.github/CODEOWNERS). A sole-owner exception
is explicitly recorded for each current sensitive area because a second
maintainer is not presently available. That exception documents residual risk
and requires green blocking CI plus a recorded independent adversarial review;
it does not claim that the sole CODEOWNER supplies two-party approval.

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

Validate the offline attestation alone, preserving the historical positional
form:

```bash
uv run python -m infrastructure.project.promotion attestation promotion.yaml \
  --as-of 2026-07-20
uv run python -m infrastructure.project.promotion promotion.yaml
```

Validate a candidate checkout and compose its security scan with the
candidate-security attestation:

```bash
uv run python -m infrastructure.project.promotion candidate \
  --project-root /path/to/private/candidate \
  --attestation /path/to/private/candidate/promotion-security.yaml \
  --as-of 2026-07-20 --json
```

Both commands are read-only. Passing `--as-of` makes expiry decisions
deterministic for fixtures and release evidence.
Call `evaluate_promotion_candidate(...)` when one typed report must combine
the orchestration attestation and candidate-security decisions. Callers must
provide the qualified `project_name`; the composite rejects a mismatched
attestation project, a `source_commit` different from candidate `HEAD`, or
uncommitted candidate changes outside the attestation files.

See [`TO-DO.md`](../../TO-DO.md) for the remaining ownership, promotion, and
external branch-protection follow-up.
