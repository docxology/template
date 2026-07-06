## Limitations

This section states what the exemplar does *not* do, alongside what it does.
Coverage and test-count figures are not restated as literal numbers here —
those live only in the `{{TEST_COUNT}}` / `{{COVERAGE_PCT}}` tokens, resolved
at render time from a live measurement
(`src/manuscript_variables.py::measure_test_summary`), not hand-typed.

### Reserved slots are excluded from the effective product space

The grammar declares six slots, but `materialize()` only branches on three of
them — `primitive_domain`, `track`, `section_set`. The remaining
{{RESERVED_SLOT_COUNT}} (`{{RESERVED_SLOT_NAMES}}`) are parsed and contribute
to `spec_hash` like any other slot, but `manuscript_figures.py`,
`sealing.py`, and `integrity.py` are unconditionally exercised regardless of
`figure_profile`, `qr_profile`, or `integrity_profile` — those modules do not
currently branch on the reserved slots' selected option. The practical
consequence: distinct seeds can produce a nominally distinct `spec_hash`
while materializing byte-identical children, since only three slots vary
output. That inflation, {{PRODUCT_SIZE}} nominal vs. {{EFFECTIVE_PRODUCT_SIZE}}
effective, is disclosed rather than hidden: `generate_variables`
(`src/manuscript_variables.py`) exposes both `PRODUCT_SIZE` and
`EFFECTIVE_PRODUCT_SIZE` as separate tokens, so nowhere in this manuscript
can the larger, nominal number be quoted without the smaller, effective one
appearing beside it. Wiring the reserved slots into `materialize()` is an
open item, not a claimed capability.

### No child-PDF rendering in CI

`realize.py::render_child_manuscript()` writes manuscript stubs for a
generated child but does not invoke Pandoc or Chrome. Absent a full
rendering toolchain — the default posture in CI — it returns
`{"success": False, "reason": "Chrome/Pandoc rendering not available in
child context", ...}` rather than raising or silently skipping. Verifying a
child's *files* (`verify_child` / `verify_child_full`) is decoupled from
verifying that its manuscript renders; only the former is tested here.

### Within-platform guarantee only

Determinism is derived from `hashlib.sha256` over Python strings
(`expand.py`'s seed/slot/ordinal/options digest, and
`integrity.py::tree_hash_from_content_hashes` over file contents), which is
itself platform-independent. But the surrounding pipeline — file iteration
order ahead of `sorted()` normalization, path-separator handling, the
specific CPython minor version running `materialize()` — is not
independently fuzzed across platforms in this suite. What is actually tested
is determinism within one CPython version on one OS, a narrower claim than
the cross-platform, bit-for-bit reproducibility discussed in the
reproducible-builds literature [@reproducible_builds]. A second CI leg that
materializes the same seed on a second OS/Python and diffs tree hashes would
close this gap; it does not currently exist.

### Grammar does not self-modify

The autopoiesis metaphor is figurative. Maturana and Varela's operational
sense of autopoiesis is a system that continuously regenerates its own
constitutive components through its own operation [@maturana_varela_1980].
Here the grammar (`manuscript/config.yaml`) is fixed input; `parse_grammar`
and `expand` are pure functions of that input plus a seed; no code path
feeds a materialized child back into the grammar or rewrites
`src/grammar.py`. Children are causally downstream of the grammar — the
reverse direction does not occur in the current codebase. The name is a
provocation about what genuine self-production would require, not a claim
this exemplar achieves it.

### Integrity verification checks self-consistency, not tamper-proofing

`verify_child` recomputes a tree hash from the files *listed inside*
`provenance.json` and compares it against the `tree_hash` field stored in
that same file (`src/verify.py`, `src/materialize.py`). Both the manifest
and the expected hash are self-reported at materialization time; nothing
external anchors them. An actor who can rewrite `provenance.json` can edit
its `files` list and recompute a matching hash from whatever content they
choose, and `verify_child` would report a match — it only checks internal
consistency, not consistency against something outside the child's own
directory [@merkle_tree_provenance]. `verify_seal` similarly checks the
shape of an optional `seal.json` written by the same run it would need to
audit. This detects accidental post-generation drift, the tested use case;
it is not a defense against deliberate tampering with write access. Also
worth naming precisely: `tree_hash_from_content_hashes` sorts
`path:content_hash` pairs and hashes their concatenation once — a flat
manifest digest, not a hierarchical Merkle tree with per-file inclusion
proofs. `integrity.py` separately defines `merkle_root`, an actual
pairwise-reduction tree, but `materialize()`/`verify()` call the flat
function, not that one.

