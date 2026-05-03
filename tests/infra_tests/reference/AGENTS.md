# tests/infra_tests/reference/

## Overview

| File | Focus |
| --- | --- |
| `test_bibtex_parser.py` | Parser edge cases and round-trips |
| `test_bibtex_writer.py` | Writer output stability |
| `test_escape.py` | LaTeX/BibTeX escaping |
| `test_models.py` | Citation dataclasses |
| `test_converter.py` | Format conversion |
| `test_cli.py` / `test_cli_direct.py` | Package CLI |

## Run

```bash
uv run pytest tests/infra_tests/reference/ -v
```

## See also

- [`README.md`](README.md)
- [`../../../infrastructure/reference/AGENTS.md`](../../../infrastructure/reference/AGENTS.md)
