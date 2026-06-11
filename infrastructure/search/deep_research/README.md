# `infrastructure/search/deep_research/`

Provider-neutral deep research orchestration for long-running research jobs.
The package chooses between OpenAI and Gemini based on credentials and
request shape, then builds provider-specific payloads lazily.

For project-scale runs, `collect_project_context()` packages rendered project
plaintext into a bounded prompt block, including manuscript markdown, `.bib`
bibliography files, and extracted PDF text when a rendered PDF is present.
`DeepResearchClient.submit_and_wait_many()` can fan the same request out to
OpenAI and Gemini and return both terminal reports.
`DeepResearchClient.submit_project_and_save_reports()` wraps that flow and
persists each provider’s report to `output/reports/deep_research/` as Markdown,
JSON, and a plain-text log, plus an index file.

## Providers

| Provider | API surface | Best fit |
| --- | --- | --- |
| `openai` | Responses API with `o3-deep-research` / `o4-mini-deep-research` | Private MCP/vector-store research, analyst-grade synthesis, explicit `max_tool_calls` budgeting |
| `gemini` | Interactions API with `deep-research-preview-04-2026` / `deep-research-max-preview-04-2026` | Collaborative planning, visualization-heavy runs, long-horizon web synthesis |

## Install

The vendor SDKs are optional and live in the `deep-research` dependency group:

```bash
uv sync --group deep-research   # installs openai + google-genai
```

Without the group, `infrastructure.search` stays importable (adapters are
lazy); actual submission raises a clear "SDK not installed" error.

## Environment

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | Enables the OpenAI provider |
| `OPENAI_DEEP_RESEARCH_MODEL` | Optional model override |
| `GEMINI_API_KEY` | Enables the Gemini provider |
| `GEMINI_DEEP_RESEARCH_AGENT` | Optional agent override |

## CLI

Symmetric with the `literature` and `exa` subpackages:

```bash
uv run python -m infrastructure.search.deep_research providers
uv run python -m infrastructure.search.deep_research submit "survey of X" --provider openai
uv run python -m infrastructure.search.deep_research poll openai resp_abc123
uv run python -m infrastructure.search.deep_research run-project \
    projects/templates/template_active_inference \
    "Review this manuscript; suggest fixes and new citations." --providers openai
```

## Cost model (measured live, 2026-06-10)

One full manuscript review (template_active_inference exemplar, ~277 KB packaged
context, web search enabled) — exact `usage` objects retrieved from both APIs:

| Provider | Input tokens | Output (+thought) | Tool-use tokens | Measured cost |
| --- | --- | --- | --- | --- |
| OpenAI `o3-deep-research` (`max_tool_calls=12`) | 96,479 | 19,215 (8,896 reasoning) | ≤12 searches | **≈ $2** |
| Gemini `deep-research-preview-04-2026` | 6,520,393 (700k cached) | 75,514 + 229,057 thought | 2,474,446 | **≈ $20–35** |

Rules of thumb:

- **Budget ≈ $2 per project per OpenAI report; ≈ $25 per Gemini report.**
  A both-providers run on one project ≈ $25–40. Looping the 9 public
  exemplars ≈ $20 (OpenAI-only) vs ≈ $250–350 (both providers).
- Gemini's agentic loop re-reads context every step (9.3M total tokens for one
  job) — it is ~10× OpenAI's cost for comparable output. Default to
  `providers=("openai",)` for routine reviews; add Gemini when you want a
  second independent report.
- `max_tool_calls` (OpenAI) is the main cost knob; `max_total_chars` on
  `collect_project_context()` bounds the input side.
- **`background=True` jobs bill to completion even if never polled.** Cancel
  diagnostic submissions; do not fire-and-forget probes. Cancel a job with
  `DeepResearchClient.cancel(handle)` or the CLI `cancel <provider> <job_id>`
  subcommand (wraps OpenAI `responses.cancel` / Gemini `interactions.cancel`).
- Gemini deep-research jobs run **30–60+ minutes**. `wait`/`wait_many` poll
  forever by default; pass `max_wait_seconds` (also `run-project --max-wait`)
  to bound the budget — set it **well above 30 minutes** or you will time out a
  job that is fine. On expiry these raise `DeepResearchWaitTimeout` carrying the
  still-pending handles (`.pending`) so the paid jobs can be re-polled or
  cancelled rather than lost.

### Looping over all projects (recipe — costs real money, run deliberately)

```python
# ≈ $2/project (OpenAI-only). Add "gemini" to providers for ≈ $25-40/project.
from pathlib import Path
from infrastructure.project.discovery import discover_projects
from infrastructure.search.deep_research import DeepResearchClient

client = DeepResearchClient.from_env()
for project in discover_projects(Path(".")):
    client.submit_project_and_save_reports(
        project.path,
        "Review this manuscript: weaknesses, concrete fixes, and NEW citations "
        "(title/authors/venue/year/DOI) not already in its references.",
        providers=("openai",),
    )  # reports land in <project>/output/reports/deep_research/
```

## Reliability notes (live-verified 2026-06-10)

- Submissions retry transient connection/timeout errors with exponential
  backoff (see `retry.py`); non-transient errors propagate immediately.
- Large packaged contexts (~300 KB) submit successfully but showed a higher
  transient-failure rate on the Gemini Interactions API; the retry absorbs
  this. Tune `collect_project_context(max_total_chars=...)` to shrink payloads.
- Gemini's Interactions API is marked experimental by the SDK and emits a
  `UserWarning` on use.

## Example

```python
from infrastructure.search.deep_research import DeepResearchClient, DeepResearchRequest

client = DeepResearchClient.from_env()
handle = client.submit(
    DeepResearchRequest(
        query="Assess the market landscape for privacy-preserving inference in healthcare.",
        provider="auto",
    )
)
result = client.poll(handle)
print(result.output_text)
```

## Project context

```python
from infrastructure.search.deep_research import (
    DeepResearchClient,
    build_project_deep_research_request,
)

client = DeepResearchClient.from_env()
request = build_project_deep_research_request(
    "projects/templates/template_code_project",
    "Summarize the project outputs and identify the highest-risk gaps.",
)
results = client.submit_and_wait_many(request)
for provider, result in results.items():
    print(provider, result.status)
    print(result.output_text)
```

## See also

- [`AGENTS.md`](AGENTS.md)
- [`../AGENTS.md`](../AGENTS.md)
