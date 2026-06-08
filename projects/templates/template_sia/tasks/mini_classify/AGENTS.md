# tasks/mini_classify/

Default exemplar task: a tiny supervised-classification problem the SIA loop
improves across generations. Deterministic by default (fixture replay); see
[`docs/testing_philosophy.md`](../../docs/testing_philosophy.md) for the
fixture-vs-live boundary.

## Data boundary (public vs private)

- **`data/public/`** — everything a target agent may read at generation time:
  `train.csv` (features + a training label column), `task.md` (the problem
  statement), and `evaluate.py` (the scorer). Target agents read **only** this
  tree.
- **`data/private/`** — `labels.csv` is the held-out scoring key consumed by
  `evaluate.py` **after** the agent runs. Target agents must never import from
  or read `data/private/`; doing so is label leakage and invalidates the
  evaluation.

## Evaluation output contract

`evaluate.py` writes `results.json` with exactly:

- `metric_name` (str) — `"accuracy"` for this task,
- `metric_value` (float) — score in `[0, 1]`,
- `n_samples` (int) — number of scored rows (`6` for `mini_classify`).

The loop reads these fields back via
`infrastructure.sia.evaluation_runner.read_results_json`, which rejects hollow
or wrong-typed objects (see `tests/test_gate_negative_controls.py`).

## Reference baseline

`reference/reference_target_agent.py` is the canonical generation-1 scaffold.
Live mode copies and executes it to seed the loop; fixture replay requires the
file to exist (task-layout contract) but never executes it — replay is driven
entirely by `src/fixtures/recorded_generations/`.
