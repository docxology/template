"""Complete, source-declared module partition for ordinary hosted infrastructure CI.

These selection records describe ordinary CI's existing marker-filtered suite.
They do not classify Root release obligations or authorize a Platform 4 release.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path, PurePosixPath
from typing import Any

from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.core.pipeline.fingerprints import canonical_digest, tree_records
from infrastructure.core.testing.pytest_marker_exprs import build_pytest_marker_expression
from infrastructure.project.public_capabilities import CANONICAL_CI_PYTHON_VERSIONS

SHARD_COUNT = 4
SCHEMA = "template-ordinary-infra-ci-selection-v1"
# The retained C4 timings identify these expensive families. No case is removed.
RESERVED_MODULES = {
    "tests/infra_tests/core/pipeline/test_run_matrix.py": 0,
    "tests/infra_tests/core/pipeline/test_shared_runtime_namespace.py": 1,
    "tests/infra_tests/core/test_execution_contract.py": 2,
    "tests/infra_tests/project/test_root_acceptance.py": 3,
}
INFRA_MARKERS = build_pytest_marker_expression(
    skip_requires_ollama=True,
    skip_slow=True,
    skip_bench=True,
    skip_long_running=False,
    skip_private_project=False,
    skip_external_fixture=False,
)
RECEIPT_DIR = Path("output/readiness/ordinary-infra-ci")


def ci_matrix() -> dict[str, list[dict[str, object]]]:
    """Keep the existing four OS/minor pairs and partition each completely."""
    environments = [("ubuntu-latest", version) for version in CANONICAL_CI_PYTHON_VERSIONS]
    environments.append(("macos-latest", CANONICAL_CI_PYTHON_VERSIONS[-1]))
    return {
        "include": [
            {"os": os_name, "python-version": version, "shard": shard}
            for os_name, version in environments
            for shard in range(SHARD_COUNT)
        ]
    }


def _shard(value: object) -> int:
    if type(value) is not int or not 0 <= value < SHARD_COUNT:
        raise ValueError(f"infrastructure shard must be an integer in [0, {SHARD_COUNT})")
    return value


def case_module(node_id: str) -> str:
    """Require the actual collected identity to belong to the declared suite."""
    if type(node_id) is not str or "::" not in node_id or "\0" in node_id:
        raise ValueError("infrastructure partition requires canonical collected node IDs")
    module = node_id.split("::", 1)[0]
    # Parametrization IDs legitimately escape bytes and newlines with
    # backslashes (``[co_code-\x97...]``); only the module path must be POSIX.
    if "\\" in module:
        raise ValueError("infrastructure partition requires canonical collected node IDs")
    path = PurePosixPath(module)
    if (
        path.is_absolute()
        or path.as_posix() != module
        or ".." in path.parts
        or len(path.parts) < 3
        or path.parts[:2] != ("tests", "infra_tests")
        or path.suffix != ".py"
    ):
        raise ValueError(f"collected infrastructure node ID escapes declared suite: {node_id}")
    return module


def module_shard(module: str) -> int:
    """Assign every module; unknown future modules receive a stable assignment."""
    case_module(module + "::partition-admission")
    reserved = RESERVED_MODULES.get(module)
    if reserved is not None:
        return reserved
    return int.from_bytes(hashlib.sha256(module.encode()).digest()[:8], "big") % SHARD_COUNT


def partition(node_ids: list[str] | tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
    """Reject empty/duplicate inventory, preserving every real selected case."""
    if not node_ids or len(set(node_ids)) != len(node_ids):
        raise ValueError("infrastructure collection must be nonempty and have unique node IDs")
    shards: list[list[str]] = [[] for _ in range(SHARD_COUNT)]
    for node_id in sorted(node_ids):
        shards[module_shard(case_module(node_id))].append(node_id)
    return tuple(tuple(shard) for shard in shards)


def selection_source(root: Path) -> str:
    """Bind selection to actual infra/entrypoint/test/policy bytes, not mtimes.

    This is a bounded ordinary-CI selection identity, not a full public project
    source or artifact acceptance record. Mature tree traversal rejects links
    and observes additions, removals and renamed source entries.
    """
    records: dict[str, object] = {
        directory: tree_records(root / directory, source=True) for directory in ("infrastructure", "scripts", "tests")
    }
    # Root and tests conftest/helper source participates in actual collection
    # and execution, even though the selected cases live in tests/infra_tests.
    records["conftest.py"] = tree_records(root / "conftest.py", source=True)
    for name in ("pyproject.toml", "uv.lock", ".github/workflows/ci.yml"):
        records[name] = hashlib.sha256(read_bytes_confined(root, root / name, max_bytes=16 * 1024 * 1024)).hexdigest()
    return canonical_digest(records)


def receipt_path(root: Path, shard: int) -> Path:
    return root / RECEIPT_DIR / f"shard-{_shard(shard)}.json"


def selected_runtime() -> str:
    return f"{sys.version_info.major}.{sys.version_info.minor}"


def validate_receipts(values: list[dict[str, Any]], *, expected_source: str, expected_runtime: str) -> tuple[str, ...]:
    """Refuse incomplete, duplicate, stale, overlapping or altered selections."""
    if len(values) != SHARD_COUNT:
        raise ValueError("coverage merge requires every declared infrastructure shard")
    seen: set[int] = set()
    full: tuple[str, ...] | None = None
    for value in values:
        shard = _shard(value.get("shard"))
        if shard in seen:
            raise ValueError("duplicate infrastructure shard receipt")
        seen.add(shard)
        node_ids = value.get("all_node_ids")
        assigned = value.get("assigned_node_ids")
        if not isinstance(node_ids, list) or not all(type(node) is str for node in node_ids):
            raise ValueError("invalid infrastructure collection receipt")
        expected = partition(node_ids)
        canonical = tuple(sorted(node_ids))
        if full is not None and full != canonical:
            raise ValueError("infrastructure shards disagree on complete selected collection")
        full = canonical
        if (
            value.get("schema_version") != SCHEMA
            or value.get("shard_count") != SHARD_COUNT
            or value.get("source_sha256") != expected_source
            or value.get("python_minor") != expected_runtime
            or value.get("marker_expression") != INFRA_MARKERS
            or type(value.get("original_pytest_exit_code")) is not int
            or value.get("original_pytest_exit_code") != 0
            or type(value.get("exit_code")) is not int
            or value.get("exit_code") != 0
            or value.get("complete") is not True
            or value.get("diagnostics") != []
            or not expected[shard]
            or assigned != list(expected[shard])
            or value.get("completed_node_ids") != list(expected[shard])
        ):
            raise ValueError("infrastructure selection receipt is incomplete, stale or incompatible")
    assert full is not None
    return full


def read_receipt(root: Path, path: Path) -> dict[str, Any]:
    value = json.loads(read_bytes_confined(root, path, max_bytes=32 * 1024 * 1024))
    if not isinstance(value, dict):
        raise ValueError("infrastructure receipt must be an object")
    return value


__all__ = [
    "SHARD_COUNT",
    "SCHEMA",
    "RESERVED_MODULES",
    "INFRA_MARKERS",
    "RECEIPT_DIR",
    "ci_matrix",
    "case_module",
    "module_shard",
    "partition",
    "selection_source",
    "receipt_path",
    "selected_runtime",
    "validate_receipts",
    "read_receipt",
]
