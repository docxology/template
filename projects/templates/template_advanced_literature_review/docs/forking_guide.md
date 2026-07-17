# Forking & Re-targeting Guide — `template_advanced_literature_review`

> How to point this template at **your own domain and your own phase design** —
> new phases, new query sets, new temporal boundaries, new LLM filters, and new
> hypotheses — and get a complete, reproducible multi-phase literature review
> out the other end. The whole template is **config-driven**: in the common
> case you edit one YAML file and re-run. The bundled instance reviews
> exoplanet atmospheric composition across three phases; this guide shows how
> to make it yours.

## The one idea to internalize

**Every domain-specific fact in the paper is injected from
[`manuscript/config.yaml`](../manuscript/config.yaml) and the pipeline's own
outputs**, the same discipline as `template_literature_meta_analysis`. On top
of that, this template adds a second control surface: **the phase design
itself** — how many phases, what each phase searches for, what temporal
window each phase covers, and how phases validate each other — is *also*
config, not code.

## When to fork this template vs. the single-term sibling

Fork **this** template when your review question needs distinct retrieval
phases with phase-specific filters and explicit cross-phase provenance (e.g.
"foundational work" → "a technology inflection point" → "a narrow follow-on
focus", the way exoplanet atmosphere research splits into pre-JWST, JWST-era,
and molecule-specific work). Fork `template_literature_meta_analysis` instead
if a single query with one filter set covers your question — it is simpler
and has no phase-integration surface to configure.

## TL;DR

```bash
# 0. From the repo root, install deps once
uv sync --group scientific --group llm

# 1. Clean-copy the exemplar to your new project name (local-only fork)
uv run python scripts/audit/copy_exemplar.py \
  --source templates/template_advanced_literature_review \
  --dest projects/working/my_phased_review \
  --new-name my_phased_review

# 2. Edit ONE file: projects/working/my_phased_review/manuscript/config.yaml
#    → project_config.search_phases        (your phase design)
#    → project_config.llm_filters           (your content classifiers, if any)
#    → project_config.phase_integration     (dedup/validation/quality-gate policy)
#    → project_config.hypothesis_definitions (your hypotheses, tagged with relevant_phases)

# 3. Run the pipeline (from inside the project dir)
cd projects/working/my_phased_review
uv run python scripts/01_multi_phase_search.py
uv run python scripts/02_meta_analysis_pipeline.py
uv run python scripts/04_generate_figures.py --dpi 300
uv run python scripts/05_inject_variables.py     # fails loudly on any unresolved token

# 4. Render the PDF (from the repo root)
cd -
uv run python scripts/pipeline/stage_03_render.py --project working/my_phased_review
```

**Confidentiality invariant.** Your fork under `projects/working/my_phased_review/`
is local-only and won't be pushed even with `git add -f` —
`scripts/audit/check_tracked_all.py` blocks it in `pre-push-quick`. See the
root [`CLAUDE.md`](../../../../CLAUDE.md) "CONFIDENTIALITY INVARIANT" and
`STANDALONE.md` for the public-export path.

## Designing your phases: `search_phases`

Each entry under `project_config.search_phases` is one phase. Order matters —
a later phase's `depends_on` list names the earlier phases it should cross-validate.

```yaml
project_config:
  search_phases:
    phase_1_foundation:
      name: "..."
      description: "..."
      queries: ['"your broad domain query"']
      max_results_per_query: 500
      engines: { arxiv: true, openalex: true, semantic_scholar: true, crossref: true }
      deterministic_filters:
        min_year: 2010
        max_year: 2026
        min_citation_count: 0

    phase_2_inflection:
      queries: ['"your narrower, later-era query"']
      max_results_per_query: 300
      deterministic_filters: { min_year: 2020, max_year: 2026, min_citation_count: 0 }
      depends_on: ["phase_1_foundation"]   # can cross-reference phase 1 for validation

    phase_3_focus:
      queries: ['"your most specific query"']
      deterministic_filters: { min_year: 2015, max_year: 2026, min_citation_count: 0 }
      depends_on: ["phase_1_foundation", "phase_2_inflection"]
```

Any number of phases is supported; three is the bundled convention, not a
hard limit. Each phase's `queries` list is dispatched to its own `engines`
selection, then filtered by its own `deterministic_filters` — phases do not
share a filter set, which is what lets an early broad phase and a late narrow
phase coexist in one corpus.

