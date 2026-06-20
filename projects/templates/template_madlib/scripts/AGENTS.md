# scripts

Scripts stay thin. They may set up import paths, call project-local `src/` functions, print artifact paths, and call shared manuscript injection.

Do not add Madlib business logic here. Put schema parsing in `src/config.py`, token planning in `src/tokens.py`, section/table composition in `src/composition.py`, artifact writing in `src/analysis.py`, and variable-map construction in `src/manuscript_variables.py`.

Scripts may report generated method evidence, but they must not define the method protocol, figure registry, review-packet contract, or fork-migration obligations. Protocol rows, phases, probes, failure modes, audit rules, contribution claims, and review surfaces belong in `manuscript/config.yaml` plus project-local `src/`.

After source or config edits, rebuild generated outputs through the Stage 02-05 path. Do not patch `output/` from a script to make validation pass.
