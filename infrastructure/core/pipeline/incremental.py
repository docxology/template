"""Opt-in content-bound stage reuse.

Cache schema versions are independent of platform releases. Reuse requires an
exact contract, recursive input/source/configuration/tool identity, and validated
stable output bytes. Unsupported or malformed records are misses. Cleanup,
publication, and live effects are excluded by the resolved plan.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.core.pipeline.artifacts import declared_output_paths
from infrastructure.core.pipeline.types import StageContract
from infrastructure.core.pipeline.fingerprints import (
    canonical_digest,
    paths_digest,
    source_fingerprint,
    tool_reuse_refusal,
)
from infrastructure.core.files.secure_write import atomic_write_text_confined, read_text_confined
from infrastructure.core.pipeline.execution_environment import effective_environment_identity
from infrastructure.core.pipeline.artifact_contracts import declared_input_paths

logger = get_logger(__name__)

#: Manifest location, relative to ``output/``.
INCREMENTAL_MANIFEST_RELPATH = Path(".pipeline") / "incremental.json"

#: Sentinel mixed into the hash for declared-but-missing input files. Keeps the
#: hash deterministic (and distinct from an empty/zero-byte file) without raising.
CACHE_SCHEMA_VERSION = 3
_MANIFEST_READ_BUDGET = 1024 * 1024


@dataclass(frozen=True)
class IncrementalConfig:
    """Opt-in configuration for content-hash stage skipping.

    Attributes:
        enabled: Master switch. ``False`` (default) means the feature is
            completely inert — the executor behaves exactly as before.
    """

    enabled: bool = False


@dataclass(frozen=True)
class StageHashRecord:
    """One stage's recorded input/output hashes from a prior run."""

    input_hash: str
    output_hash: str


@dataclass(frozen=True)
class SkipDecision:
    """Result of :func:`should_skip_stage`.

    Attributes:
        skip: Whether the stage may be skipped.
        input_hash: The freshly computed input hash (``""`` when not computed,
            i.e. when the feature is disabled).
    """

    skip: bool
    input_hash: str = ""


class HashManifest:
    """Mutable in-memory map of stage name -> :class:`StageHashRecord`.

    Persisted as a small JSON document under ``output/.pipeline/incremental.json``.
    """

    def __init__(self, records: dict[str, StageHashRecord] | None = None) -> None:
        self._records: dict[str, StageHashRecord] = dict(records or {})

    def get(self, stage_name: str) -> StageHashRecord | None:
        """Get a cached value, or None if not present."""
        return self._records.get(stage_name)

    def record(self, stage_name: str, *, input_hash: str, output_hash: str) -> None:
        """Record a result in the store."""
        self._records[stage_name] = StageHashRecord(input_hash=input_hash, output_hash=output_hash)

    def output_hashes(self) -> dict[str, str]:
        """Return ``{stage_name: output_hash}`` for all recorded stages."""
        return {name: rec.output_hash for name, rec in self._records.items()}

    def to_dict(self) -> dict[str, object]:
        """Serialize this object to a plain dict for JSON output."""
        return {
            "version": CACHE_SCHEMA_VERSION,
            "stages": {
                name: {"input_hash": rec.input_hash, "output_hash": rec.output_hash}
                for name, rec in sorted(self._records.items())
            },
        }


# -- Manifest read/write -----------------------------------------------------


def _manifest_path(output_dir: Path) -> Path:
    return output_dir / INCREMENTAL_MANIFEST_RELPATH


def load_hash_manifest(output_dir: Path) -> HashManifest:
    """Load the hash manifest for a project ``output/`` directory.

    Fail-safe: a missing, unreadable, or malformed manifest yields an empty
    manifest (so every stage looks "unseen" and therefore re-runs).
    """
    path = _manifest_path(output_dir)
    try:
        payload = json.loads(read_text_confined(output_dir, path, max_bytes=_MANIFEST_READ_BUDGET))
    except FileNotFoundError:
        return HashManifest()
    except (OSError, ValueError, RecursionError) as exc:
        logger.warning("Ignoring unreadable incremental manifest %s: %s", path, exc)
        return HashManifest()
    if (
        not isinstance(payload, dict)
        or type(payload.get("version")) is not int
        or payload["version"] != CACHE_SCHEMA_VERSION
    ):
        return HashManifest()
    stages = payload.get("stages", {})
    if not isinstance(stages, dict):
        return HashManifest()
    records: dict[str, StageHashRecord] = {}
    for name, row in stages.items():
        if not isinstance(name, str) or not name or not isinstance(row, dict):
            return HashManifest()
        input_hash = row.get("input_hash")
        output_hash = row.get("output_hash")
        if not all(
            isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)
            for value in (input_hash, output_hash)
        ):
            return HashManifest()
        assert isinstance(input_hash, str) and isinstance(output_hash, str)
        records[name] = StageHashRecord(input_hash=input_hash, output_hash=output_hash)
    return HashManifest(records)


