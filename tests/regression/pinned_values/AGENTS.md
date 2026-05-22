# `tests/regression/pinned_values/` — agent guide

> Read [`../AGENTS.md`](../AGENTS.md) first.

## What lives here

Per-project pinned ground-truth JSON. **Do not** add ad-hoc
scratch files here — only the per-project `<project>.json`
artefacts.

## When changing a value

Pair every value edit with a `_provenance.<key>` entry containing
commit + date + reason + script. The fixture in
`../conftest.py` exposes these via `pinned_values(project_name)`.

## When adding a new project

Create `<new_project>.json` matching the shape in
[`README.md`](README.md). Bootstrap with empty groups
(`{"figures": {}, "tables": {}, "_provenance": {}}`) and grow as
regression tests are written.
