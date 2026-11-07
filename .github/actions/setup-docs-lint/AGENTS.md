# `setup-docs-lint` — technical reference

This composite action provisions the external tools required by the blocking
documentation linter. Both `Static Health Report` and `Documentation Lint`
must call this action before running `scripts/audit/lint_docs.py`.

## Invariants

- `actions/setup-node` and `actions/cache` remain pinned to full SHAs.
- Select exactly Node 24.22.0 LTS; Root's `24.x` engine and native
  Mermaid CLI12.2 admission require the same major. Preserve the Source-declared
  npm serializer and every third-party lock record.
- `setup-node` enables `cache: npm` (CI-FAST-DOCSLINT-NPM-1): the npm
  download cache is keyed on the lockfile by the official action; `npm ci`
  semantics stay unchanged (deterministic reinstall), only tarball
  downloads are skipped.
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


The Source lock binds CLI12.2.0, Mermaid12.3.0 and its embedded patched KaTeX;
the standalone KaTeX/CSS package has its own exact locked version. The setup
runs the repository's output-only inherited-trust regression after npm install,
with dependency lifecycle scripts disabled. Chrome's cache is keyed on this
lock, and the awaited installed Puppeteer `executablePath({headless: 'shell'})`
selects the actual required browser after installation. Cache enumeration cannot
select an older retained browser. Preparation and these scoped controls do not
grant native or release acceptance.
