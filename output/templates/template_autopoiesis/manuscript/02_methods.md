## Methods

### The A→E generation spine

Generation proceeds through five stages, each implemented as a pure function
in its own module (`src/grammar.py`, `src/expand.py`, `src/materialize.py`,
`src/verify.py`, `src/sealing.py`). No stage depends on interactive state or
network access; every stage takes an immutable input and returns an immutable
(or file-system-materialized) output.

```mermaid
flowchart LR
    A[Load Grammar] --> B[Expand Spec]
    B --> C[Materialize Child]
    C --> D[Verify Integrity]
    D --> E[Seal + QR]
```

### Stage A — Grammar loading and validation

`load_grammar(project_root)` reads `manuscript/config.yaml`, extracts the
`autopoiesis:` block, and hands it to `parse_grammar()`. Parsing enforces
four invariants before a `Grammar` object can exist at all:

1. **The seed must be an integer.** `parse_grammar` reads `block.get("seed",
   42)` and raises `GrammarError` if the value is not an `int` — a stray
   string or float seed in `config.yaml` fails loudly at load time rather
   than silently coercing.
2. **At least one slot must be defined.** An empty or missing `slots:` list
   raises `GrammarError("Grammar must define at least one slot")`.
3. **Every slot must have a non-empty name and ≥1 option.** These checks live
   in `GrammarSlot.__post_init__`, so they fire the instant a `GrammarSlot`
   is constructed — a malformed entry cannot survive to become part of a
   `Grammar`.
4. **No slot may contain duplicate options.** `GrammarSlot.__post_init__`
   also computes `{o for o in self.options if self.options.count(o) > 1}`
   and raises if that set is non-empty, so two identical options in one slot
   (e.g. `[optimization, optimization]`) are rejected rather than silently
   collapsing the product space.

`parse_grammar` additionally validates every entry in `deps:` against
`VENDORABLE_DEPS` — the fixed tuple `(logging, glossary_gen, figure_manager,
manuscript_injection, steganography)` — raising `GrammarError` on any unknown
dependency name. This project's own grammar (see `manuscript/config.yaml`)
currently declares `deps: []`, so the deps-vendoring path exercised in
`materialize.py` is present in the code and covered by
`test_deps_vendoring.py`, but not active for the manuscript's own default
render.

A successfully constructed `Grammar` is a frozen dataclass carrying `seed`,
the tuple of `GrammarSlot` objects, the tuple of `deps`, and an optional
`source_path` (excluded from equality/hash comparison so two grammars loaded
from different files but with identical content still compare equal).

### Reserved slots vs. effective slots

Not every slot in the grammar contributes to what this paper calls the
*effective product size*. `RESERVED_SLOTS` is a fixed tuple —
`figure_profile`, `qr_profile`, `integrity_profile` — naming slots that
control **presentation and provenance mechanics** (how many figures render,
whether a QR seal is embedded, which hash scheme secures the tree hash)
rather than **domain content** (which primitive kernel, which analytical
track, which manuscript section set). `Grammar` exposes both views as
properties:

- `Grammar.slots` — every slot as declared in `config.yaml`.
- `Grammar.reserved_slots` — the subset whose `name` appears in
  `RESERVED_SLOTS`.
- `Grammar.effective_slots` — the complementary subset, i.e. every slot
  *not* in `RESERVED_SLOTS`.
- `Grammar.product_size` — the raw cross product over *all* slots
  (`n *= len(s.options)` for every slot, reserved or not).
- `Grammar.effective_product_size` — the cross product restricted to
  `effective_slots` only.

The distinction matters for honest reporting: a grammar can nominally claim a
large product space by adding presentation-only slots, while the number of
*substantively distinct* generated projects — different kernel domain,
different analytical track, different section layout — is the smaller
effective figure. Both `360` (nominal) and
`45` (effective) are reported in this manuscript
side-by-side rather than only the larger, more impressive-looking number —
this is the paper's concrete instance of the "hard to vary" honesty
discipline the project holds itself to (see the Honesty Contract, §4).
`3` reserved slots (`figure_profile, qr_profile, integrity_profile`) are
excluded from the effective figure; `SYNTAX.md` documents the same slot
table and the *inflation factor* (nominal ÷ effective) as a first-class,
honestly-reported quantity rather than an implementation detail.

