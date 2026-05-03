# tests/infra_tests/search/

## Overview

| File | Focus |
| --- | --- |
| `test_models.py` | Request/response models |
| `test_backends_http.py` | HTTP client paths against local servers |
| `test_backends_local.py` | Local/offline backends |
| `test_client_and_cache.py` | Client orchestration + cache semantics |
| `test_fulltext.py` | Fulltext retrieval helpers |
| `test_cli.py` / `test_cli_direct.py` | CLI |

## Run

```bash
uv run pytest tests/infra_tests/search/ -v
```

## See also

- [`README.md`](README.md)
- [`../../../infrastructure/search/AGENTS.md`](../../../infrastructure/search/AGENTS.md)
