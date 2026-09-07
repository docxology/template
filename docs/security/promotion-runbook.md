# Private-project promotion runbook

> **Operator action and explicit authority required.** Validation is read-only;
> activation, copying into the public roster, deployment, archival, and release
> are separate write operations. A passing report never authorizes those writes.

## Choose the boundary first

There are two different operations:

- **Local activation:** a project remains in the external private sidecar and is
  linked into local-only `projects/active/<name>/`. The link and its contents
  must never be tracked or pushed.
- **Public promotion:** a reviewed, sanitized copy becomes a canonical exemplar
  under `projects/templates/<name>/`. This requires an explicit public-release
  decision, updates to the authoritative public roster, and the normal CI,
  confidentiality, provenance, accessibility, and publication gates.

Do not use a local `projects/active/` link as a shortcut into public git history.
Deployment or archival of private material is a third boundary and requires the
destination owner's authorization.

## Prerequisites

1. Record the candidate's canonical private checkout, exact commit, intended
   destination, and approving owner.
2. Inspect `git status --short --branch` in both repositories. Preserve unrelated
   or nested-repository work; use a dedicated branch or isolated worktree for a
   public promotion rather than editing `main` directly.
3. Prepare both independent attestations below. Keep them in the private change
   record unless and until a sanitized public record is intentionally approved.
4. Never print, copy, or commit credentials or candidate source as diagnostic
   evidence.

## 1. Orchestration attestation

The orchestration contract binds the qualified project name and source commit to
the review decision:

```yaml
promotion:
  project: "working/<candidate-name>"
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

Every boolean must be `true`, or `risk_acceptance` must name an owner,
rationale, and unexpired ISO-date `expiry`.

Validate this contract offline:

```bash
uv run python -m infrastructure.project.promotion attestation \
  /path/to/promotion.yaml --as-of <YYYY-MM-DD>
```

Use the actual decision date for `--as-of`; a copied historical date can make an
expired exception appear current. This command validates the YAML contract only.
It does not inspect Git, authenticate an operator, or authorize promotion.

## 2. Candidate-security attestation

The candidate CLI consumes a different schema, normally stored as
`promotion-security.yaml` inside the candidate root:

```yaml
schema_version: 1
project: "<candidate-directory-name>"
review:
  reviewed_by: "<security reviewer>"
  reviewed_at: "<YYYY-MM-DD>"
checks:
  authentication: {status: closed, evidence: "<evidence reference>"}
  authorization: {status: closed, evidence: "<evidence reference>"}
  redaction: {status: closed, evidence: "<evidence reference>"}
  secret_store: {status: closed, evidence: "<evidence reference>"}
  route_handlers: {status: closed, evidence: "<evidence reference>"}
  mcp: {status: closed, evidence: "<evidence reference>"}
  export_tests: {status: closed, evidence: "<evidence reference>"}
security_findings: {}
```

Each check may instead be `not-applicable` with evidence, or `risk-accepted`
with evidence, rationale, accepting owner, and expiry. The validator also scans
text files for security-related TODO markers, rejects candidate symlinks and
out-of-root attestations, and fails closed on unresolved findings.

```bash
uv run python -m infrastructure.project.promotion candidate \
  --project-root /path/to/private/candidate \
  --attestation /path/to/private/candidate/promotion-security.yaml \
  --as-of <YYYY-MM-DD> --json
```

This command is read-only, but it does **not** bind the orchestration
`source_commit`, reject a dirty Git tree, or run the repository's general
confidentiality/generated-artifact/export suites. Its report is one security
input, not a complete promotion decision.

## 3. Bind the exact checkout

Use the library-only composite API when the decision must bind both attestations
to the candidate's qualified name, Git `HEAD`, and working-tree state:

```python
from datetime import date
from pathlib import Path

from infrastructure.project.promotion import evaluate_promotion_candidate

report = evaluate_promotion_candidate(
    Path("/path/to/private/candidate"),
    project_name="working/<candidate-name>",
    orchestration_attestation=Path("/path/to/promotion.yaml"),
    security_attestation=Path(
        "/path/to/private/candidate/promotion-security.yaml"
    ),
    as_of=date.fromisoformat("<YYYY-MM-DD>"),
)
```

The composite rejects an unqualified or mismatched project name, a
`source_commit` different from candidate `HEAD`, and uncommitted candidate
changes outside the two attestation files. It still does not grant external
release authority.

## 4. Run boundary-specific gates

For local activation, preview the sidecar links before writing them:

```bash
uv run python -m infrastructure.orchestration link-projects --dry-run
```

For a proposed public exemplar, review the sanitized copy on a dedicated branch
and run, at minimum, the public-scope confidentiality, generated-artifact,
no-standins, tests, manuscript/evidence, rendering, accessibility, and docs
gates that apply to that copy. Derive the current public roster from
`infrastructure.project.public_scope`; do not hand-add a path to prose alone.

## 5. Record separate decisions

Record independently:

- validation result and exact source revision;
- security/risk acceptance and expiry;
- scientific and scholarship review status;
- accessibility and rendered-artifact status;
- owner approval for local activation, public promotion, deployment, archival,
  or publication;
- remote push, release, and publication outcomes.

If any required input fails or is unchecked, stop at candidate status. Never
translate a skipped/unavailable check into a pass.

## Focused contract tests

```bash
uv run pytest tests/infra_tests/project/test_promotion.py \
  tests/infra_tests/project/test_private_project_promotion.py \
  -q --no-cov --timeout=120
```

## See also

- [`ownership-and-promotion.md`](ownership-and-promotion.md)
- [`branch-protection-checklist.md`](branch-protection-checklist.md)
- [`infrastructure/project/promotion/`](../../infrastructure/project/promotion/)
