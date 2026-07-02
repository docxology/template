# template_search_project/docs — Agent guide

## Purpose

Project-local agent-facing documentation. This is the operational rulebook for AI agents and contributors working inside the literature-discovery exemplar. Repo-wide literature references live under [`docs/modules/`](../../../../docs/modules/) and [`docs/guides/`](../../../../docs/guides/); manuscript-syntax canon lives at [`docs/guides/manuscript-semantics.md`](../../../../docs/guides/manuscript-semantics.md).

## File Inventory

| File | Purpose |
|---|---|
| [`README.md`](README.md) | Quick navigation by audience |
| [`AGENTS.md`](AGENTS.md) | This index |
| [`agent_instructions.md`](agent_instructions.md) | Behavioural constraints for AI agents (read-first priority) — 7 rules + verification checklist |
| [`architecture.md`](architecture.md) | Two-layer compliance, module-responsibilities table, idempotency contract |
| [`testing_philosophy.md`](testing_philosophy.md) | Zero-mock + LLM-as-callable; live counts in [`docs/_generated/COUNTS.md`](../../../../docs/_generated/COUNTS.md) |
| [`rendering_pipeline.md`](rendering_pipeline.md) | Five-phase flow (search → compose → figures+vars → PDF → review); `config.yaml` controls; troubleshooting |
| [`style_guide.md`](style_guide.md) | 7 rules: zero-mock, infrastructure delegation, thin orchestrator, show-not-tell, explicit paths, dataclass standards, error messages |
| [`syntax_guide.md`](syntax_guide.md) | Pandoc-crossref labels, `{{TOKEN}}` registry from `src/manuscript_variables.py`, two-bibliography citation rule |
| [`faq.md`](faq.md) | Architecture, testing, search, LLM, manuscript, common-pitfall answers |
| [`quickstart.md`](quickstart.md) | Six-step first-run walkthrough |
| [`output_conventions.md`](output_conventions.md) | Producer / consumer mapping for every artifact |
| [`troubleshooting.md`](troubleshooting.md) | Symptom-driven diagnostic recipes (with mermaid flowchart) |

## Reading Order

This sequence is intentional. Each document provides context the next assumes:

1. [`agent_instructions.md`](agent_instructions.md) — start here; 7 hard rules and the verification checklist.
2. [`architecture.md`](architecture.md) — layer boundaries before touching any file.
3. [`testing_philosophy.md`](testing_philosophy.md) — zero-mock policy and the LLM-as-callable corollary before writing or modifying any test.
4. [`rendering_pipeline.md`](rendering_pipeline.md) — the five-phase flow before editing manuscript or output paths.
5. [`style_guide.md`](style_guide.md) — coding style before editing `src/`, `tests/`, or `scripts/`.
6. [`syntax_guide.md`](syntax_guide.md) — `{{TOKEN}}` registry and figure-label registry before editing any manuscript `.md` file.
7. [`faq.md`](faq.md) — design rationale and pitfall answers when in doubt.

## Key Conventions

**Read-first protocol.** Skipping `agent_instructions.md` is the most common source of errors: agents who skip it tend to introduce mocks (violating Rule 1 of `style_guide.md`), import `infrastructure.rendering` or `infrastructure.scientific` from `src/` (violating Rule 3 of `agent_instructions.md`), or hardcode numbers in manuscript prose (violating Rule 4 of `style_guide.md`).

**Architecture isolation.** `src/pipeline.py` and `src/deep_search.py` are the only modules that touch `infrastructure.search.*`. `src/synthesis.py` takes a duck-typed `llm: Callable[[str], str]` argument so tests pass deterministic local functions and runtime callers pass the adapter from `src/llm_runtime.py`. Every other `src/` module is pure.

**Zero-mock enforcement.** No `unittest.mock`, `MagicMock`, `@patch`, or `create_autospec` anywhere in `tests/`. The LLM is tested by passing a Python function — never a mock — to `synthesise_per_paper` / `synthesise_corpus`.

**Show-not-tell.** Manuscript prose must reference concrete file paths and APIs. A reader of `02_methodology.md` should be able to open `src/pipeline.py` and find the named function within seconds.

**Two bibliographies.** `manuscript/references.bib` (single-query) and `manuscript/references_deep.bib` (deep-search) coexist; Pandoc `--natbib` merges every `manuscript/*.bib` at render time.

**Alphabetical script order.** `run_*` < `s_*` < `y_*` < `z_*` < `zz_*` is enforced by `tests/test_script_order.py`. The composer must run before the resolver.

## Verification Commands

Run all four before submitting any change:

```bash
# 1. Tests pass and coverage gate is met
uv run pytest projects/templates/template_search_project/tests/ \
    --cov=projects/templates/template_search_project/src \
    --cov-fail-under=90 -q

# 2. No mocks anywhere in tests/
grep -rE "unittest\.mock|MagicMock|@patch|create_autospec" \
    projects/templates/template_search_project/tests/ || echo "Clean"

# 3. src/ stays in its lane (no rendering/reporting/scientific imports)
grep -rE "from infrastructure\.(rendering|reporting|scientific)" \
    projects/templates/template_search_project/src/ || echo "Clean"

# 4. The configurable review CLI lists the nine stages
cd projects/templates/template_search_project && uv run python scripts/review --list
```

## Contracts

- Prefer linking to [`../manuscript/config.yaml`](../manuscript/config.yaml) as the single configuration reference.
- Paths in docs assume execution from the repository root (`template/`) unless stated otherwise.
- Cross-references inside this directory use relative links.

## Cross-References

- [`README.md`](README.md) — audience-targeted entry points.
- [`../AGENTS.md`](../AGENTS.md) — project-level overview.
- [`../pyproject.toml`](../pyproject.toml) — coverage-gate settings (`fail_under = 90`, `branch = true`).
- [`../tests/conftest.py`](../tests/conftest.py) — `sys.path` setup and `MPLBACKEND=Agg`.
- [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md) — manuscript-directory protocol.
- [`../manuscript/SYNTAX.md`](../manuscript/SYNTAX.md) — project-local Pandoc syntax overlay.
- [`../src/AGENTS.md`](../src/AGENTS.md) — `src/` module-level guide.
- [`../../../AGENTS.md`](../../../AGENTS.md) — root template documentation.
