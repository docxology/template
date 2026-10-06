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
| [`rendering_pipeline.md`](rendering_pipeline.md) | Explicit core allowlist, opt-in deep composition, hydrated bibliography/S02 dependencies, rendering |
| [`style_guide.md`](style_guide.md) | 7 rules: zero-mock, infrastructure delegation, thin orchestrator, show-not-tell, explicit paths, dataclass standards, error messages |
| [`syntax_guide.md`](syntax_guide.md) | Pandoc-crossref labels, `{{TOKEN}}` registry from `src/template_search_project/publish/manuscript_variables.py`, curated/generated citation rule |
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

**Declared layer boundary.** `manuscript/layer_contract.yaml` admits exact generic platform adapters, including mature confined I/O and source custody. Domain algorithms remain project-owned; synthesis accepts a real callable. Controlled functions exercise behavior without establishing actual model acceptance.

**Zero-mock enforcement.** No `unittest.mock`, `MagicMock`, `@patch`, or `create_autospec` anywhere in `tests/`. The LLM is tested by passing a Python function — never a mock — to `synthesise_per_paper` / `synthesise_corpus`.

**Show-not-tell.** Manuscript prose must reference concrete file paths and APIs. A reader of `02_methodology.md` should be able to open `src/template_search_project/pipeline/pipeline.py` and find the named function within seconds.

**Curated and generated bibliographies.** Authored `manuscript/*.bib` remains unchanged. Producers write `output/bibliography/*.bib`; hydration retains curated definitions, rejects meaningful conflicts, and projects additional keys into `output/manuscript/generated_search.bib`. Renderers consume the hydrated union.

**Explicit execution order.** Core analysis runs search, figures, hydration, review report, and dashboard through the five-script allowlist. Deep search and composition require direct opt-in execution. Composition binds the actual producer receipt/input bytes/S02 SHA; hydration refuses stale or manual substitutions.

## Verification Commands

Run the complete project suite separately with its declared 90 percent branch
coverage floor, followed by public Ruff/type, no-mocks, layer-contract, and
relevant domain controls. The optional project review CLI is `scripts/review
--list`. See [`testing_philosophy.md`](testing_philosophy.md) for actual commands
and evidence boundaries. Earlier count or coverage snapshots are historical.

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
- [`../src/AGENTS.md`](../src/template_search_project/AGENTS.md) — `src/` module-level guide.
- [`../../../AGENTS.md`](../../../AGENTS.md) — root template documentation.
