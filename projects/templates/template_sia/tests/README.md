# Tests — template_sia

Project test suite for SIA wiring, tokens, and fixture replay. 90% coverage floor on `src/`.

Behavior tests mirror the source subpackages (`loop/`, `ledger/`, `manuscript/`);
cross-cluster tests (`architecture contract`, `figures`, `scripts`, `claim
ledger`) stay at the tests root. See [AGENTS.md](AGENTS.md) for the file map.

```bash
uv run pytest projects/templates/template_sia/tests/ -m "not requires_ollama" -v
```
