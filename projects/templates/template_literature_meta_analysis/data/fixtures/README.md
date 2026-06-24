# `data/fixtures/`

Committed, deterministic **offline seed corpora** for the default pipeline run.

`modafinil_corpus.jsonl` is a synthetic corpus (80 records, reserved `10.5555/`
test DOIs, generated authors) produced by
[`scripts/generate_fixture_corpus.py`](../../scripts/generate_fixture_corpus.py)
(logic in [`src/literature/fixture_corpus.py`](../../src/literature/fixture_corpus.py)).
It lets CI and a fresh clone exercise the whole meta-analysis pipeline with no
network, byte-identically across runs.

These records are **illustrative, not empirical** — they are not real modafinil
findings. A live retrieval run replaces them with real records.
