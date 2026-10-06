"""Real pytest execution with nonce-bound complete collection and case evidence."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any

import pytest

from infrastructure.project.public_acceptance_dependencies import MissingRuntimeProvider, capture_runtime_providers
from infrastructure.project.public_acceptance_cases import PYTEST_SPEC_SCHEMA, project_python_hashes, pytest_command
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.project.public_acceptance_scope import MissingRootCasePolicy, RuntimeScope
from infrastructure.project.public_acceptance_evidence import (
    PYTEST_RECEIPT_SCHEMA,
    read_json,
    runtime_identity,
    verify_runtime_execution,
    write_json,
)


class CollectionEvidence:
    """Observe real pytest hooks; preserve failures, skips and deselection explicitly."""

    def __init__(self) -> None:
        self.nodeids: list[str] = []
        self.deselected: list[str] = []
        self.collection_errors: list[str] = []
        self.collection_skips: list[str] = []
        self.reports: dict[str, list[tuple[str, str]]] = {}
        self.reasons: dict[str, str] = {}

    def pytest_collection_finish(self, session: pytest.Session) -> None:
        self.nodeids = [item.nodeid for item in session.items]

    def pytest_deselected(self, items: list[pytest.Item]) -> None:
        self.deselected.extend(item.nodeid for item in items)

    def pytest_collectreport(self, report: pytest.CollectReport) -> None:
        if report.failed:
            self.collection_errors.append(report.nodeid)
        elif report.skipped:
            self.collection_skips.append(report.nodeid)

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        self.reports.setdefault(report.nodeid, []).append((report.when, report.outcome))
        if report.failed or report.skipped:
            self.reasons[report.nodeid] = str(report.longrepr)[-2000:]

    def outcomes(self) -> dict[str, str]:
        """A setup/teardown error cannot be hidden by a successful call."""
        results = {}
        for node in self.nodeids:
            reports = self.reports.get(node, [])
            if any(outcome == "failed" and when != "call" for when, outcome in reports):
                result = "errors"
            elif ("call", "failed") in reports:
                result = "failed"
            elif any(outcome == "skipped" for _, outcome in reports):
                result = "skipped"
            elif ("call", "passed") in reports and ("teardown", "passed") in reports:
                result = "passed"
            else:
                result = "incomplete"
            results[node] = result
        return results


def main(argv: list[str] | None = None) -> int:
    """Execute one declared collection/chunk in the selected current interpreter."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--dependency-spec", type=Path)
    parser.add_argument("--execution-spec", type=Path, required=True)
    parser.add_argument("--execution-spec-sha256", required=True)
    parser.add_argument("pytest_args", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    project = args.project_root.resolve()
    if not project.is_relative_to(root) or args.receipt.exists():
        raise ValueError("pytest scope/receipt must be confined and fresh")
    if re.fullmatch(r"[0-9a-f]{64}", args.execution_spec_sha256) is None:
        parser.error("--execution-spec-sha256 must be its original SHA-256")
    reader = SnapshotReader(root)
    snapshot = reader.read(args.execution_spec.absolute().relative_to(root).as_posix())
    if snapshot.sha256 != args.execution_spec_sha256:
        raise ValueError("pytest execution specification hash differs from its original admission")
    spec = snapshot.json_object()
    admitted_scope = spec.get("scope")
    if not isinstance(admitted_scope, str):
        raise ValueError("pytest execution spec requires its stable source scope")
    resolved = RuntimeScope(root, admitted_scope)
    if resolved.base != project:
        raise ValueError("pytest source scope differs from its admitted execution base")
    os.chdir(project)
    sys.path[:0] = [str(project / "src"), str(project)]
    observer = CollectionEvidence()
    pytest_args = args.pytest_args[1:] if args.pytest_args[:1] == ["--"] else args.pytest_args
    providers = read_json(root, args.dependency_spec) if args.dependency_spec is not None else {}
    before: dict[str, Any] = {}
    after: dict[str, Any] = {}
    artifacts: dict[str, Any] = {}
    diagnostic = ""
    original_exit: int | None = None
    source_before: str | None = None
    source_after: str | None = None
    deliverables_before: str | None = None
    deliverables_after: str | None = None
    hashes_before: dict[str, str] = {}
    hashes_after: dict[str, str] = {}
    scope = resolved.name
    try:
        resolved.require_case_policy(reader)
        selectors, timeout, collect = spec.get("selectors"), spec.get("test_timeout_seconds"), spec.get("collect")
        if (
            spec.get("schema_version") != PYTEST_SPEC_SCHEMA
            or spec.get("root") != str(root)
            or spec.get("scope") != scope
            or spec.get("run_id") != args.run_id
            or spec.get("receipt") != args.receipt.absolute().relative_to(root).as_posix()
            or spec.get("directory") != args.receipt.parent.absolute().relative_to(root).as_posix()
            or not isinstance(spec.get("nonce"), str)
            or not spec["nonce"]
            or type(collect) is not bool
            or type(timeout) is not int
            or timeout <= 0
            or not isinstance(selectors, list)
            or not selectors
            or any(not isinstance(item, str) for item in selectors)
            or not isinstance(spec.get("audit_roots"), list)
            or spec.get("runtime") != runtime_identity()
            or spec.get("dependency_providers") != providers
        ):
            raise ValueError("pytest execution spec differs from its actual child admission")
        command = pytest_command(
            Path(sys.executable),
            root,
            args.receipt.parent.absolute(),
            args.run_id,
            scope,
            args.receipt.absolute(),
            args.execution_spec.absolute(),
            selectors,
            spec_sha256=args.execution_spec_sha256,
            collect=collect,
            test_timeout=timeout,
            audit_roots=tuple(Path(item) for item in spec["audit_roots"]),
        )
        if pytest_args != list(command[command.index("--") + 1 :]):
            raise ValueError("actual pytest arguments differ from the source-owned execution spec")
        source_before = resolved.source_identity()
        deliverables_before = resolved.deliverables_identity()
        hashes_before = project_python_hashes(root, scope)
        if (
            source_before != spec.get("source_identity")
            or deliverables_before != spec.get("deliverables_identity")
            or hashes_before != spec.get("source_hashes")
        ):
            raise ValueError("pytest consumed source differs from its admitted source hashes")
        before, artifacts = capture_runtime_providers(
            root,
            providers,
            args.receipt.parent / (args.receipt.stem + "-dependencies"),
            retain_metadata=True,
        )
        original_exit = int(pytest.main(pytest_args, plugins=[observer]))
        exit_code = original_exit
        after, _ = capture_runtime_providers(root, providers, args.receipt.parent, retain_metadata=False)
        if before != after:
            raise ValueError("actual installed provider changed during pytest execution")
        verify_runtime_execution(project, root=root, scope=scope)
        source_after = resolved.source_identity()
        deliverables_after = resolved.deliverables_identity()
        hashes_after = project_python_hashes(root, scope)
        if (
            source_after != source_before
            or deliverables_after != deliverables_before
            or hashes_after != hashes_before
            or not reader.unchanged()
        ):
            raise ValueError("pytest source or execution spec changed during the actual child")
    except (MissingRuntimeProvider, MissingRootCasePolicy) as exc:
        exit_code, diagnostic = original_exit if original_exit in (130, 124) else 75, str(exc)
    except (OSError, ValueError, RuntimeError, ImportError) as exc:
        exit_code, diagnostic = original_exit if original_exit in (130, 124) else 1, str(exc)
    payload: dict[str, Any] = {
        "schema_version": PYTEST_RECEIPT_SCHEMA,
        "run_id": args.run_id,
        "nonce": spec.get("nonce"),
        "spec_artifact": {"path": snapshot.relative, "sha256": snapshot.sha256},
        "receipt": args.receipt.absolute().relative_to(root).as_posix(),
        "scope": scope,
        "source_identity_before": source_before,
        "source_identity_after": source_after,
        "deliverables_identity_before": deliverables_before,
        "deliverables_identity_after": deliverables_after,
        "source_hashes_before": hashes_before,
        "source_hashes_after": hashes_after,
        "pytest_exit_code": original_exit,
        "exit_code": exit_code,
        "runtime": runtime_identity(),
        "nodeids": observer.nodeids,
        "deselected": observer.deselected,
        "collection_errors": observer.collection_errors,
        "collection_skips": observer.collection_skips,
        "outcomes": observer.outcomes(),
        "reasons": observer.reasons,
        "dependency_custody": {scope: {"before": before.get(scope), "after": after.get(scope)} for scope in providers},
        "dependency_artifacts": artifacts,
        "diagnostic": diagnostic,
    }
    write_json(root, args.receipt, payload)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
