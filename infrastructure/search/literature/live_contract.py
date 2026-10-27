"""Fresh, bounded acceptance evidence for unpaid literature capabilities."""

from __future__ import annotations

import hashlib
import importlib
import json
import re
import sys
import time
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infrastructure.core.implementation_custody import (
    capture_dependency_custody,
    capture_implementation_custody,
    runtime_identity,
    source_file_manifest,
    source_file_digest,
    source_file_bytes,
    verify_fresh_module_bytecode,
)


class LiteratureBlocked(RuntimeError):
    """A declared unpaid service, installed model, or deadline is unavailable."""


class LiteratureFailed(ValueError):
    """A responding producer violated a source, format, or domain contract."""


def write_json(path: Path, value: Any) -> None:
    """Write finite JSON with stable bytes for subsequent custody checks."""
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def sha256(raw: bytes) -> str:
    """Identify the exact consumed bytes."""
    return hashlib.sha256(raw).hexdigest()


def exact_json(raw: str | bytes) -> Any:
    """Reject duplicate keys, nonfinite constants, and surrounding prose."""

    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in rows:
            if key in result:
                raise LiteratureFailed(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def constant(value: str) -> Any:
        raise LiteratureFailed(f"nonfinite JSON constant: {value}")

    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    except (ValueError, UnicodeError) as exc:
        raise LiteratureFailed(f"invalid strict JSON: {exc}") from exc


@dataclass(frozen=True)
class LiveSettings:
    """Explicit ceilings; selecting a live lane never acquires models or credentials."""

    model: str
    endpoint: str = "http://127.0.0.1:11434"
    max_results: int = 3
    timeout_seconds: int = 60
    run_timeout_seconds: int = 600
    num_predict: int = 1024

    def __post_init__(self) -> None:
        from infrastructure.llm.core.local_ollama import validate_local_endpoint

        if not isinstance(self.model, str) or not self.model.strip() or len(self.model) > 128:
            raise LiteratureFailed("an explicit installed local model is required")
        validate_local_endpoint(self.endpoint)
        for key, low, high in (
            ("max_results", 1, 5),
            ("timeout_seconds", 1, 60),
            ("run_timeout_seconds", 1, 600),
            ("num_predict", 64, 2048),
        ):
            value = getattr(self, key)
            if type(value) is not int or not low <= value <= high:
                raise LiteratureFailed(f"{key} must be an exact integer in [{low}, {high}]")


def implementation_custody() -> dict[str, Any]:
    """Capture actual checkout/wheel custody and the trusted launcher's cache binding."""
    prefix = Path(sys.pycache_prefix) if sys.pycache_prefix is not None else None
    return capture_implementation_custody(fresh_pycache_prefix=prefix)


def _platform_manifest(custody: dict[str, Any]) -> dict[str, str]:
    """Project a just-observed custody record; this formatter admits no source."""
    result = {"platform/" + key: value for key, value in custody["files"].items()}
    selected = custody["distribution"]
    if selected is not None:
        result["platform/distribution/METADATA"] = selected["metadata_sha256"]
        result["platform/distribution/RECORD"] = selected["record_sha256"]
    return result


def platform_manifest() -> dict[str, str]:
    """Bind actual source and selected distribution records without fictional wheel files."""
    return _platform_manifest(implementation_custody())


def environment_identity() -> dict[str, Any]:
    """Describe the selected installed interpreter without acquiring dependencies."""
    return runtime_identity()


def verify_platform(
    expected: dict[str, str],
    environment: dict[str, Any],
    custody: dict[str, Any] | None = None,
    *,
    fresh_prefix: Path | None = None,
) -> None:
    """Reject stale loaded code, altered installed records, and a different worker runtime."""
    prefix = Path(sys.pycache_prefix) if sys.pycache_prefix is not None else None
    selected_prefix = fresh_prefix or prefix
    # One new observation supplies all three comparisons at this boundary. A
    # supplied full contract retains the shared verifier's exact normalization;
    # no observation is retained or reused across callers or later boundaries.
    actual = capture_implementation_custody(fresh_pycache_prefix=selected_prefix if custody is not None else prefix)
    if custody is not None:
        required = dict(custody, bytecode_binding="fresh-owned-prefix") if selected_prefix is not None else custody
        if actual != required:
            raise ValueError("public implementation, distribution, bytecode binding or runtime changed")
    if _platform_manifest(actual) != expected or actual["runtime_environment"] != environment:
        raise LiteratureFailed("platform source or runtime environment changed across workers")


def source_manifest(project_root: Path, *, active_source_root: Path | None = None) -> dict[str, str]:
    """Reject source-directory links before selecting source/configuration/data suffixes."""
    result = platform_manifest()
    for prefix, directory, suffixes in (
        ("project/src/", project_root / "src", frozenset({".py"})),
        ("project/data/", project_root / "data", frozenset({".json", ".jsonl", ".yaml"})),
    ):
        result.update({prefix + key: value for key, value in source_file_manifest(directory, suffixes).items()})
    for name in ("pyproject.toml", "manuscript/config.yaml"):
        result["project/" + name] = source_file_digest(project_root / name)
    if active_source_root is not None:
        bytecode_prefix = Path(sys.pycache_prefix) if sys.pycache_prefix is not None else None
        if bytecode_prefix is not None:
            verify_fresh_module_bytecode(active_source_root, bytecode_prefix)
        result.update(
            {
                "active-producer/" + key: value
                for key, value in source_file_manifest(active_source_root, frozenset({".py"})).items()
            }
        )
        project = active_source_root.parent if active_source_root.name == "src" else active_source_root.parent.parent
        scripts = project / "scripts"
        if scripts.is_dir() and (project / "pyproject.toml").is_file():
            if bytecode_prefix is not None:
                verify_fresh_module_bytecode(scripts, bytecode_prefix)
            result.update(
                {
                    "active-controller/" + key: value
                    for key, value in source_file_manifest(scripts, frozenset({".py"})).items()
                }
            )
    for name, custody in declared_dependency_custody(
        project_root, expected_metadata_sha256=result["project/pyproject.toml"]
    ).items():
        result.update({"dependency/" + name + "/" + key: value for key, value in custody["files"].items()})
        selected = custody["distribution"]
        if selected is not None:
            result["dependency/" + name + "/METADATA"] = selected["metadata_sha256"]
            result["dependency/" + name + "/RECORD"] = selected["record_sha256"]
    return result


def declared_dependency_custody(project_root: Path, *, expected_metadata_sha256: str | None = None) -> dict[str, Any]:
    """Bind the explicitly declared canonical literature engine when this producer uses it."""
    raw = source_file_bytes(project_root / "pyproject.toml")
    if expected_metadata_sha256 is not None and sha256(raw) != expected_metadata_sha256:
        raise LiteratureFailed("project dependency declaration changed while consumed")
    project = tomllib.loads(raw.decode("utf-8"))["project"]
    selected = [
        value
        for value in project.get("dependencies", [])
        if isinstance(value, str) and value.startswith("template-literature-meta-analysis==")
    ]
    if not selected:
        return {}
    if len(selected) != 1:
        raise LiteratureFailed("the canonical literature engine needs one exact declared version")
    module = importlib.import_module("template_literature_meta_analysis")
    if module.__file__ is None:
        raise LiteratureFailed("the canonical literature engine has no actual source location")
    source = Path(module.__file__).absolute().parent
    candidate = source.parent
    checkout = candidate if source.name == "src" and (candidate / "pyproject.toml").is_file() else None
    prefix = Path(sys.pycache_prefix) if sys.pycache_prefix is not None else None
    custody = capture_dependency_custody(
        "template-literature-meta-analysis", source, checkout_root=checkout, fresh_pycache_prefix=prefix
    )
    version = selected[0].split("==", 1)[1]
    if custody["distribution"] is not None and custody["distribution"]["version"] != version:
        raise LiteratureFailed("the selected literature engine differs from its exact declared dependency")
    if checkout is not None:
        metadata_bytes = source_file_bytes(checkout / "pyproject.toml")
        if sha256(metadata_bytes) != custody["files"]["checkout/pyproject.toml"]:
            raise LiteratureFailed("dependency declaration changed while consumed")
        actual = tomllib.loads(metadata_bytes.decode("utf-8"))["project"]["version"]
        if actual != version:
            raise LiteratureFailed("the literature engine checkout differs from its declared version")
    return {"template-literature-meta-analysis": custody}


class LiveSession:
    """Own only one fresh ignored run directory; never replace publication evidence."""

    def __init__(
        self,
        project_root: Path,
        directory: Path,
        settings: LiveSettings,
        capabilities: list[str],
        *,
        active_source_root: Path | None = None,
    ) -> None:
        self.root = project_root.absolute()
        base = self.root / "output/.pipeline/literature_acceptance"
        raw = directory if directory.is_absolute() else self.root / directory
        if ".." in raw.parts:
            raise LiteratureFailed("run directory cannot contain parent traversal")
        for path in (raw, *raw.parents):
            if path.is_symlink():
                raise LiteratureFailed("run directory cannot contain symlinks")
        self.directory = raw.resolve()
        if self.directory == base.resolve() or not self.directory.is_relative_to(base.resolve()):
            raise LiteratureFailed("live evidence must use a fresh child of output/.pipeline/literature_acceptance")
        if self.directory.exists():
            raise LiteratureFailed("live evidence directory already exists")
        self.settings = settings
        self.active_source_root = active_source_root
        self.started = time.monotonic()
        self.deadline = self.started + settings.run_timeout_seconds
        self.sources = source_manifest(self.root, active_source_root=active_source_root)
        self.implementation = implementation_custody()
        self.dependencies = declared_dependency_custody(
            self.root, expected_metadata_sha256=self.sources["project/pyproject.toml"]
        )
        self.platform_sources = platform_manifest()
        self.environment = environment_identity()
        verify_platform(self.platform_sources, self.environment, self.implementation)
        self.directory.mkdir(parents=True)
        self.consumed: dict[str, str] = {}
        self.frozen_inputs: dict[str, str] = {}
        self._frozen_input_bytes: dict[str, bytes] = {}
        self.receipt: dict[str, Any] = {
            "schema_version": "template/literature-unpaid-acceptance/1",
            "project": self.root.name,
            "execution_mode": "live-unpaid",
            "status": "running",
            "capabilities": capabilities,
            "paid_integrations": False,
            "run_deadline_seconds": settings.run_timeout_seconds,
            "request_deadline_seconds": settings.timeout_seconds,
            "python_executable": sys.executable,
            "python_version": sys.version.split()[0],
            "source_manifest": self.sources,
            "runtime_environment": self.environment,
            "implementation_custody": self.implementation,
            "declared_dependencies": self.dependencies,
            "frozen_project_inputs": self.frozen_inputs,
            "loaded_implementation_verified": True,
            "producer_results": {},
            "issues": [],
        }
        write_json(self.directory / "receipt.json", self.receipt)

    def freeze_project_input(self, relative: str) -> Path:
        """Retain an owned snapshot of bytes admitted by the initial source manifest."""
        name = Path(relative)
        if name.is_absolute() or ".." in name.parts:
            raise LiteratureFailed("frozen project input must stay inside the declared project")
        key = "project/" + name.as_posix()
        expected = self.sources.get(key)
        if expected is None:
            raise LiteratureFailed("project input is absent from the admitted public source manifest")
        raw = source_file_bytes(self.root / name)
        if sha256(raw) != expected:
            raise LiteratureFailed("project input changed before consumption")
        destination = self.directory / "inputs" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            if source_file_bytes(destination) != raw:
                raise LiteratureFailed("frozen project input changed between consumers")
        else:
            destination.write_bytes(raw)
        self.consume(destination, raw)
        self.frozen_inputs[name.as_posix()] = expected
        self._frozen_input_bytes[name.as_posix()] = raw
        return destination

    def freeze_project_input_bytes(self, relative: str) -> bytes:
        """Return exact immutable admitted bytes for a parser, without reopening its snapshot."""
        self.freeze_project_input(relative)
        return self._frozen_input_bytes[Path(relative).as_posix()]

    def timeout(self) -> int:
        """Respect the request ceiling and the remaining whole-run budget."""
        value = min(self.settings.timeout_seconds, int(self.deadline - time.monotonic()))
        if value < 1:
            raise LiteratureBlocked("whole-run literature acceptance deadline exhausted")
        return value

    def consume(self, path: Path, raw: bytes | None = None) -> bytes:
        """Bind exactly the bytes used by a parser/model, then recheck them at finalization."""
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(self.directory):
            raise LiteratureFailed("consumed artifact must be a regular file inside this run")
        content = path.read_bytes() if raw is None else raw
        key = str(path.relative_to(self.directory))
        digest = sha256(content)
        if key in self.consumed and self.consumed[key] != digest:
            raise LiteratureFailed(f"artifact changed between consumers: {key}")
        self.consumed[key] = digest
        return content

    def finalize(self, status: str, *, issue: str | None = None) -> Path:
        """Fail closed on partial producers, source drift, and consumed-byte replacement."""
        if status not in {"passed", "failed", "blocked"}:
            raise LiteratureFailed("unknown final acceptance status")
        if issue:
            self.receipt["issues"].append(issue)
        try:
            verify_platform(self.platform_sources, self.environment, self.implementation)
            source_unchanged = source_manifest(self.root, active_source_root=self.active_source_root) == self.sources
        except ValueError, LiteratureBlocked, OSError:
            source_unchanged = False
        try:
            artifact_manifest = source_file_manifest(
                self.directory, frozenset(path.suffix for path in self.directory.rglob("*") if path.is_file())
            )
            custody_unchanged = all(artifact_manifest.get(key) == digest for key, digest in self.consumed.items())
        except ValueError, OSError:
            artifact_manifest, custody_unchanged = {}, False
        if not source_unchanged or not custody_unchanged:
            status = "failed"
            self.receipt["issues"].append("source or consumed artifact changed during acceptance")
        results = self.receipt["producer_results"]
        if status == "passed" and any(
            results.get(name, {}).get("status") != "passed" for name in self.receipt["capabilities"]
        ):
            status = "failed"
            self.receipt["issues"].append("a required producer is absent, partial, or unsuccessful")
        if status == "passed" and time.monotonic() >= self.deadline:
            status = "blocked"
            self.receipt["issues"].append("whole-run deadline exceeded before final acceptance")
        artifacts = {key: value for key, value in artifact_manifest.items() if key != "receipt.json"}
        if status == "passed" and time.monotonic() >= self.deadline:
            status = "blocked"
            self.receipt["issues"].append("whole-run deadline exceeded during final custody checks")
        self.receipt.update(
            status=status,
            source_unchanged=source_unchanged,
            consumed_unchanged=custody_unchanged,
            consumed_artifacts=self.consumed,
            artifacts=artifacts,
            elapsed_seconds=time.monotonic() - self.started,
        )
        path = self.directory / "receipt.json"
        write_json(path, self.receipt)
        finished = time.monotonic()
        if status == "passed" and finished >= self.deadline:
            self.receipt.update(status="blocked", elapsed_seconds=finished - self.started)
            self.receipt["issues"].append("whole-run deadline exceeded during receipt promotion")
            write_json(path, self.receipt)
        return path


def safe_slug(value: str) -> str:
    """Bounded artifact component independent of provider-controlled paths."""
    return re.sub(r"[^a-zA-Z0-9_-]", "_", value)[:80] or "record"
