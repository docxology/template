# `prose.analysis` submodule

## Role

Frozen dataclasses and pure helpers used by [`infrastructure/prose`](../):

| Module | Contents |
| --- | --- |
| `metrics.py` | Syllables, sentences, `compute_metrics` (Flesch, FKGL, Fog, …). |
| `structure.py` | Heading parse, outline, section depth. |
| `quality.py` | Passive voice, hedges, long sentences, Pandoc-ish `@cite` snippets. |

## Invariants

- **No `open()`, no sockets.** Same inputs → same outputs (deterministic).
- Changing a metric shape requires updating [`ManuscriptReport`](../report.py) builders and [`tests/infra_tests/prose/`](../../../tests/infra_tests/prose/).

## See also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
