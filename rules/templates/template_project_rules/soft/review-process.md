# Review Process

These are **soft** guidelines for conducting and requesting code reviews.
Apply them with judgment; adapt the depth of review to the risk level of the
change.

---

## Review Stages

Every PR or patch should pass through the following stages in order:

| Stage | Focus | Required for |
|-------|-------|-------------|
| 1. **Triage** | Scope, intent, missing context | All changes |
| 2. **Logic** | Correctness, edge cases, error handling | All changes |
| 3. **Style** | Consistency with `soft/style-guide.md` | All changes |
| 4. **Security scan** | Auth, crypto, input validation, secrets | Changes touching auth / network / crypto |
| 5. **Test coverage** | Tests present and meaningful | New features and bug fixes |
| 6. **Documentation** | Docstrings, README, CHANGELOG updated | Public API changes |

---

## Roles

- **Author** — Opens the PR, responds to comments, merges after approval.
- **Reviewer** — Completes all applicable stages; approves or requests changes.
- **Maintainer** — Resolves disputes; may override reviewer decisions.

---

## Comment Labels

Use these prefixes in review comments to signal intent:

| Label | Meaning |
|-------|---------|
| `nit:` | Minor style preference; author may ignore |
| `suggest:` | Improvement idea; not blocking |
| `question:` | Needs clarification before approval |
| `block:` | Must be addressed before merge |
| `praise:` | Positive signal; no action required |

---

## Approval Criteria

A PR may be merged when:
- All `block:` comments are resolved.
- At least one reviewer has approved.
- All strong rules (coverage gate, module structure) pass.
- CI is green.

---

## Turnaround Expectations

- First review response within **1 business day** for normal PRs.
- Hotfixes: within **2 hours** during business hours.
- Large refactors (> 500 lines changed): schedule a review session.

---

## AI-Assisted Reviews

When an AI agent performs the review:
- It must complete all applicable stages and label every comment.
- It must explicitly state whether each strong rule passed or failed.
- It may approve only if all blockers are resolved and all strong rules pass.
