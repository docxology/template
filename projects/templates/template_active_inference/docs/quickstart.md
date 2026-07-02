# Quickstart — Active Inference

```bash
# Regenerate all tracks (in order)
uv run python scripts/generate_toy_sweep_tracks.py
uv run python scripts/generate_formal_interop_tracks.py
uv run python scripts/generate_integration_audit.py
uv run python scripts/generate_sheaf_tracks.py
uv run python scripts/z_generate_manuscript_variables.py

# Run tests
uv run pytest projects/templates/template_active_inference/tests/ --cov=src --cov-fail-under=90

# Validation-only compose
uv run python scripts/compose_manuscript.py --validate-only --strict
```
