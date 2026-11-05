"""Fixed live GitHub transport; credential DATA never grants receipt authority."""

from __future__ import annotations

import hashlib
import math
import os
import sys
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Iterator

from infrastructure.core.execution_boundary import build_bounded_env, run_bounded_subprocess
from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.project.public_acceptance_evidence import evidence_directory, write_json
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.release_readiness_snapshot import json_object_from_bytes

_PENDING: ContextVar[_ReaderCredentials | None] = ContextVar("fixed_hosted_reader_credentials", default=None)
_KEY = object()


class _ReaderCredentials:
    def __init__(self, value: str | None, key: object) -> None:
        if key is not _KEY:
            raise ValueError("hosted credentials require the fixed reader entry")
        self._value = value
        self._pid = os.getpid()
        self.source: Any = None
        self.deadline: float | None = None
        self.active = True

    def environment(self, root: Path, deadline: float, selected: dict[str, str]) -> dict[str, str]:
        if not self.active or self._pid != os.getpid() or self.source is None or self.deadline is None:
            raise ValueError("hosted credential nomination lacks its admitted reader Source")
        if root != self.source.bindings.current_root or deadline > self.deadline:
            raise ValueError("hosted credentials differ from their reader Source/clock")
        return {**selected, **({"GH_TOKEN": self._value} if self._value else {})}


@contextmanager
def reader_credential_nomination() -> Iterator[None]:
    """Remove ambient credential DATA before the fixed reader performs any work."""
    if _PENDING.get() is not None:
        raise ValueError("fixed reader cannot replace an existing credential nomination")
    held = _ReaderCredentials(os.environ.pop("GH_TOKEN", None), _KEY)
    token = _PENDING.set(held)
    try:
        yield
    finally:
        held.active = False
        held._value = None
        _PENDING.reset(token)


def bind_reader_credentials(source: Any, *, deadline: float) -> None:
    """Bind only after genuine Source admission, never from transported JSON."""
    from infrastructure.reporting.native_source_external_admission import NativeSourceContext

    held = _PENDING.get()
    if type(source) is not NativeSourceContext or held is None or held.source is not None:
        raise ValueError("fixed hosted reader requires its genuine admitted Source and private nomination")
    source.verify_correspondence(source.reference, source.bindings.current_root, source.current_source_reader, deadline)
    held.source = source
    held.deadline = deadline