## Content filtering: `llm_filters`

Optional, phase-scoped LLM classification of abstracts. Each filter names
which phases it applies to (`apply_to_phases`) and which returned category/
value keeps a paper:

```yaml
  llm_filters:
    my_classifier:
      name: "My Classification"
      prompt: |
        Classify this paper's abstract into ONE of these categories: ...
        Abstract: {abstract}
        Return only the category name.
      apply_to_phases: ["phase_2_inflection"]   # empty list = disabled
      keep_categories: ["observational", "theoretical"]
```

The bundled `study_type_classifier`, `jwst_data_filter`, and
`molecular_detection_filter` ship with `apply_to_phases: []` (disabled) so the
default offline run maximizes coverage; enable them per phase once you have a
local Ollama server (see `manuscript/config.yaml` → `project_config.llm_extraction`).

## Cross-phase policy: `phase_integration`

```yaml
  phase_integration:
    duplicate_resolution: "merge_metadata"   # or keep_first, keep_last
    citation_validation:
      enabled: true
      min_cross_phase_citations: 2           # later-phase papers should cite ≥N earlier-phase papers
    quality_gates:
      phase_1_foundation: { min_papers: 100, min_citation_avg: 20 }
      phase_2_inflection: { min_papers: 20, min_citation_avg: 5 }
      phase_3_focus: { min_papers: 50, min_citation_avg: 10 }
```

`quality_gates` are per-phase minimums, not a single global floor — a young,
fast-moving phase (like the bundled JWST phase) can have a lower
`min_citation_avg` than a mature foundational phase.

## Hypotheses: `hypothesis_definitions`

Same shape as the single-term sibling, plus `relevant_phases` so the
knowledge-graph stage scopes evidence scoring to the phases that actually
bear on each hypothesis:

```yaml
  hypothesis_definitions:
    H1:
      name: "..."
      description: "..."
      scope: "observational"
      relevant_phases: ["phase_1_foundation", "phase_2_inflection"]
```

## What re-targeting does and doesn't require

| You change… | You must also… | Auto-handled? |
|---|---|---|
| Phase `queries` / `engines` / `deterministic_filters` | nothing else | all phase-aware prose/figures derive from `phase_metadata.json` |
| Add/remove/rename a phase | update any `depends_on` referencing it, and `phase_integration.quality_gates` | ⚠️ partial — dependency and gate keys must match the new phase key |
| `llm_filters` | nothing (rerun stage 03 for live classification) | ✅ |
| `hypothesis_definitions` | nothing (rerun stage 03 for live scores) | ✅ `{{HYPOTHESIS_TABLE}}` adapts |
| Add a **new** computed number to the prose | add the token to `src/manuscript/variables/compute.py` or an `extractors/` module, and reference `{{NEW_TOKEN}}` | ⚠️ unresolved tokens make stage 5 fail loudly |

## Token discipline (why stage 5 fails loudly)

`05_inject_variables.py` replaces `{{TOKEN}}` in every manuscript body file. If
a body file references a token that variable computation doesn't produce,
injection raises — there are no silent `{{…}}` leaks in the rendered PDF. See
`syntax_guide.md` for the phase-aware token families.

## Verify your fork

```bash
uv run pytest projects/working/my_phased_review/tests/ \
  --cov=projects/working/my_phased_review/src --cov-fail-under=90 -q

grep -ro '{{[A-Z_0-9]*}}' projects/working/my_phased_review/output/manuscript/ ; echo "exit=$? (1 = none found = good)"

uv run python scripts/audit/check_template_drift.py
```

## Sibling exemplars

If your review is single-phase, fork
[`template_literature_meta_analysis`](../../template_literature_meta_analysis) instead.
For code-centric algorithm work, see
[`template_code_project`](../../template_code_project).

## See also

- [`quickstart.md`](quickstart.md) — 5-minute run of the bundled exoplanet-atmosphere instance
- [`architecture.md`](architecture.md) — symlinked vs. project-specific module boundaries
- [`syntax_guide.md`](syntax_guide.md) — the phase-aware `{{TOKEN}}` system
- [`output_inventory.md`](output_inventory.md) — producer/consumer graph of every artifact
- [`testing_philosophy.md`](testing_philosophy.md) — the zero-mock standard
- [`troubleshooting.md`](troubleshooting.md) — symptom-driven fixes