`force_domain(grammar, domain)` provides a targeted override: it returns a
new `Grammar` with the `primitive_domain` slot's options collapsed to a
single forced value (raising `GrammarError` if `domain` is not one of the
five `KNOWN_DOMAINS`), leaving every other slot — reserved or effective —
untouched. This is how the pipeline can materialize "one child per domain"
deterministically without re-deriving the whole grammar.

### Stage B — Deterministic spec expansion

`expand(grammar, seed=None)` walks `grammar.slots` in declaration order and,
for each slot, computes an index into that slot's options via
`_digest_index`:

```python
def _digest_index(seed, slot_name, ordinal, options):
    key = f"{seed}\x1f{slot_name}\x1f{ordinal}\x1f{','.join(options)}"
    digest = hashlib.sha256(key.encode()).digest()
    value = int.from_bytes(digest[:8], "big")
    return value % len(options)
```

Four inputs — the seed, the slot's own name, its ordinal position in the
slot list, and the full joined option string — are concatenated with an
ASCII unit-separator (`\x1f`) between fields and hashed with SHA-256. The
first eight bytes of the digest are read as a big-endian integer and reduced
modulo the option count. This construction has three consequences load-
bearing for the rest of the pipeline:

- **No shared PRNG state.** Each slot's selection is an independent hash of
  its own key, not a draw from a stateful random-number generator advanced
  slot-by-slot. Reordering unrelated slots elsewhere in the list does not
  perturb a given slot's selection unless that slot's own `ordinal` changes.
- **Full avalanche on any input change.** Because the selection is a SHA-256
  digest, changing the seed, renaming a slot, or adding/removing a single
  option string anywhere in that slot's option tuple changes the digest —
  and therefore, with high probability, the selected index — for that slot.
- **Reproducibility without stored randomness.** Nothing about the selection
  is persisted except the seed and the grammar itself; re-running `expand`
  against the same grammar and seed recomputes the identical digest and
  therefore the identical selection, with no cached or serialized RNG state
  to keep in sync.

The result is a frozen `Spec` dataclass: `schema_version` (the fixed string
`"autopoiesis/spec/1"`), the `seed` actually used (the explicit override if
supplied, otherwise `grammar.seed`), the `grammar_hash` this spec was
expanded against, an ordered tuple of `(slot_name, chosen_value)`
`selections`, the `deps` inherited unchanged from the grammar, and the
resolved `primitive_domain` (read out of the selections if a
`primitive_domain` slot exists, else defaulted to `KNOWN_DOMAINS[0]`). A
`Spec` additionally exposes `spec_hash`, computed by serializing
`to_dict()` to canonical (sorted-key, compact-separator) JSON and taking the
first 16 hex characters of its SHA-256 — the same truncation convention used
for `grammar_hash`.

Two auxiliary functions extend `expand` to families of children rather than
one: `derive_seed(base_seed, index)` hashes `f"{base_seed}\x1f{index}"` to
produce a new seed masked to 63 bits (`& 0x7FFFFFFFFFFFFFFF`, keeping it a
non-negative Python `int`), and `sample(grammar, count, base_seed=None)`
calls `expand` once per derived seed to produce `count` independent `Spec`
objects — independent in the sense that each is keyed off a distinct
derived seed, not off any shared mutable state. `enumerate_all(grammar)`
takes the orthogonal path: rather than sampling, it walks the full
`itertools.product` over every slot's options (reserved slots included) and
returns one plain dict per cell, giving direct access to the entire nominal
product space for exhaustive audits.

### Stage C — Materialization into a runnable child tree

