# template_autopoiesis — TODO

## Current Validation Evidence
- **Tests**: 493 tests passed, 1 skipped, 96.41% branch coverage (re-measured
  2026-07-06 via `uv run pytest projects/templates/template_autopoiesis/tests/
  --cov=projects/templates/template_autopoiesis/src --cov-branch --cov-fail-under=90`;
  the manuscript's own `{{TEST_COUNT}}`/`{{COVERAGE_PCT}}` tokens are
  sourced from a real per-render measurement — see `src/manuscript_variables.py::measure_test_summary` —
  not a hardcoded literal. Counts drift upward release to release as tests
  are added; treat any specific number in this file as the value at its own
  stated measurement date, not a permanent fact — re-run the command above
  for the current figure.)
- **Ruff**: clean
- **Mypy**: clean
- **Bandit**: clean
- **Markdown validator**: clean
- **PDF validator**: clean (0 issues)
- **Pre-render gate**: clean
- **Tracked projects guard**: clean
- **Public scope**: registered as `templates/template_autopoiesis`
- **Analysis pipeline**: 7/7 scripts pass (previously 6/9 with a naive glob —
  `manuscript/config.yaml` now declares an explicit `analysis.scripts`
  allowlist in dependency order; `autopoiesis.py`/`seal_child.py` are CLI/library
  helpers, not analysis steps, so they're excluded from discovery)
- **Manuscript**: expanded 2026-07-06 from ~1,100 words / 11 PDF pages / 0 embedded
  figures / 1 placeholder self-citation to ~10,900 words / 20 PDF pages / 4 embedded,
  captioned, cross-referenced figures / 5 live-verified real citations (see
  "Manuscript expansion" below)

## Integrity and template-status gaps
- [x] All canonical exemplar files present (README, AGENTS, pyproject, .gitignore, TODO, manuscript/*)
- [x] Cover image wired into the rendered PDF title page (`manuscript/config.yaml` -> `paper.cover.image`)
- [x] Cover art: QR seal (encoding `grammar_hash`), gradient glow, and seed dots
  are all present in the shipped `output/figures/cover_art.png`
  (`scripts/generate_cover_art.py` passes `grammar_hash=grammar.grammar_hash`
  to `render_cover()`; verified 2026-07-06 by re-running the analysis stage
  and reading the regenerated PNG). The QR-drawing branch in `src/cover_art.py`
  now has a dedicated test (`tests/test_cover_art.py::test_render_cover_with_grammar_hash_*`,
  added this session) — `cover_art.py` measures at 100% branch coverage.
- [ ] `src/emit_templates.py` is fully implemented and independently tested
  (100% coverage, `tests/test_emit_templates.py`) but is not wired into
  `materialize.py`: `_emit_manuscript()` (`src/materialize.py:255`) builds
  child manuscript stubs with its own inline logic rather than calling
  `emit_templates.emit_all()`. Two parallel implementations of the same
  responsibility, one dead in production — a code-quality gap, not a
  manuscript-accuracy one. Deliberately not wired this session: touching
  `materialize.py`'s tested output shape immediately before a real DOI
  publish is exactly the last-minute-risk pattern to avoid; tracked here for
  a dedicated pass instead.

## Configurable-surface gaps
- [x] `manuscript/config.yaml` — full grammar with 6 slots
- [x] `manuscript/config.yaml.example` — fork-safe copy
- [x] `.agents/skills/template-autopoiesis/SKILL.md` — Hermes-compatible skill
- [x] Zenodo deposit metadata sourced from `manuscript/config.yaml` (`paper`,
  `authors`, `keywords`, `metadata.license`) by `scripts/publish/publish_project_release.py`
  — no separate `publish/zenodo_metadata.json` file exists in this project;
  an earlier draft of this TODO claimed one did (this bullet corrects that)
- [x] `manuscript/references.bib` — 5 real, live-verified external citations
  plus the one legitimately-forthcoming self-citation (DOI cannot exist
  before Zenodo deposit; see "Publish readiness" below)

## Documentation and signposting gaps
- [x] README — use-this-template, config-entry-points, template-integrity signposts all present
- [x] AGENTS.md — full architecture, module inventory
- [x] CHANGELOG.md — Wave 9 filled
- [x] STANDALONE.md — standalone usage guide
- [x] SYNTAX.md — grammar syntax reference
- [x] SPEC.md — full spec document, Phase 10 partially checked
- [x] IMPROVEMENTS.md — all items A-E resolved

## Test and validator gaps
- [x] 493 tests collected (`uv run pytest projects/templates/template_autopoiesis/tests/
  --cov=projects/templates/template_autopoiesis/src --cov-branch`, measured 2026-07-06); 1 skipped
- [x] `manuscript_figures.py` covered (was 0% — untested production code path; now 98.15%)
- [x] `sealing.py`, `verify.py`, `cli.py` — previously below-floor (51%/88%/75%),
  now 97.06% / 97.65% / 93.55% branch coverage respectively (measured
  2026-07-06 via a fresh `stage_02_analysis.py` run + `output/data/coverage_full.json`)
- [x] `common.py` — was 73.91%, now 100% (`tests/test_common.py`, new file,
  covers `trunc()`'s clipping branch and `CheckReport.failed`/`all_passed`)
- [x] `figures.py` — was 80.95%, now 98.41% (`tests/test_figures.py` extended
  with the `list`/`tuple` branch of `_first_plottable_array`, the generic
  `repr()` fallback in `_scalar_summary_lines`, and the array-plotting branch
  of `render_primitive_figure`; one small partial-branch gap remains at
  `figures.py:21->23`)
- [x] `cover_art.py` — was 82.05%, now 100% (`tests/test_cover_art.py` extended
  with `test_render_cover_with_grammar_hash_*`, calling `render_cover(...,
  grammar_hash=...)` directly for the first time)
- [x] Every module in `src/` now measures at or above 90% branch coverage —
  no module sits below the floor as of this measurement (2026-07-06); see
  `output/figures/fig_coverage_by_module.png` for the current per-module
  ranking, and treat it as a snapshot to regenerate, not a permanent fact
- [x] Manuscript figure labels/paths verified against actual generated output
  2026-07-06 — all four embedded figures (`fig_stacked_product`,
  `fig_product_space`, `fig_domain_coverage`, `fig_coverage_by_module`)
  resolve to real files under `output/figures/` after a fresh analysis run
- [ ] Repo-wide `scripts/pipeline/stage_01_test.py --project templates/<name>` resolves
  a wrong test path (`scripts/projects/templates/<name>/tests`, missing the leading
  `projects/`) — reproduces on other templates too (e.g. `template_gold_refinement`),
  so this is a pipeline-wide infra bug, not specific to this project. Direct
  `pytest projects/templates/template_autopoiesis/tests/ --cov=... --cov-fail-under=90`
  is unaffected and remains the authoritative gate until that script is fixed.

## Manuscript expansion (2026-07-06)
- [x] Sections 01-06 expanded ~6x, each grounded in a Read of the real source
  files it describes (grammar.py, expand.py, materialize.py, primitives/*,
  honesty.py, verify.py, sealing.py, integrity.py) — no invented capabilities.
- [x] 4 figures embedded with captions and pandoc-crossref labels (previously
  generated but never referenced in any manuscript section): stacked product
  space, domain coverage, product-space annotation, and a new real per-module
  coverage chart (`fig_coverage_by_module`, `src/manuscript_figures.py`).
- [x] 5 real citations added, each verified via a live fetch this session
  (Crossref API / DBLP / JOSS / DOI resolution — never from training-data
  memory): Maturana & Varela 1980, Claessen & Hughes 2000 (QuickCheck),
  MacIver et al. 2019 (Hypothesis), Lamb & Zacchiroli 2022 (Reproducible
  Builds), Merkle 1987. Fetch evidence recorded in `ISA.md ## Verification`.
- [x] Fixed a citation-key mismatch bug (`[@property_based_testing]` used in
  5 files didn't match either real bibtex key) and a citation-parser trap
  (an inline-code `` `@pytest.mark.parametrize(...)` `` was parsed as an
  undefined citation attempt by the pre-render validator, blocking the
  combined PDF render).
- [x] Forge cross-vendor audit (E4 hard gate) caught 4 CRITICAL + 2 MEDIUM
  factual defects in the expanded prose that the mechanical honesty gate
  could not catch (none used a banned word): a fabricated variable name
  (`NOMINAL_OVER_EFFECTIVE`, not in `src/manuscript_variables.py`), an
  off-by-one in the honesty gate's own word-count description, a direct
  contradiction between two sections about whether `hypothesis` is optional,
  an overclaim about `src/honesty.py`'s actual guarantee scope, an
  inaccurate/uncited/mislocated Knuth reference, and a mislabeled abstract
  diagram node. All 6 fixed and re-verified (see `ISA.md` for detail).
- [x] Fixed ~30 honesty-gate violations (`src/honesty.py`'s
  `_UNSUPPORTED_CLAIM_PATTERN` regex over absolute-certainty words) introduced
  by the expanded prose — including a self-referential case where
  `04_honesty.md`'s own description of that regex quoted the banned words
  literally, tripping the gate it was describing.
- [x] Fixed a project-local-`.venv` interpreter bug in
  `measure_test_summary()`: when the pipeline invokes this project's scripts
  via `uv run --directory <project_root>` (a non-workspace-member gets an
  isolated `.venv` per `uv`'s rules), `sys.executable` resolved to that
  venv, which has no `pytest` installed, silently degrading both
  `{{TEST_COUNT}}`/`{{COVERAGE_PCT}}` and the new coverage figure to
  `"pending"`/missing. Now resolves the monorepo root's own `.venv` explicitly.

## Publish readiness (2026-07-06 assessment)
- **Not yet published** — `README.md` PUBLISHING-STATUS block shows 0/20 platforms published (Zenodo/GitHub/etc. all `⚪ available`, no DOI minted). Publishing (Zenodo deposit, GitHub push) is a real, credentialed, irreversible action and was intentionally left for explicit user trigger — see `docs/guides/publishing-guide.md`.
- **Quality gates now green**: tests/coverage/ruff/mypy/bandit all pass; analysis pipeline 7/7; PDF renders cleanly with cover image (QR seal + gradient glow + seed dots all present), dense margins/font, and honest self-reported metrics.
- **Before publishing**: no known blocking gaps remain in the manuscript itself. `src/emit_templates.py` non-wiring (see below) is a code-quality item, not a manuscript-accuracy one, and was deliberately left untouched this close to a real DOI deposit.

## Ordered improvement ladder
1. Wire `src/emit_templates.py` into `materialize.py`'s `_emit_manuscript()`, or remove one of the two parallel implementations
2. Fix `stage_01_test.py --project templates/<name>` path resolution (repo-wide, not project-specific)

### Closed off the ladder (previously items 1–5 above, across two passes today)
- `references.bib` real DOIs — closed (5 live-verified citations + forthcoming self-citation)
- Cover art QR seal / gradient glow / seed dots — closed (all three wired and rendered)
- Manuscript figure labels vs. generated filenames — verified aligned
- `sealing.py`/`verify.py`/`cli.py` coverage gaps — closed (all now above 90%)
- `common.py`/`figures.py`/`cover_art.py` coverage gaps — closed (100%/98.41%/100%);
  every module in `src/` now clears the 90% floor as of this measurement