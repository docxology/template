## Honesty Contract

### Ground-truth table

| Claim | Evidence location | Test |
|---|---|---|
| Grammar parses | `src/grammar.py::parse_grammar` | `test_grammar_and_expand.py` |
| Expansion is deterministic | `src/expand.py::expand`, `_digest_index` | `test_grammar_and_expand.py` |
| Materialize writes files | `src/materialize.py::materialize` | `test_materialize.py` |
| Integrity hashes | `src/integrity.py::tree_hash_from_content_hashes` | `test_integrity_and_verify.py` |
| Verify recomputes | `src/verify.py::verify_child` | `test_integrity_and_verify.py` |
| Primitives collected | `src/primitives/__init__.py::collect_primitives` | `test_primitives_registry.py` |

### Honesty manifest

The `verify_honesty` command inspects each source file via AST to confirm
every claimed function actually exists.  Missing functions are reported as
`missing_calls`.

### Mutation gate

`test_meta_teeth.py` is parametrized over all {{DOMAIN_COUNT}} domains.  For
each domain with a `negative_control`, it asserts that the control output
differs from the primary output.  This ensures negative controls are not
accidentally no-ops and that primary implementations are not accidentally
broken.
