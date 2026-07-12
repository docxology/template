## Reproducibility

Reproducibility is not a claim this manuscript makes about itself; it is a
property the code enforces on every run. Every number that appears below the
Determinism heading — f84a8f9dbcb18e37, 42, 493,
96.28 — is a token substituted at render time by
`src/manuscript_variables.py::generate_variables()` from a live grammar load
and a live pytest run (`src/manuscript_variables.py::measure_test_summary()`).
Neither function accepts a hardcoded literal as a fallback: if the subprocess
pytest run cannot be parsed, `measure_test_summary` returns the string
`"pending"` for both the test count and the coverage percentage rather than a
plausible-looking number [@reproducible_builds]. This design choice is a direct
consequence of an earlier failure mode in this project — a manuscript draft
that stated fixed test and coverage values in prose instead of
through the token pipeline. A number that cannot be traced back to a specific
function call in `src/` is, for the purposes of this project, not a number
this manuscript is permitted to assert.

### Determinism guarantee

Given the same `manuscript/config.yaml` grammar definition (grammar hash
`f84a8f9dbcb18e37`), the same seed (`42`), and the same
`template_autopoiesis` source tree, `scripts/autopoiesis.py expand` produces
byte-identical selections on every invocation, and `materialize` produces a
byte-identical child project tree. The determinism chain has three concrete
steps, each implemented as a pure function with no random or wall-clock input:

1. **Selection.** For every grammar slot, `src/expand.py::_digest_index()`
   builds the key
   `f"{seed}\x1f{slot_name}\x1f{ordinal}\x1f{','.join(options)}"` (a unit
   separator, `\x1f`, joins the fields so that no combination of seed/name/
   ordinal/option values can collide across a field boundary), hashes it with
   SHA-256, and reduces the first eight bytes of the digest modulo
   `len(options)` to obtain the chosen option's index. Because the digest is a
   pure function of `(seed, slot_name, ordinal, options)`, the same grammar
   and seed walk every slot to the same choice on every run — there is no
   `random.choice`, no `numpy.random`, and no seed-independent entropy source
   anywhere in the selection path.
2. **Spec identity.** The resolved selections, together with the grammar hash
   and seed, are assembled into a `Spec` dataclass
   (`src/expand.py::Spec`). Its `spec_hash` property serializes the full spec
   to canonical JSON (`sort_keys=True`, compact separators) and takes the
   first sixteen hex characters of the SHA-256 of that string. Sorting keys
   before hashing means insertion order in the underlying dict cannot
   perturb the hash — only the actual selections can.
3. **Tree identity.** `materialize()` (`src/materialize.py`) writes every
   vendored and generated file into the child project directory, then folds
   the complete `{relative_path: content}` mapping through
   `src/integrity.py::tree_hash_from_content_hashes()`. That function sorts
   the mapping lexicographically by path before hashing
   (`"\n".join(f"{k}:{v}" for k, v in sorted(...))`) specifically so that
   filesystem iteration order — which is not stable across
   platforms or `dict` construction paths — cannot change the result. The
   hash is computed from file *contents*, not from file metadata (mtime,
   permissions, inode), so copying a child project to a new machine or
   re-materializing it a year later reproduces the same tree hash as long as
   the source and the seed are unchanged.

Multiple children can be derived from one root seed without collisions: given
a `base_seed` and an integer `index`, `src/expand.py::derive_seed()` hashes
`f"{base_seed}\x1f{index}"` through SHA-256 and folds the first eight bytes to
a new integer seed. `sample(grammar, count)` calls `expand()` once per derived
seed, so a batch of `count` children is itself deterministic — the same
`base_seed` and `count` yield the same sequence of child seeds on every
invocation, hence the same sequence of children.

### The seal.json provenance mechanism

Materialization and sealing are deliberately two separate steps, and the
second one is optional. `materialize()` writes a `provenance.json`
into the child root containing the schema version
(`PROVENANCE_SCHEMA_VERSION = "autopoiesis/provenance/1"`), the full resolved
spec (`spec.to_dict()`), the tree hash, and the sorted list of every file path
that was written. This is the record `verify_child()` (`src/verify.py`)
recomputes against later.

A child project can additionally be **sealed**: `scripts/seal_child.py` (and
the pipeline-facing wrapper `scripts/04_seal.py`, which seals the
most-recently materialized child under `output/children/`) reads
`provenance.json`, re-runs `verify_child()` against the live files as a
pre-seal sanity check, and writes `seal.json` alongside it. The seal payload —
built by `src/sealing.py::build_payload()` — is a compact JSON object
`{"spec_hash": ..., "tree_hash": ..., "seed": ...}`. A shorter,
colon-delimited variant (`build_barcode_payload()`, truncating each hash to
its first eight hex characters) exists for embedding into a QR code or
barcode image via `src/sealing.py::qr_matrix()` / `qr_image()`, so that a
printed or exported artifact can carry a scannable, self-describing pointer
back to the exact spec and tree hash that produced it. Both the QR encoder and
its optional decode path (`read_qr_matrix()`, which depends on `pyzbar` and
`PIL`) degrade gracefully when those optional dependencies are absent: `qr_matrix()`
falls back to a deterministic checkerboard stub so callers and tests do not
hard-fail on a missing image dependency, and `read_qr_matrix()` simply returns
an empty string. The seal itself does not gate materialization — a child
project is fully valid and independently verifiable from `provenance.json`
alone; `seal.json` is an additive, portable pointer, not a second source of
truth. Sealing does not currently run inside `verify_child_full()`; it is a
separate check (`src/verify.py::verify_seal()`) invoked only when a caller
explicitly asks whether a seal exists, parses, and carries a `spec_hash`.

