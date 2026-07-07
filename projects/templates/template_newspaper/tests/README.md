# tests/

```bash
python -m pytest                  # full suite
python -m pytest --cov=newspaper  # ~99% branch coverage (gate 90%, see pyproject.toml)
```

| File | Covers |
|------|--------|
| `test_geometry.py` | column math, page geometry, error paths |
| `test_config.py` | strict render config, page sizes, validation |
| `test_content.py` | content model + loaders + validation errors |
| `test_typography.py` | font registration, stylesheet, no-hyphenation headlines |
| `test_figures.py` | halftone scenes + charts + colour ad graphics + `generate_all` |
| `test_components.py` | component flowable builders (pull quotes, figures, boxes, ads) not reached by integration render tests |
| `test_furniture.py` | canvas-drawn furniture branches (headline without kicker/deck, nameplate font-size scaling) |
| `test_ads.py` | classified/display ad rendering |
| `test_robustness.py` | malformed-input handling, HTML escaping, overset detection |
| `test_engine.py` | integration: render the real edition + a synthetic one to PDF |

Logic is tested here; **appearance** is verified visually (see
`../docs/testing_philosophy.md`).
