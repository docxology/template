# Functional CI and optional hardening

The public template should be easy to install and use. Default CI checks that
contract on Linux/Python 3.14, without starting Docker, Lean, a browser, or a
native document acceptance matrix.

Every public template builds a wheel and runs the real behavioral tests listed
in `.github/project-smoke.json`, in a separate pytest process. Most tests use a disposable project copy; tests
whose fixtures require genuine monorepo source/DATA run from their canonical
project and use their existing disposable fixtures. The selection
must cover the complete public roster and contain existing project-local tests.
Infrastructure runs its existing pipeline smoke selection. Lint/type checks,
Bandit, secret scanning and the public tracking boundary remain blocking. The
`CI Gate` requires every functional job to succeed; a missing, cancelled,
skipped or failed required job cannot turn green.

Run a project's same selection locally after locked root setup:

```bash
uv sync --locked --group installed-build
uv run python scripts/gates/ci_smoke.py --project templates/template_code_project
```

Advanced Literature Review also needs its declared Meta provider installed;
CI builds that provider wheel before its behavioral tests. A project wheel
build is packaging evidence; these source-tree tests do not certify installation
outside the checkout, publication, native rendering, or scientific validity.

## Further hardening

Use the manual **Optional Hardening** workflow for the former complete
infrastructure shards, Python 3.12–3.14 project suites, aggregate coverage,
platform breadth and extended documentation checks. Use the separate manual
**Platform required acceptance** workflow when original source/runtime custody,
native document replay or formal release acceptance is needed. Neither runs
on an ordinary main push. Existing full-suite coverage floors and release
custody requirements remain in those lanes.

Each project's README suggests its next hardening step. Focused CI passing
means the named functional selection passed. It does not close the recorded
exhaustive acceptance or historical measurement gaps. Coverage snapshots are
dated evidence and must be remeasured before promoting them to a current
full-suite claim. An explicit hardening run may still expose those gaps.
