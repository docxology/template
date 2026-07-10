# Standalone fork guide

Use this exemplar when starting a data descriptor project outside the monorepo.

1. Copy with `uv run python scripts/audit/copy_exemplar.py --source templates/template_data_descriptor --dest <destination> --new-name <project_slug>`.
2. Replace `data/example_descriptor.json` with your descriptor.
3. Add units, bounds, allowed values, and pattern constraints for every publishable field.
4. Update `manuscript/config.yaml` and `domain_profile.yaml`.
5. Run `uv run pytest tests --cov=src --cov-fail-under=90` from the fork root after adapting imports.

Do not copy generated `output/`, local virtual environments, or cache folders.
