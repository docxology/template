"""Stable re-exports for literature search backends."""

from infrastructure.search.literature.arxiv_backend import ArxivBackend
from infrastructure.search.literature.base import BackendError, SearchBackend
from infrastructure.search.literature.crossref_backend import CrossrefBackend
from infrastructure.search.literature.http_client import HttpClient, HttpResponse, UrllibHttpClient
from infrastructure.search.literature.local_backend import LocalBackend
from infrastructure.search.literature.paperclip_backend import PaperclipBackend

__all__ = [
    "ArxivBackend",
    "BackendError",
    "CrossrefBackend",
    "HttpClient",
    "HttpResponse",
    "LocalBackend",
    "PaperclipBackend",
    "SearchBackend",
    "UrllibHttpClient",
]
