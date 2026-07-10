# Standalone fork guide

Use this exemplar for lawful release-review and redaction workflows outside the monorepo.

1. Copy with `uv run python scripts/audit/copy_exemplar.py --source templates/template_redacted_report --dest <destination> --new-name <project_slug>`.
2. Replace public fixture segments with cleared sample content only.
3. Configure the lawful classification taxonomy, release ceiling, residual-risk patterns, and required reviewer roles for your organization.
4. Replace invented review records with cleared approval records that do not expose source text.
5. Update `manuscript/config.yaml`, `domain_profile.yaml`, and `experiment_plan.yaml`.
6. Run tests before generating a release report.

Never commit real classified, privileged, or source-identifying material to a public fork.
