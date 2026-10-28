"""Actual Root collection metadata, without invoking fixtures or test cases."""

from __future__ import annotations

import hashlib
import inspect
import sysconfig
from collections import defaultdict
from pathlib import Path
from typing import Any

import pytest

from infrastructure.project.public_acceptance_case_policy import CENSUS_SCHEMA, digest
from infrastructure.project.public_acceptance_pytest import CollectionEvidence
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def _value(value: object) -> object:
    """Keep marker metadata finite and portable; never serialize object reprs."""
    if value is None or type(value) in (bool, int):
        return value
    if isinstance(value, str):
        return {"type": "source-bound-string"}
    if type(value) is float:
        return {"type": "float", "value": str(value)}
    if isinstance(value, (list, tuple)):
        return [_value(item) for item in value]
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise ValueError("marker metadata requires explicit textual keys")
        return {key: _value(item) for key, item in value.items()}
    return {"type": "opaque-source-bound"}


def _policy_metadata(value: object) -> object:
    """Keep runtime provider bytes in observation, not cross-runtime source policy.

    The independent producer/reader authenticates each selected runtime provider's
    exact bytes. Policy metadata binds the stable origin path; public source SHA
    remains exact. This avoids claiming that Python 3.12 and 3.14 have equal bytes.
    """
    if isinstance(value, dict):
        scope = value.get("scope")
        runtime = isinstance(scope, str) and scope in {"runtime-site", "runtime-stdlib"}
        return {key: _policy_metadata(item) for key, item in value.items() if key != "sha256" or not runtime}
    if isinstance(value, list):
        return [_policy_metadata(item) for item in value]
    return value


def _nonpublic(value: object) -> bool:
    if isinstance(value, dict):
        scope = value.get("scope")
        return (
            isinstance(scope, str)
            and scope in {"inadmissible-nonpublic", "unresolved"}
            or any(_nonpublic(item) for item in value.values())
        )
    return isinstance(value, list) and any(_nonpublic(item) for item in value)


