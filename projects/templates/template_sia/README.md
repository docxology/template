# template_sia

Public exemplar for the SIA (Self-Improvement Agent) harness: Meta → Target → Feedback
loops with public/private task splits and canonical generation artifacts.

## Quick start

```bash
uv run python projects/templates/template_sia/scripts/run_sia_loop.py
uv run python projects/templates/template_sia/scripts/z_generate_manuscript_variables.py
uv run python scripts/01_run_tests.py --project templates/template_sia --project-only
```

Default runs replay fixtures under `src/fixtures/recorded_generations/`. Pass
`--live-sia` for bounded subprocess execution.

## Documentation

- [`AGENTS.md`](AGENTS.md) — module map and contracts
- [`docs/quickstart.md`](docs/quickstart.md) — fork and extend
- [`../../../infrastructure/sia/README.md`](../../../infrastructure/sia/README.md) — Layer 1 API
