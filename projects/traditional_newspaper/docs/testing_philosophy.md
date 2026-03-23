# Testing philosophy — `traditional_newspaper`

## Requirements

- **Coverage:** `projects/traditional_newspaper/src` is measured with a **90%** minimum under the root test orchestrator (see root `pyproject.toml` / CI).
- **No mocks:** Do not use `unittest.mock`, `pytest` monkeypatch for faking I/O, or HTTP stubs unless the template explicitly adopts a pattern (this project uses real files and subprocesses).

## Layout

| File | Role |
|------|------|
| `conftest.py` | Prepends `../src` to `sys.path`; sets `MPLBACKEND=Agg` |
| `test_layout_spec.py` | Layout dataclass and column validation |
| `test_sections.py` | Slice ordering, inventory, on-disk manuscript completeness |
| `test_sections_extended.py` | `get_slice`, `all_tracked_manuscript_basenames`, etc. |
| `test_snippets.py` / `test_snippets_extended.py` | LaTeX builders and escaping |
| `test_content.py` | Fixture paragraph/copy determinism |
| `test_masthead.py` | PNG bytes, dimensions, seed sensitivity |
| `test_layout_figure.py` | Schematic PNG determinism |
| `test_script_stats.py` | Runs `report_manuscript_stats.py` via **subprocess**; asserts JSON shape |
| `test_visualization.py` | Stats parsing, B&W chart determinism, grayscale pixel bounds |
| `test_visualization_script.py` | Subprocess chain: stats script then `visualization_wordcount_bw.py` |
| `test_section_graphics.py` | Section banner PNG determinism and grayscale checks |
| `test_section_banners_script.py` | Subprocess `generate_section_banners.py` |
| `test_init_exports.py` | Package surface |

## Commands

```bash
uv run pytest projects/traditional_newspaper/tests/ \
  --cov=projects/traditional_newspaper/src \
  --cov-fail-under=90
```

## See also

- [../tests/AGENTS.md](../tests/AGENTS.md) — test file map
- [agent_instructions.md](agent_instructions.md) — editing constraints
