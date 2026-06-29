# Workflow Composition Map

> How an agent assembles a **custom** research workflow from composable stages — instead of running the monolithic `./run.sh --pipeline`.

The default pipeline (see [`../core/workflow.md`](../core/workflow.md) and [`../RUN_GUIDE.md`](../RUN_GUIDE.md)) presents one fixed sequence. In practice the research lifecycle is a chain of **composable stages**, each realized by a concrete CLI seam. An agent selects the subset of stages a task actually needs and invokes those seams directly.

```
discover → fetch → synthesize → write → verify → review → validate → publish
```

## The composable stages and their CLI seams

Each stage below names a real entry point. The `scripts/0N_*.py` orchestrators, the `python -m infrastructure.orchestration` subcommands, the `run_matrix.py` stage tokens, and the `docs/prompts/<skill>/SKILL.md` workflow skills are all verified against live discovery.

| Stage | What it does | Concrete CLI seam(s) | Workflow skill |
| --- | --- | --- | --- |
| **discover** | Find the question, scope, and sources | research skill (no single script) | [`deep-research/SKILL.md`](deep-research/SKILL.md) |
| **fetch** | Retrieve corpus / run analysis to produce figures + data | [`../../scripts/02_run_analysis.py`](../../scripts/02_run_analysis.py); `run_matrix.py` stage `analysis` | [`literature-synthesis/SKILL.md`](literature-synthesis/SKILL.md) |
| **synthesize** | Turn corpus into thematic synthesis / methods | (logic in `infrastructure/methods/`, `infrastructure/search/`) | [`methods-orchestration/SKILL.md`](methods-orchestration/SKILL.md), [`literature-synthesis/SKILL.md`](literature-synthesis/SKILL.md) |
| **write** | Draft / outline / revise the manuscript | scaffold via [`../guides/new-project-one-shot-prompt.md`](../guides/new-project-one-shot-prompt.md); render [`../../scripts/03_render_pdf.py`](../../scripts/03_render_pdf.py); `run_matrix.py` stage `render_pdf` | [`academic-paper/SKILL.md`](academic-paper/SKILL.md), [`manuscript-creation/SKILL.md`](manuscript-creation/SKILL.md) |
| **verify** | Triple-check every claim and citation against evidence | `uv run python -m infrastructure.reference.verification verify <bib>`; `uv run python -m infrastructure.validation.cli markdown <manuscript>` | [`manuscript-claim-verification/SKILL.md`](manuscript-claim-verification/SKILL.md), [`manuscript-cross-references/SKILL.md`](manuscript-cross-references/SKILL.md) |
| **review** | Peer / methodology review of the draft | [`../../scripts/06_llm_review.py`](../../scripts/06_llm_review.py) `--reviews-only`; `run_matrix.py` stage `llm_reviews` | [`academic-paper-reviewer/SKILL.md`](academic-paper-reviewer/SKILL.md) |
| **validate** | Quality gates on PDFs and outputs | [`../../scripts/04_validate_output.py`](../../scripts/04_validate_output.py); `uv run python -m infrastructure.validation.cli pdf <pdf>`; `run_matrix.py` stage `validate` | [`validation-quality/SKILL.md`](validation-quality/SKILL.md) |
| **publish** | Copy deliverables, bundle, archive, mint DOI | [`../../scripts/05_copy_outputs.py`](../../scripts/05_copy_outputs.py) (`copy`), [`../../scripts/08_executable_bundle.py`](../../scripts/08_executable_bundle.py), [`../../scripts/09_archive_publication.py`](../../scripts/09_archive_publication.py); `python -m infrastructure.orchestration secure` | [`reproducibility-audit/SKILL.md`](reproducibility-audit/SKILL.md) |

## Whole-pipeline seams (for reference)

When you *do* want the whole chain, the orchestrator wraps it:

- **Single project:** `uv run python scripts/execute_pipeline.py --project {name}` (or `python -m infrastructure.orchestration pipeline --project {name}`); `--core-only` drops the two LLM stages.
- **Reproducible subset matrix:** `uv run python scripts/run_matrix.py` reads `run.config` and pins exactly which stages run for exactly which projects. Valid stage tokens: `setup, infra_tests, project_tests, tests, analysis, render_pdf, validate, copy, llm_reviews, llm_translations, executive_report`. See [`../../run.config.example.yaml`](../../run.config.example.yaml).
- **Multi-project / secure:** `python -m infrastructure.orchestration multi` and `python -m infrastructure.orchestration secure`.

## Composing a custom workflow

**An agent composes a CUSTOM workflow by selecting a subset of stages — it does not have to run the whole `--pipeline`.** Pick only the stages the task needs:

- *"Just re-verify the claims and re-validate"* → run `verify` + `validate` only. With `run_matrix.py`: `stages: [render_pdf, validate]` (render first if the PDF is stale). No `analysis`, no `llm_reviews`.
- *"Draft from a brief, then render"* → `write` via [`manuscript-creation/SKILL.md`](manuscript-creation/SKILL.md), then `render_pdf`. Skip `review`.
- *"Full research-to-publication"* → walk the whole chain via [`academic-pipeline/SKILL.md`](academic-pipeline/SKILL.md), which sequences the academic skills end to end.

Stage handoffs between workflow skills are declared in [`MODE_REGISTRY.md`](MODE_REGISTRY.md) — consult it to find the next skill in a chain.

## THE TWO-TREE ROUTING RULE (restated)

- To **EDIT/extend an infrastructure module** (change the machinery) → use that module's `infrastructure/<module>/SKILL.md`.
- To **RUN a research workflow** (operate the machinery) → use `docs/prompts/<skill>/SKILL.md`.

Discover the full set of both trees in [`../_generated/skills_index.md`](../_generated/skills_index.md); the agent-invocable CLI operations are cataloged in [`../../.cursor/operations_manifest.json`](../../.cursor/operations_manifest.json).
