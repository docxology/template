# `src/` — Agent Guide

setuptools **src-layout**. The only importable package is
[`template_formal/`](template_formal/) one level down — see
[`template_formal/AGENTS.md`](template_formal/AGENTS.md) for the package map,
subpackage responsibilities, and the layer-dependency contract.

## Contract

- [`__init__.py`](__init__.py) at this level is a forkability-contract stub
  (every exemplar's `src/` has one). Do not add code here — it belongs in
  `template_formal/`.
- Never hard-code the package's filesystem location. `tests/conftest.py`
  inserts repo root, project root, and `src/` onto `sys.path` explicitly;
  `pyproject.toml`'s `[tool.pytest.ini_options] pythonpath = [".", "src"]` and
  `[tool.mypy] mypy_path = "src"` are the two other places this path is
  declared. Keep all three in sync if the layout ever changes.
- `mypy --strict` is invoked with `--explicit-package-bases
  --namespace-packages` (see `tests/test_mypy_oracle.py`) specifically because
  of this src-layout — a plain `mypy --strict src/` without those flags
  resolves package roots differently.

See [`../AGENTS.md`](../AGENTS.md) (project root) for the full project map.
