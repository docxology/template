# Documentation mega-file decomposition policy

Human-authored guides above **800 lines** are tracked as **P1 watch** items in
[`infrastructure/AGENTS.md`](../../infrastructure/AGENTS.md). They are not CI
failures; decomposition is done when a guide's edit churn or navigation cost
justifies the split.

## When to split

Split a mega guide when **any** of the following hold:

1. Two or more distinct audiences (operator vs author vs API consumer) share one file.
2. More than three unrelated TOC sections are edited in the same release cycle.
3. Cross-link density inside the file exceeds ~40 internal anchors (grep `](#` count).
4. A new leaf would drop the parent below **650 lines** without losing narrative flow.

Do **not** split generated inventories (`docs/_generated/*`, `api-reference.md`);
those are refreshed by scripts and are exempt.

## Current P1 watch list (2026-06-11)

| Path | Lines | Suggested leaf topics |
| --- | ---: | --- |
| [`docs/reference/api-reference.md`](../reference/api-reference.md) | 3245 | Generated — no split; refresh via `scripts/docgen/api_reference.py` |
| [`docs/rules/manuscript_style.md`](../rules/manuscript_style.md) | 1145 | LaTeX math · citations · figures · accessibility |
| [`docs/guides/figures-and-analysis.md`](../guides/figures-and-analysis.md) | 860 | Registry figures · analysis scripts · manifest hooks |
| [`docs/rules/llm_standards.md`](../rules/llm_standards.md) | 800 | Prompt hygiene · Ollama workflow · review templates |
| [`docs/reference/common-workflows.md`](../reference/common-workflows.md) | 813 | Pipeline · validation · publishing |

## Leaf naming

- Place operational splits under `docs/operational/<topic>/`.
- Place author-facing splits under `docs/guides/<topic>-*.md`.
- Keep the parent as a **hub** with a short intro + links; do not duplicate prose.

## Verification

After splitting:

1. Run `uv run python scripts/audit/lint_docs.py`.
2. Update hub links in [`docs/documentation-index.md`](../documentation-index.md).
3. Refresh measured counts: `uv run python scripts/docgen/counts.py --write`.
