# AI Agent Instructions — search_project Exemplar

## Why This File Exists

`template_search_project` is the **literature-discovery exemplar** for the template repository: the canonical demonstration that the `infrastructure.search`, `infrastructure.reference.citation`, and `infrastructure.llm` modules compose into a runnable, fully-tested, offline-by-default pipeline. The value of this project is that its `src/` is a **thin orchestration layer** over those infrastructure modules — adding mocks, hardcoding numbers in prose, or breaking the script-order convention dilutes the exemplar.

Read this file before touching any other file in this project.

---

## Rule 1: Read the Hub First

Reading order is mandatory, not advisory. Each document gates a category of action:

| Document | Governs | Skip consequence |
|---|---|---|
| **This file** | All modifications | Risk all violations below |
| [`architecture.md`](architecture.md) | Any file-boundary change | Risk violating the `src/`/`infrastructure/` orchestration boundary |
| [`testing_philosophy.md`](testing_philosophy.md) | Any test modification | Risk introducing mocks or LLM dependencies in tests |
| [`rendering_pipeline.md`](rendering_pipeline.md) | Any manuscript or output change | Risk unresolved `{{TOKEN}}` markers or stale BibTeX in the PDF |
| [`style_guide.md`](style_guide.md) | Any source code modification | Risk wrong import layer, missing dataclass discipline, vague error messages |
| [`syntax_guide.md`](syntax_guide.md) | Any manuscript `.md` modification | Risk hardcoded numbers, broken figure references, missing two-bib citations |
| [`faq.md`](faq.md) | Cross-cutting questions | Risk re-asking answered design questions |

For navigation, [`README.md`](README.md) lists every doc by audience.

---

## Rule 2: Coverage Gate — 90% Floor on `src/`

Live test count and coverage are tracked in [`docs/_generated/COUNTS.md`](../../../../docs/_generated/COUNTS.md); the declared floor is 90 percent branch coverage of the complete own-source surface. Earlier snapshots do not establish a current pass.

Before modifying any file in `src/`, count the tests that exercise it. After modifying, run:

```bash
uv run pytest projects/templates/template_search_project/tests/ \
    --cov=projects/templates/template_search_project/src \
    --cov-fail-under=90 \
    --cov-report=term-missing \
    -q
```

Report the actual executed selection and measured coverage. Do not omit source or delete tests to satisfy the floor.

---

## Rule 3: The Declared Layer Boundary

[`../manuscript/layer_contract.yaml`](../manuscript/layer_contract.yaml) names
exact project adapters permitted to import generic platform APIs. Search
orchestration delegates retrieval and enrichment to `infrastructure.search`;
publication adapters use mature confined I/O, bibliography, and source-custody
contracts. Domain algorithms remain in project `src/`; scripts invoke them.
Do not maintain a contradictory second adapter allowlist in prose.

`template_search_project.pipeline.synthesis` accepts a real
`Callable[[str], str]`. A controlled callable tests synthesis behavior. Actual
model acceptance separately binds transport, model identity, source/environment,
consumed input, response, and finite budget evidence.

## Rule 4: "Show, Not Tell" Documentation

When updating `manuscript/` or any docs, refer to concrete file paths and concrete API surfaces, not vague descriptions.

**BAD** (vague, unverifiable):
```markdown
Our pipeline uses standard literature-search APIs and produces a citation list.
```

**GOOD** (concrete, linkable):
```markdown
`src/template_search_project/pipeline/pipeline.py::run_literature_pipeline` calls
`infrastructure.search.literature.LiteratureClient.search` against the backends
listed in `project_config.search.sources`, then writes BibTeX entries via
`infrastructure.reference.citation.paper_to_bibentry` to
`projects/templates/template_search_project/output/bibliography/references.bib`.
```

**BAD**:
```markdown
The deep-search stage runs the LLM on every paper.
```

**GOOD**:
```markdown
`src/template_search_project/search/deep_search.py::run_deep_search` invokes the callable returned by
`src/template_search_project/pipeline/llm_runtime.py::build_llm_callable` for each paper that survives
enrichment, writing per-paper notes to
`output/deep_search/<keyword_slug>/per_paper/<safe_id>.md`.
```

---

## Rule 5: Core Defaults and Evidence

