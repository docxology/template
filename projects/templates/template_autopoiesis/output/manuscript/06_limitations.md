## Limitations

This section states what the exemplar does *not* do, alongside what it does.
Coverage and test-count figures are not restated as literal numbers here —
those live only in the `578` / `92.18` tokens, resolved
at render time from a live measurement
(`src/template_autopoiesis/manuscript/manuscript_variables.py::measure_test_summary`), not hand-typed.

### Reserved slots are excluded from the effective product space

The grammar declares six slots, but `materialize()` only branches on three of
them — `primitive_domain`, `track`, `section_set`. The remaining
3 (`figure_profile, qr_profile, integrity_profile`) are parsed and contribute
to `spec_hash` like any other slot, but `manuscript_figures.py`,
`sealing.py`, and `integrity.py` are unconditionally exercised regardless of
`figure_profile`, `qr_profile`, or `integrity_profile` — those modules do not
currently branch on the reserved slots' selected option. The practical
consequence: distinct seeds can produce a nominally distinct `spec_hash`
while materializing byte-identical children, since only three slots vary
output. That inflation, 360 nominal vs. 45
effective, is disclosed rather than hidden: `generate_variables`
(`src/template_autopoiesis/manuscript/manuscript_variables.py`) exposes both `PRODUCT_SIZE` and
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
`src/template_autopoiesis/core/grammar.py`. Children are causally downstream of the grammar — the
reverse direction does not occur in the current codebase. The name is a
provocation about what genuine self-production would require, not a claim
this exemplar achieves it.

### Integrity verification checks self-consistency, not tamper-proofing

`verify_child` recomputes a tree hash from the files *listed inside*
`provenance.json` and compares it against the `tree_hash` field stored in
that same file (`src/template_autopoiesis/gates/verify.py`, `src/template_autopoiesis/gates/materialize.py`). Both the manifest
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

### Coverage is uneven across modules

The aggregate 92.18% combines covered statements and branch exits
across the measured source inventory. Passing the configured 90% aggregate gate
(`--cov-fail-under=90`) does not establish a 90% floor for every module.
[@fig:coverage_by_module] preserves the per-module spread and marks values below
that reference line in red. The chart and headline percentage come from the same
persisted `output/data/coverage_full.json`, rather than independently assembled
measurements.

Coverage identifies executed paths, not correctness or completeness. Property-based
tests (`tests/gates/test_property_invariants.py`, Hypothesis) and the stress/edge
suite (`tests/core/test_stress_edge_cases.py`) exercise boundary seeds and
all-reserved-slot configurations [@claessen2000quickcheck; @maciver2019hypothesis],
but generated inputs do not replace direct negative controls or inspection of
unexecuted statements and branch exits.

Module rankings and gaps can change whenever source or tests change. Inspect the
current coverage report and regenerate the analysis and figure after a changed
input, rather than treating an earlier module list or a passing aggregate as
proof that all modules clear the reference line.

### Cover art includes the QR seal with direct rendering controls

An earlier draft of this section reported that the title-page cover image
omitted the originally envisioned QR seal, gradient glow, and seed-derived
dot placement. That is no longer accurate and is corrected here rather than
left to silently drift: `scripts/generate_cover_art.py` now calls
`render_cover(..., grammar_hash=grammar.grammar_hash)`, and `src/template_autopoiesis/figures/cover_art.py`
draws all three elements unconditionally except the QR seal, which is drawn
whenever `grammar_hash` is not `None` — the shipped `paper.cover.image`
(`output/figures/cover_art.png`) is generated by exactly this call, so the
rendered title page carries a real gradient glow, real seed-derived dot
scatter, and a real QR-style pixel grid encoding `a1f3e428cf1fb3e3` with the
hash printed as a text label beneath it. An earlier draft of this section
also noted that no test called `render_cover` with an explicit
`grammar_hash=`, leaving the QR-drawing branch (`src/template_autopoiesis/figures/cover_art.py`, the `if
grammar_hash is not None:` block) exercised in production but untested; that
gap now has direct controls in `tests/figures/test_cover_art.py::test_render_cover_with_grammar_hash_*`.
Those controls render an explicit hash, compare sealed and unsealed images, and
check byte stability for identical inputs; they do not establish exhaustive
visual correctness or QR decoding on every output.

Separately, for most of this project's life `manuscript/references.bib` held
a single self-referential `friedman2026autopoiesis` entry noting the DOI was
forthcoming, while `99_references.md` carried a hand-written, uncited list
alongside it — a citation without a resolvable BibTeX entry is exactly the
kind of unverifiable claim this project's honesty contract exists to catch.
That gap is now closed twice over: `references.bib` carries five real,
live-verified external citations, and following this project's own Zenodo
deposit the self-citation's DOI (`10.5281/zenodo.21227869`, verified by a
live `curl` against `doi.org` before being written into the entry) is real
rather than forthcoming. `99_references.md` annotates each entry against the
section that relies on it rather than listing citations independent of the
bibliography.
