# AGENTS.md — template_textbook

Agent-facing reference for working inside the **template_textbook** exemplar: a
modular, fillable book scaffold. Read this before editing anything. For the
human-facing overview and quick-start commands, see [`README.md`](README.md).

Decision memory and verifier hardening follow [`docs/rules/memory_and_decision_records.md`](../../../docs/rules/memory_and_decision_records.md): use nearby `WHY:` comments only for surprising local choices, keep volatile counts generated, and add negative controls for verifier-like gates.

## Invariants (do not violate)

1. **`manuscript/config.yaml` is the single source of truth.** Book structure —
   parts, chapters, labels, directories, the order of analysis scripts, front
   matter, and appendices — lives there and nowhere else. Never hand-number
   chapters, figures, equations, or sections; the TOC and numbering are derived
   from this file by `src/textbook/toc.py`.

2. **Thin orchestrators.** All business logic lives in `src/textbook/`,
   `src/visualization/`, `src/mermaid/`, or `infrastructure/`. Scripts under
   `scripts/` only import tested methods, handle I/O and visualization, and
   orchestrate. They never implement algorithms. If you find yourself writing a
   computation inside a script, move it into `src/` behind a test.

3. **The content contract.** Every chapter carries, in order: a labelled H1
   (`{#sec:<part>_<stem>}`), one figure (`{#fig:...}`) with alt text, a metadata
   badge (`<!-- chapter-metadata-badge -->`), a Study Blueprint
   (`<!-- curriculum-scaffold-start -->`), Learning Objectives, a worked
   formalism (equation `{#eq:...}` plus parameter table `{#tbl:...}`), an inline
   ```mermaid``` diagram, and Summary / Key Terms / Further Reading / Practice
   sections. Stub markers are `<!-- STUB -->`, `TODO:`, and `TKTK`.

4. **Cross-references use pandoc-crossref.** Refer with `[@fig:..]`, `[@tbl:..]`,
   `[@eq:..]`, `[@sec:..]`. The target definition (`{#fig:..}` etc.) must exist —
   a reference without its definition renders as a dangling `??`.

5. **Citations and glossary links must resolve.** Every `[@key]` must match a key
   in `manuscript/references.bib` (`smith2020foundations`, `doe2019methods`,
   `lee2021systems`, `garcia2022dynamics`, `patel2018models`,
   `nguyen2023synthesis`, `kim2020data`, `brown2017principles`,
   `wilson2021analysis`, `taylor2019theory`). Glossary links are
   `[**term**](#gl:<anchor>)` with anchors: `system`, `model`, `parameter`,
   `variable`, `equilibrium`, `feedback`, `gradient`, `threshold`, `network`,
   `dynamics`, `emergence`, `regulation`, `boundary`, `state`, `observable`.

6. **No mocks.** Tests use real data and real computation — never `MagicMock`,
   `mocker.patch`, or any mocking framework. Use real temp files, real PDFs,
   local test servers. Determinism via fixed RNG seeds.

7. **Coverage floor is 90%** for project `src/` (enforced in `pyproject.toml`).
   Exit code 0 is not proof: confirm tests collected > 0 and coverage met the
   floor.

8. **Tooling is `uv`** (never `pip`/`npm`). Markdown only for content (no raw
   HTML except `<details>`). Figures and diagrams come from the scripts, never
   hand-drawn.

## Editing checklist

Before claiming a change is done:

- [ ] Did structural intent change? If so, edit `config.yaml` first, then run
      `scripts/scaffold_chapter.py` to materialise stubs — do not create chapter
      files by hand.
- [ ] Do all `[@fig:]`/`[@tbl:]`/`[@eq:]`/`[@sec:]` references have matching
      definitions in the manuscript?
- [ ] Does every `[@key]` resolve in `references.bib`, and every
      `[**term**](#gl:anchor)` use a known anchor?
- [ ] Is the chapter still contract-complete (badge, blueprint, objectives,
      formalism, diagram, summary/terms/reading/practice)?
- [ ] New figure or diagram? Regenerate with `scripts/generate_figures.py` /
      `scripts/generate_diagrams.py` (deterministic, fixed seed).