Current `project_config` defaults are local search, abstract/fulltext enrichment
disabled, `llm.enabled: false`, and `deep_search.enabled: false`. The core
`analysis.scripts` allowlist is, in order:

1. `run_search_pipeline.py`
2. `y_generate_search_figures.py`
3. `z_generate_manuscript_variables.py`
4. `zz_generate_review_report.py`
5. `zzz_build_dashboard.py`

Deep search and composition require explicit direct invocation. A disk-source
producer record binds current configuration and consumed artifact bytes; it does
not establish loaded-code custody or successful live-provider acceptance.
Composition additionally binds the producer receipt, inputs, and S02 SHA, and
hydration refuses stale/manual dependencies.

Local corpus/citation outputs can be compared for exact bytes with fixed inputs.
Cache acquisition timestamps and actual provider/model receipts describe real
operations. A model seed and temperature are configuration controls, not a
promise of identical model responses. Canonical candidate jobs use the nominated
candidate's measured `SOURCE_DATE_EPOCH` and retain its provenance.

## Rule 6: Style and Syntax Guides Govern Their Domains

- [`style_guide.md`](style_guide.md) governs `src/*.py`, `tests/test_*.py`, `scripts/*.py` — mock prohibition, infrastructure-delegation table, dataclass standards, error-message format.
- [`syntax_guide.md`](syntax_guide.md) governs `manuscript/*.md` — Pandoc-crossref labels, the live `{{TOKEN}}` registry from `src/template_search_project/publish/manuscript_variables.py`, the curated/generated citation rule, and the figure label registry.

Do not apply code-style rules to manuscript prose, and do not apply manuscript syntax rules to Python source.

---

## Rule 7: `output/` Is Disposable — Never Edit Generated Files

Generated outputs are regenerated from their declared producers. Authored `manuscript/*.md` and curated `manuscript/*.bib` remain source inputs; analysis preserves them. Historical published output is retained until a current producer run is explicitly admitted.

If you need to change what a generated file contains, change the **generator**:

- To change generated `output/bibliography/references.bib` → modify `src/template_search_project/pipeline/pipeline.py` or the inputs in `data/corpus.json` / `manuscript/config.yaml`.
- To change generated `output/bibliography/references_deep.bib` → modify `src/template_search_project/search/deep_search.py` or `project_config.deep_search.keywords`.
- To change generated `output/manuscript/S02_generated_literature_review.md` → modify its src composition module. Direct explicit `--output` authoring remains available.
- To change `output/figures/*.png` → modify `src/template_search_project/publish/figures.py` and the matching call in `scripts/y_generate_search_figures.py`.
- To change resolved tokens in `output/manuscript/*.md` → modify `src/template_search_project/publish/manuscript_variables.py` (token definitions) or `manuscript/*.md` (templates).

See [`output_conventions.md`](output_conventions.md) for the complete producer / consumer mapping.

---

## Verification Checklist

Run the declared project coverage gate, full public Ruff/type checks, repository
no-mocks and layer-contract checks, and relevant real domain failure controls.
Run this project separately from other `tests/` roots. Use `--cov-branch` and the
90 percent floor; report actual outcomes, not stored counts. The optional review
CLI is `scripts/review --list` from the project directory.

Controlled callable/protocol tests, actual unpaid-provider acceptance,
installed-wheel acceptance, and rendered artifact evidence remain separate.
Unsafe output/cache ancestry must refuse before external writes. Authored
manuscript and curated bibliography bytes stay unchanged.

## Optional gap-filler search (Monid)

This exemplar does **not** call Monid from `src/` — the default pipeline remains
offline and cost-free. Precedence for live agents:

1. User-configured MCP connectors and direct API keys (Paperclip, Exa, etc.).
2. Monid (`infrastructure/search/monid/`) only for gaps — `discover` → `inspect`
   → `run` with wallet pricing; requires `MONID_API_KEY`.

Compare direct-provider list prices in
[`infrastructure/search/monid/PRICING.md`](../../../../infrastructure/search/monid/PRICING.md).
Skill routing: [`infrastructure/search/monid/SKILL.md`](../../../../infrastructure/search/monid/SKILL.md).
Do not add Monid to default CI or project scripts without an explicit opt-in
budget gate.
