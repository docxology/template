# tests/

```bash
python -m pytest                  # 28 tests
python -m pytest --cov=newspaper  # ~95% line coverage (gate 85%)
```

| File | Covers |
|------|--------|
| `test_geometry.py` | column math, page geometry, error paths |
| `test_config.py` | strict render config, page sizes, validation |
| `test_content.py` | content model + loaders + validation errors |
| `test_typography.py` | font registration, stylesheet, no-hyphenation headlines |
| `test_figures.py` | halftone scenes + charts + `generate_all` |
| `test_engine.py` | integration: render the real edition + a synthetic one to PDF |

Logic is tested here; **appearance** is verified visually (see
`../docs/testing_philosophy.md`).
