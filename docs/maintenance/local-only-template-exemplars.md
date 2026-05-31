# Local-only template exemplars

Some directories under `projects/templates/` may exist on disk but are **not**
part of `PUBLIC_PROJECT_NAMES`, CI, or git tracking. They are listed in
`LOCAL_ONLY_TEMPLATE_NAMES` in [`infrastructure/project/public_scope.py`](../../infrastructure/project/public_scope.py).

## Current entries

| Qualified name | Why local-only |
| --- | --- |
| `templates/template_autoscientists` | AutoScientists (arXiv:2605.28655) coordination exemplar with a live Hermes plug-in that depends on local model weights. Exercised locally; not part of public CI. |

## Promoting an exemplar to the public set

1. Add its qualified name to `PUBLIC_PROJECT_NAMES` in `public_scope.py`.
2. Add a `.gitignore` negation for `projects/templates/<name>` (mirror the six tracked exemplars).
3. Update the exemplar roster in `CLAUDE.md`, regenerate [`docs/_generated/active_projects.md`](../_generated/active_projects.md), and refresh publication records.

Remove the name from `LOCAL_ONLY_TEMPLATE_NAMES` when promotion is complete.
