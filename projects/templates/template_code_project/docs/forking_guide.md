# Forking Guide — template_code_project

> A 5-minute walkthrough for copying this exemplar into a new
> research-project directory. The point of the guide is to make every
> decision explicit so a forker doesn't have to read every other doc to
> find out *what's required vs aesthetic, what's enforced vs convention,
> and what they'll hit friction on*.

## TL;DR

```bash
# 0. From the repo root, install deps once
uv sync

# 1. Copy the exemplar to your new project name
cp -r projects/templates/template_code_project projects/my_project
rm -rf projects/my_project/src/*.egg-info     # stale package metadata
rm -rf projects/my_project/output              # disposable

# 2. Rename the package in pyproject.toml + manuscript/config.yaml
sed -i.bak 's/template_code_project/my_project/g' \
  projects/my_project/pyproject.toml \
  projects/my_project/manuscript/config.yaml
rm projects/my_project/pyproject.toml.bak projects/my_project/manuscript/config.yaml.bak

# 3. Run the tests against your fork
uv run pytest projects/my_project/tests/ \
    --cov=projects/my_project/src \
    --cov-fail-under=90 -q

# 4. Run the analysis pipeline against your fork
uv run python projects/my_project/scripts/optimization_analysis.py
```

**⚠️ Confidentiality invariant.** The repo `.gitignore` is configured so
that **only** the public canonical exemplars listed in
[`../../../docs/_generated/active_projects.md`](../../../../docs/_generated/active_projects.md)
under `projects/` are ever git-tracked. Your fork (`projects/my_project/`)
is local-only and won't be pushed to the public repo even if you `git
add -f` it — `scripts/check_tracked_projects.py` blocks the push in
`pre-push-quick`. Read [`../../../../CLAUDE.md`](../../../../CLAUDE.md)
"CONFIDENTIALITY INVARIANT" for the full fence.

## What you're forking

This template is a **research-project skeleton**: pure-math `src/`,
thin-orchestrator `scripts/`, real-data `tests/`, token-substituted
`manuscript/`, and a 4-phase analysis → variables → render → copy pipeline.
The included gradient-descent algorithm is throwaway scaffolding for the
**transferable pattern**: every numeric in the manuscript is a
`{{TOKEN}}` registered in one Python function and cross-checked by one
regression test. That's the discipline being taught — your fork should
preserve it regardless of what domain you swap in.

## REQUIRED vs AESTHETIC

A pipeline-enforced gate fails CI if you delete a REQUIRED path. An
AESTHETIC path is convention only — delete it and nothing complains
automatically. The full inventory lives in [`AGENTS.md`](AGENTS.md);
the short version:

| Class | Examples | Action |
|---|---|---|
| REQUIRED — pipeline gate | `src/optimizer.py` and `invariants.py` (math primitives), all `tests/test_*.py`, `pyproject.toml`, `manuscript/config.yaml`, `manuscript/*.md`, `manuscript/references.bib`, `manuscript/preamble.md` | Keep them; the 90% coverage gate + LaTeX render depend on them |
| REQUIRED — orchestration | `src/analysis/`, `src/figures/`, `src/dashboard.py`, `src/manuscript_variables.py`, all `scripts/*.py` | May import `infrastructure.*`; exercised by the end-to-end pipeline run |
| AESTHETIC | `docs/*.md`, `*/STYLE.md`, `*/PATTERNS.md`, `*/CONVENTIONS.md`, `*/AGENTS.md`, `*/README.md` | Drift detected only by `scripts/check_template_drift.py` and audits; aspire to update them when code changes |

## Concrete first steps after fork

### 1. Replace the algorithm
Edit `src/optimizer.py` with your real algorithm. Keep it
**infrastructure-free** (no `from infrastructure import ...`) — the
math-primitive purity is what lets you copy `src/optimizer.py` into any
Python environment without the pipeline installed. The orchestration
modules (`analysis/`, `figures/`, etc.) are the right place for
infrastructure-coupled code.

### 2. Update the manuscript variables
`src/manuscript_variables.py::generate_variables()` is the **single
function** that produces every numeric token referenced in
`manuscript/*.md`. When you change the algorithm:

1. Add new tokens to `generate_variables()`.
2. Reference them in your manuscript as `{{NEW_TOKEN}}`.
3. The regression test
   `tests/test_manuscript_variables.py::test_all_manuscript_tokens_are_generated`
   automatically fails if a token is referenced but not generated.

### 3. Update the test suite
`tests/` enforces the [Zero-Mock Policy](testing_philosophy.md). Every
test exercises real algorithms with real data — no `unittest.mock`,
`MagicMock`, or `@patch`. Orchestration tests may use `pytest.MonkeyPatch`
on module attributes or subprocess import isolation (see [`../tests/PATTERNS.md`](../tests/PATTERNS.md)) — not mock factories that fake algorithm output. If you find
yourself wanting to mock something inside pure-math `src/`, that means the code
belongs in `scripts/` instead.

### 4. Run the drift checker before pushing
```bash
uv run python scripts/check_template_drift.py
```
The checker runs 9 detectors against the public canonical exemplars; while
forks are not yet covered, the gate will still flag any global drift
your changes introduced into the shipped templates.

## Common friction points (and fixes)

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: optimizer` | Running a script from inside `src/` instead of the repo root | `cd` to the repo root; `uv run python projects/my_project/scripts/optimization_analysis.py` |
| `PDF Rendering` stage fails with `mmdc could not find Chrome` | Manuscript embeds `mermaid` blocks; `mmdc` needs a pinned `chrome-headless-shell` not in your Puppeteer cache | One-time: `npx --yes puppeteer browsers install chrome-headless-shell`; the included `scripts/00_preflight.py` emits an actionable warning before the PDF stage if this is missing |
| Test count drift / coverage drift | Docs in `docs/` hardcoded an old number | The drift checker now warns; replace literal numbers with a link to `docs/_generated/canonical_facts.md` |
| `{{TOKEN}}` appears literally in rendered PDF | `scripts/z_generate_manuscript_variables.py` was not re-run, or the token is not in `generate_variables()` | Re-run `z_generate_manuscript_variables.py`; if still literal, add the token to `generate_variables()` |
| Stale `*.egg-info/` after rename | `pip install -e .` regenerated it under the old package name | `rm -rf src/*.egg-info/`; the `.gitignore` glob already covers any future occurrence |

## Sibling exemplar

[`template_prose_project`](../../template_prose_project) is the
prose-review sibling — same shape, no algorithm, validates a manuscript
instead of analyzing it. If your work is editorial rather than
numerical, fork that one instead.

## See also

- [`AGENTS.md`](AGENTS.md) — full doc inventory and reading order
- [`agent_instructions.md`](agent_instructions.md) — 7 hard rules
- [`architecture.md`](architecture.md) — module boundaries
- [`testing_philosophy.md`](testing_philosophy.md) — zero-mock standard
- [`output_inventory.md`](output_inventory.md) — producer/consumer graph
- [`troubleshooting.md`](troubleshooting.md) — symptom-driven fixes
- [`../../../scripts/check_template_drift.py`](../../../../scripts/check_template_drift.py) — the drift checker
