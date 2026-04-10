# projects/template/src/ — Template Source Wrapper

## Purpose

Thin source wrapper for the template project. Contains exactly one Python subpackage — `template/` — which holds all of the template's actual code (introspection, metrics, injection, visualization). This level exists only to align the template with the standard `projects/<name>/src/<package>/` layout used by the other active projects (`code_project`, `cognitive_case_diagrams`, `fep_lean`).

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
