# AGENTS — tests/

- Add a test with every engine change. Logic gets a unit test; layout changes
  also get a **visual** render check (rasterize and look).
- Integration tests render the *real* edition from `../content/` — keep them
  asserting page count (12), trim, and `all_pages_fit`.
- Use `tmp_path` for any written PDF/figure; never write into `../output/`.
- Keep the suite fast (< a few seconds) and deterministic.

## File inventory

| File | Coverage |
| --- | --- |
| [`conftest.py`](conftest.py) | Shared project-root/content fixtures. |
| [`test_ads.py`](test_ads.py) | Classified and display-ad rendering. |
| [`test_components.py`](test_components.py) | Flowable/component builders. |
| [`test_config.py`](test_config.py) | Strict render configuration. |
| [`test_content.py`](test_content.py) | Content models and YAML loaders. |
| [`test_engine.py`](test_engine.py) | Real and synthetic PDF rendering. |
| [`test_figures.py`](test_figures.py) | Scenes, charts, ads, and figure generation. |
| [`test_furniture.py`](test_furniture.py) | Canvas-drawn furniture. |
| [`test_geometry.py`](test_geometry.py) | Page and column geometry. |
| [`test_robustness.py`](test_robustness.py) | Malformed input, escaping, and overset behavior. |
| [`test_typography.py`](test_typography.py) | Font resolution and stylesheet contracts. |
