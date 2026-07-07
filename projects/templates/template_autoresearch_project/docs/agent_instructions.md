# Agent Instructions — AutoResearch Project

## Operational Constraints

1. **Always deterministic.** All ML task evaluation must be reproducible
   with fixed seeds. Never use network calls or live LLM during the
   core pipeline.
2. **Evidence-bound claims.** Every manuscript claim must trace to a
   concrete artifact on disk. `readiness_valid = True` only when every
   required artifact is substantively populated.
3. **No autonomous approval.** No generated readiness can self-approve
   publication. Human review gates (`human_review.yaml`) are the only
   authority for publication decisions.
4. **Budget finite.** The ML candidate budget is capped. Candidates
   beyond it are recorded as "deferred" — never silently discarded.

## Workflow

1. Edit loop logic in `src/loop.py`. Add I/O handlers in `src/writers/`.
2. Add manuscript tokens in `src/manuscript/manuscript_tokens_*.py`.
3. Register any new figure in the figure registry.
4. Run: `uv run pytest tests/ --cov=src --cov-fail-under=90`.
5. Run the bounded ML pipeline: `uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_autoresearch_project`.
6. Validate: `uv run python -m infrastructure.autoresearch.cli validate --project template_autoresearch_project --fail-on-issues`.

## Critical references

- `autoresearch.yaml` — stage names must exactly match `pipeline.yaml`.
- `seed_ideas.yaml` — accepted ideas must link to evidence paths.
- `human_review.yaml` — the only publication authority.
