# Storybook Tests

```bash
uv run pytest projects/templates/template_storybook/tests/ \
  --cov=projects/templates/template_storybook/src --cov-fail-under=90
```

The tests validate the YAML story contract, opposite-family character pairing,
single-page PNG rendering, PDF assembly, and script-level orchestration.
