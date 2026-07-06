# CHANGELOG — template_autopoiesis

## Wave 10 — Manuscript accuracy re-audit (2026-07-06)

A fresh `stage_02_analysis.py` run regenerated `output/data/coverage_full.json`
and `output/figures/fig_coverage_by_module.png` from the current source tree
and surfaced two manuscript claims that had drifted from the code they
described — the same class of failure `src/honesty.py` and this changelog's
own Wave 9 entry exist to prevent, this time caught by re-running the
generator rather than trusting a prior session's committed prose.

### Fixed

- **Stale below-floor module list.** `03_results.md` and `06_limitations.md`
  named `sealing.py`, `verify.py`, and `cli.py` as the modules below the 90%
  branch-coverage line. A fresh measurement shows all three now pass (97.06%,
  97.65%, 93.55%); the real below-floor set is `common.py` (73.91%),
  `figures.py` (80.95%), and `cover_art.py` (82.05%). Both manuscript
  sections and `TODO.md` updated to name the current set, with the specific
  untested branch in each module identified from `coverage_full.json`'s
  `missing_lines`.
- **Stale cover-art gap claim.** `06_limitations.md` stated the cover art
  omitted the QR seal, gradient glow, and seed dots. Reading
  `scripts/generate_cover_art.py` and `src/cover_art.py` directly, and
  regenerating `output/figures/cover_art.png`, shows all three are present
  in the shipped image — `render_cover()` is called with
  `grammar_hash=grammar.grammar_hash`, and the gradient glow / seed-dot code
  draws unconditionally. The real, narrower gap: no test in
  `test_cover_art.py` exercises the QR-drawing branch directly with an
  explicit `grammar_hash=` argument, even though it runs in production.
  `06_limitations.md` and `TODO.md` rewritten to state this precisely rather
  than repeat the outdated "simplified placeholder" framing.

### Added

- `tests/test_common.py` (new file, 8 tests) covering `trunc()`'s clipping
  branch and `CheckReport.failed`/`all_passed` — `common.py` had no dedicated
  test file before this session and was measured at 73.91% branch coverage.
- Three tests in `tests/test_figures.py` closing `figures.py`'s `list`/`tuple`
  branch of `_first_plottable_array`, the generic `repr()` fallback in
  `_scalar_summary_lines`, and the array-plotting branch of
  `render_primitive_figure` (was 80.95%).
- Three tests in `tests/test_cover_art.py`
  (`test_render_cover_with_grammar_hash_*`) exercising `render_cover(...,
  grammar_hash=...)` directly for the first time — the QR-seal drawing branch
  that runs in production via `scripts/generate_cover_art.py` (was 82.05%).
- Net effect: 478 → 493 tests, 93.68% → 96.41% branch coverage; `common.py`
  and `cover_art.py` reach 100%, `figures.py` reaches 98.41%. As of this
  measurement every module in `src/` clears the repository's 90% branch-
  coverage floor — `03_results.md` and `06_limitations.md` updated again to
  say so, with an explicit note that this is a snapshot, not a permanent
  property (the same caution this changelog entry itself now needs, having
  already been wrong twice in one session).
- Deliberately NOT wired: `src/emit_templates.py` (fully implemented,
  100%-covered, but unused by `materialize.py`'s own inline
  `_emit_manuscript()`) was left as a tracked code-quality item rather than
  integrated — changing `materialize.py`'s tested output shape immediately
  before a real DOI deposit is exactly the last-minute-risk pattern this
  project's own doctrine warns against. See `TODO.md`.

## Wave 9 — Deep Review Pass

### Closed

**A. Honesty manifest coverage**
- `STRUCTURAL_EVIDENCE` now covers all six key functions: `parse_grammar`, `expand`, `_digest_index`, `materialize`, `tree_hash_from_content_hashes`, `verify_child`, `collect_primitives`.
- `verify_honesty` scans manuscript for unsupported quantitative claims.
- `test_honesty.py` confirms all structural evidence passes on the live source AST.

**B. Reserved slot accounting**
- `generate_variables` now computes and surfaces `PRODUCT_SIZE`, `EFFECTIVE_PRODUCT_SIZE`, and `RESERVED_SLOT_COUNT` as manuscript tokens.
- The abstract explicitly reports the inflation factor.
- `test_manuscript_variables.py` asserts `EFFECTIVE_PRODUCT_SIZE == 45` and `RESERVED_SLOT_COUNT == 3`.

**C. Mutation meta-gate completeness**
- `test_meta_teeth.py` parametrized over all 5 `KNOWN_DOMAINS`:
  - Stub `run_analysis` (constant success=True) must fail the gate
  - Real primitive call must pass the gate
  - Negative controls produce distinguishable output
- Gate has teeth: four domain-specific keys checked.

**D. Verify tests completeness**
- `test_integrity_and_verify.py` covers: tampered file, missing file, missing provenance.json, `verify_child_full` schema version check, `verify_seal` with and without seal.json.
- All three failure modes (tamper/delete/add) are tested.

**E. Property invariants**
- `test_property_invariants.py` uses Hypothesis for:
  - Grammar product invariants across arbitrary seeds
  - Expand determinism across any seed in [0, 10^9]
  - Double materialize byte-stability per domain
  - Verify passes clean / fails tamper per domain
  - QR matrix square and deterministic for arbitrary text
- `test_stress_edge_cases.py` covers: single slot, zero options/slots raises, all-reserved effective product = 1, boundary seeds (0, MAX_INT, -1), 1000-seed stress, Merkle invariants.