class RootCaseObserver(CollectionEvidence):
    """Record true inherited declarations and resolved fixture definitions.

    Public paths are admitted by the caller's confined Python-source manifest.
    Nonpublic source paths/content never enter the public metadata. Actual
    process/spec/runtime/provider/bytecode custody belongs to the producer and
    independent receipt reader, not this pytest observation hook.
    """

    def __init__(self, reader: SnapshotReader, source_hashes: dict[str, str]) -> None:
        super().__init__()
        self.reader = reader
        self.root = reader.root
        self.source_hashes = dict(source_hashes)
        self.cases: list[dict[str, Any]] = []
        self.executed_reports = 0
        self._origins: dict[str, dict[str, str]] = {}
        self.runtime_roots = tuple(
            Path(sysconfig.get_path(name)).resolve() for name in ("purelib", "platlib", "stdlib")
        )

    def _origin(self, value: object) -> dict[str, str]:
        if not isinstance(value, (str, Path)):
            return {"scope": "unresolved"}
        path = Path(value).absolute()
        actual = path.resolve(strict=True)
        cached = self._origins.get(str(path))
        if cached is not None:
            return dict(cached)
        if path == actual and actual.is_relative_to(self.root):
            relative = actual.relative_to(self.root).as_posix()
            if relative in self.source_hashes:
                snapshot = self.reader.read(relative)
                if snapshot.sha256 != self.source_hashes[relative]:
                    raise ValueError("Root case source changed during collection observation")
                result = {"scope": "public-owned", "path": relative, "sha256": snapshot.sha256}
                self._origins[str(path)] = result
                return dict(result)
        for index, base in enumerate(self.runtime_roots):
            if actual.is_relative_to(base):
                # Selected providers and these bytes must be authenticated by
                # the independent caller. Exclude interpreter-specific paths.
                result = {
                    "scope": "runtime-site" if index < 2 else "runtime-stdlib",
                    "path": actual.relative_to(base).as_posix(),
                    "sha256": hashlib.sha256(actual.read_bytes()).hexdigest(),
                }
                self._origins[str(path)] = result
                return dict(result)
        return {"scope": "inadmissible-nonpublic"}

    def _object_origin(self, value: object) -> dict[str, str]:
        try:
            if inspect.ismodule(value) or inspect.isclass(value):
                return self._origin(inspect.getsourcefile(value))
            if callable(value):
                return self._origin(inspect.getsourcefile(inspect.unwrap(value)))
            return {"scope": "unresolved"}
        except OSError, TypeError, ValueError:
            return {"scope": "unresolved"}

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        self.executed_reports += 1
        super().pytest_runtest_logreport(report)

    def pytest_collection_finish(self, session: pytest.Session) -> None:
        super().pytest_collection_finish(session)
        for item in session.items:
            if not isinstance(item, pytest.Function) or item.parent is None:
                raise ValueError("Root case census requires genuine Python function items with parents")
            function = item.getparent(pytest.Module)
            cls = item.getparent(pytest.Class)
            callspec = getattr(item, "callspec", None)
            parameter = callspec.id if callspec is not None else None
            original = getattr(item, "originalname", None) or item.name
            family = item.parent.nodeid + "::" + original
            markers = []
            for parent, marker in item.iter_markers_with_node():
                arguments = _value(marker.args)
                # Source identity binds the actual predicate. Its evaluated
                # boolean varies when required fixtures/platforms are prepared.
                if marker.name == "skipif" and isinstance(arguments, list):
                    arguments = [{"type": "source-conditioned-bool"} if type(arg) is bool else arg for arg in arguments]
                markers.append(
                    {
                        "name": marker.name,
                        "args": arguments,
                        "kwargs": _value(marker.kwargs),
                        "inherited_from": parent.nodeid,
                        "origin": self._origin(getattr(parent, "path", None)),
                    }
                )
            fixtures = {}
            for name in item.fixturenames:
                definitions = item._fixtureinfo.name2fixturedefs.get(name, ())
                fixtures[name] = [
                    {
                        "scope": definition.scope,
                        "baseid": definition.baseid,
                        "dependencies": list(definition.argnames),
                        "origin": self._object_origin(definition.func),
                    }
                    for definition in definitions
                ]
            self.cases.append(
                {
                    "family": family,
                    "nodeid": item.nodeid,
                    "parameter_id": parameter,
                    "parameter_names": sorted(callspec.params) if callspec is not None else [],
                    "function_origin": self._object_origin(item.obj),
                    "module_origin": self._object_origin(function.obj)
                    if function is not None
                    else {"scope": "unresolved"},
                    "class_origin": self._object_origin(cls.obj) if cls is not None else None,
                    "markers": markers,
                    "fixtures": fixtures,
                }
            )

    def census(self, *, source_identity: str, runtime: str, platform: str) -> dict[str, Any]:
        """Normalize a complete real collection; no marker-based classification."""
        if (
            not self.nodeids
            or self.collection_errors
            or self.collection_skips
            or self.deselected
            or self.executed_reports
            or len(set(self.nodeids)) != len(self.nodeids)
            or [case["nodeid"] for case in self.cases] != self.nodeids
            or not self.reader.unchanged()
        ):
            raise ValueError("Root case census is empty, partial, filtered, executed or source-stale")
        families: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for case in self.cases:
            origin = case["function_origin"]
            if origin.get("scope") != "public-owned" or not origin["path"].startswith("tests/"):
                raise ValueError("Root case function does not originate in its public test source")
            families[case["family"]].append(case)
        rows = []
        for family, cases in sorted(families.items()):
            cases = sorted(cases, key=lambda case: case["nodeid"])
            hashes = {case["function_origin"]["sha256"] for case in cases}
            if len(hashes) != 1:
                raise ValueError("Root case family source differs between parameter members")
            rows.append(
                {
                    "id": family,
                    "members": [{"nodeid": case["nodeid"], "parameter_id": case["parameter_id"]} for case in cases],
                    "source_sha256": hashes.pop(),
                    "metadata_sha256": digest(_policy_metadata(cases)),
                    "markers": sorted({mark["name"] for case in cases for mark in case["markers"]}),
                    "public_closure": not any(_nonpublic(case) for case in cases),
                }
            )
        return {
            "schema_version": CENSUS_SCHEMA,
            "source_identity": source_identity,
            "runtime": runtime,
            "platform": platform,
            "families": rows,
            "nodeids": sorted(self.nodeids),
        }


__all__ = ["RootCaseObserver"]
