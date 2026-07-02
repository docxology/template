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

Live test count and coverage are tracked in [`docs/_generated/COUNTS.md`](../../../../docs/_generated/COUNTS.md); the suite runs well above the 90% gate (set by the project `pyproject.toml` and re-enforced at the root pipeline).

Before modifying any file in `src/`, count the tests that exercise it. After modifying, run:

```bash
uv run pytest projects/templates/template_search_project/tests/ \
    --cov=projects/templates/template_search_project/src \
    --cov-fail-under=90 \
    --cov-report=term-missing \
    -q
```

The current margin leaves buffer before the gate; do not consume it gratuitously, and do not delete tests to make a number work — fix the gap.

---

## Rule 3: The Thin-Orchestrator Boundary

Unlike `template_code_project` (whose `src/` is `infrastructure`-free), this project's `src/` **does** import from infrastructure. The boundary is narrower and more specific:

| Module | May touch `infrastructure.search.*` | May touch `infrastructure.reference.citation.*` | May touch `infrastructure.llm.*` |
|---|---|---|---|
| `src/pipeline.py` | yes | yes | no |
| `src/deep_search.py` | yes | yes | no |
| `src/synthesis.py` | no | no | no — receives a duck-typed `llm: Callable[[str], str]` |
| `src/llm_runtime.py` | no | no | yes (builds the runtime adapter) |
| `src/figures.py`, `src/report.py`, `src/manuscript_variables.py`, `src/analysis.py`, `src/search_invariants.py` | no | no | no |

**`src/pipeline.py` and `src/deep_search.py` are the only modules that touch `infrastructure.search.*`.** Every downstream module receives data through dataclass parameters or reads it from disk. This keeps the rest of the project testable without `pytest-httpserver` or a network connection.

**`src/synthesis.py` does not depend on Ollama.** Its public functions (`synthesise_per_paper`, `synthesise_corpus`) accept a callable of shape `(str) -> str`. Tests pass a deterministic local function. Runtime callers build a real adapter via `src/llm_runtime.py::build_llm_callable`.

---

## Rule 4: "Show, Not Tell" Documentation

When updating `manuscript/` or any docs, refer to concrete file paths and concrete API surfaces, not vague descriptions.

**BAD** (vague, unverifiable):
```markdown
Our pipeline uses standard literature-search APIs and produces a citation list.
```

**GOOD** (concrete, linkable):
```markdown
`src/pipeline.py::run_literature_pipeline` calls
`infrastructure.search.literature.LiteratureClient.search` against the backends
listed in `config.search.sources`, then writes BibTeX entries via
`infrastructure.reference.citation.paper_to_bibentry` to
`projects/templates/template_search_project/manuscript/references.bib`.
```

**BAD**:
```markdown
The deep-search stage runs the LLM on every paper.
```

**GOOD**:
```markdown
`src/deep_search.py::run_deep_search` invokes the callable returned by
`src/llm_runtime.py::build_llm_callable` for each paper that survives
enrichment, writing per-paper notes to
`output/deep_search/<keyword_slug>/per_paper/<safe_id>.md`.
```

---

## Rule 5: Determinism Policy

This project is offline- and reproducibility-first. Four caches and one seeded LLM combine to produce byte-stable runs:

1. `infrastructure.search.literature.SearchCache` — keyed on canonical query identity; re-runs are cache hits.
2. `infrastructure.search.literature.AbstractFetcher` — per-paper `<safe_id>.txt` under `output/cache/abs/`.
3. `infrastructure.search.literature.FulltextFetcher` — per-paper `<safe_id>.{pdf,txt}` under `output/cache/pdf/`.
4. BibTeX writer (`paper_to_bibentry` + `_disambiguate_citation_key`) — deterministic citation keys with alphabetical disambiguation.
5. LLM — `seed=42`, `temperature=0.0`, model pinned via `config.llm.model` (default `gemma3:4b`).

CI-safe defaults in `manuscript/config.yaml`:

```yaml
search:
  sources: [local]      # data/corpus.json — no network
llm:
  enabled: false        # no Ollama dependency
deep_search:
  enabled: false        # opt-in
```

Tests assume these defaults. When changing them, also update `tests/test_readme_config_consistency.py`.

---

## Rule 6: Style and Syntax Guides Govern Their Domains

- [`style_guide.md`](style_guide.md) governs `src/*.py`, `tests/test_*.py`, `scripts/*.py` — mock prohibition, infrastructure-delegation table, dataclass standards, error-message format.
- [`syntax_guide.md`](syntax_guide.md) governs `manuscript/*.md` — Pandoc-crossref labels, the live `{{TOKEN}}` registry from `src/manuscript_variables.py`, the two-bib citation rule, and the figure label registry.

Do not apply code-style rules to manuscript prose, and do not apply manuscript syntax rules to Python source.

---

## Rule 7: `output/` Is Disposable — Never Edit Generated Files

The entire `projects/templates/template_search_project/output/` tree (and the auto-populated files `manuscript/references.bib`, `manuscript/references_deep.bib`, `manuscript/S01_literature_review.md`) is rewritten on every run. Editing those files has zero lasting effect.

If you need to change what a generated file contains, change the **generator**:

- To change `manuscript/references.bib` → modify `src/pipeline.py` or the inputs in `data/corpus.json` / `manuscript/config.yaml`.
- To change `manuscript/references_deep.bib` → modify `src/deep_search.py` or `config.deep_search.keywords`.
- To change `manuscript/S01_literature_review.md` → modify `scripts/s_compose_literature_review.py`.
- To change `output/figures/*.png` → modify `src/figures.py` and the matching call in `scripts/y_generate_search_figures.py`.
- To change resolved tokens in `output/manuscript/*.md` → modify `src/manuscript_variables.py` (token definitions) or `manuscript/*.md` (templates).

See [`output_conventions.md`](output_conventions.md) for the complete producer / consumer mapping.

---

## Verification Checklist

Run all four commands before submitting any change to this project:

```bash
# 1. Tests pass and coverage gate is met
uv run pytest projects/templates/template_search_project/tests/ \
    --cov=projects/templates/template_search_project/src \
    --cov-fail-under=90 -q

# 2. No mocks anywhere in tests/
grep -rE "unittest\.mock|MagicMock|@patch|create_autospec" \
    projects/templates/template_search_project/tests/ || echo "Clean — no mocks found"

# 3. src/ touches only the permitted infrastructure modules
#    (search, reference.citation, llm — never .scientific / .reporting / .rendering)
grep -rE "from infrastructure\.(scientific|reporting|rendering)" \
    projects/templates/template_search_project/src/ || echo "Clean — src/ stays in its lane"

# 4. The configurable review CLI is wired
cd projects/templates/template_search_project && uv run python scripts/review --list
```

Checks 2 and 3 must produce the "Clean" message. Check 4 must list the nine review stages without raising.
