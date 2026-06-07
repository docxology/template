# FAQ — template_sia

## When should I fork `template_sia` vs `template_autoresearch_project`?

Fork **`template_sia`** when you need a Meta → Target → Feedback benchmark harness with public/private task splits and generation artifact trees.

Fork **`template_autoresearch_project`** when you need readiness checks, evidence ledgers, and claim/artifact gates without a generation loop.

## Does this vend upstream SIA code?

No. It reimplements the **contract** (task layout, artifact tree, evaluation schema) described in [arXiv:2605.27276](https://arxiv.org/abs/2605.27276) and the [hexo-ai/sia](https://github.com/hexo-ai/sia) repository — not the upstream orchestrator.

## Why fixture replay instead of live LLM in CI?

Reproducibility and cost. Default runs copy recorded generations from `src/fixtures/recorded_generations/` so CI never depends on Ollama or non-deterministic model output.

## How do I add a new task?

1. Copy `tasks/mini_classify/` to `tasks/<your_task>/`
2. Keep `data/public/`, `data/private/`, `reference/`, and `evaluate.py`
3. Point `sia.task_name` in `manuscript/config.yaml`
4. Add fixtures under `src/fixtures/recorded_generations/` for default replay
5. Validate: `uv run python -m infrastructure.sia.cli validate tasks/<your_task>`

## Where are live metrics documented?

Only in generated outputs and manuscript tokens after a live run. Committed manuscript prose uses `{{SIA_*}}` placeholders — not hard-coded benchmark numbers.
