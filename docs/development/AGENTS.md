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

## Key Conventions

- All contributions require tests (90% project, 60% infrastructure coverage)
- No mocks — all tests use real numerical examples
- Thin orchestrator pattern enforced for all scripts
- Security vulnerabilities reported via `security.md` process

## See Also

- [README.md](README.md) — Quick navigation
- [Contributing](contributing.md) — How to contribute
- [Testing](testing/) — Testing sub-folder
