# `data/fixtures/` — agent reference

| File | Producer | Contract |
| --- | --- | --- |
| `modafinil_corpus.jsonl` | `scripts/generate_fixture_corpus.py` → `src/literature/fixture_corpus.py::build_synthetic_corpus` | One `Paper.to_dict()` JSON object per line; deterministic for `(term, n, seed)`; byte-stable. |

Regenerate: `uv run python scripts/generate_fixture_corpus.py` (default term
`modafinil`, n=80, seed=42). Do not hand-edit; the file is a generated artifact and
its determinism is asserted by `tests/literature/test_fixture_corpus.py`.
