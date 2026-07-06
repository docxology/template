# scripts

Scripts stay thin. They may set up import paths via `_bootstrap.py`, call project-local `src/` functions, print artifact paths, and call shared manuscript injection.

Do not add Madlib business logic here. Put schema parsing in `src/config.py`, token planning in `src/tokens.py`, session assembly in `src/run.py`, section/table composition in `src/composition*.py` and `src/figure_specs.py`, artifact writing in `src/analysis.py`, and variable-map construction in `src/manuscript_variables.py`.

| Script | Calls |
| --- | --- |
| `_bootstrap.py` | Shared `sys.path` setup for project `src/` imports. |
| `01_generate_madlib_artifacts.py` | `analysis.generate_artifacts` |
| `z_generate_manuscript_variables.py` | `manuscript_variables.generate_variables` plus shared injection |

Scripts may report generated method evidence, but they must not define the method protocol, figure registry, review-packet contract, or fork-migration obligations. Protocol rows, phases, probes, failure modes, audit rules, contribution claims, and review surfaces belong in `manuscript/config.yaml` plus project-local `src/`.

After source or config edits, rebuild generated outputs through the Stage 02–05 path. Do not patch `output/` from a script to make validation pass.
