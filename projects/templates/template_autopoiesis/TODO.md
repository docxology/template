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
- [x] Repo-wide `scripts/pipeline/stage_01_test.py --project templates/<name>` path bug —
  closed 2026-07-06. `repo_root` was computed as `Path(__file__).parent.parent`, which
  resolves to `scripts/` (the script lives at `scripts/pipeline/stage_01_test.py`,
  two levels deep, needing three `.parent`s / `parents[2]`), causing
  `resolve_project_root` to prepend `scripts/` to every project path and
  silently discover 0 tests. Fixed to `Path(__file__).resolve().parents[2]`;
  verified `--project templates/template_autopoiesis --project-only` now
  finds and runs 493/494 tests at 97.5% coverage. Same-session sweep of
  `scripts/**/*.py` for the identical depth-miscount pattern found and fixed
  two more instances directly in this project's publish path
  (`scripts/pipeline/stage_05_copy.py`, `scripts/publish/publish_project_release.py`
  — the latter is what blocked this project's own Zenodo/GitHub release
  until fixed). **Not yet fixed** (found but out of scope for this session —
  each needs its own verify-and-test pass before touching): the same
  `.parent.parent` / `parents[1]` depth-miscount also appears in
  `scripts/pipeline/stage_00_setup.py`, `stage_06_llm_review.py`,
  `stage_07_executive_report.py`, `scripts/audit/audit_filepaths.py`, and
  four `scripts/docgen/*.py` files (`api_reference.py`,
  `architecture_overview.py`, `coverage_history.py`, `stage_table.py`) —
  flagged as a repo-wide follow-up, not template_autopoiesis-specific.

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

## Publish readiness / published state (2026-07-06)
- **Published.** Real production Zenodo deposit + GitHub release, run via
  `scripts/publish/publish_project_release.py --production --reserve-doi-first`
  after fixing the repo_root bug above that was blocking it:
  - Concept DOI: `10.5281/zenodo.21227869` — [resolves](https://doi.org/10.5281/zenodo.21227869)
  - Version DOI: `10.5281/zenodo.21227870`
  - GitHub release: https://github.com/docxology/template/releases/tag/v1.0.0
  - Cross-posted (verified live via direct fetch, not just receipt files):
    IPFS/Pinata (`QmanoQUGKKFeYFtd5HRpB4ysE9jVxbzvaWpqgpWu5rRi8V`), OSF
    (https://osf.io/ksmzp/), TestPyPI (`template-autopoiesis` 0.1.0)
  - **Not completed**: Hugging Face Hub upload failed (documented adapter
    limitation — base64-inlines binaries, needs Git-LFS for a PDF this size;
    see `docs/guides/publishing-guide.md` Troubleshooting). A fix via the
    official `huggingface_hub` client was attempted but blocked by the
    session's own permission system as a separate, not-yet-authorized action
    (creating a repo under the `ActiveInference` org namespace). Software
    Heritage archival was skipped — it archives the *executable bundle*
    (Stage 12), a separate artifact not yet built for this project, not the
    manuscript PDF. Netlify credential does not authenticate (401); real PyPI
    (vs. TestPyPI), arXiv, GitHub Pages, and Cloudflare/Netlify static-site
    deploys were not attempted this session.
- **Quality gates green at publish time**: tests/coverage/ruff/mypy/bandit all pass; analysis pipeline 7/7; PDF renders cleanly with cover image (QR seal + gradient glow + seed dots all present), dense margins/font, and honest self-reported metrics.
- **Abstract revised and re-published as v1.0.1** (2026-07-06): `00_abstract.md`
  rewritten from a one-sentence lede + bare diagrams/bullets into three real
  prose paragraphs (what it does, the three usually-unverified claims made
  structurally checkable, the result summary), verified live in both the
  re-rendered PDF and the Zenodo deposit description. New version DOI
  `10.5281/zenodo.21229620` (concept DOI unchanged); GitHub release v1.0.1.
- **Standalone repo created**: https://github.com/docxology/template_autopoiesis
  (public, mirrors this project's own directory content — source of truth
  remains the monorepo per `docs/guides/publishing-guide.md`). Has its own
  v1.0.1 release with the same PDF/DOI. `publication.github_repository` and
  `CITATION.cff`'s `repository-code` both point here now, matching the
  `template_gold_refinement`/`template_madlib` convention.
- **Found: tag-namespace collision with `.github/workflows/release.yml`.**
  This repo runs an automated, repo-wide release-notes bot (generic name
  "Research Project Template vX.Y.Z", auto-generated changelog body) that
  shares the same bare-semver tag namespace (`v1.0.0`, `v1.0.1`, ...) as
  per-project releases created by `publish_project_release.py`. It silently
  overwrote both this project's GitHub release names/bodies (verified via
  `gh release view v1.0.0`/`v1.0.1` showing the bot's generic content, not
  the abstract/DOI content the publish script wrote) — though the uploaded
  PDF assets were untouched. The Zenodo record itself (the actual DOI-bearing
  durable artifact) is unaffected. **Follow-up recommendation, not applied
  this session**: future per-project releases on `docxology/template` should
  use a project-scoped tag (e.g. `template_autopoiesis-v1.0.0`) to avoid this
  collision, or the standalone repo (which has no such bot) should be treated
  as the canonical place for per-project GitHub releases.

## Ordered improvement ladder
1. Wire `src/emit_templates.py` into `materialize.py`'s `_emit_manuscript()`, or remove one of the two parallel implementations
2. Fix the same repo_root depth-miscount bug in the 7 remaining `scripts/**/*.py`
   files identified above (out of scope for this session; not template_autopoiesis-specific)

### Closed off the ladder (previously items 1–6 above, across three passes today)
- `references.bib` real DOIs — closed (5 live-verified citations; self-citation now carries the real minted DOI, see "Publish readiness")
- Cover art QR seal / gradient glow / seed dots — closed (all three wired and rendered)
- Manuscript figure labels vs. generated filenames — verified aligned
- `sealing.py`/`verify.py`/`cli.py` coverage gaps — closed (all now above 90%)
- `common.py`/`figures.py`/`cover_art.py` coverage gaps — closed (100%/98.41%/100%);
  every module in `src/` now clears the 90% floor as of this measurement
- `stage_01_test.py --project templates/<name>` path bug — closed (see "Test and validator gaps")