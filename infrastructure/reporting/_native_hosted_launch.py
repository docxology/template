"""One lexical credential route for the actual fixed installed Source reader."""

from __future__ import annotations

import hashlib
import os
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Iterator

from infrastructure.project.public_reference_git import remaining

_ACTIVE: ContextVar[_ReaderLaunch | None] = ContextVar("actual_fixed_hosted_reader_launch", default=None)
_KEY = object()


class _ReaderLaunch:
    def __init__(self, key: object, prepared: Any, command: tuple[str, ...], environment: dict[str, str]) -> None:
        if key is not _KEY:
            raise ValueError("hosted reader route requires the actual fixed preparation factory")
        self.prepared, self.command = prepared, command
        self._environment = dict(environment)
        self._owner_pid, self._active, self._used = os.getpid(), True, False
        self._custody: dict[str, Any] | None = None

    def select(
        self,
        directory: Path,
        name: str,
        arguments: list[str],
        cwd: Path,
        environment: dict[str, str],
        deadline: float,
        purpose: str,
    ) -> None:
        if (
            not self._active
            or _ACTIVE.get() is not self
            or self._used
            or os.getpid() != self._owner_pid
            or directory != self.prepared.evidence
            or (name, *arguments) != self.command
            or cwd != self.prepared.current_root
            or environment != self._environment
            or deadline != self.prepared.deadline
            or purpose != "actual-native-reader"
        ):
            raise ValueError("hosted reader route differs from its one actual fixed Source launch")
        remaining(deadline)
        self._used = True

    def capture(
        self, selected: dict[str, str], bounded: dict[str, str], token: str
    ) -> tuple[dict[str, str], dict[str, Any]]:
        from infrastructure.reporting.native_environment_custody import _capture_hosted_reader_environment

        if not self._used or not self._active or _ACTIVE.get() is not self:
            raise ValueError("hosted reader environment lacks its actual selected fixed launch")
        actual = {
            **bounded,
            **({"GH_TOKEN": self._environment["GH_TOKEN"]} if self._environment.get("GH_TOKEN") else {}),
        }
        self._custody = _capture_hosted_reader_environment(self._environment, selected, bounded, actual, token)
        return actual, self._custody

    def validate_result(self, result: dict[str, Any]) -> None:
        from infrastructure.reporting.native_environment_custody import _validate_hosted_reader_environment

        if (
            not self._active
            or _ACTIVE.get() is not self
            or self._custody is None
            or result.get("environment_custody") != self._custody
        ):
            raise ValueError("fixed hosted reader lost its direct original environment observation")
        _validate_hosted_reader_environment(self._custody, self._environment)


def _arguments(prepared: Any, arguments: tuple[str, ...], implementation: Path, raw: bytes) -> None:
    repeated = {"--provider-wheel", "--office-font-file", "--receipt", "--root-receipt", "--auxiliary-receipt"}
    allowed = repeated | {
        "--repo-root",
        "--revision",
        "--current-analysis-root",
        "--repository",
        "--run-id",
        "--sdk-package-root",
        "--implementation-input",
        "--implementation-sha256",
        "--pdfium-site",
        "--pdfium-wheel",
        "--epubcheck-jar",
        "--java-executable",
        "--mermaid-package-root",
        "--mermaid-dependency-root",
        "--mermaid-node-executable",
        "--mermaid-chrome-executable",
        "--operation-started-monotonic",
        "--timeout",
        "--acceptance-artifact-id",
        "--acceptance-receipt-sha256",
    }
    values: dict[str, str] = {}
    index = 0
    while index < len(arguments):
        flag = arguments[index]
        if flag in {"--stage-bundle", "--help"}:
            if flag in values:
                raise ValueError("fixed hosted reader refuses repeated flags")
            values[flag] = "present"
            index += 1
            continue
        if flag not in allowed or index + 1 >= len(arguments) or flag in values and flag not in repeated:
            raise ValueError("fixed hosted reader arguments differ from its Source CLI")
        values[flag] = arguments[index + 1]
        index += 2
    expected = {
        "--repo-root": str(prepared.current_root),
        "--revision": prepared.source_commit,
        "--sdk-package-root": str(prepared.sdk_package_root),
        "--implementation-input": str(implementation),
        "--implementation-sha256": hashlib.sha256(raw).hexdigest(),
    }
    if any(values.get(key) != value for key, value in expected.items()):
        raise ValueError("fixed hosted reader differs from its concrete verified preparation")
    if (
        float(values.get("--operation-started-monotonic", "nan")) + int(values.get("--timeout", "0"))
        != prepared.deadline
    ):
        raise ValueError("fixed hosted reader cannot restart its actual prepared deadline")


@contextmanager
def fixed_prepared_reader_launch(
    prepared: Any,
    implementation: Path,
    raw: bytes,
    *,
    roots: tuple[Path, ...],
    closure: Path,
    body: str,
    arguments: tuple[str, ...],
    environment: dict[str, str],
) -> Iterator[_ReaderLaunch]:
    """Construct from real verified preparation and exact Source reader Code only."""
    from infrastructure.core.implementation_custody import source_file_bytes
    from infrastructure.reporting.native_installed_preparation import NativePreparedRuntime
    from infrastructure.reporting.native_source_provider_bootstrap import (
        NATIVE_READER_MODULE,
        format_selected_sdk_native_bootstrap,
    )

    if type(prepared) is not NativePreparedRuntime or _ACTIVE.get() is not None:
        raise ValueError("fixed hosted reader requires its actual independently verified prepared runtime")
    prepared.verify()
    if source_file_bytes(implementation) != raw:
        raise ValueError("fixed hosted reader selected implementation changed")
    _arguments(prepared, arguments, implementation, raw)
    if (
        closure != prepared.evidence / "reader-code"
        or closure != closure.resolve(strict=True)
        or not closure.is_dir()
        or any(closure.iterdir())
    ):
        raise ValueError("fixed hosted reader requires its fresh actual parent-held Code directory")
    identity = closure.stat().st_dev, closure.stat().st_ino
    expected_body = format_selected_sdk_native_bootstrap(
        source_file_bytes(prepared.sdk_package_root / "core/bytecode_audit.py"),
        prepared.sdk_package_root,
        roots,
        implementation,
        hashlib.sha256(raw).hexdigest(),
        closure,
        identity,
        prepared.deadline,
        required_worker_module=NATIVE_READER_MODULE,
    )
    if body != expected_body:
        raise ValueError("fixed hosted reader must execute the actual admitted Source bootstrap")
    route = _ReaderLaunch(_KEY, prepared, (str(prepared.python), "-I", "-c", body, *arguments), environment)
    token = _ACTIVE.set(route)
    try:
        yield route
    finally:
        route._active = False
        route._environment.clear()
        _ACTIVE.reset(token)


def current_fixed_reader_launch(
    directory: Path,
    name: str,
    arguments: list[str],
    *,
    cwd: Path,
    environment: dict[str, str],
    deadline: float,
    purpose: str,
) -> _ReaderLaunch | None:
    """Private supervisor read; ordinary callers cannot nominate a privileged route."""
    route = _ACTIVE.get()
    if route is not None:
        route.select(directory, name, arguments, cwd, environment, deadline, purpose)
    return route
