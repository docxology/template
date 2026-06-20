# template_sia

Public exemplar for the SIA (Self-Improvement Agent) harness: Meta → Target → Feedback
loops with public/private task splits and canonical generation artifacts.

## Run via the template monorepo

This exemplar lives at `projects/templates/template_sia/` in the public
[docxology/template](https://github.com/docxology/template) repository.
**Tests, analysis, PDF rendering, and CI all run through that monorepo** —
clone it, run `uv sync` at the repository root, then:

```bash
./run.sh --project templates/template_sia --pipeline --core-only
# or: uv run python scripts/execute_pipeline.py --project templates/template_sia --core-only
```

Several exemplars also publish standalone GitHub/Zenodo releases for citation;
those mirrors are outputs of this pipeline. The monorepo remains the canonical
build and render surface.

## When to use this template

Use this template when you need a **self-improvement-agent evaluation
harness**: Meta → Target → Feedback generation loops, public/private task
splits to detect overfitting, deterministic fixture replay for testability,
and fail-closed loop validation. It demonstrates the harness *mechanics* —
not autonomous live code modification (see the honesty note below). For
agent-team coordination mechanisms see
[`template_autoscientists`](../template_autoscientists/); for a bounded
AutoResearch loop see
[`template_autoresearch_project`](../template_autoresearch_project/). Full
roster:
[`projects/AGENTS.md`](../../AGENTS.md#permanent-canonical-exemplars-and-optional-search-add-on).

## Quick start

```bash
uv run python projects/templates/template_sia/scripts/run_sia_loop.py
uv run python projects/templates/template_sia/scripts/z_generate_manuscript_variables.py
uv run python scripts/01_run_tests.py --project templates/template_sia --project-only
```

Default runs replay fixtures under `src/fixtures/recorded_generations/`. Pass
`--live-sia` for bounded subprocess execution.

> **Live mode is a deterministic stub.** `--live-sia` runs the *reference* agent
> as a bounded subprocess and records its evaluation, but it does **not** mutate
> target code and uses **no sandbox**: the `improvement.md` feedback note is
> illustrative and is never applied, so the target agent is identical across
> generations. Self-improvement *across generations* is demonstrated only via
> **fixture replay**. This exemplar shows the harness mechanics, not autonomous
> live code modification.

## Documentation

- [`AGENTS.md`](AGENTS.md) — module map and contracts
- [`docs/quickstart.md`](docs/quickstart.md) — fork and extend
- [`../../../infrastructure/sia/README.md`](../../../infrastructure/sia/README.md) — Layer 1 API

## Template integrity

- Forward backlog: [`TODO.md`](TODO.md).
- Copy-and-customize config: [`manuscript/config.yaml.example`](manuscript/config.yaml.example).
- Project validation: `uv run pytest projects/templates/template_sia/tests/ --cov=projects/templates/template_sia/src --cov-fail-under=90`.
- Repo drift validation: `uv run python scripts/check_template_drift.py --strict`.
