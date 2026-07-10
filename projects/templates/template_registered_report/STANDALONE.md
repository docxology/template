# Standalone fork guide

Use this exemplar for preregistered reports or replication projects outside the monorepo.

1. Copy with `uv run python scripts/audit/copy_exemplar.py --source templates/template_registered_report --dest <destination> --new-name <project_slug>`.
2. Replace `data/example_registration.json`.
3. Record registered-report stage metadata, ethics-review status, and sensitivity analyses.
4. Update `manuscript/config.yaml`, `domain_profile.yaml`, and `experiment_plan.yaml`.
5. Run tests before interpreting any results.

Do not treat exploratory analyses as confirmatory without recording the deviation.
