# `infrastructure/search/literature/backends/`

Stable re-exports for literature search backends. Implementations live in sibling modules:

| Module | Types |
| --- | --- |
| `base.py` | `SearchBackend`, `BackendError` |
| `http_client.py` | `HttpClient`, `HttpResponse`, `UrllibHttpClient`, `HttpGetMixin` |
| `local_backend.py` | `LocalBackend` |
| `crossref_backend.py` | `CrossrefBackend` |
| `arxiv_backend.py` | `ArxivBackend` |
| `paperclip_backend.py` | `PaperclipBackend` |
| `paperclip_text_parser.py` | `parse_cli_blocks`, `papers_from_text_content` |

Import via `from infrastructure.search.literature.backends import CrossrefBackend` or the parent `literature` package.