- [ ] `uv run --extra dev python -m pytest <tests/> --cov=<src> --cov-fail-under=90`
      passes (collected > 0, ≥90%).
- [ ] `scripts/audit_textbook_quality.py` passes.

## Frozen vs. fillable

**Frozen — do not modify** (the engine and the structural contract):

- All `.py` under `src/` and `scripts/` — the content engine, models,
  visualization, Mermaid renderer, and thin orchestrators.
- `manuscript/config.yaml` — structure is changed by adding entries, but the
  schema and existing keys are stable; treat it as the contract.
- `manuscript/references.bib`, `manuscript/glossary.md` — the citation-key and
  glossary-anchor namespaces other files depend on.
- `tests/` — especially `test_manuscript_integrity.py`, which encodes the
  contract.

**Fillable — author here:**

- The prose between stub markers in the chapter files under
  `manuscript/part_*/`, the labs under `manuscript/labs/`, and the question banks
  under `manuscript/questions/`. Keep the labelled headings and cross-references;
  replace the `<!-- STUB -->` / `TODO:` / `TKTK` placeholders with real content.
- New parts/chapters: add them to `config.yaml`, then scaffold and fill.

## Key modules (for orientation)

- `src/textbook/constants.py` — `CITATION_KEYS`, `GLOSSARY_ANCHORS`,
  `REQUIRED_SECTION_HEADINGS`, `REQUIRED_TOKENS`, `STUB_MARKERS`.
- `src/textbook/content.py` — `scaffold_chapter` / `scaffold_lab` /
  `scaffold_question_bank` / `validate_chapter` / `count_stub_markers` /
  `count_words`.
- `src/textbook/config.py` — `load_config`, `iter_chapters`, `validate_config`.
- `src/textbook/toc.py` — numbering and labels.
- `src/textbook/models.py` — worked formalisms (`logistic_growth`,
  `saturating_response`, `exponential_decay`, `half_life`, `linear_fit`,
  `descriptive_statistics`, `normalize_unit_interval`).
- `src/visualization/`, `src/mermaid/` — deterministic figures and diagrams.

For monorepo-wide pipeline semantics, CI job names, and the two-layer
architecture, see the root [`AGENTS.md`](https://github.com/docxology/template/blob/main/AGENTS.md) and
[`CLAUDE.md`](https://github.com/docxology/template/blob/main/CLAUDE.md).

## Promotion to a tracked public exemplar (clean-tree follow-up)

This project is **built and standalone-green** (75 tests, ≥90% coverage, ruff +
mypy clean, audit gate green, discoverable as `templates/template_textbook`) but
is **not yet registered** in the repo's public-exemplar rosters. Registering it
touches shared `infrastructure/` files and cascades into several CI gates, so do
it only on a **clean working tree** (not mid-way through unrelated WIP). Steps:

1. **`infrastructure/project/git_guards.py`** — add
   `"projects/templates/template_textbook/"` to `ALLOWED_PROJECT_DIRS` (so the
   files may be git-tracked past the pre-push guard) and
   `"output/templates/template_textbook/"` to `ALLOWED_TRACKED_OUTPUT_PREFIXES`
   if you intend to track rendered output.
2. **`infrastructure/project/public_scope.py`** — add
   `"templates/template_textbook"` to `PUBLIC_PROJECT_NAMES` (puts it in public
   CI lint/type/coverage-union scope).
3. **Publication records** — `tests/infra_tests/documentation/test_publication_records.py`
   iterates `PUBLIC_PROJECT_NAMES`; add the matching publication-record entry (or
   adjust the generator in `infrastructure/`) so that test stays green.
4. **Doc-pair lint** — `tests/infra_tests/validation/docs/test_doc_pair_lint.py`
   expects README/AGENTS doc pairs across the project; they already exist here —
   re-run to confirm.
5. **Methods orchestration / drift** — re-run
   `tests/infra_tests/methods/test_methods_orchestration.py`,
   `tests/infra_tests/project/test_public_scope.py`, and
   `uv run python scripts/check_template_drift.py` and resolve any roster
   assertions.
6. Re-run the combined public-projects coverage gate:
   `uv run python scripts/01_run_tests.py --project-only --all-projects --public-projects`.

Until promoted, keep the project local-only (do not `git add -f`).
