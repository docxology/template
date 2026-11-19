# projects/templates/template_template/src/ — Template Source Wrapper

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
    ├── core/
    │   ├── __init__.py
    │   ├── introspection.py
    │   ├── contracts.py
    │   └── paths.py
    ├── metrics/
    │   ├── __init__.py
    │   ├── metrics.py
    │   └── inject_metrics.py
    └── figures/
        ├── __init__.py
        ├── architecture_viz.py
        ├── viz_palette.py
        ├── figure_specs.py
        ├── figure_architecture_overview.py
        ├── figure_pipeline_stages.py
        ├── figure_module_inventory.py
        ├── figure_comparative_matrix.py
        └── figure_comparative_panels.py
```

## Where to look

Module documentation: [`template_template/AGENTS.md`](template_template/AGENTS.md).

## Publishing

Release workflow (monorepo docs): [Publishing guide](https://github.com/docxology/template/blob/main/docs/guides/publishing-guide.md) and [Zenodo DOI strategy](https://github.com/docxology/template/blob/main/docs/guides/zenodo-doi-strategy.md). Concept DOI lives in `manuscript/config.yaml` → `publication.doi`.

## See Also

- [`README.md`](template_template/README.md)
- [`template_template/AGENTS.md`](template_template/AGENTS.md)
- [`../AGENTS.md`](../AGENTS.md)
