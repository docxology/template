# Development Documentation

## Overview

Technical guide for `docs/development/` — contribution guidelines, testing, security, and development roadmap.

## Files

| File | Purpose |
|------|---------|
| `contributing.md` | Contribution guidelines and process |
| `code-of-conduct.md` | Community standards |
| `security.md` | Security policy and vulnerability reporting |
| `roadmap.md` | Development roadmap and future plans |
| `coverage-gaps.md` | Test coverage gap analysis |
| `testing/testing-guide.md` | Testing framework and patterns |
| `testing/testing-with-credentials.md` | External service credential testing |
| `no-mocks-http-testing.md` | No-mocks HTTP testing with `pytest-httpserver` |
| `code-review-checklist.md` | Eight-criterion review checklist |
| `validation_gates.md` | Validation gate stages and enforcement |
| `contribution-map.md` | Pre-contribution overlap check, contribution-shape routing, current live repo signals |
| `optional-dependencies.md` | Capability matrix for optional dependency groups and their gating behavior |

## Key Conventions

- **Project layout reference**: [`projects/templates/template_code_project/`](../../projects/templates/template_code_project/); discoverable names → [_generated/active_projects.md](../_generated/active_projects.md).
- All behavior changes require meaningful tests. Coverage floors are 90% for
  each public project's `src/` and 60% for `infrastructure/`; generated counts
  and current measurements belong in [`../_generated/COUNTS.md`](../_generated/COUNTS.md).
- Mock frameworks and semantic dependency replacement are prohibited. Real
  local fixtures, temporary files, local HTTP servers, and narrowly scoped
  environment isolation remain valid; verify both the lexical and inventory
  contracts with `scripts/audit/verify_no_mocks.py`.
- Thin orchestrator pattern enforced for all scripts
- Security vulnerabilities reported via `security.md` process
- Never commit local-only `projects/{active,working,ongoing,archive}/` content
  or non-template `fonds/`, `rules/`, or `tools/` content. Run
  `scripts/audit/check_tracked_all.py` before publication-oriented pushes.
- Local validation, scientific readiness, owner approval, merge, release, and
  publication are separate states. Documentation must not collapse them into
  one "passed" claim.

## See Also

- [README.md](README.md) — Quick navigation
- [Contributing](contributing.md) — How to contribute
- [Testing](testing/) — Testing sub-folder