### Coverage is uneven across modules, not uniform (though every module now clears the floor)

Two earlier drafts of this section each named a different below-floor
trio — first `sealing.py`/`verify.py`/`cli.py`, then, after those were
hardened, `common.py`/`figures.py`/`cover_art.py`. As of this measurement no
module sits below the 90% branch-coverage line
([@fig:coverage_by_module]): dedicated tests were added for `common.py`'s
`trunc()` clipping branch and `CheckReport.failed` (`tests/test_common.py`,
new this session), `figures.py`'s `list`/`tuple` input branch of
`_first_plottable_array`, the generic `repr()` fallback in
`_scalar_summary_lines`, and the array-plotting branch of
`render_primitive_figure` (`tests/test_figures.py`), and `cover_art.py`'s
QR-seal drawing branch (`tests/test_cover_art.py`,
`test_render_cover_with_grammar_hash_*`) — the same branch identified above
as running in production but previously untested.

Smaller residual gaps remain in modules that are otherwise well above the
floor: `sealing.py`'s `read_qr_matrix` `pyzbar`-decode path is untested since
`pyzbar` is not installed here; `verify.py`'s schema-version and
malformed-JSON `except` branches are not independently exercised; `cli.py`'s
`cmd_materialize`/`cmd_verify` have no end-to-end CLI-level test, though the
library functions they wrap are covered elsewhere in `test_materialize.py`
and `test_integrity_and_verify.py`; `honesty.py` itself sits closest to the
floor at just above 90%. None of these pull the aggregate below the 90%
floor (`--cov-fail-under=90`), and the aggregate {{COVERAGE_PCT}} alone would
obscure exactly where the remaining, smaller gaps live — which is the reason
this section, and [@fig:coverage_by_module], exist as a per-module view
rather than trusting one headline number. Property-based tests
(`tests/test_property_invariants.py`, Hypothesis) and a stress/edge suite
(`tests/test_stress_edge_cases.py`) cover invariants like boundary seeds and
all-reserved-slot configurations [@claessen2000quickcheck;
@maciver2019hypothesis], but generated inputs are not a substitute for
direct tests of the specific branches named above.

This whole section is itself evidence for a point made elsewhere in this
manuscript: a coverage ranking is a measurement, not a fact about the code —
each of its two prior versions was accurate when written and became false as
soon as new tests shipped. Readers should treat any specific module name and
percentage in this document as dated to its stated measurement, and re-run
`stage_02_analysis.py` for the current ranking rather than trust a prior
render.

### Cover art now includes the QR seal, but that code path is untested

An earlier draft of this section reported that the title-page cover image
omitted the originally envisioned QR seal, gradient glow, and seed-derived
dot placement. That is no longer accurate and is corrected here rather than
left to silently drift: `scripts/generate_cover_art.py` now calls
`render_cover(..., grammar_hash=grammar.grammar_hash)`, and `src/cover_art.py`
draws all three elements unconditionally except the QR seal, which is drawn
whenever `grammar_hash` is not `None` — the shipped `paper.cover.image`
(`output/figures/cover_art.png`) is generated by exactly this call, so the
rendered title page carries a real gradient glow, real seed-derived dot
scatter, and a real QR-style pixel grid encoding `{{GRAMMAR_HASH}}` with the
hash printed as a text label beneath it. An earlier draft of this section
also noted that no test called `render_cover` with an explicit
`grammar_hash=`, leaving the QR-drawing branch (`src/cover_art.py`, the `if
grammar_hash is not None:` block) exercised in production but untested; that
gap is now closed by `tests/test_cover_art.py::test_render_cover_with_grammar_hash_*`,
added this session (see "Coverage is uneven across modules" below).

Separately, for most of this project's life `manuscript/references.bib` held
a single self-referential `friedman2026autopoiesis` entry noting the DOI is
forthcoming, while `99_references.md` carried a hand-written, uncited list
alongside it — a citation without a resolvable BibTeX entry is exactly the
kind of unverifiable claim this project's honesty contract exists to catch.
That gap is now closed: `references.bib` carries five real, live-verified
external citations plus the one legitimately-forthcoming self-citation
(`references.bib`'s own DOI cannot exist before this manuscript is deposited;
see `TODO.md`), and `99_references.md` annotates each entry against the
section that relies on it rather than listing citations independent of the
bibliography.
