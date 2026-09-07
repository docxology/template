# Scripts — template_pools_rules_tools

Thin orchestrators: they run source checks, integration, manuscript-variable
generation, strong-rule compliance checks, and figure generation. Business
logic lives in `src/`. Source validation fails closed: non-compliant sources
stop the run before any figures generate rather than shipping contradictions
(negative control: `tests/test_strong_rule_evaluator.py::test_section_schema_flags_missing_section`
proves the validator fires on a missing section).

## Files

| File | Role |
| --- | --- |
| `01_validate_sources.py` | Validate fonds, rule sets, and tool manifests. |
| `02_run_integration.py` | Run the end-to-end integration demo and write its report. |
| `03_generate_manuscript.py` | Write integration-derived manuscript variables. |
| `04_validate_strong_rules.py` | Evaluate strong rules against the project context. |
| `05_generate_figures.py` | Generate the nine PNG assets and the eight-label registry. |
| `z_generate_manuscript_variables.py` | Hydrate tokens into the render tree. |

`05_generate_figures.py` runs the real integration-derived figure set, mirrors
it to `output/figures/`, and writes `figure_registry.json` only after the eight
referenced figures declared in `src/figures.py` are present. Cover art remains
an unreferenced extra and is not misrepresented as manuscript evidence.

## See also

- [`../AGENTS.md`](../AGENTS.md)
- [`README.md`](README.md)