### SHA-256 vs. Merkle integrity profiles

`src/integrity.py` provides two distinct ways of turning a collection of
hashes into one summary digest, and the project does not conflate them:

- **`tree_hash_from_content_hashes()`** — the profile used by
  `materialize()`/`verify_child()` above — is a single-pass, order-independent
  digest over a `{path: content}` mapping. It answers exactly one question:
  does this set of files, at these paths, have these exact contents? It is
  cheap to compute and cheap to verify, but a single changed file forces a
  full recompute over every path to detect *which* file changed — the digest
  itself carries no positional structure.
- **`merkle_root()`** builds a binary Merkle tree
  [@merkle_tree_provenance] over an *ordered* list of hex digests: each level
  pairwise-concatenates adjacent nodes and hashes the concatenation, promoting
  an unpaired trailing node unchanged to the next level, until one root
  remains (the empty list is defined as the SHA-256 of the empty string,
  not a magic sentinel). Because the tree is addressable node-by-node, a
  Merkle profile supports proving that one specific file's hash is part of the
  committed set without re-hashing every other file — a property the flat
  tree-hash profile does not have.

Both are exercised in this codebase, but at present the materialize/verify
path in `src/materialize.py` and `src/verify.py` uses the flat,
order-independent tree hash exclusively; `merkle_root()` is available in
`src/integrity.py` and covered by its own tests as an independent integrity
primitive, not yet as the provenance root written into `provenance.json`. A
manuscript describing this project should not claim Merkle-tree provenance for
`provenance.json` today — that would be exactly the kind of prose-outruns-code
gap this project's honesty checks exist to catch (`src/honesty.py`).

### Recompute / verify workflow

```bash
# 1. Expand the grammar into a resolved spec (pure function of seed + config)
uv run python scripts/autopoiesis.py expand --seed 42 --output output/spec.json

# 2. Materialize the spec into a runnable child project + provenance.json
uv run python scripts/autopoiesis.py materialize --seed 42 --out-root output/children

# 3. Recompute the tree hash from the live files and compare to provenance.json
uv run python scripts/autopoiesis.py verify output/children/<child_name>

# 4. (optional) Seal the child — writes seal.json next to provenance.json
uv run python scripts/seal_child.py output/children/<child_name>
```

`verify` (`src/cli.py::cmd_verify` → `src/verify.py::verify_child_full()`)
performs four checks in sequence and exits non-zero if any fails:
`provenance_exists`, `provenance_parseable`, `all_files_present` (every path
listed in `provenance.json["files"]` still exists on disk), and
`tree_hash_matches` (the hash recomputed from the live file contents equals
the hash recorded at materialization time), followed by a
`schema_version_correct` check against the constant
`PROVENANCE_SCHEMA_VERSION`. There is no partial-credit outcome: a single
missing file or a single byte of drift in any tracked file flips
`tree_hash_matches` to `False`, because the tree hash is a single SHA-256 over
the sorted, concatenated `path:content` pairs — there is no per-file
tolerance to fall back on.

Re-running steps 1–2 with the same seed and the same source tree on the same
machine reproduces the identical spec hash and tree hash reported by step 3;
this is the operational meaning of "deterministic" for this project, and it
is exactly what a reviewer or a downstream user can check for themselves
without trusting any claim made in this document.

### Toolchain

- Python ≥ 3.10
- `numpy`, `matplotlib`, `pyyaml` (runtime)
- `pytest`, `pytest-cov` (test)
- `hypothesis` [@claessen2000quickcheck; @maciver2019hypothesis] (declared
  under this project's `dev` optional-dependency group in `pyproject.toml`,
  but imported unconditionally at the top of `test_property_invariants.py` —
  a real dependency of that test module, not a soft, try/except-guarded one;
  see Methods)
- `qrcode`, `pillow` (optional — `src/sealing.py`'s QR/barcode payload
  encoding degrades to a deterministic stub when unavailable; `pyzbar` is
  needed only for the optional decode path)

Outside the parent `template` repository checkout, `STANDALONE.md` documents
what is and is not vendored into a generated child project: single-file
modules under `primitives/` and `figures.py` are copied in and the child runs
entirely from its own vendored sources at runtime, with no dependency on the
parent's `src/`; optional infrastructure modules (logging, glossary
generation, figure management) are vendored as single-file stubs when the
corresponding module cannot be found under the parent repo's
`infrastructure/` tree. PDF/HTML rendering and prerender validation are
explicitly **not** vendored — a standalone child can be expanded, materialized,
tested, and verified, but manuscript rendering to PDF still requires the
parent repository's `infrastructure/rendering` and `infrastructure/validation`
modules. Byte-stability of a materialized tree is documented as
within-platform only (same Python interpreter, same OS) rather than an
unconditional cross-platform guarantee.

### Build command

```bash
uv run pytest projects/templates/template_autopoiesis/tests/ \
  --cov=projects/templates/template_autopoiesis/src \
  --cov-fail-under=90
```

This is the same command family `measure_test_summary()` runs internally
(with `--cov-branch` added explicitly, matching the repo-root
`pyproject.toml`'s `branch = true` setting rather than this project's own,
so the reported 96.28 agrees with the authoritative CI gate
methodology rather than silently using a different one) to produce the
493 and 96.28 tokens substituted above — the same
build, not a paraphrase of it, is the source of both this document's prose
and its own regeneration.
