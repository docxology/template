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

## Private-project promotion boundary

Private work remains in the separate sidecar repository. A local link under
`projects/active/` remains private and must never be tracked; it is not a public
promotion. A sanitized copy under `projects/templates/`, a deployment, an
archive deposit, and a publication are each separate boundaries with separate
owner authority.

The implementation has two independent evidence contracts:

- `promotion.yaml` binds the qualified project name and source commit to the
  orchestration review.
- `promotion-security.yaml` records candidate-specific security checks and any
  time-bounded risk acceptance.

The `attestation` CLI validates only the first schema. The `candidate` CLI
validates only the second schema and scans the candidate for security TODOs and
unsafe symlinks; it does not verify Git `HEAD` or general repository gates. The
library-only `evaluate_promotion_candidate(...)` composite binds both contracts
to the candidate name, `HEAD`, and clean working-tree state. None of these
read-only checks authenticates an operator or grants permission to copy,
deploy, archive, push, release, or publish.

Use the complete schemas, commands, and boundary-specific checklist in
[`promotion-runbook.md`](promotion-runbook.md). Before any public promotion,
run the applicable confidentiality, generated-artifact, tests, scholarship,
publication-preflight, rendering, and accessibility gates against the exact
reviewed revision. Record skipped or unavailable checks honestly rather than
converting them to passes.

See [`TO-DO.md`](../../TO-DO.md) for the remaining ownership, promotion, and
external branch-protection follow-up.
