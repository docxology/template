## Honesty Contract

### Why a manifest, not a claim

A generator that produces a manuscript describing its own code faces an
obvious temptation: assert a capability in prose without checking whether the
capability exists.  The abstract of this manuscript survived exactly this
failure once — a hand-written "Tests: 371 · Coverage: 99.94%" line that no
generator step had computed — and was corrected by replacing the literal
numbers with `493` / `96.28` tokens filled in at render
time by `scripts/02_measure_test_coverage.py`.  `src/honesty.py` exists to
make that class of failure structurally harder: every load-bearing claim in
this manuscript must resolve to a named function in a named file, and a
dedicated module inspects the source tree to confirm that resolution rather
than trusting the prose that asserts it.

The framing is not incidental to a project named `template_autopoiesis`. An
autopoietic system, in Maturana and Varela's original sense, is one whose
components participate in producing and verifying the very network of
processes that produced them [@maturana_varela_1980] — organizational
closure, not open-loop assertion. The honesty manifest is the narrow,
literal, code-level analogue of that closure: the manuscript's claims about
the code are checked *by the code*, not by a separate act of faith from the
author. The analogy should not be over-read — `src/honesty.py` is a static
AST scan, not a self-maintaining living system — but it is the reason this
mechanism exists at all rather than a simple "trust me" comment block.

### Ground-truth table

| Claim | Evidence location | Test |
|---|---|---|
| Grammar parses | `src/grammar.py::parse_grammar` | `test_grammar_and_expand.py` |
| Expansion is deterministic | `src/expand.py::expand`, `_digest_index` | `test_grammar_and_expand.py` |
| Materialize writes files | `src/materialize.py::materialize` | `test_materialize.py` |
| Integrity hashes | `src/integrity.py::tree_hash_from_content_hashes` | `test_integrity_and_verify.py` |
| Verify recomputes | `src/verify.py::verify_child` | `test_integrity_and_verify.py` |
| Primitives collected | `src/primitives/__init__.py::collect_primitives` | `test_primitives_registry.py` |

Each row is not prose describing an intention — it is a key into
`STRUCTURAL_EVIDENCE`, the dict in `src/honesty.py` that the code below
walks mechanically. If a row's evidence path stops existing, the manifest
fails and `test_honesty.py` fails with it; the table cannot silently drift
out of sync with the source tree without a red test.

### The structural evidence catalogue

`STRUCTURAL_EVIDENCE` is a `dict[str, list[str]]` mapping a claim identifier
(`"grammar_parses"`, `"expand_deterministic"`, `"materialize_writes_files"`,
`"integrity_hashes"`, `"verify_recomputes"`, `"primitives_collected"`) to one
or more `"relative/path.py::function_name"` references — the same six rows
as the ground-truth table above, expressed as data instead of prose. This
catalogue is the single source of truth the checker walks; the manuscript
table is a human-readable rendering of it, not an independent claim.

### How `build_manifest` inspects the AST

`build_manifest(project_root)` iterates every claim in `STRUCTURAL_EVIDENCE`
and, for each `"path::function"` reference:

1. Splits the reference on `::` into a relative file path and an optional
   function name.
2. Resolves the path under `project_root` and checks `Path.exists()`. A
   missing file appends `"{path} not found"` to `missing_calls` and marks
   the claim as failed.
3. If a function name is given, reads the file's source and calls
   `_collect_function_names(source_code)`, which parses the text with
   `ast.parse` and walks the resulting tree (`ast.walk`) collecting the
   `.name` of every `ast.FunctionDef` and `ast.AsyncFunctionDef` node into a
   `set[str]`. If the required name is not in that set, `"{fn} not in
   {path}"` is appended to `missing_calls` and the claim is marked failed.
   A `SyntaxError` during parsing is caught and yields an empty name set —
   fail-closed rather than raising.
4. `HonestyManifest.evidence[claim]` is set to `True` only if every
   reference for that claim resolved cleanly.

It is worth being precise about what this proves and what it does not. The
check confirms that a function *definition* with the claimed name exists,
syntactically, in the claimed file — nothing more. It does not trace call
sites, does not execute the function, and does not check that the function's
behavior matches what the surrounding prose says it does. A function named
`materialize` that silently did nothing would still satisfy this check; only
the separately-run test suite (`test_materialize.py` et al., named in the
ground-truth table) exercises actual behavior. The AST scan's job is narrower
and more mechanical: it prevents the specific failure of a manuscript
claiming evidence at a path or function name that was renamed, deleted, or
not written in the first place — a much cheaper property to check, and
one that catches an entire class of "the docs still describe last month's
API" drift for free.

### The `HonestyManifest` dataclass

```python
@dataclass
class HonestyManifest:
    evidence: dict[str, bool] = field(default_factory=dict)
    missing_calls: list[str] = field(default_factory=list)
    unsupported_claims: list[str] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(self.evidence.values()) and not self.missing_calls and not self.unsupported_claims
```

`all_passed` is a conjunction over three independent failure modes: any
claim whose evidence resolution failed, any specific missing-call detail
recorded during that resolution, and any unsupported-claim hit from the
prose scan below. `test_honesty.py::test_structural_evidence_all_pass` and
`test_no_missing_calls` both call `build_manifest(PROJECT_ROOT)` against this
project's own real source tree and assert the manifest is clean — the
checker is run against itself, not only against synthetic fixtures.
`test_verify_honesty_with_nonexistent_project` runs `build_manifest` against
an empty `tmp_path` and asserts `missing_calls` is non-empty, which is the
negative control for the checker itself: a project with no source files at
all must fail every claim, or the checker has no teeth.

### Prose scanning for unsupported claims

