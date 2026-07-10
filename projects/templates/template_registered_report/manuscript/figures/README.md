# figures - template_registered_report

Committed manuscript figures for the registered-report exemplar. Each PNG is
regenerated deterministically by `scripts/generate_figures.py` from tested
functions in `src/registered_report/demo_study.py`:

- `hypothesis_map.png` — registered hypothesis-to-outcome-to-analysis mapping
  (`fig:hypothesis_map`).
- `analysis_dag.png` — registered-report workflow with the pre-results lock
  boundary (`fig:analysis_dag`).
- `deviation_timeline.png` — preregistration-versus-executed deviation ledger
  timeline (`fig:deviation_timeline`).
- `permutation_result.png` — seeded permutation null distribution and observed
  difference for the demonstration study (`fig:permutation_result`).

Regenerate from the repository root:

```bash
MPLBACKEND=Agg uv run python \
    projects/templates/template_registered_report/scripts/generate_figures.py
```

These figures are embedded directly by the manuscript sections under
`manuscript/`. Do not hand-edit the PNGs; change the source functions or the
registration fixture and regenerate.
