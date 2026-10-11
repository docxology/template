"""Source-owned exact Root census specifications and confined evidence validation."""

from __future__ import annotations

import json
import re
import sys
import sysconfig
from pathlib import Path
from typing import Any, cast

from infrastructure.core.implementation_custody import (
    capture_implementation_custody,
    source_file_digest,
    verify_implementation_custody,
)
from infrastructure.project.public_acceptance_cases import project_python_hashes
from infrastructure.project.public_acceptance_evidence import bootstrap_command, evidence_directory, runtime_identity
from infrastructure.project.public_acceptance_scope import RuntimeScope
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader

SPEC_SCHEMA = "template-root-census-spec-v2"


RECEIPT_SCHEMA = "template-root-census-receipt-v2"


PROCESS_SCHEMA = "template-root-census-process-v2"

COORDINATOR_SCHEMA = "template-root-census-coordinator-v2"


_SPEC_FIELDS = {
    "schema_version",
    "root",
    "directory",
    "run_id",
    "nonce",
    "test_files",
    "source_identity",
    "source_hashes",
    "runtime",
    "runtime_locations",
    "timeout_seconds",
    "implementation",
    "root_identity",
}


def root_python_hashes(root: Path, reader: SnapshotReader) -> dict[str, str]:
    """Bind Root and any canonical public exemplar sources admitted to collection."""
    hashes = project_python_hashes(root, "root", reader)
    for name in PUBLIC_PROJECT_NAMES:
        project = root / "projects" / name
        if project.exists():
            hashes.update(project_python_hashes(root, name, reader))
    if not reader.unchanged():
        raise ValueError("public Python source changed during census admission")
    return dict(sorted(hashes.items()))


def _root_identity(root: Path) -> list[int]:
    current = root.stat()
    return [current.st_dev, current.st_ino]


def _fresh_prefix() -> Path | None:
    return Path(sys.pycache_prefix) if sys.pycache_prefix else None


def _runtime_locations() -> dict[str, str]:
    return {name: str(Path(sysconfig.get_path(name)).resolve()) for name in ("purelib", "platlib", "stdlib")}


def census_command(root: Path, directory: Path, binding: dict[str, str], *, origin: Any = None) -> tuple[str, ...]:
    """Reconstruct the exact isolated source-owned collection worker invocation."""
    if root / binding["path"] != directory / "census-spec.json":
        raise ValueError("canonical census command requires its exact admitted specification path")
    launch = (
        (lambda module, *args: origin.bootstrap(root, module, *args))
        if origin
        else (lambda module, *args: bootstrap_command(Path(sys.executable), root, module, *args))
    )
    return launch(
        "infrastructure.project.public_root_case_census",
        "--root",
        str(root),
        "--worker-spec",
        str(root / binding["path"]),
        "--spec-sha256",
        binding["sha256"],
    )


def coordinator_command(
    root: Path, directory: Path, timeout: int, run_id: str, nonce: str, *, origin: Any = None
) -> tuple[str, ...]:
    """Supervise admission, collection and readback inside one finite boundary."""
    launch = (
        (lambda module, *args: origin.bootstrap(root, module, *args))
        if origin
        else (lambda module, *args: bootstrap_command(Path(sys.executable), root, module, *args))
    )
    return launch(
        "infrastructure.project.public_root_case_census",
        "--root",
        str(root),
        "--directory",
        str(directory),
        "--timeout-seconds",
        str(timeout),
        "--coordinator-run",
        run_id,
        "--coordinator-nonce",
        nonce,
    )


def _json(snapshot: ArtifactSnapshot) -> dict[str, Any]:
    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in rows:
            if key in result:
                raise ValueError("Root case evidence has duplicate JSON fields")
            result[key] = value
        return result

    def nonfinite(value: str) -> object:
        raise ValueError("Root case evidence has a nonfinite JSON constant")

    value = json.loads(snapshot.content, object_pairs_hook=pairs, parse_constant=nonfinite)
    if not isinstance(value, dict):
        raise ValueError("Root case evidence must be a finite JSON object")
    from infrastructure.project.public_root_census_encoding import ENCODING_SCHEMAS, decode

    if value.get("schema_version") in ENCODING_SCHEMAS:
        decoded: dict[str, Any] = decode(value)
        value = decoded
        if value.get("schema_version") != RECEIPT_SCHEMA or value.get("role") != "canonical-collection-only":
            raise ValueError("compact encoding may contain only original canonical census observations")
    return cast(dict[str, Any], value)


