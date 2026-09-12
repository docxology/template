# scripts

Scripts stay thin. They may set up import paths via `_bootstrap.py`, call project-local `src/` functions, print artifact paths, and call shared manuscript injection.

Do not add Madlib business logic here. Put schema parsing in `src/template_madlib/config.py`, token planning in `src/template_madlib/tokens.py`, session assembly in `src/template_madlib/run.py`, section/table composition in `src/template_madlib/composition*.py` and `src/template_madlib/figure_specs.py`, artifact writing in `src/template_madlib/analysis.py`, and variable-map construction in `src/template_madlib/manuscript_variables.py`.

| Script | Calls |
| --- | --- |
| `00_preflight.py` | Runs shared manuscript preflight checks before rendering. |
| `02_validate_outputs.py` | Runs `template_madlib.output_validator.validate_generated_outputs` and writes `output/reports/output_validation.json`; fails the stage when token provenance, figure registry, field origins, or the declared artifact inventory drift. |
| `_bootstrap.py` | Adds project root and repo root to `sys.path` for `from template_madlib…` imports. |
| `01_generate_madlib_artifacts.py` | `template_madlib.analysis.generate_artifacts` |
| `z_generate_manuscript_variables.py` | `template_madlib.manuscript_variables.generate_variables` plus shared injection |

Scripts may report generated method evidence, but they must not define the method protocol, figure registry, review-packet contract, or fork-migration obligations. Protocol rows, phases, probes, failure modes, audit rules, contribution claims, and review surfaces belong in `manuscript/config.yaml` plus project-local `src/template_madlib/`.

After source or config edits, rebuild generated outputs through the Stage 02–05 path. Do not patch `output/` from a script to make validation pass.
