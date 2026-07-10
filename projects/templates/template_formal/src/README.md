# `src/` — src-layout root

This project uses setuptools **src-layout**: the importable package lives at
[`src/template_formal/`](template_formal/), one level below this directory, not
at the project root. [`src/__init__.py`](__init__.py) exists only to satisfy the
repo-wide exemplar forkability contract (every `src/` needs an `__init__.py`
present); it is never itself imported and carries no code.

Everything that matters — the type vocabulary, storage, protocol, network,
agent, and colony subpackages — is documented in
[`src/template_formal/README.md`](template_formal/README.md) and
[`AGENTS.md`](template_formal/AGENTS.md).

## Why src-layout

`pyproject.toml`'s `[build-system]` is `setuptools.build_meta`, and
`pyproject.toml` is what installs `template_formal` — src-layout keeps the
package import path (`import template_formal`) decoupled from the repo's
current working directory, so `uv run pytest` and `mypy --strict` resolve the
same package whether invoked from the project root or the monorepo root (see
`tests/conftest.py`'s explicit `sys.path` wiring for the three roots this
needs: repo root, project root, and `src/`).