`materialize(spec, out_root, template_root, clean=False)` turns a resolved
`Spec` into an actual directory of files on disk. The child's directory name
is derived deterministically by `child_name(spec)` as
`child_{primitive_domain}_{spec_hash}` — so the name itself encodes both the
selected domain and a content-derived identity, without any counter or
timestamp. `_build_tree` then assembles the file map that will be written:

- **Kernel primitives.** `_vendor_kernel_sources` copies `src/primitives/
  base.py` and `src/primitives/{domain}.py` for the spec's
  `primitive_domain`, rewriting `from src.primitives` / `from .primitives`
  imports to a bare `from primitives` so the copied module resolves
  correctly once it is no longer nested under the parent template's
  package. It also synthesizes a minimal `primitives/__init__.py` whose
  `collect_primitives()` imports only the one selected domain submodule —
  the child ships exactly one domain's kernel, not all five.
- **Figures source**, vendored verbatim from `src/figures.py` when present.
- **Dependency vendoring.** `_resolve_deps` reads `dep_mode` out of the
  spec's selections (defaulting to `"vendor"`) and, for each name in
  `spec.deps`, resolves the corresponding path from
  `_VENDORABLE_MODULE_PATHS` relative to the repository root
  (`template_root.parent.parent.parent`), embedding the real infrastructure
  source when it exists on disk or writing an explicit `"Source not found at
  build time."` stub when it does not — a vendored dependency the pipeline
  could not actually locate is marked as such in the generated file, not
  silently omitted. A seam `vendored/__init__.py` re-exports every vendored
  module by name.
- **A minimal `pyproject.toml`** declaring the child as its own installable
  project (`name = "child_{domain}"`, `numpy`/`matplotlib`/`pyyaml` runtime
  deps, pytest configured with `pythonpath = ["."]`).
- **A generated `analysis.py`** that calls `collect_primitives()`, iterates
  the selected domain's registered `PrimitiveSpec` entries, and prints each
  one's name and result on its `example_input` — a real, executable entry
  point rather than a stub that only imports.
- **A generated smoke test**, `tests/test_analysis.py`, asserting only that
  `run()` completes without raising.
- **Manuscript stubs** (`_emit_manuscript`) — abstract, introduction,
  results, and limitations sections written directly from the spec's own
  fields (domain, spec hash, all non-domain selections), so the child's own
  manuscript is itself traceable to the same `Spec` that generated its code.

Every file in the assembled tree is written to `child_root` and also
retained in-memory as `written: dict[str, str]`. `materialize` then calls
`tree_hash_from_content_hashes(written)` — sorting all relative paths
lexicographically, joining each as `"{path}:{content}"`, and taking the
SHA-256 of the concatenation — so the tree hash is a function of path names
and byte content only, not file-system metadata such as mtimes or
insertion order. The resulting `provenance.json` records a schema version
(`"autopoiesis/provenance/1"`), the full `spec.to_dict()`, the computed tree
hash, and the sorted list of every written relative path — the single
artifact Stage D re-derives from.

### Stage D — Verification

`verify_child(child_root)` (implemented in `src/verify.py`, not
`materialize.py`) loads `provenance.json`, reads back every file named in its
`files` list, recomputes the tree hash from those live contents via the same
`tree_hash_from_content_hashes` function used at materialization time, and
compares it against the recorded hash. Each individual predicate —
`provenance_exists`, `provenance_parseable`, `all_files_present`,
`tree_hash_matches` — is captured as a `CheckResult(name, passed, detail)`
inside an aggregate `CheckReport`, so a caller can distinguish *which*
invariant broke rather than receiving a single boolean. Any edit, deletion,
or addition to a file listed in provenance — anything from a hand-edited
line to a regenerated timestamp — changes at least one entry in `live`, which
changes the recomputed hash, which fails `tree_hash_matches` without
requiring the verifier to inspect a diff. `verify_child_full` extends this
with a `schema_version_correct` check against `materialize.PROVENANCE_SCHEMA_VERSION`,
catching provenance written by a different schema generation of the tool.

