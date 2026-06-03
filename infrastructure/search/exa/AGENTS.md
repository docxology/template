# AGENTS — `infrastructure.search.exa`

Exa REST client. One subpackage per search interface (`search/`, `contents/`,
`answer/`, `find_similar/`); shared core (`client.py`, `config.py`, `models.py`,
`http.py`, `errors.py`) at the package root.

## Invariants (do not break)

- **No import-time side effects.** Importing the package must not read
  `EXA_API_KEY` or hit the network. Env is read only in `ExaConfig.from_env`.
- **No external SDK.** Transport is stdlib `urllib` via `UrllibExaHttpClient`,
  injectable for tests. Do not add an `exa_py` runtime dependency.
- **No mocks in tests.** Use `pytest-httpserver` and a `base_url` override
  (`tests/infra_tests/search/test_exa.py`).
- **camelCase on the wire.** Build payloads with `models.prune` + the per-field
  camelCase keys. Content keys (`highlights`/`text`/`summary`) nest under
  `contents` for `/search` and `/findSimilar`, but are **top-level** for
  `/contents`.
- **Errors are `ExaError`** carrying `.status`/`.body` for non-2xx.

## Adding a new Exa endpoint

1. New subfolder `exa/<endpoint>/` with `interface.py` (an `Exa<Name>Interface`
   taking the client) + `__init__.py` exporting it + a one-line `README.md`.
2. Add a lazy `@cached_property` + convenience pass-through on `ExaClient`.
3. Add response model to `models.py` (a `from_dict` classmethod).
4. Add a `pytest-httpserver` test asserting the wire payload and parsed result.
5. Re-export from `exa/__init__.py`.

## Source of truth

<https://docs.exa.ai/reference/search-api-guide-for-coding-agents> — if behaviour
contradicts this code, fetch it and reconcile; report staleness.