`verify_honesty(project_root, manuscript_dir=None)` first calls
`build_manifest`, then — if a `manuscript/` directory exists — reads every
`*.md` file in it and scans for a fixed, case-insensitive regex over six
absolute-certainty words and one hard percentage figure, defined verbatim in
`_UNSUPPORTED_CLAIM_PATTERN` in `src/honesty.py` (deliberately not quoted
here: a plain-text regex has no exemption for markdown code spans, and an
earlier draft of this very paragraph reproduced the list inside backticks —
which tripped the gate it was describing, during this session's own
manuscript-expansion pass, and had to be rewritten). Each match is recorded
as `"{filename}:{offset}: '{match}'"` in `manifest.unsupported_claims`.

Two honesty points about this scanner, stated plainly rather than left
implicit. First, it is a fixed lexical denylist, not a semantic checker — it
will not catch a false quantitative claim phrased without one of those seven
tokens (the "371 tests" incident described above would not have tripped it;
that failure mode is closed instead by the `493` token
substitution, a separate mechanism). Second, `unsupported_claims` *is*
enforced, but only on one of the two paths through this module:
`HonestyManifest.all_passed` is a conjunction over `evidence`,
`missing_calls`, *and* `unsupported_claims`, and `src/cli.py::cmd_honesty`
calls `verify_honesty()` (the function that populates all three) and exits
the process with code 1 whenever `all_passed` is false —
`tests/test_cli.py::test_main_honesty_exits_zero` pins exactly this
behavior. The one place prose hits are *not* enforced is
`test_verify_honesty_all_passed` in `tests/test_honesty.py`, which asserts
only `all(m.evidence.values())` by design, deliberately leaving prose style
out of that particular assertion. Reading only that one test in isolation
would suggest the prose scanner is a lint rather than a gate; reading the
CLI path shows it is a real gate on the `honesty` subcommand specifically.

### The mutation gate: proving the acceptance criteria have teeth

`test_meta_teeth.py` targets a different failure mode than `honesty.py`: not
"does the claimed function exist" but "would a fake implementation of it get
away with passing." It is parametrized via the
`pytest.mark.parametrize("domain", list(KNOWN_DOMAINS))` decorator over all
5 primitive domains from `src/grammar.py`, and runs three
checks per domain:

1. **`test_stub_fails_gate_per_domain`** — `_stub_run_analysis` is a
   constant-success stub that returns `{"success": True, "output": "stub"}`
   regardless of input. `_gate_checks_real_computation` is asserted to
   reject it for every domain. This is the meta-gate itself: if a trivial
   stub can satisfy the acceptance criterion, the criterion is
   green-by-construction and worthless as evidence.
2. **`test_real_primitive_passes_gate_per_domain`** — the first
   `PrimitiveSpec` for the domain (from `collect_primitives()`) is run on
   its own `example_input`, and the same gate is asserted to *accept* the
   real result. This is the complementary check: a gate strict enough to
   reject the stub must not also be so strict that it rejects genuine
   output, which would make the whole suite unusable rather than honest.
3. **`test_negative_control_distinguished_per_domain`** — for the first
   primitive that declares a `negative_control` callable, both the normal
   and control outputs are computed and their key sets compared. Stated
   precisely: the current assertion is `normal_keys == control_keys or
   len(normal_result) > 0`. Because primitives are already ensured to
   return non-empty dicts (`test_primitives_return_nonempty_per_domain`),
   the second disjunct is close to trivially true, so this test — as written
   — verifies structural shape more than it verifies that the negative
   control's *values* actually diverge from the primary output. That is
   weaker than the literal claim "the control output differs from the
   primary output," and is recorded here as a known gap between the test's
   docstring intent and its present assertion strength, rather than papered
   over in the prose that describes it.

`test_primitives_return_nonempty_per_domain` closes the loop: every spec in
`collect_primitives()[domain]`, run on its own example input, must return a
non-empty `dict`. Together, the four tests in `test_meta_teeth.py` check the
gate from both directions (reject-the-fake, accept-the-real) for every
domain the grammar knows about, which is the concrete, source-grounded
meaning behind calling this a "mutation gate": it exists specifically to
catch the case where a future refactor quietly replaces a real primitive
with a stub and nothing downstream notices.

### What this buys, and what it does not

The honesty manifest and the mutation gate are complementary, not
redundant, but both are narrower than they might sound. `src/honesty.py`'s
AST check covers exactly the six `STRUCTURAL_EVIDENCE` entries (`grammar
parses`, `expand deterministic`, `materialize writes files`, `integrity
hashes`, `verify recomputes`, `primitives collected`) — it does not scan
this manuscript for every function or variable name it mentions, so a false
claim about a piece of code outside that list of six would not be caught by
this mechanism. (This is not a hypothetical gap: an earlier draft of the
Limitations section below claimed `generate_variables` exposed a
`NOMINAL_OVER_EFFECTIVE` token that does not exist anywhere in
`src/manuscript_variables.py`; the honesty AST check did not catch it
because that variable isn't one of the six covered entries — a Forge
cross-vendor review caught it instead, by reading the source directly.)
`test_meta_teeth.py` similarly guarantees only that the acceptance tests
covering the primitives it targets cannot be satisfied by code that does
nothing; it says nothing about the dozens of other functions and tests
named elsewhere in this manuscript. Neither mechanism proves the primitives
are numerically correct in any deeper sense than "the
first `PrimitiveSpec` in each domain returns domain-shaped keys on its
example input" — correctness of the underlying mathematics is the job of
`test_grammar_and_expand.py`, `test_integrity_and_verify.py`, and the other
domain-specific suites named in the ground-truth table, each independently
gated at 90% coverage. What this section documents is narrower and more
modest: the mechanism by which this manuscript's claims are kept from
silently diverging from the source code that is supposed to back them.
