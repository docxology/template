# Scripts — template_pools_rules_tools

Thin orchestrators: validate sources, run integration, generate manuscript
variables, validate strong-rule compliance. Business logic lives in `src/`.

`05_generate_figures.py` runs the real integration-derived figure set, mirrors
it to `output/figures/`, and writes `figure_registry.json` only after the eight
referenced figures declared in `src/figures.py` are present. Cover art remains
an unreferenced extra and is not misrepresented as manuscript evidence.

## See also

- [`../AGENTS.md`](../AGENTS.md)
- [`README.md`](README.md)
