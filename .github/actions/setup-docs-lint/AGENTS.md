# `setup-docs-lint` — technical reference

This composite action provisions the shared external Mermaid-rendering tools.
Both `Static Health Report` and `Documentation Lint` call it before running
`scripts/audit/lint_docs.py`; the two `template_textbook` project-matrix cells
call it before their real Mermaid resolver and renderer tests.

## Invariants

- `actions/setup-node` and `actions/cache` remain pinned to full SHAs.
- Mermaid diagrams are rendered by the real `mmdc` command against a real
  `chrome-headless-shell`; missing tools fail closed.
- The resolved Chrome path is exported through `GITHUB_ENV` for later workflow
  steps in the caller job.
- Python setup and `uv sync` remain caller responsibilities.

## Verification

- Run `actionlint` after editing this action or any caller.
- The CI `Documentation Lint`, `Static Health Report`, and textbook project
  jobs are the real behavioral controls because the hosted-runner cache and
  `GITHUB_ENV` propagation are GitHub Actions behavior.
