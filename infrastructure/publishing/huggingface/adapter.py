"""HuggingFace Hub publishing adapter — thin orchestrator over the Hub REST API.

Implements two documented Hub HTTP endpoints with raw ``requests`` (matching the
Zenodo / IPFS provider style in this package), so the adapter has no hard
dependency on the ``huggingface_hub`` client library and is fully testable
against a local ``pytest-httpserver``:

1. **Create repo** — ``POST {base}/api/repos/create``
2. **Commit files** — ``POST {base}/api/{repo_type}s/{repo_id}/commit/{revision}``
   using the newline-delimited-JSON ("ndjson") commit protocol, base64-inlining
   each file as a regular (non-LFS) blob.

Usage::

    from pathlib import Path
    from infrastructure.publishing.huggingface import HuggingFaceHubAdapter, HuggingFaceConfig

    adapter = HuggingFaceHubAdapter(HuggingFaceConfig(repo_id="docxology/my-paper"))
    result = adapter.publish(Path("output/bundle"), dry_run=False)  # token from env
    print(result.url)

The adapter never raises on a network/credential failure — callers inspect
``HuggingFaceResult.status`` / ``.error``.

Large-file / Git-LFS note: the raw inline-commit path cannot satisfy the Hub's
LFS requirement for large or binary blobs (e.g. PDFs), which it rejects. When the
optional ``huggingface_hub`` client is installed (the ``publishing`` dependency
group) and the target is the real Hub, the adapter automatically escalates to
``HfApi.upload_file`` (which handles LFS) — both for files over the inline ceiling
and as a fallback when a raw commit fails. With the client absent it stays fully
dependency-free: small text blobs upload inline, and oversized files return a
clear error. Test servers (custom ``base_url``) always use the raw path.
"""

from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from infrastructure.core.logging.utils import get_logger
from infrastructure.publishing._adapter_http import iter_bundle_files, lazy_session

from .models import HuggingFaceConfig, HuggingFaceResult, HFRepoType

logger = get_logger(__name__)

# Hub rejects very large blobs on the inline (non-LFS) commit path.
_INLINE_BYTE_CEILING = 10 * 1024 * 1024  # 10 MiB

_PUBLIC_HUB_URL = "https://huggingface.co"


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _hub_available() -> bool:
    """True when the optional ``huggingface_hub`` client (the ``publishing`` extra) is importable."""
    try:
        import huggingface_hub  # noqa: F401, PLC0415

        return True
    except ImportError:
        return False


