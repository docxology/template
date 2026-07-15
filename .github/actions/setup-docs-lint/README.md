# Setup documentation lint environment

Repository-local composite action that installs the real Mermaid CLI and
Puppeteer `chrome-headless-shell`, then exports `CHROME_EXECUTABLE_PATH`.

```yaml
- uses: actions/checkout@<pinned-sha>
- uses: ./.github/actions/setup-python-env
- uses: ./.github/actions/setup-docs-lint
- run: uv sync
- run: uv run python scripts/audit/lint_docs.py --quiet
```

The action intentionally does not run Python setup, dependency sync, or the
linter itself; callers retain those explicit job-level steps.