class _FixedHostedApi:
    def __init__(
        self,
        root: Path,
        directory: Path,
        repository: str,
        run_id: int,
        head: str,
        deadline: float,
        environment: dict[str, str],
    ) -> None:
        from infrastructure.project.public_hosted_origin import _context

        _context(repository, run_id, head)
        if any(part in {".", ".."} for part in repository.split("/")):
            raise ValueError("hosted repository segments must be literal owner and repository names")
        if type(deadline) not in (int, float) or not math.isfinite(deadline):
            raise ValueError("fixed hosted API requires the existing finite absolute deadline")
        remaining(deadline)
        self.root, self.directory = root, evidence_directory(root, directory)
        if not self.directory.is_dir() or self.directory.is_symlink():
            raise ValueError("fixed hosted API requires an existing physical evidence directory")
        self.repository, self.run_id, self.head, self.deadline = repository, run_id, head, deadline
        self._selected = build_bounded_env(environment)
        held = _PENDING.get()
        # A reader-owned executor keeps the owner, never a copied secret that
        # could outlive its lexical nomination. Standalone public collectors
        # retain their explicit input only for this fixed live API executor.
        self._credentials = held
        self._nominated = environment.get("GH_TOKEN") if held is None else None
        if held is not None:
            held.environment(root, deadline, self._selected)
        self._used: set[str] = set()

    def _execute(self, command: list[str], label: str) -> tuple[dict[str, Any], dict[str, str]]:
        from infrastructure.project.public_hosted_origin import _process

        from infrastructure.project.public_hosted_origin import DOWNLOAD_SCRIPT, WORKFLOW, _api_command
        import re

        api_command = command
        if command[:4] == [sys.executable, "-I", "-c", DOWNLOAD_SCRIPT]:
            if len(command) < 6 or Path(command[4]).parent != self.directory:
                raise ValueError("fixed hosted wrapper lacks its confined destination")
            api_command = command[5:]
        endpoint = api_command[-1] if api_command else ""
        prefix = f"repos/{self.repository}"
        allowed = (
            endpoint in {f"{prefix}/actions/runs/{self.run_id}", f"{prefix}/contents/{WORKFLOW}?ref={self.head}"}
            or re.fullmatch(
                re.escape(prefix)
                + rf"/actions/(?:artifacts/[1-9][0-9]*(?:/zip)?|runs/{self.run_id}/"
                + r"(?:artifacts|jobs)\?per_page=100&page=[1-9][0-9]*)",
                endpoint,
            )
            is not None
        )
        if not allowed or api_command != _api_command(endpoint):
            raise ValueError("fixed hosted executor refuses arbitrary commands, hosts or endpoints")
        if command is not api_command and not endpoint.endswith("/zip"):
            raise ValueError("fixed hosted wrapper is only for an exact artifact ZIP")
        if label in self._used:
            raise ValueError("fixed hosted API refuses duplicate original operations")
        if self._credentials is not None:
            if _PENDING.get() is not self._credentials:
                raise ValueError("fixed hosted executor outlived its admitted reader credential owner")
            environment = self._credentials.environment(self.root, self.deadline, self._selected)
        else:
            environment = {**self._selected, **({"GH_TOKEN": self._nominated} if self._nominated else {})}
        self._used.add(label)
        result = run_bounded_subprocess(
            command,
            cwd=self.root,
            env=environment,
            guardian_env=self._selected,
            timeout=remaining(self.deadline),
            capture_output=True,
        )
        raw = {
            "command": command,
            "exit_code": result.returncode,
            "original_exit_code": result.original_returncode,
            "timed_out": result.timed_out,
            "custody_refused": result.custody_refused,
            "diagnostic": result.command_error,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
        binding = write_json(self.root, self.directory / (label + "-process.json"), raw)
        _process(raw, command)
        return raw, binding

    def _json(self, endpoint: str, label: str) -> tuple[dict[str, Any], dict[str, str]]:
        from infrastructure.project.public_hosted_origin import _api_command

        raw, binding = self._execute(_api_command(endpoint), label)
        return json_object_from_bytes(raw["stdout"].encode()), binding

    def run_metadata(self) -> tuple[dict[str, Any], dict[str, str]]:
        return self._json(f"repos/{self.repository}/actions/runs/{self.run_id}", "run")

    def workflow_metadata(self) -> tuple[dict[str, Any], dict[str, str]]:
        from infrastructure.project.public_hosted_origin import WORKFLOW

        return self._json(f"repos/{self.repository}/contents/{WORKFLOW}?ref={self.head}", "workflow")

    def artifact_metadata(self, artifact_id: int) -> tuple[dict[str, Any], dict[str, str]]:
        self._positive(artifact_id)
        return self._json(f"repos/{self.repository}/actions/artifacts/{artifact_id}", f"metadata-{artifact_id}")

    @staticmethod
    def _positive(value: int) -> None:
        if type(value) is not int or value <= 0:
            raise ValueError("fixed hosted API requires a positive integer identity")

    def _page(self, page: int, category: str) -> tuple[dict[str, Any], dict[str, str]]:
        from infrastructure.project.public_hosted_origin import MAX_LISTING_PAGES

        self._positive(page)
        if page > MAX_LISTING_PAGES:
            raise ValueError("hosted API page exceeds its existing finite bound")
        return self._json(
            f"repos/{self.repository}/actions/runs/{self.run_id}/{category}?per_page=100&page={page}",
            ("listing" if category == "artifacts" else "jobs") + f"-{page}",
        )

    def artifact_page(self, page: int) -> tuple[dict[str, Any], dict[str, str]]:
        return self._page(page, "artifacts")

    def job_page(self, page: int) -> tuple[dict[str, Any], dict[str, str]]:
        return self._page(page, "jobs")

    def download_artifact(self, artifact_id: int, destination: Path) -> tuple[bytes, dict[str, str]]:
        from infrastructure.project.public_hosted_origin import DOWNLOAD_SCRIPT, MAX_ARCHIVE, _api_command

        self._positive(artifact_id)
        if destination.parent != self.directory or destination.exists() or destination.is_symlink():
            raise ValueError("fixed hosted download requires one fresh confined evidence file")
        command = [
            sys.executable,
            "-I",
            "-c",
            DOWNLOAD_SCRIPT,
            str(destination),
            *_api_command(f"repos/{self.repository}/actions/artifacts/{artifact_id}/zip"),
        ]
        raw, binding = self._execute(command, f"artifact-{artifact_id}")
        content = read_bytes_confined(self.root, destination, max_bytes=MAX_ARCHIVE)
        if json_object_from_bytes(raw["stdout"].encode()) != {
            "original_exit_code": 0,
            "archive_sha256": hashlib.sha256(content).hexdigest(),
        }:
            raise ValueError("fixed hosted download differs from its actual original bytes")
        return content, binding


def fixed_hosted_api(
    root: Path,
    directory: Path,
    *,
    repository: str,
    run_id: int,
    head_sha: str,
    deadline: float,
    environment: dict[str, str],
) -> _FixedHostedApi:
    """Construct only a live fixed executor, never an original from retained DATA."""
    return _FixedHostedApi(root, directory, repository, run_id, head_sha, deadline, environment)
