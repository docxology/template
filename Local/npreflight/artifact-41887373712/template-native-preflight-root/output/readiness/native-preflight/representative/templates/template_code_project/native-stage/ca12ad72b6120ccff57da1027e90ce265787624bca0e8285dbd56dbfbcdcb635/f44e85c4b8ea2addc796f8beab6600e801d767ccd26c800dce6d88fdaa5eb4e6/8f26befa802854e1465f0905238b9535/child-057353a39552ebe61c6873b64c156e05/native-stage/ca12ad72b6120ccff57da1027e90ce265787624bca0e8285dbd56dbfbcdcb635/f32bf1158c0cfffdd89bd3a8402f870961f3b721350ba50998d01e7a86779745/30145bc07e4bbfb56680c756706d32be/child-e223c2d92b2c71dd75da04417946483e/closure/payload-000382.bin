"""Shared HTTP/bundle helpers for the publishing adapters (R6 de-duplication).

Consolidates two helper bodies that previously lived verbatim on every
publishing adapter (Zenodo/IPFS archival providers, HuggingFace Hub, OSF):

* :func:`lazy_session` — return an injected (test) session, otherwise lazily
  create and cache a real ``requests.Session`` on the adapter instance.
  ``requests`` is imported *inside* the function so that importing an adapter
  module never triggers a top-level ``import requests`` (and the associated
  ``http`` namespace resolution that clashes with a local ``http`` module when a
  subprocess puts ``infrastructure/publishing/`` on ``sys.path[0]``).
* :func:`iter_bundle_files` — expand a bundle path into the ordered list of
  files to upload: the file itself, or every file under the tree, sorted.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

__all__ = ["iter_bundle_files", "lazy_session"]


def lazy_session(adapter: Any) -> Any:
    """Return ``adapter._session_arg`` when set, else a cached lazy ``requests.Session``.

    The adapter must expose ``_session_arg`` (an injected session or ``None``).
    On first real use the session is created and cached on ``adapter._lazy_session``.
    """
    if adapter._session_arg is not None:
        return adapter._session_arg
    import requests  # noqa: PLC0415 — deferred to first network use

    if not hasattr(adapter, "_lazy_session"):
        adapter._lazy_session = requests.Session()
    return adapter._lazy_session


def iter_bundle_files(bundle: Path) -> list[Path]:
    """Return the files in *bundle*: the file itself, or every file under the tree, sorted."""
    if bundle.is_file():
        return [bundle]
    return [p for p in sorted(bundle.rglob("*")) if p.is_file()]
