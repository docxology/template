# `setup-docs-lint` — technical reference

This composite action provisions the external tools required by the blocking
documentation linter. Both `Static Health Report` and `Documentation Lint`
must call this action before running `scripts/audit/lint_docs.py`.

## Invariants

- `actions/setup-node` and `actions/cache` remain pinned to full SHAs.
- Mermaid diagrams are rendered by the real `mmdc` command against a real
  `chrome-headless-shell`; missing tools fail closed.
- The resolved Chrome path is exported through `GITHUB_ENV` for later workflow
  steps in the caller job.
- Python setup and `uv sync` remain caller responsibilities.

## Verification

- Run `actionlint` after editing this action or either caller.
- The CI `Documentation Lint` and `Static Health Report` jobs are the real
  behavioral controls because the hosted-runner cache and `GITHUB_ENV`
  propagation are GitHub Actions behavior.
