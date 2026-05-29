# Forking Guide — template_prose_project

> A 5-minute walkthrough for copying this exemplar into a new
> editorial-review project. The point of the guide is to make every
> decision explicit so a forker doesn't have to read every other doc to
> find out *what's required vs aesthetic, what's enforced vs convention,
> and what they'll hit friction on*.

## TL;DR

```bash
# 0. From the repo root, install deps once
uv sync

# 1. Copy the exemplar to your new project name
cp -r projects/template_prose_project projects/my_review_project
rm -rf projects/my_review_project/src/*.egg-info
rm -rf projects/my_review_project/output

# 2. Rename the package in pyproject.toml + manuscript/config.yaml
sed -i.bak 's/template_prose_project/my_review_project/g' \
  projects/my_review_project/pyproject.toml \
  projects/my_review_project/manuscript/config.yaml
rm projects/my_review_project/pyproject.toml.bak projects/my_review_project/manuscript/config.yaml.bak

# 3. Drop in your own manuscript
rm projects/my_review_project/manuscript/0*_*.md projects/my_review_project/manuscript/99_*.md
cp -r /path/to/your/manuscript_sections/*.md projects/my_review_project/manuscript/
cp /path/to/your/references.bib projects/my_review_project/manuscript/

# 4. Run the tests against your fork
uv run pytest projects/my_review_project/tests/ \
    --cov=projects/my_review_project/src \
    --cov-fail-under=90 -q

# 5. Run the prose pipeline against your fork
uv run python projects/my_review_project/scripts/run_prose_pipeline.py
```

