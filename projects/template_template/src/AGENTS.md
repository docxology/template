# projects_in_progress/template/src/ — Template Source Wrapper

## Purpose

Thin source wrapper for the template meta-project. Contains exactly one Python subpackage (`template/`) implementing introspection, metrics, Markdown injection helpers, and architecture figures. Directory shape mirrors onboarding exemplars (**`projects/template_*_project/src/`**); this slug currently lives under `projects_in_progress/template/src/` pending promotion beside the canonical trio.

## Layout

```text
src/
├── AGENTS.md                 # this file
├── README.md
├── template/                 # actual scaffold subpackage
│   ├── AGENTS.md             # full module inventory
│   ├── README.md
│   ├── __init__.py           # public API surface (32 symbols)
│   ├── introspection.py
│   ├── metrics.py
│   ├── inject_metrics.py
│   └── architecture_viz.py
└── template_meta_project.egg-info/   # build artifact (ignored)
```

## Where to look

All real documentation lives one level down at [`template/AGENTS.md`](template/AGENTS.md). This `src/AGENTS.md` exists only so the doc tree is symmetric with the other active projects (each of which has both an `src/AGENTS.md` and an `src/<package>/AGENTS.md`).

## See Also

- [`README.md`](README.md)
- [`template/AGENTS.md`](template/AGENTS.md) — the actual scaffold module reference
- [`../AGENTS.md`](../AGENTS.md) — project-level docs
