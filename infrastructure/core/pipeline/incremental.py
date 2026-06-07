"""Content-hash stage skipping for the pipeline (INCREMENTAL-PIPELINE-1).

This module lets the executor SKIP a stage whose declared inputs have not
changed since a previous successful run, instead of re-running every stage on
every invocation.

DEFAULT-OFF / OPT-IN contract
-----------------------------
The feature is gated entirely on :class:`IncrementalConfig.enabled`, which
defaults to ``False``. When disabled:

- :func:`should_skip_stage` always returns "do not skip";
- the executor never reads or writes the hash manifest;
- execution is byte-identical to today — every stage runs.

So with no opt-in, nothing about the default pipeline path changes.

How skipping is decided (only when enabled)
-------------------------------------------
For each stage the executor:

1. Computes a deterministic *input hash* over the stage's declared
   ``input_artifacts`` (file contents) PLUS the recorded *output hashes* of the
   stages it depends on (``upstream_output_hashes``) PLUS the stage name.
2. Skips the stage ONLY when ALL of the following hold:
   - a hash was previously recorded for this stage, AND
   - the recorded input hash equals the freshly computed one, AND
   - the stage declares at least one output, AND
   - every declared output file currently exists (fail-safe).
3. Otherwise runs the stage and records the new input hash plus an output hash
   computed over the (now present) declared outputs.

Invalidation is transitive without any explicit dependency walk: because a
downstream stage's input hash folds in its upstream stages' recorded *output*
hashes, mutating an upstream input changes the upstream output, which changes
the recorded upstream output hash, which changes the downstream input hash —
so the downstream stage re-runs as well.

Determinism
-----------
Hashes are SHA-256 over a canonical, sorted serialization of declared paths and
their byte contents. No wall-clock or randomness enters any recorded artifact.

Part of the infrastructure layer (Layer 1) — reusable across all projects.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.core.pipeline.artifacts import _declared_output_paths
from infrastructure.core.pipeline.types import StageContract

logger = get_logger(__name__)

#: Manifest location, relative to ``output/``.
INCREMENTAL_MANIFEST_RELPATH = Path(".pipeline") / "incremental.json"

#: Sentinel mixed into the hash for declared-but-missing input files. Keeps the
#: hash deterministic (and distinct from an empty/zero-byte file) without raising.
_MISSING_INPUT_SENTINEL = b"\x00<missing>\x00"


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
        return self._records.get(stage_name)

    def record(self, stage_name: str, *, input_hash: str, output_hash: str) -> None:
        self._records[stage_name] = StageHashRecord(input_hash=input_hash, output_hash=output_hash)

    def output_hashes(self) -> dict[str, str]:
        """Return ``{stage_name: output_hash}`` for all recorded stages."""
        return {name: rec.output_hash for name, rec in self._records.items()}

    def to_dict(self) -> dict[str, object]:
        return {
            "version": 1,
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
    if not path.exists():
        return HashManifest()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Ignoring unreadable incremental manifest %s: %s", path, exc)
        return HashManifest()
    if not isinstance(payload, dict):
        return HashManifest()
    stages = payload.get("stages", {})
    if not isinstance(stages, dict):
        return HashManifest()
    records: dict[str, StageHashRecord] = {}
    for name, row in stages.items():
        if not isinstance(name, str) or not isinstance(row, dict):
            continue
        input_hash = row.get("input_hash")
        output_hash = row.get("output_hash")
        if isinstance(input_hash, str) and isinstance(output_hash, str):
            records[name] = StageHashRecord(input_hash=input_hash, output_hash=output_hash)
    return HashManifest(records)


def save_hash_manifest(output_dir: Path, manifest: HashManifest) -> None:
    """Persist the hash manifest deterministically (sorted keys, trailing newline)."""
    path = _manifest_path(output_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


# -- Path resolution ---------------------------------------------------------


def _resolve_input_paths(repo_root: Path, project_dir: Path, contract: StageContract) -> tuple[Path, ...]:
    """Resolve declared ``input_artifacts`` to absolute paths.

    Reuses the same rendering rules as declared outputs so ``{project}``
    placeholders and ``projects/``/``output/`` prefixes resolve identically.
    """
    proxy = StageContract(output_artifacts=contract.input_artifacts)
    return _declared_output_paths(repo_root, project_dir, proxy)


def _hash_paths(paths: tuple[Path, ...]) -> str:
    """Hash a set of files by their relative-order-independent content digest.

    Each path contributes ``<resolved-path>\\0<sha256-of-bytes-or-sentinel>``.
    Missing files contribute a fixed sentinel so the hash stays deterministic.
    Entries are sorted so ordering of the declared tuple does not matter.
    """
    digest = hashlib.sha256()
    parts: list[str] = []
    for path in paths:
        key = path.as_posix()
        if path.is_file():
            file_digest = hashlib.sha256()
            with path.open("rb") as fh:
                for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                    file_digest.update(chunk)
            parts.append(f"{key}\x00{file_digest.hexdigest()}")
        else:
            parts.append(f"{key}\x00{hashlib.sha256(_MISSING_INPUT_SENTINEL).hexdigest()}")
    for part in sorted(parts):
        digest.update(part.encode("utf-8"))
        digest.update(b"\x1e")  # record separator
    return digest.hexdigest()


# -- Public hashing API ------------------------------------------------------


def compute_stage_input_hash(
    *,
    repo_root: Path,
    project_dir: Path,
    stage_name: str,
    contract: StageContract,
    upstream_output_hashes: dict[str, str],
) -> str:
    """Compute a deterministic input hash for a stage.

    The hash folds in: the stage name, the content hash of declared input
    artifacts, and the recorded output hashes of dependency stages
    (``upstream_output_hashes``). Any change to those flips the hash.
    """
    digest = hashlib.sha256()
    digest.update(b"stage\x00")
    digest.update(stage_name.encode("utf-8"))
    digest.update(b"\x1e")
    digest.update(b"inputs\x00")
    digest.update(_hash_paths(_resolve_input_paths(repo_root, project_dir, contract)).encode("ascii"))
    digest.update(b"\x1e")
    digest.update(b"upstream\x00")
    # A stage never folds its OWN recorded output hash into its input hash, only
    # those of other (upstream) stages. Otherwise re-recording a stage would
    # perturb its own input hash and break skip detection.
    for dep_name in sorted(upstream_output_hashes):
        if dep_name == stage_name:
            continue
        digest.update(dep_name.encode("utf-8"))
        digest.update(b"=")
        digest.update(upstream_output_hashes[dep_name].encode("ascii", errors="replace"))
        digest.update(b"\x1e")
    return digest.hexdigest()


def compute_stage_output_hash(
    *,
    repo_root: Path,
    project_dir: Path,
    contract: StageContract,
) -> str:
    """Compute a deterministic content hash over a stage's declared outputs."""
    return _hash_paths(_declared_output_paths(repo_root, project_dir, contract))


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
    paths = _declared_output_paths(repo_root, project_dir, contract)
    if not paths:
        return False
    return all(path.exists() for path in paths)


def should_skip_stage(
    *,
    config: IncrementalConfig,
    manifest: HashManifest,
    repo_root: Path,
    project_dir: Path,
    stage_name: str,
    contract: StageContract,
) -> SkipDecision:
    """Decide whether a stage may be skipped under incremental mode.

    Returns ``SkipDecision(skip=False)`` immediately when the feature is
    disabled (the default), guaranteeing the legacy behavior. When enabled, the
    stage is skippable only when the recorded input hash matches AND all
    declared outputs are present.
    """
    if not config.enabled:
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
    )
    record = manifest.get(stage_name)
    if record is None or record.input_hash != input_hash:
        return SkipDecision(skip=False, input_hash=input_hash)
    if not declared_outputs_present(repo_root=repo_root, project_dir=project_dir, contract=contract):
        # Fail-safe: matching hash but a declared output is absent -> re-run.
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