**⚠️ Confidentiality invariant.** The repo `.gitignore` is configured so
that **only** the public canonical exemplars listed in
[`../../../docs/_generated/active_projects.md`](../../../../docs/_generated/active_projects.md)
under `projects/` are ever git-tracked. Your fork (`projects/my_review_project/`)
is local-only and won't be pushed to the public repo even if you `git
add -f` it. Read [`../../../CLAUDE.md`](../../../../CLAUDE.md)
"CONFIDENTIALITY INVARIANT" for the full fence.

## What you're forking

This template is a **prose-review pipeline**: it has **no algorithm of
its own** — instead, `src/pipeline/` calls
`infrastructure.prose.analyze_manuscript` and
`infrastructure.reference.citation.parse_bibfile`, applies five
threshold checks (grade-level band, citation density, H1-per-file,
no-skipped-heading-levels, bibliography consistency), and emits JSON +
Markdown + three PNGs.

The transferable pattern is **self-grading**: the bundled
`manuscript/config.yaml` is deliberately permissive (FKGL band 10–18,
citation floor 0.0) so the exemplar's own abstract passes its own gate.
A forker who tightens any threshold without rewriting the methodology
section will discover that the project's own documentation fails the
gate that the documentation describes. The
[`manuscript/config.yaml.example`](../manuscript/config.yaml.example)
ships a stricter starting point (FKGL 12–16, citation floor 3.0,
`fail_on_unused=true`) for a more realistic editorial workflow.

## REQUIRED vs AESTHETIC

A pipeline-enforced gate fails CI if you delete a REQUIRED path. An
AESTHETIC path is convention only. The full inventory lives in
[`AGENTS.md`](AGENTS.md); short version:

| Class | Examples | Action |
|---|---|---|
| REQUIRED — pipeline gate | All `src/*.py`, all `tests/test_*.py`, `tests/conftest.py` (pins `MPLBACKEND=Agg`), `pyproject.toml`, `manuscript/config.yaml`, `manuscript/*.md`, `manuscript/references.bib`, `manuscript/preamble.md` | Keep them; the 90% coverage gate + LaTeX render depend on them |
| REQUIRED — orchestration | `scripts/run_prose_pipeline.py`, `scripts/y_generate_prose_figures.py`, `scripts/z_generate_manuscript_variables.py` | Subprocess-tested in `tests/test_scripts.py`; the alphabetical prefix (none / `y_` / `z_`) is an ordering hint |
| AESTHETIC | `docs/*.md`, `*/STYLE.md`, `*/PATTERNS.md`, `*/CONVENTIONS.md`, `*/AGENTS.md`, `*/README.md`, `scripts/00_preflight.py`, `manuscript/config.yaml.example` | Drift detected only by `scripts/check_template_drift.py` and audits |

## Concrete first steps after fork

### 1. Drop in your manuscript
Replace `manuscript/00_abstract.md` through `manuscript/99_references.md`
with your own sections. Section files are CommonMark Markdown with
Pandoc `[@key]` citations. `manuscript/references.bib` is
**hand-curated and read-only** — `_check_bibliography` validates that
every `[@key]` cited resolves to an entry but never writes to the bib.

### 2. Update thresholds
Every knob lives in `manuscript/config.yaml`. The defaults are
permissive so the bundled prose passes; tighten them once your real
manuscript is in:

- `prose.target_grade_level_min` / `_max` — Flesch-Kincaid Grade Level band
- `prose.long_sentence_threshold` — words-per-sentence cutoff
- `prose.citation_density_min_per_1000` — minimum citations per 1000 words
- `bibliography.fail_on_missing` / `fail_on_unused` — strictness flags

The loader rejects unknown YAML keys and enforces invariants
(`target_grade_level_min < target_grade_level_max`, etc.) with
`ValueError` listing the offending value — see
[`faq.md`](faq.md#yaml-loader-rejects-my-new-key).

### 3. Add new checks
[`AGENTS.md`](../AGENTS.md) "Extending" documents the four-step process:

1. Add a field to `ProseAnalysisConfig` in `src/config.py` (and to the
   `_KNOWN_PROSE_KEYS` registry).
2. Add a `_check_<name>` function in `src/pipeline/checks.py`.
3. Wire it into `run_prose_pipeline` so it appears in
   `artifacts.checks`.
4. Add a test in `tests/test_pipeline.py` covering both
   `passed=True` and `passed=False`.

### 4. Run the drift checker before pushing
```bash
uv run python scripts/check_template_drift.py
```
20 unit tests in
[`tests/infra_tests/test_check_template_drift.py`](../../../../tests/infra_tests/test_check_template_drift.py)
prove each detector catches the bug class it was built for.

## Common friction points (and fixes)

| Symptom | Cause | Fix |
|---|---|---|
| Tests collect 0 / coverage 0% | Per-project `.venv` lacks `pytest` (`uv venv` without `uv sync`) | The runner now hard-fails; the canonical gate is the `uv run pytest …` command above |
| `PDF Rendering` stage fails with `mmdc could not find Chrome` | `manuscript/05_pipeline_internals.md` embeds `mermaid` blocks | One-time: `npx --yes puppeteer browsers install chrome-headless-shell`; `scripts/00_preflight.py` emits an actionable warning before the PDF stage |
| Matplotlib backend error in CI | `MPLBACKEND` not set | `tests/conftest.py` pins `MPLBACKEND=Agg` at import time — keep it |
| `Unknown prose key` ValueError | Typo in `manuscript/config.yaml` (e.g., `target_grade_level_minimum`) | The strict loader rejects unknown keys; check spelling against `_KNOWN_PROSE_KEYS` in `src/config.py` |
| `{{TOKEN}}` appears literally in the rendered PDF | `scripts/z_generate_manuscript_variables.py` did not run or the token is not in `compute_variables()` | Re-run `z_generate_manuscript_variables.py`; if still literal, add to `ManuscriptVariables` |

## Sibling exemplar

[`template_code_project`](../../template_code_project) is the
numerical-research sibling — same shape, has its own gradient-descent
algorithm in `src/optimizer.py`. If your work is computational rather
than editorial, fork that one instead.

## See also

- [`AGENTS.md`](AGENTS.md) — full doc inventory and reading order
- [`agent_instructions.md`](agent_instructions.md) — 7 hard rules
- [`architecture.md`](architecture.md) — module boundaries
- [`testing_philosophy.md`](testing_philosophy.md) — zero-mock standard
- [`rendering_pipeline.md`](rendering_pipeline.md) — 4-phase pipeline
- [`faq.md`](faq.md) — recurring questions
- [`../../../scripts/check_template_drift.py`](../../../../scripts/check_template_drift.py) — the drift checker
