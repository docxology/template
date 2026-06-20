# template_prose_project

A configurable, reproducible **prose-review** pipeline built on
`infrastructure/prose/` (readability + structure + quality) and
`infrastructure/reference/` (BibTeX validation). Exemplar roster:
[`projects/AGENTS.md`](../../AGENTS.md#permanent-canonical-exemplars-and-optional-search-add-on).

## Run via the template monorepo

This exemplar lives at `projects/templates/template_prose_project/` in the public
[docxology/template](https://github.com/docxology/template) repository.
**Tests, analysis, PDF rendering, and CI all run through that monorepo** —
clone it, run `uv sync` at the repository root, then:

```bash
./run.sh --project templates/template_prose_project --pipeline --core-only
# or: uv run python scripts/execute_pipeline.py --project templates/template_prose_project --core-only
```

Several exemplars also publish standalone GitHub/Zenodo releases for citation;
those mirrors are outputs of this pipeline. The monorepo remains the canonical
build and render surface.

## When to use this template

Use this template for **manuscript-focused editorial pipelines**: readability
gates (Flesch-Kincaid bands), structural checking, citation/BibTeX
validation, and prose-quality review workflows where the document itself is
the artifact under test. If you are implementing algorithms with numerical
experiments, start from [`template_code_project`](../template_code_project/)
instead; for book-length structure see
[`template_textbook`](../template_textbook/). Full roster:
[`projects/AGENTS.md`](../../AGENTS.md#permanent-canonical-exemplars-and-optional-search-add-on).

## Why this template — the transferable pattern

The bundled `manuscript/config.yaml` is intentionally permissive (FKGL band
10–18, citation floor 0.0) so the exemplar's *own abstract passes its own
gate*. This is a self-referential pipeline: the document describing the
gate runs *through* the gate. The transferable discipline is that the
explanatory prose and the threshold settings co-evolve — a forker who
tightens `prose.target_grade_level_max` to 14.0 without rewriting the
methodology section will discover that the project's own methodology fails
the methodology check. The pedagogy is "configuration drift is detected by
the artifact itself, not by an external reviewer". A stricter starting
point lives in
[`manuscript/config.yaml.example`](manuscript/config.yaml.example).

## What it does

```mermaid
flowchart LR
    CFG[manuscript/config.yaml] --> READ[src/pipeline/ · read manuscript]
    READ --> PROSE[infrastructure.prose<br/>metrics · structure · quality]
    READ --> BIB[infrastructure.reference<br/>BibTeX validation]
    PROSE --> CHECKS[evaluate threshold checks]
    BIB --> CHECKS
    CHECKS --> JSON[manuscript_report.json<br/>checks.json]
    CHECKS --> RPT[src/report.py<br/>review_report.md]
    PROSE --> FIG[src/figures.py<br/>word counts · readability ·<br/>citation density PNGs]
    JSON --> MV[src/manuscript_variables.py<br/>variable token substitution]
    MV --> SUB[output/manuscript/*.md<br/>tokens resolved]

    classDef io fill:#0f766e,stroke:#0f172a,color:#fff
    classDef proc fill:#1e3a8a,stroke:#0f172a,color:#fff
    classDef out fill:#7c2d12,stroke:#0f172a,color:#fff
    class CFG io
    class READ,PROSE,BIB,CHECKS,MV proc
    class JSON,RPT,FIG,SUB out
```

## Quick start

```bash
# Run the full prose review (offline, no Ollama)
uv run python projects/templates/template_prose_project/scripts/run_prose_pipeline.py

# Strict mode: exit non-zero if any check fails
uv run python projects/templates/template_prose_project/scripts/run_prose_pipeline.py --strict

# Generate figures (after a pipeline run)
uv run python projects/templates/template_prose_project/scripts/y_generate_prose_figures.py

# Hydrate manuscript variables for the abstract
uv run python projects/templates/template_prose_project/scripts/z_generate_manuscript_variables.py
```

After the run, look in `output/`:

* `manuscript_report.json` — raw `ManuscriptReport`.
* `checks.json` — list of `CheckResult` (one per configured check).
* `review_report.md` — the human-readable review.
* `figures/{section_word_counts,readability_metrics,citation_density}.png`.
* `data/manuscript_variables.json` — substitution variables for the abstract.
* `run_summary.json` — one-line metadata.

## Prerequisites & verification

**Combined-PDF rendering needs headless Chrome.** This manuscript embeds
Mermaid diagrams (`manuscript/05_pipeline_internals.md`); the combined PDF is
built with `mmdc`, which requires a pinned `chrome-headless-shell`. Install
it once (CI provisions it automatically; a fresh clone does not):

```bash
npx --yes puppeteer browsers install chrome-headless-shell
```

Without it the **PDF Rendering** stage fails while per-section slides still
render — see [`docs/troubleshooting.md`](docs/troubleshooting.md#pdf-rendering-stage-fails-mmdc-could-not-find-chrome).

**Test/coverage gate (authoritative per-project command).** Exit code 0
alone is not proof; confirm tests collected > 0 and coverage ≥ 90%:

```bash
uv run pytest projects/templates/template_prose_project/tests/ \
  --cov=projects/templates/template_prose_project/src --cov-fail-under=90
# exemplar baseline → docs/_generated/COUNTS.md
```

Full end-to-end (tests → analysis → render → validate → copy):

```bash
uv run python scripts/execute_pipeline.py --project template_prose_project --core-only
```

## Configuration

Every knob lives in `manuscript/config.yaml`:

| Section | Key | Default | Meaning |
|---|---|---|---|
| `prose` | `target_grade_level_min` / `_max` | `10.0 / 18.0` | Acceptable Flesch-Kincaid Grade Level band. |
| `prose` | `long_sentence_threshold` | `35` | Words per sentence above which sentences are flagged. |
| `prose` | `citation_density_min_per_1000` | `0.0` | Minimum citations per 1000 words. |
| `prose` | `require_h1_per_section` | `true` | Every file must have an H1. |
| `prose` | `forbid_skipped_levels` | `true` | Heading levels must be contiguous. |
| `bibliography` | `references_path` | `manuscript/references.bib` | Path to BibTeX file. |
| `bibliography` | `fail_on_missing` | `true` | Fail if a cited `[@key]` is not in the bib. |
| `bibliography` | `fail_on_unused` | `false` | Fail if a bib entry is never cited. |

## Agentic research overlays

This exemplar includes two declarative overlays for advisory research controls:

- [`domain_profile.yaml`](domain_profile.yaml) declares the prose-research
  domain, review gates, citation/source policy, artifact expectations, and
  benchmark rubric weights.
- [`experiment_plan.yaml`](experiment_plan.yaml) declares the prose-validation
  conditions, primary metric direction, expected figures and tables, baseline,
  and strict-bibliography ablation.
- [`data/claim_ledger.yaml`](data/claim_ledger.yaml) registers sourced numeric
  claims that are intentionally tied to prose-review code, manuscript examples,
  or generated reports.

These files are validation and benchmark inputs only. They do not generate
experiments, mutate prompts, or run autonomous review agents.

## Architecture

* `src/config.py` — typed YAML loader.
* `src/pipeline/` — read manuscript → analyse → cross-check bibliography → evaluate checks. **Pure orchestration over `infrastructure/`.**
* `src/figures.py` — matplotlib renderers (no business logic).
* `src/manuscript_variables.py` — abstract substitution variables.
* `src/report.py` — markdown review-report assembly.
* `scripts/run_prose_pipeline.py` — thin orchestrator.
* `scripts/y_generate_prose_figures.py` — figure stage.
* `scripts/z_generate_manuscript_variables.py` — variable-hydration stage.

## Testing

```bash
uv run pytest projects/templates/template_prose_project/tests/ -v
```

All tests are offline; no mocks. The test suite uses real prose, real
BibTeX files, real `tmp_path` directories, real subprocess invocation
of the orchestrator scripts.

## See also

* [`AGENTS.md`](AGENTS.md) — agent-oriented walkthrough.
* [`manuscript/SYNTAX.md`](manuscript/SYNTAX.md) — Pandoc citation / cross-reference conventions for this project.
* [`../../docs/guides/manuscript-semantics.md`](../../../docs/guides/manuscript-semantics.md) — repository-wide canonical manuscript semantics.
* [`docs/architecture.md`](docs/architecture.md) — architectural diagram.
* [`docs/quickstart.md`](docs/quickstart.md) — getting started guide.
* [`infrastructure/prose/SKILL.md`](../../../infrastructure/prose/SKILL.md) —
  underlying prose-analysis API.

## Template integrity

- Forward backlog: [`TODO.md`](TODO.md).
- Copy-and-customize config: [`manuscript/config.yaml.example`](manuscript/config.yaml.example).
- Project validation: `uv run pytest projects/templates/template_prose_project/tests/ --cov=projects/templates/template_prose_project/src --cov-fail-under=90`.
- Repo drift validation: `uv run python scripts/check_template_drift.py --strict`.
