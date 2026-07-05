# Public active projects

This file is **generated**. Do not edit by hand.

The names below are the public CI/documentation scope: tracked template projects under `projects/` that have both `src/` and `tests/`.

Runtime discovery still uses `infrastructure.project.discovery.discover_projects()` and may include local-only private symlinked projects. Do not copy that local roster into public docs.

Human-written documentation should **not** copy this list into RUN_GUIDE, PAI, or other guides; link here instead. For concrete paths, commands, and layout examples, default to the stable exemplar [`projects/templates/template_code_project/`](../../projects/templates/template_code_project/) unless a doc explicitly compares layouts.

Generated at (timezone.utc): `2026-07-05T19:59:24+00:00`

Current entries:

- `templates/template_active_inference`
- `templates/template_autoresearch_project`
- `templates/template_autoscientists`
- `templates/template_code_project`
- `templates/template_eda_notebook`
- `templates/template_gold_refinement`
- `templates/template_literature_meta_analysis`
- `templates/template_madlib`
- `templates/template_methods_paper`
- `templates/template_newspaper`
- `templates/template_prose_project`
- `templates/template_search_project`
- `templates/template_sia`
- `templates/template_storybook`
- `templates/template_template`
- `templates/template_textbook`

Regenerate after adding, removing, or renaming projects:

```bash
uv run python scripts/generate_active_projects_doc.py
```
