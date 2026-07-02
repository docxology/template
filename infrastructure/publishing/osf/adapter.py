"""Open Science Framework (OSF) publishing adapter — thin orchestrator.

Implements the documented OSF API v2 + Waterbutler flow with raw ``requests``
(matching the Zenodo / IPFS provider style in this package), so the adapter is
fully testable against a local ``pytest-httpserver`` with no live OSF account:

1. **Create node** (only when ``node_id`` is not supplied) —
   ``POST {api_base}/nodes/`` with a JSON:API body.
2. **Upload each file** — ``PUT {files_base}/resources/{node_id}/providers/
   {storage_provider}/?kind=file&name=<name>`` (Waterbutler), raw bytes body.

OSF deliberately splits metadata (``api.osf.io``) from file I/O
(``files.osf.io``); both bases are configurable for hermetic testing.

The adapter never raises on a network/credential failure — callers inspect
``OSFResult.status`` / ``.error``.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from infrastructure.core.logging.utils import get_logger
from infrastructure.publishing._adapter_http import iter_bundle_files, lazy_session

from .models import OSFConfig, OSFResult

logger = get_logger(__name__)

_JSONAPI = "application/vnd.api+json"


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class OSFAdapter:
    """Create-node-and-upload publisher for the Open Science Framework.

    Parameters
    ----------
    config:
        :class:`OSFConfig`. The token, when absent, is resolved from
        ``OSF_TOKEN`` in the environment.
    env:
        Environment mapping for token resolution (defaults to ``os.environ``).
    session:
        Optional ``requests.Session`` for tests; created lazily otherwise.
    """

    name: str = "osf"

    def __init__(
        self,
        config: OSFConfig,
        *,
        env: dict[str, str] | None = None,
        session: Any | None = None,
    ) -> None:
        source = env if env is not None else dict(os.environ)
        token = config.token or source.get("OSF_TOKEN")
        self.config = OSFConfig(
            title=config.title,
            token=token,
            node_id=config.node_id,
            category=config.category,
            public=config.public,
            description=config.description,
            api_base=config.api_base.rstrip("/"),
            files_base=config.files_base.rstrip("/"),
            storage_provider=config.storage_provider,
            timeout=config.timeout,
        )
        self._session_arg = session

    # ------------------------------------------------------------------
    @staticmethod
    def _node_web_url(node_id: str) -> str:
        return f"https://osf.io/{node_id}/"

    # ------------------------------------------------------------------
    def publish(self, bundle: Path, *, dry_run: bool = True) -> OSFResult:
        """Create (or reuse) an OSF node and upload every file in *bundle*.

        Parameters
        ----------
        bundle:
            A single file or a directory tree to upload. For a directory, files
            are uploaded flat into osfstorage by basename (OSF folder nesting is
            a documented follow-up).
        dry_run:
            When ``True`` (default) nothing is sent; a ``"dry-run"`` result lists
            the endpoints and files that would be used.
        """
        files = iter_bundle_files(bundle)
        names = tuple(p.name for p in files)

        if dry_run:
            target = self.config.node_id or "<new-node>"
            return OSFResult(
                status="dry-run",
                node_id=self.config.node_id,
                url=self._node_web_url(self.config.node_id) if self.config.node_id else None,
                uploaded=names,
                timestamp_utc=_now_utc_iso(),
                extra={
                    "would_create_node": "" if self.config.node_id else f"{self.config.api_base}/nodes/",
                    "would_upload_to": f"{self.config.files_base}/resources/{target}/providers/"
                    f"{self.config.storage_provider}/",
                },
            )

        if not self.config.token:
            return OSFResult(
                status="error",
                error="Missing OSF_TOKEN credential",
                timestamp_utc=_now_utc_iso(),
            )

        import requests  # noqa: PLC0415 — deferred; see module docstring

        headers = {"Authorization": f"Bearer {self.config.token}"}
        session = lazy_session(self)

        try:
            node_id = self.config.node_id
            if not node_id:
                node_id = self._create_node(session, headers)
                if node_id is None:
                    return OSFResult(
                        status="error",
                        error="OSF node creation returned no node id",
                        timestamp_utc=_now_utc_iso(),
                    )

            uploaded: list[str] = []
            for path in files:
                ok = self._upload_file(session, headers, node_id, path)
                if ok:
                    uploaded.append(path.name)

            logger.info("OSF published node %s (%d/%d files)", node_id, len(uploaded), len(files))
            status = "ok" if len(uploaded) == len(files) else "error"
            return OSFResult(
                status=status,
                node_id=node_id,
                url=self._node_web_url(node_id),
                uploaded=tuple(uploaded),
                timestamp_utc=_now_utc_iso(),
                error=None if status == "ok" else f"Uploaded {len(uploaded)}/{len(files)} files",
            )
        except requests.RequestException as exc:
            return OSFResult(
                status="error",
                node_id=self.config.node_id,
                error=f"OSF HTTP error: {exc}",
                timestamp_utc=_now_utc_iso(),
            )

    # ------------------------------------------------------------------
    def _create_node(self, session: Any, headers: dict[str, str]) -> str | None:
        body = {
            "data": {
                "type": "nodes",
                "attributes": {
                    "title": self.config.title,
                    "category": self.config.category,
                    "description": self.config.description,
                    "public": self.config.public,
                },
            }
        }
        resp = session.post(
            f"{self.config.api_base}/nodes/",
            headers={**headers, "Content-Type": _JSONAPI, "Accept": _JSONAPI},
            json=body,
            timeout=self.config.timeout,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})
        node_id = data.get("id")
        return str(node_id) if node_id else None

    def _upload_file(self, session: Any, headers: dict[str, str], node_id: str, path: Path) -> bool:
        resp = session.put(
            f"{self.config.files_base}/resources/{node_id}/providers/{self.config.storage_provider}/",
            headers=headers,
            params={"kind": "file", "name": path.name},
            data=path.read_bytes(),
            timeout=self.config.timeout,
        )
        resp.raise_for_status()
        return resp.status_code in (200, 201)
