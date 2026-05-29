# AI Agent Instructions — prose_project Exemplar

## Why This File Exists

`template_prose_project` is the **editorial-review exemplar** of the
template repository: the canonical example proving that `infrastructure/prose/`
and `infrastructure/reference/citation/` can be wired into a project that
produces a publication-ready PDF, a JSON report, and a human-readable review
without an algorithm of its own. Deviating from the rules below — introducing
a mock, leaking analysis logic into `scripts/`, or scattering infrastructure
imports across `src/` — breaks the exemplar purpose and misleads future agents
who study this project to understand how the prose pipeline composes.

Read this file before touching any other file in this project.

---

## Rule 1: Read the Hub First

Reading order is mandatory, not advisory. Each document gates a category of action:

| Document | Governs | Skip consequence |
|---|---|---|
| **This file** | All modifications | Risk all violations below |
| [`architecture.md`](architecture.md) | Any file-boundary change | Risk violating the two-layer compliance |
| [`testing_philosophy.md`](testing_philosophy.md) | Any test modification | Risk introducing mocks or reducing coverage |
| [`rendering_pipeline.md`](rendering_pipeline.md) | Any manuscript or output change | Risk unresolved `{{TOKEN}}` in the PDF |
| [`style_guide.md`](style_guide.md) | Any source code modification | Risk wrong import layer, leaking analysis into `scripts/` |
| [`syntax_guide.md`](syntax_guide.md) | Any manuscript `.md` modification | Risk hardcoded numbers, broken `[@sec:…]` references |
| [`faq.md`](faq.md) | Edge cases and recurring questions | Risk repeating known pitfalls |

---

## Rule 2: Coverage Gate — ≥90% on `src/`

The test suite covers `tests/test_config.py`, `tests/test_figures.py`,
`tests/test_manuscript_variables.py`, `tests/test_pipeline.py`,
`tests/test_pipeline_integration.py`, `tests/test_report.py`, and
`tests/test_scripts.py`. Live test count + achieved coverage are tracked in
[`docs/_generated/canonical_facts.md`](../../../../docs/_generated/canonical_facts.md) —
do not hardcode either number in prose. The gate is **90%**
(`fail_under = 90` in the project's own `pyproject.toml` and at the root
pipeline; both gate the same number).

Before modifying any file in `src/`, count the existing tests for the function
you are changing. After modifying, run:

```bash
uv run pytest projects/template_prose_project/tests/ \
    --cov=projects/template_prose_project/src \
    --cov-fail-under=90 \
    --cov-report=term-missing \
    -v
```

Do not delete tests to make a coverage number work — fix the gap.

---

## Rule 3: The Thin-Orchestrator Boundary

The prose project does not own a scientific algorithm. Its `src/` is
**project-orchestration glue** over `infrastructure.prose` and
`infrastructure.reference.citation`. The boundary is enforced at the
sub-module level inside `src/`:

| File | May call infrastructure operations | Notes |
|---|---|---|
| `src/pipeline/` | **Yes** — the primary infra-operations entry point | Calls `analyze_manuscript`, `write_report`, `parse_bibfile` |
| `src/figures.py` | **Yes** — `infrastructure.prose.ManuscriptReport` (top-level type only) | Must not re-implement analysis — plot only over a typed report |
| `src/report.py` | **Yes** — `infrastructure.prose.{ManuscriptReport, render_outline}` (type + pure helper) | No `analyze_*`, no `parse_*`, no I/O into infrastructure |
| `src/manuscript_variables.py` | **Yes** — `load_report_payload` for raw JSON; calls `infrastructure.rendering.manuscript_injection.{substitute_manuscript_text, write_resolved_manuscript_tree}` inside `write_resolved_manuscript_tree` and the `{{TOKEN}}` substitution path | Reads JSON written by `pipeline.py`; rendering helpers are pure delegations to infrastructure |
| `scripts/y_generate_prose_figures.py` | **Yes** — `infrastructure.prose.report.load_report_json` rehydrates a typed `ManuscriptReport` before calling `src/figures.py` | No inline analysis logic |
| `src/config.py` | No | Pure YAML loading + dataclasses |
| `scripts/*.py` | No analysis logic — only CLI shim | `run_prose_pipeline.py` is a wrapper around `src.pipeline.run_prose_pipeline` |

**The boundary test**: if you find yourself writing a regex over
manuscript prose, computing readability, or parsing BibTeX inside `scripts/`
or inside `src/figures.py`, stop. That work belongs in `infrastructure/prose/`
or `infrastructure/reference/`, called from `src/pipeline/`.