def save_hash_manifest(output_dir: Path, manifest: HashManifest) -> None:
    """Persist the hash manifest deterministically (sorted keys, trailing newline)."""
    path = _manifest_path(output_dir)
    atomic_write_text_confined(output_dir, path, json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n")


# -- Path resolution ---------------------------------------------------------


def _resolve_input_paths(repo_root: Path, project_dir: Path, contract: StageContract) -> tuple[Path, ...]:
    """Resolve declared ``input_artifacts`` to absolute paths.

    Reuses the same rendering rules as declared outputs so ``{project}``
    placeholders and ``projects/``/``output/`` prefixes resolve identically.
    """
    return declared_input_paths(repo_root, project_dir, contract)


def _hash_paths(paths: tuple[Path, ...], *, output_roots: tuple[Path, ...] = ()) -> str:
    """Hash recursive contents, additions, deletions, and renames."""
    return paths_digest(paths, output_roots=output_roots)


# -- Public hashing API ------------------------------------------------------


def compute_stage_input_hash(
    *,
    repo_root: Path,
    project_dir: Path,
    stage_name: str,
    contract: StageContract,
    upstream_output_hashes: dict[str, str],
    execution_identity: str = "",
    mode: str | None = None,
) -> str:
    """Compute a deterministic input hash for a stage.

    The hash folds in: the stage name, the content hash of declared input
    artifacts, and the recorded output hashes of dependency stages
    (``upstream_output_hashes``). Any change to those flips the hash.
    """
    from dataclasses import asdict

    return canonical_digest(
        {
            "stage": stage_name,
            "contract": asdict(contract),
            "inputs": _hash_paths(
                _resolve_input_paths(repo_root, project_dir, contract), output_roots=(project_dir / "output",)
            ),
            "source": source_fingerprint(repo_root, project_dir),
            "environment": effective_environment_identity(repo_root, project_dir, mode=mode),
            "execution": execution_identity,
            "upstream": {key: value for key, value in upstream_output_hashes.items() if key != stage_name},
        }
    )


def compute_stage_output_hash(
    *,
    repo_root: Path,
    project_dir: Path,
    contract: StageContract,
) -> str:
    """Compute a deterministic content hash over a stage's declared outputs."""
    return paths_digest(
        declared_output_paths(repo_root, project_dir, contract),
        stable_output=True,
        output_roots=(project_dir / "output",),
    )


def declared_outputs_present(
    *,
    repo_root: Path,
    project_dir: Path,
    contract: StageContract,
) -> bool:
    """True only when the stage declares >=1 output and every one exists.

    A stage with no declared outputs cannot be proven complete, so it returns
    ``False`` (never skippable) — the fail-safe default.
    """
    paths = declared_output_paths(repo_root, project_dir, contract)
    if not paths:
        return False
    return all(path.exists() and not path.is_symlink() for path in paths)


def should_skip_stage(
    *,
    config: IncrementalConfig,
    manifest: HashManifest,
    repo_root: Path,
    project_dir: Path,
    stage_name: str,
    contract: StageContract,
    execution_identity: str = "",
    stage_script: str | None = None,
    mode: str | None = None,
) -> SkipDecision:
    """Decide whether a stage may be skipped under incremental mode.

    Returns ``SkipDecision(skip=False)`` immediately when the feature is
    disabled (the default), so every selected stage executes. When enabled, the
    stage is skippable only when the recorded input hash matches, all declared
    outputs are present, AND the current output hash matches the recorded one.
    """
    if not config.enabled:
        return SkipDecision(skip=False)
    if contract.mutable_artifacts:
        return SkipDecision(skip=False)
    from infrastructure.core.runtime.python_binding import is_analysis_capability

    if is_analysis_capability(stage_name, stage_script):
        return SkipDecision(skip=False)
    if tool_reuse_refusal(repo_root, project_dir) is not None:
        return SkipDecision(skip=False)

    # Transitive invalidation is carried by declared-input *content*: a downstream
    # stage declares the upstream's output file as its own input, so when the
    # upstream output changes the downstream input hash changes too. We therefore
    # do not fold the (run-order-dependent) recorded upstream hashes in here —
    # doing so would make record-time and check-time asymmetric and re-run
    # stages whose own inputs are unchanged.
    input_hash = compute_stage_input_hash(
        repo_root=repo_root,
        project_dir=project_dir,
        stage_name=stage_name,
        contract=contract,
        upstream_output_hashes={},
        execution_identity=execution_identity,
        mode=mode,
    )
    record = manifest.get(stage_name)
    if record is None or record.input_hash != input_hash:
        return SkipDecision(skip=False, input_hash=input_hash)
    if not declared_outputs_present(repo_root=repo_root, project_dir=project_dir, contract=contract):
        # Fail-safe: matching hash but a declared output is absent -> re-run.
        return SkipDecision(skip=False, input_hash=input_hash)
    current_output = compute_stage_output_hash(
        repo_root=repo_root,
        project_dir=project_dir,
        contract=contract,
    )
    if record.output_hash != current_output:
        # Recorded input matched but the declared outputs were rewritten or swapped.
        return SkipDecision(skip=False, input_hash=input_hash)
    return SkipDecision(skip=True, input_hash=input_hash)


def record_stage_hash(
    *,
    manifest: HashManifest,
    repo_root: Path,
    project_dir: Path,
    stage_name: str,
    contract: StageContract,
    upstream_output_hashes: dict[str, str],
    input_hash: str | None = None,
    execution_identity: str = "",
    mode: str | None = None,
) -> None:
    """Record a stage's input and output hashes into the manifest.

    ``input_hash`` may be passed to reuse a value already computed by
    :func:`should_skip_stage`; otherwise it is computed here.
    """
    if input_hash is None:
        input_hash = compute_stage_input_hash(
            repo_root=repo_root,
            project_dir=project_dir,
            stage_name=stage_name,
            contract=contract,
            upstream_output_hashes=upstream_output_hashes,
            execution_identity=execution_identity,
            mode=mode,
        )
    output_hash = compute_stage_output_hash(repo_root=repo_root, project_dir=project_dir, contract=contract)
    manifest.record(stage_name, input_hash=input_hash, output_hash=output_hash)


__all__ = [
    "INCREMENTAL_MANIFEST_RELPATH",
    "HashManifest",
    "IncrementalConfig",
    "SkipDecision",
    "StageHashRecord",
    "compute_stage_input_hash",
    "compute_stage_output_hash",
    "declared_outputs_present",
    "load_hash_manifest",
    "record_stage_hash",
    "save_hash_manifest",
    "should_skip_stage",
]
