# projects/template_template/src/ — Template Source Wrapper

## Purpose

Thin source wrapper for the template meta-project. Contains the `template_template/` Python subpackage (introspection, metrics, Markdown injection, architecture figures).

## Layout

```text
src/
├── AGENTS.md
├── README.md
├── __init__.py
└── template_template/
    ├── AGENTS.md
    ├── README.md
    ├── __init__.py
    ├── introspection.py
    ├── metrics.py
    ├── inject_metrics.py
    └── architecture_viz.py
```

## Where to look

Module documentation: [`template_template/AGENTS.md`](template_template/AGENTS.md).

## Publishing

Release workflow: [`../../../docs/guides/publishing-guide.md`](../../../docs/guides/publishing-guide.md) and [`../../../docs/guides/zenodo-doi-strategy.md`](../../../docs/guides/zenodo-doi-strategy.md). Concept DOI lives in `manuscript/config.yaml` → `publication.doi`.

## See Also

- [`README.md`](README.md)
- [`template_template/AGENTS.md`](template_template/AGENTS.md)
- [`../AGENTS.md`](../AGENTS.md)