---

## Rule 4: "Show, Not Tell" Documentation

When updating `manuscript/` files, use explicit, verifiable references instead
of vague descriptions.

**BAD** (vague, unverifiable):
```markdown
The pipeline analyses the manuscript using standard readability metrics.
```

**GOOD** (concrete, linkable):
```markdown
`projects/template_prose_project/src/pipeline/__init__.py::run_prose_pipeline` calls
`infrastructure.prose.analyze_manuscript` to compute Flesch-Kincaid Grade
Level, Flesch Reading Ease, and Gunning Fog from the files under
`manuscript/`, then validates citations against `manuscript/references.bib`
via `infrastructure.reference.citation.parse_bibfile`.
```

**BAD** (vague):
```markdown
The bibliography is automatically validated.
```

**GOOD** (concrete):
```markdown
`_check_bibliography` in `src/pipeline/checks.py` cross-references the
`[@key]` citations extracted by `infrastructure.prose` against the
`BibDatabase` returned by `infrastructure.reference.citation.parse_bibfile`,
emitting a `CheckResult` with `name="bibliography_consistency"` whose
`details.missing` lists unmatched keys.
```

---

## Rule 5: Determinism Policy

Every threshold and toggle lives in `manuscript/config.yaml`. There are no
random draws anywhere in `src/` or `scripts/`. Two requirements apply:

1. **Configuration is the single source of truth.** Do not hard-code a
   threshold (e.g. `if grade > 18`) anywhere; read it from
   `ProseAnalysisConfig` (`src/config.py`).
2. **Outputs are reproducible byte-for-byte for a given configuration and
   manuscript.** `output/manuscript_report.json`, `output/checks.json`,
   `output/run_summary.json`, and the figure PNGs are stable across runs
   when nothing under `manuscript/` changes.

If you need to introduce randomness for any reason, document the seed in
the call site and assert against bounds, not exact values, in tests.

---

## Rule 6: Style and Syntax Guides Govern Their Domains

- **[`style_guide.md`](style_guide.md)** governs Python source under
  `src/`, `scripts/`, `tests/` — zero-mock policy, infrastructure delegation,
  thin orchestrator, error-message format, type hints.
- **[`syntax_guide.md`](syntax_guide.md)** governs Markdown under
  `manuscript/` — `{{TOKEN}}` injection, `[@sec:…]` Pandoc-crossref section
  references, citation syntax, code-block tagging.

Do not apply code-style rules to manuscript prose, and do not apply manuscript
syntax rules to Python source.

---

## Rule 7: `output/` Is Disposable — Never Edit Generated Files

The entire `projects/template_prose_project/output/` tree is written by the
pipeline and overwritten on every run. Editing a file in `output/` has zero
lasting effect and will confuse future agents.

If you need to change what a generated file contains, change the **generator**:
- To change `output/manuscript_report.json` → modify `infrastructure.prose`
  or the wiring in `src/pipeline/`.
- To change `output/checks.json` → add or adjust a `_check_<name>` function
  in `src/pipeline/`.
- To change `output/review_report.md` → modify `src/report.py`.
- To change `output/figures/*.png` → modify `src/figures.py`.
- To change `output/manuscript/*.md` (token-substituted copies) → modify the
  template under `manuscript/` and/or `src/manuscript_variables.py`.
- To change `output/pdf/template_prose_project_combined.pdf` → modify the
  manuscript source files, then re-render.

See [`output_conventions.md`](output_conventions.md) for the complete
producer/consumer table.

---

## Verification Checklist

Run all three commands before submitting any change to this project:

```bash
# 1. Tests pass and coverage gate is met
uv run pytest projects/template_prose_project/tests/ \
    --cov=projects/template_prose_project/src \
    --cov-fail-under=90 -q

# 2. No mocks exist anywhere in tests/
grep -r "unittest.mock\|MagicMock\|@patch\|create_autospec" \
    projects/template_prose_project/tests/ || echo "Clean — no mocks found"

# 3. pipeline.py is the only module performing infrastructure operations
grep -nE "analyze_manuscript|parse_bibfile|write_report" \
    projects/template_prose_project/src/figures.py \
    projects/template_prose_project/src/report.py \
    projects/template_prose_project/src/manuscript_variables.py \
    projects/template_prose_project/src/config.py \
    || echo "Clean — only pipeline.py performs infrastructure operations"
```

All three must produce zero violations (or the "Clean" message for checks 2 and 3).