def _spec(
    reader: SnapshotReader, snapshot: ArtifactSnapshot, *, reader_context: bool = False, origin: Any = None
) -> dict[str, Any]:
    spec = _json(snapshot)
    root = reader.root
    resolved = RuntimeScope(root, "root")
    directory = spec.get("directory")
    if (
        set(spec) != _SPEC_FIELDS
        or spec["schema_version"] != SPEC_SCHEMA
        or spec["root"] != str(origin.root if origin else root)
        or not isinstance(spec["root_identity"], list)
        or any(type(item) is not int for item in spec["root_identity"])
        or spec["root_identity"] != (origin.identity if origin else _root_identity(root))
        or not isinstance(spec["implementation"], dict)
        or not isinstance(directory, str)
        or not isinstance(spec["run_id"], str)
        or re.fullmatch(r"[0-9a-f]{32}", spec["run_id"]) is None
        or not isinstance(spec["nonce"], str)
        or re.fullmatch(r"[0-9a-f]{32}", spec["nonce"]) is None
        or type(spec["timeout_seconds"]) is not int
        or not 1 <= spec["timeout_seconds"] <= 3600
        or spec["test_files"] != list(resolved.test_files())
        or not spec["test_files"]
        or spec["source_identity"] != resolved.source_identity()
        or spec["source_hashes"] != root_python_hashes(root, reader)
        or spec["runtime"] != (origin.runtime if origin else runtime_identity())
        or spec["runtime"]["missing"]
        or spec["runtime_locations"] != (origin.locations if origin else _runtime_locations())
    ):
        raise ValueError("canonical Root census specification differs from source/runtime/full selection")
    expected = spec["implementation"]
    if expected.get("bytecode_binding") != "fresh-owned-prefix":
        raise ValueError("original canonical census requires its audited worker bytecode binding")
    prefix = _fresh_prefix()
    if origin:
        if expected != origin.implementation:
            raise ValueError("portable original audited implementation changed")
    elif reader_context:
        # A plain independent reader has its own loaded baseline. This label
        # cannot replace or waive the original audited worker launch contract.
        actual = capture_implementation_custody(fresh_pycache_prefix=prefix)
        if actual != dict(expected, bytecode_binding=actual["bytecode_binding"]):
            raise ValueError("canonical reader implementation, distribution or selected runtime changed")
    else:
        if prefix is None:
            raise ValueError("canonical census workers require their actual fresh audited launcher")
        verify_implementation_custody(expected, fresh_pycache_prefix=prefix)
    destination = evidence_directory(root, root / directory)
    if snapshot.path != destination / "census-spec.json" or not reader.unchanged():
        raise ValueError("canonical Root census specification path or source changed")
    return spec


def _pytest_arguments(root: Path, directory: Path, files: list[str]) -> list[str]:
    return [
        "-c",
        str(root / "pyproject.toml"),
        "--rootdir",
        str(root),
        "--confcutdir",
        str(root),
        "-o",
        "addopts=",
        "-o",
        "python_files=test_*.py *_test.py",
        "--import-mode=importlib",
        "--strict-markers",
        "--assert=plain",
        "--collect-only",
        "--no-cov",
        "-p",
        "no:cacheprovider",
        "--benchmark-storage=" + str(directory / "benchmarks"),
        "--basetemp=" + str(directory / "pytest-tmp"),
        "-q",
        "--tb=short",
        *files,
    ]


def _artifact(reader: SnapshotReader, binding: object) -> ArtifactSnapshot:
    if not isinstance(binding, dict) or set(binding) != {"path", "sha256"}:
        raise ValueError("census evidence requires an exact original artifact binding")
    snapshot = reader.read(binding["path"])
    if snapshot.sha256 != binding["sha256"]:
        raise ValueError("original census evidence hash changed")
    return snapshot


def _origin(origin: object, hashes: dict[str, str], locations: dict[str, str], *, context: Any = None) -> None:
    if not isinstance(origin, dict) or set(origin) != {"scope", "path", "sha256"}:
        raise ValueError("census source origin is unresolved, nonpublic or malformed")
    scope, relative, expected = origin["scope"], origin["path"], origin["sha256"]
    if (
        not isinstance(relative, str)
        or Path(relative).is_absolute()
        or any(part in ("", ".", "..") for part in relative.split("/"))
        or "\\" in relative
        or "\0" in relative
    ):
        raise ValueError("census provider origin is not an exact confined relative file")
    if scope == "public-owned":
        if hashes.get(relative) != expected:
            raise ValueError("census origin differs from current public source bytes")
    elif scope in {"runtime-site", "runtime-stdlib"}:
        if context:
            context.provider(scope, relative, expected)
            return
        choices = ("purelib", "platlib") if scope == "runtime-site" else ("stdlib",)
        matches = False
        for key in choices:
            try:
                matches = matches or source_file_digest(Path(locations[key]) / relative) == expected
            except FileNotFoundError:
                continue
        if not matches:
            raise ValueError("census fixture provider differs from selected runtime bytes")
    else:
        raise ValueError("nonpublic provider cannot authorize public Root collection")
