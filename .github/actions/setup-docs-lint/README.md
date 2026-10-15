# Setup documentation lint environment

Repository-local composite action that installs the real Mermaid CLI and
Puppeteer `chrome-headless-shell`, then exports `CHROME_EXECUTABLE_PATH`.
It explicitly installs and verifies the exact npm version declared by Root
`package.json`'s `packageManager` before `npm ci`. npm 11 preserves the locked
Linux `libc` declaration that npm 10 omits from its installed hidden lock.
The complete native lock comparison remains strict; no metadata is fabricated
or discarded after installation.

```yaml
- uses: actions/checkout@<pinned-sha>
- uses: ./.github/actions/setup-python-env
- uses: ./.github/actions/setup-docs-lint
- run: uv sync
- run: uv run python scripts/audit/lint_docs.py --quiet
```

The npm download cache is enabled (`setup-node` `cache: npm`, keyed on the
lockfile) so repeated provisioning skips tarball downloads while `npm ci`
keeps its deterministic reinstall semantics.

The action intentionally does not run Python setup, dependency sync, or the
linter itself; callers retain those explicit job-level steps.
