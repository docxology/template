# Local-only template exemplars

Some directories under `projects/templates/` may exist on disk but are **not**
part of `PUBLIC_PROJECT_NAMES`, CI, or git tracking. They are listed in
`LOCAL_ONLY_TEMPLATE_NAMES` in [`infrastructure/project/public_scope.py`](../../infrastructure/project/public_scope.py).

## Current entries

_None._ All on-disk exemplars under `projects/templates/` are now fully public:
tracked, CI-gated, and double-published (GitHub + Zenodo). `template_autoscientists`
was the last local-only exemplar and was promoted to the public set on 2026-06-03
(its deterministic coordination core is public-CI-safe; the optional live Hermes
plug-in remains skipped without local model weights).

## Promoting an exemplar to the public set

1. Add its qualified name to `PUBLIC_PROJECT_NAMES` in `public_scope.py`.
2. Add a `.gitignore` negation for `projects/templates/<name>` (mirror the six tracked exemplars).
3. Update the exemplar roster in `CLAUDE.md`, regenerate [`docs/_generated/active_projects.md`](../_generated/active_projects.md), and refresh publication records.

Remove the name from `LOCAL_ONLY_TEMPLATE_NAMES` when promotion is complete.
