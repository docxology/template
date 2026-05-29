# Literature backends package

## Public API (`backends/__init__.py`)

Re-exports: `SearchBackend`, `BackendError`, `HttpClient`, `HttpResponse`, `UrllibHttpClient`, `LocalBackend`, `CrossrefBackend`, `ArxivBackend`, `PaperclipBackend`.

HTTP backends accept injectable `http_client=` for `pytest-httpserver` tests (no mocks).

## Adding a backend

1. Subclass `SearchBackend` in a new module under `literature/`.
2. Set `name` and stamp `Paper.source = self.name`.
3. Raise `BackendError` on transport/parse failure.
4. Re-export from `backends/__init__.py` and `literature/__init__.py` if public.

## Tests

```bash
uv run pytest tests/infra_tests/search/ -q
```
