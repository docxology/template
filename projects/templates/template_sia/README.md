# template_sia

Public exemplar for the SIA (Self-Improvement Agent) harness: Meta → Target → Feedback
loops with public/private task splits and canonical generation artifacts.

## Publication and rendering

- Standalone GitHub: [docxology/template_sia](https://github.com/docxology/template_sia)
- Latest GitHub release: [v0.1.2](https://github.com/docxology/template_sia/releases/tag/v0.1.2)
- Zenodo concept DOI: [10.5281/zenodo.20453879](https://doi.org/10.5281/zenodo.20453879)
- Latest Zenodo version DOI: [10.5281/zenodo.20932066](https://doi.org/10.5281/zenodo.20932066) ([record](https://zenodo.org/records/20932066))
- Canonical renderer: [docxology/template](https://github.com/docxology/template) with `--project templates/template_sia`
- Tracked outputs: [`output/`](output/) in this project and `output/templates/template_sia/` in the monorepo; public output files above 50 MB stay out of git.

To regenerate this exemplar from the public monorepo:

```bash
git clone https://github.com/docxology/template
cd template
uv sync
./run.sh --project templates/template_sia --pipeline --core-only
uv run python scripts/04_validate_output.py --project templates/template_sia
uv run python scripts/05_copy_outputs.py --project templates/template_sia
```

Standalone repositories are publication mirrors for source, DOI metadata, and
tracked rendered artifacts. Use the monorepo above when you need the full shared
infrastructure, pipeline stages, or cross-template validation.

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
