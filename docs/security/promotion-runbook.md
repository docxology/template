# Private-project promotion runbook

> **Operator action.** This runbook guides a maintainer through promoting a
> private sidecar project into `projects/active/`, a public exemplar set, or
> a deployment/archive transport. The public template repository does not
> store private project code, credentials, or authentication — all steps are
> read-only against the candidate checkout.

## Prerequisites

1. The private sidecar repository is cloned and on the exact source commit
   being promoted.
2. The promotion attestation YAML is prepared in the private project's change
   record (template below).
3. The public template checkout is clean and on `main`.

## Step 1 — Prepare the attestation

Create `promotion.yaml` in the private project's change record:

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
owner, rationale, and expiry.

## Step 2 — Validate the attestation

```bash
uv run python -m infrastructure.project.promotion attestation promotion.yaml \
  --as-of 2026-07-24
```

This is read-only and deterministic. Passing `--as-of` makes expiry decisions
reproducible. The validator rejects:

- A mismatched `project` name
- An incomplete attestation (any `false` boolean without a valid
  `risk_acceptance`)
- An expired `risk_acceptance`

## Step 3 — Validate the candidate checkout

```bash
uv run python -m infrastructure.project.promotion candidate \
  --project-root /path/to/private/candidate \
  --attestation /path/to/private/candidate/promotion.yaml \
  --as-of 2026-07-24 --json
```

This command:

1. Verifies the candidate's `HEAD` matches the attestation's `source_commit`.
2. Checks for uncommitted changes outside the attestation files.
3. Runs confidentiality, generated-artifact, and export tests against the
   candidate.
4. Returns a typed JSON report.

## Step 4 — Compose the final security decision

The composite decision has **no CLI surface**. It ships as a library-only API,
`evaluate_promotion_candidate()` in
[`infrastructure/project/promotion/composite.py`](../../infrastructure/project/promotion/composite.py),
which combines the attestation and candidate-security decisions into one typed
`PromotionCompositeReport`:

```python
from datetime import date
from pathlib import Path

from infrastructure.project.promotion import evaluate_promotion_candidate

report = evaluate_promotion_candidate(
    Path("/path/to/private/candidate"),
    project_name="<qualified name>",
    orchestration_attestation=Path("/path/to/promotion.yaml"),
    as_of=date(2026, 7, 24),
)
```

`security_attestation` defaults to `promotion-security.yaml` inside the
candidate root. The composite rejects (by raising `ValueError`):

- A mismatched attestation project name
- A `source_commit` different from candidate `HEAD`
- Uncommitted candidate changes outside the attestation files

## Step 5 — Record and proceed

If all steps pass:

1. Record the promotion decision, reviewer, scope, and evidence in the
   private project's change record.
2. Symlink or copy the project into `projects/active/` (or the appropriate
   public exemplar path).
3. Run `uv run python -m infrastructure.orchestration link-projects --dry-run`
   to verify the symlink is discovered.
4. Run the full pipeline against the promoted project:
   `./run.sh --pipeline --project <name> --core-only`.

If any step fails, do not promote. Fix the gaps and re-run from Step 2.

## What this template does NOT do

- It does not implement private-project authentication.
- It does not move private credentials into public configuration.
- It does not auto-merge attestations — every promotion requires an explicit
  human decision.

## Test coverage

The attestation validator, candidate checker, and composite evaluator are
covered by `tests/infra_tests/project/test_promotion.py`. These tests use real
temp directories and real git repos — no mocks.

```bash
uv run pytest tests/infra_tests/project/test_promotion.py -v --no-cov --timeout=120
```

## See also

- [`ownership-and-promotion.md`](ownership-and-promotion.md) — sensitive
  ownership exceptions and attestation schema
- [`branch-protection-checklist.md`](branch-protection-checklist.md) —
  required GitHub branch-protection settings
- [`infrastructure/project/promotion/`](../../infrastructure/project/promotion/) —
  the validator source code