### Stage E — Sealing

`sealing.py` provides the payload and image layer for embedding a
tamper-evident summary alongside a generated child. `build_payload(spec_hash,
tree_hash, seed)` serializes a compact JSON object binding all three
identifiers; `build_pointer_payload` and `build_barcode_payload` offer
lighter-weight alternatives (a URL-plus-hash pointer, and a colon-joined
label/hash/seed string, respectively) for contexts where a full JSON payload
is unnecessary. `qr_matrix()` and `qr_image()` wrap the optional `qrcode`
library, falling back to a deterministic 5×5 checkerboard stub when it is
absent, so the sealing stage — and its tests — do not require an optional
dependency to be installed. `verify_seal(child_root)` checks for a
`seal.json`, that it parses, and that it carries a `spec_hash` field,
mirroring the same `CheckResult`/`CheckReport` pattern used in Stage D
rather than introducing a parallel reporting shape.

### Property-based invariants

Beyond the fixed example-based tests enumerated in the Honesty Contract's
ground-truth table (§4), `tests/test_property_invariants.py` exercises the
expansion and materialization functions against Hypothesis-generated inputs
using the property-based testing paradigm [@claessen2000quickcheck; @maciver2019hypothesis]:
rather than asserting fixed input/output pairs, these tests assert
invariants that must hold across a swept range of seeds — `product_size`
equals the literal product of every slot's option count regardless of
seed; `effective_product_size` does not exceed `product_size`; two grammars
parsed from the same block produce the same `grammar_hash`; `expand()`
called twice with the same seed produces the same `spec_hash` for any
seed Hypothesis draws in `[0, 10**9]`; the resolved `primitive_domain` is
one of `KNOWN_DOMAINS`; two independent `materialize()` calls from
the same spec into different output roots produce identical `tree_hash`
values, per domain; and `verify_child` reports `all_passed` on a freshly
materialized child but reports a failure the moment any listed file is
edited or deleted, per domain. A parallel Hypothesis sweep over generated
text confirms `qr_matrix()` returns a square matrix and is
deterministic on repeated calls with the same input. `hypothesis` is
declared under this project's `dev` optional-dependency group in
`pyproject.toml`, alongside `pytest` and `pytest-cov` — it is imported
unconditionally at the top of `test_property_invariants.py`, so it is a
real (if dev-only) dependency of this test module, not a soft, try/except
guarded one.

### Reproducibility framing

The tree-hash construction used at both Stage C and Stage D deliberately
mirrors the general goal of reproducible software builds
[@reproducible_builds]: a build (here, a materialize call) is reproducible
exactly when independent re-derivations from the same inputs — grammar,
seed, template source — produce byte-identical output, and that identity is
checked by content hash rather than by trusting the process that produced
it. The tree hash's construction — sort every `(path, content)` pair
lexicographically, join as `"path:content"`, and take one SHA-256 of the
concatenation — is a flat, single-level structure, not a binary hash tree.
`src/integrity.py` separately exposes a genuine binary `merkle_root()`
(pairwise concatenate-and-hash up the tree, duplicating the final odd node
when a level has odd cardinality), in the spirit of the hash-tree
provenance idea introduced for digital signatures
[@merkle_tree_provenance]. As of this writing `merkle_root()` is a
standalone, independently-tested utility: `integrity_profile` is declared
as a reserved grammar slot (options `sha256`, `merkle` in this project's
own `config.yaml`; `SYNTAX.md` documents a longer illustrative option list
including `merkle_kmyth`), but neither `materialize()` nor `verify_child()`
currently branches on its selected value — the slot is present in the
grammar and excluded from the effective product size, but is not yet wired
to switch which hashing function actually runs. Reporting that precisely,
rather than implying the profile already gates behavior, is the same
honesty discipline the project asks of its own manuscript elsewhere.
