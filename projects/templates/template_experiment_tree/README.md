# template_experiment_tree

A living research record where every experiment is a node in a
version-controlled experiment tree with **frozen nodes**. Inspired by the
OpenResearch ideas (MIT-licensed inspiration only; no upstream code copied),
this exemplar complements `template_autoresearch_project` and
`template_autoscientists` by making the *record itself* the durable
artifact: nodes are preregistered (frozen) before being run and may never
be back-filled, and the manuscript is a deterministic projection of the
tree state.

## What it honestly shows

- Answered nodes (`win`/`loss`/`dead_end`) form the results table.
- Frozen nodes are preregistrations; answering them raises.
- Dead ends are a first-class negative-result registry.
- Every manuscript number is generated from the tree (`{{EXP_*}}` tokens);
  a token with no tree backing fails hydration.

## Quick start

```bash
uv run python projects/templates/template_experiment_tree/scripts/init_tree.py
uv run python projects/templates/template_experiment_tree/scripts/record_experiment.py E002 "halving did not help" dead_end
uv run python projects/templates/template_experiment_tree/scripts/report.py
uv run python projects/templates/template_experiment_tree/scripts/z_generate_manuscript_variables.py
```

## When to use this template

Use `template_experiment_tree` when the deliverable is a research log that
stays honest over months: you want planned, preregistered, and answered
experiments in one durable tree, negative results registered (not buried),
and a manuscript that regenerates from the tree instead of drifting from
it. Choose `template_registered_report` when you need a formal
preregistration document; choose this when the record is the paper.
