# AGENTS — src/

The engine. Keep the layers honest:

- `geometry`, `content`, `config` import **no** rendering library — keep them pure.
- Only `typography.py` may name a font; everything else uses `Fonts` roles.
- `furniture` *draws* (canvas); `components` *flows* (flowables); `layout` places
  frames and pours flowables; `engine` orchestrates. Don't blur these.
- Every change ships with tests and a **visual** render check (see `../docs/testing_philosophy.md`).
- mypy- and ruff-clean, always.