class HuggingFaceHubAdapter:
    """Create-and-commit publisher for the HuggingFace Hub.

    Parameters
    ----------
    config:
        :class:`HuggingFaceConfig`. The token, when absent, is resolved from the
        environment (``HUGGINGFACE_TOKEN`` then ``HF_TOKEN``).
    env:
        Environment mapping for token resolution (defaults to ``os.environ``);
        inject a dict for hermetic tests.
    session:
        Optional ``requests.Session`` for tests. When ``None`` a real session is
        created lazily on the first network call.
    """

    name: str = "huggingface_hub"

    def __init__(
        self,
        config: HuggingFaceConfig,
        *,
        env: dict[str, str] | None = None,
        session: Any | None = None,
    ) -> None:
        source = env if env is not None else dict(os.environ)
        token = config.token or source.get("HUGGINGFACE_TOKEN") or source.get("HF_TOKEN")
        # Re-bind the resolved token without mutating the frozen input.
        self.config = HuggingFaceConfig(
            repo_id=config.repo_id,
            repo_type=config.repo_type,
            token=token,
            private=config.private,
            base_url=config.base_url.rstrip("/"),
            commit_message=config.commit_message,
            timeout=config.timeout,
        )
        self._session_arg = session

    # ------------------------------------------------------------------
    @property
    def _repo_url(self) -> str:
        rt = self.config.repo_type
        prefix = "" if rt is HFRepoType.MODEL else f"{rt.value}s/"
        return f"{self.config.base_url}/{prefix}{self.config.repo_id}"

    # ------------------------------------------------------------------
    def publish(
        self,
        bundle: Path,
        *,
        dry_run: bool = True,
        revision: str = "main",
    ) -> HuggingFaceResult:
        """Create the repo (idempotent) and commit every file in *bundle*.

        Parameters
        ----------
        bundle:
            A single file or a directory tree to upload. Directory layout is
            preserved relative to *bundle*.
        dry_run:
            When ``True`` (default) nothing is sent; a ``"dry-run"`` result lists
            the files that would be uploaded.
        revision:
            Target branch/revision (default ``main``).
        """
        files = iter_bundle_files(bundle)
        rel_names = tuple(str(p.relative_to(bundle if bundle.is_dir() else bundle.parent)) for p in files)

        if dry_run:
            return HuggingFaceResult(
                status="dry-run",
                repo_id=self.config.repo_id,
                repo_type=self.config.repo_type.value,
                url=self._repo_url,
                uploaded=rel_names,
                timestamp_utc=_now_utc_iso(),
                extra={
                    "would_create": f"{self.config.base_url}/api/repos/create",
                    "would_commit": f"{self.config.base_url}/api/"
                    f"{self.config.repo_type.value}s/{self.config.repo_id}/commit/{revision}",
                },
            )

        if not self.config.token:
            return HuggingFaceResult(
                status="error",
                repo_id=self.config.repo_id,
                repo_type=self.config.repo_type.value,
                error="Missing HUGGINGFACE_TOKEN (or HF_TOKEN) credential",
                timestamp_utc=_now_utc_iso(),
            )

        oversized = [n for n, p in zip(rel_names, files) if p.stat().st_size > _INLINE_BYTE_CEILING]
        if oversized:
            if self._should_use_hub():
                return self._publish_via_hub(files, rel_names, revision)
            return HuggingFaceResult(
                status="error",
                repo_id=self.config.repo_id,
                repo_type=self.config.repo_type.value,
                error=(
                    "File(s) exceed the inline (non-LFS) commit ceiling of "
                    f"{_INLINE_BYTE_CEILING} bytes: {oversized}. Route large files "
                    "through Git-LFS, or install the `publishing` extra "
                    "(`uv sync --group publishing`) for automatic huggingface_hub LFS upload."
                ),
                timestamp_utc=_now_utc_iso(),
            )

        import requests  # noqa: PLC0415 — deferred; see module docstring

        headers = {"Authorization": f"Bearer {self.config.token}"}
        session = lazy_session(self)

        try:
            # 1) Create repo (exist_ok semantics: 409 is treated as success).
            namespace, _, name = self.config.repo_id.partition("/")
            create_payload: dict[str, Any] = {
                "type": self.config.repo_type.value,
                "name": name or namespace,
                "private": self.config.private,
            }
            if name:
                create_payload["organization"] = namespace
            create_resp = session.post(
                f"{self.config.base_url}/api/repos/create",
                headers=headers,
                json=create_payload,
                timeout=self.config.timeout,
            )
            if create_resp.status_code not in (200, 201, 409):
                create_resp.raise_for_status()

            # 2) Commit files via the ndjson commit protocol.
            lines = [json.dumps({"key": "header", "value": {"summary": self.config.commit_message, "description": ""}})]
            for rel, path in zip(rel_names, files):
                encoded = base64.b64encode(path.read_bytes()).decode("ascii")
                lines.append(
                    json.dumps({"key": "file", "value": {"path": rel, "content": encoded, "encoding": "base64"}})
                )
            ndjson = "\n".join(lines) + "\n"

            commit_resp = session.post(
                f"{self.config.base_url}/api/{self.config.repo_type.value}s/{self.config.repo_id}/commit/{revision}",
                headers={**headers, "Content-Type": "application/x-ndjson"},
                data=ndjson.encode("utf-8"),
                timeout=self.config.timeout,
            )
            commit_resp.raise_for_status()
            try:
                body = commit_resp.json()
            except ValueError:
                body = {}
            commit_url = body.get("commitUrl") or body.get("commitOid")

            logger.info("HuggingFace Hub published %s (%d files)", self.config.repo_id, len(files))
            return HuggingFaceResult(
                status="ok",
                repo_id=self.config.repo_id,
                repo_type=self.config.repo_type.value,
                url=self._repo_url,
                commit_url=str(commit_url) if commit_url else None,
                uploaded=rel_names,
                timestamp_utc=_now_utc_iso(),
            )
        except requests.RequestException as exc:
            # The raw inline-commit path cannot handle Git-LFS, so the Hub rejects
            # binary blobs (e.g. PDFs) it auto-tracks. When the official client is
            # available on the real Hub, retry the upload through it (auto-LFS).
            if self._should_use_hub():
                hub_result = self._publish_via_hub(files, rel_names, revision)
                if hub_result.status == "ok":
                    return hub_result
            return HuggingFaceResult(
                status="error",
                repo_id=self.config.repo_id,
                repo_type=self.config.repo_type.value,
                error=f"HuggingFace Hub HTTP error: {exc}",
                timestamp_utc=_now_utc_iso(),
            )

    def _should_use_hub(self) -> bool:
        """Escalate to ``huggingface_hub`` only against the real Hub (never test servers)."""
        return _hub_available() and self.config.base_url.rstrip("/") == _PUBLIC_HUB_URL

    def _publish_via_hub(self, files: list[Path], rel_names: tuple[str, ...], revision: str) -> HuggingFaceResult:
        """Upload via the official ``huggingface_hub`` client, which handles Git-LFS."""
        from huggingface_hub import HfApi  # noqa: PLC0415

        api = HfApi(token=self.config.token)
        try:
            api.create_repo(
                repo_id=self.config.repo_id,
                repo_type=self.config.repo_type.value,
                private=self.config.private,
                exist_ok=True,
            )
            commit_url: str | None = None
            for rel, path in zip(rel_names, files):
                info = api.upload_file(
                    path_or_fileobj=str(path),
                    path_in_repo=rel,
                    repo_id=self.config.repo_id,
                    repo_type=self.config.repo_type.value,
                    revision=revision,
                    commit_message=self.config.commit_message,
                )
                commit_url = getattr(info, "commit_url", None) or (str(info) if info else commit_url)
            logger.info("HuggingFace Hub published %s via huggingface_hub (%d files)", self.config.repo_id, len(files))
            return HuggingFaceResult(
                status="ok",
                repo_id=self.config.repo_id,
                repo_type=self.config.repo_type.value,
                url=self._repo_url,
                commit_url=commit_url,
                uploaded=rel_names,
                timestamp_utc=_now_utc_iso(),
                extra={"via": "huggingface_hub"},
            )
        except Exception as exc:  # noqa: BLE001 — surface any client/transport failure as a receipt
            return HuggingFaceResult(
                status="error",
                repo_id=self.config.repo_id,
                repo_type=self.config.repo_type.value,
                error=f"huggingface_hub upload failed: {exc}",
                timestamp_utc=_now_utc_iso(),
            )
