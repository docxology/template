# `infrastructure/search/deep_research/`

## Purpose

Provider-neutral orchestration for long-running deep research tasks. The
package chooses between OpenAI and Gemini, builds provider-specific payloads,
and keeps the SDK imports lazy so the rest of the repo stays importable without
the optional vendor packages installed.

## Local rules

- Keep request/response models provider-neutral.
- Put OpenAI-specific request mapping in `openai.py`.
- Put Gemini-specific request mapping in `gemini.py`.
- Put project-context packing in `project_context.py`; include rendered
  manuscript plaintext, bibliography files, and PDF text extraction when
  available.
- Prefer the dispatcher in `client.py` for new entry points.
- Do not import the SDKs at module load time.

## Provider policy

- Prefer OpenAI when the job depends on vector stores or remote MCP.
- Prefer Gemini when the job requests collaborative planning or generated visuals.
- Require an explicit provider override only when the caller needs a hard
  routing decision.
- Use `submit_many()` / `submit_and_wait_many()` when a single request should
  be sent to both providers and returned as two reports.
- Use `submit_project_and_save_reports()` when the caller wants the same
  request to be packed from a project tree, dispatched to both providers, and
  saved under `output/reports/deep_research/`.

## Cost & budget rules (measured 2026-06-10 — see README "Cost model")

- ≈ **$2 per project report on OpenAI** (`o3-deep-research`, `max_tool_calls=12`);
  ≈ **$25 per Gemini report** (agentic loop ⇒ ~9.3M tokens/job). Default to
  OpenAI-only for routine loops; both providers ≈ $25–40/project.
- `background=True` jobs **bill to completion even if never polled** — never
  fire-and-forget diagnostic submissions; cancel or budget them.
- Gemini jobs take 30–60+ min; poll budgets must exceed 30 min.
- Cost knobs: `max_tool_calls` (OpenAI), `collect_project_context(max_total_chars=...)`
  (input side), provider selection (biggest lever).
- Multi-project loop recipe lives in [`README.md`](README.md) — deliberate,
  paid action; never wire it into default pipeline/CI.

## Validation (deterministic — free, no network)

```bash
uv run pytest tests/infra_tests/search/test_deep_research.py \
    tests/infra_tests/search/test_deep_research_retry_cli.py -q
```

Live validation (paid, opt-in, requires `.env` keys + `uv sync --group deep-research`):

```bash
uv run python -m infrastructure.search.deep_research providers   # free availability check
# then: submit / poll / run-project — see README CLI section
```

## See also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
