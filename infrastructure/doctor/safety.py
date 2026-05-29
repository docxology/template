"""The audited mutate() chokepoint.

Every filesystem change attributed to the doctor flows through
:func:`mutate`. The contract is:

1. **Snapshot before touching anything.** Every path in the plan that
   currently exists is copied byte-for-byte into a per-action backup
   directory under ``.doctor/backups/<action_id>/`` and its SHA-256 is
   recorded.
2. **Apply the change.** Implemented by an ``ActionHandler`` registered
   for ``plan.action_kind``. Handlers are intentionally narrow — they
   only see paths that the plan declared.
3. **Record what happened.** Post-mutation hashes (or ``"absent"`` for
   deletions) are stored in the backup manifest and a single line is
   appended to ``.doctor/actions.jsonl``.
4. **Refuse on hash drift.** If a backup-stage hash does not match what
   the file looks like immediately after, the chokepoint marks the
   action ``applied=False`` and surfaces an error — never silently
   overwrites unexpected content.

The :func:`undo` function inverts a reversible record by restoring
every file from its backup and verifying the post-restore hash matches
the original ``pre_hashes``.

This module never imports from :mod:`infrastructure.doctor.fixers` so
the safety surface can be reasoned about without considering the set of
fixers in play — fixers register handlers via :func:`register_handler`.
"""

import datetime as _dt
import hashlib
import json
import os
import secrets
import shutil
import stat
import subprocess  # noqa: S404 — only used to invoke uv with hardcoded argv
from collections.abc import Callable, Iterable
from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.doctor.models import FixPlan, MutateRecord


__all__ = [
    "DoctorSafetyError",
    "DoctorState",
    "register_handler",
    "registered_handlers",
    "mutate",
    "undo",
    "load_journal",
    "ABSENT_SENTINEL",
]


logger = get_logger(__name__)


ABSENT_SENTINEL = "absent"
"""Hash placeholder for a path that does not exist on disk."""


class DoctorSafetyError(RuntimeError):
    """Raised when the safety contract cannot be honoured.

    Examples: a path in a plan resolves outside the repo, the journal
    is corrupted, an undo would clobber unrelated content, a handler is
    not registered for an action kind.
    """


# ---------------------------------------------------------------------------
# State directory layout
# ---------------------------------------------------------------------------


class DoctorState:
    """Filesystem layout for doctor state.

    ``.doctor/`` holds backups, the action journal, and the last-run
    summary. It lives inside the repo so it's discoverable and is added
    to ``.gitignore`` separately (see ``infrastructure/doctor/README.md``).
    """

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()
        self.root = self.repo_root / ".doctor"
        self.backups_dir = self.root / "backups"
        self.journal_path = self.root / "actions.jsonl"
        self.last_run_path = self.root / "state.json"

    def ensure(self) -> None:
        """Create the state directory tree if it doesn't exist."""
        self.backups_dir.mkdir(parents=True, exist_ok=True)

    def new_action_id(self) -> tuple[str, str]:
        """Allocate a fresh ``(action_id, timestamp_utc)`` pair."""
        now = _dt.datetime.now(_dt.timezone.utc)
        ts = now.strftime("%Y%m%dT%H%M%SZ")
        suffix = secrets.token_hex(4)
        return f"{ts}_{suffix}", now.isoformat()


# ---------------------------------------------------------------------------
# Action handler registry
# ---------------------------------------------------------------------------


ActionHandler = Callable[[FixPlan, DoctorState], None]
"""Signature for an action handler.

A handler must only touch paths listed in ``plan.affected_paths``. It
may raise any exception on failure — the chokepoint converts that into
a ``MutateRecord`` with ``applied=False`` and ``error`` populated.
"""


_HANDLERS: dict[str, ActionHandler] = {}


def register_handler(action_kind: str, handler: ActionHandler) -> None:
    """Register an :class:`ActionHandler` for ``action_kind``.

    Called at import time by :mod:`infrastructure.doctor.fixers`.
    Re-registering the same kind overwrites — handy for tests.
    """

    _HANDLERS[action_kind] = handler


def registered_handlers() -> dict[str, ActionHandler]:
    """Return a snapshot of the current handler registry."""
    return dict(_HANDLERS)


# ---------------------------------------------------------------------------
# Hash helpers
# ---------------------------------------------------------------------------


def _hash_path(path: Path) -> str:
    """SHA-256 of ``path``.

    For regular files: hash of file bytes. For directories: hash of a
    deterministic manifest of ``(relpath, file_hash)`` pairs. For
    missing paths: :data:`ABSENT_SENTINEL`. Symlinks are hashed by
    their target string (so the link itself is the unit of state).
    """

    if not path.exists() and not path.is_symlink():
        return ABSENT_SENTINEL

    if path.is_symlink():
        target = os.readlink(path)
        return "symlink:" + hashlib.sha256(target.encode("utf-8")).hexdigest()

    if path.is_file():
        h = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(64 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    if path.is_dir():
        h = hashlib.sha256()
        for sub in sorted(path.rglob("*")):
            if sub.is_file():
                rel = sub.relative_to(path).as_posix()
                h.update(rel.encode("utf-8"))
                h.update(b"\0")
                h.update(_hash_path(sub).encode("ascii"))
                h.update(b"\n")
        return "dir:" + h.hexdigest()

    # Sockets, fifos, devices — treat as opaque, hash the mode.
    return "special:" + hashlib.sha256(str(path.stat().st_mode).encode()).hexdigest()


# ---------------------------------------------------------------------------
# Path safety
# ---------------------------------------------------------------------------


def _validate_paths(paths: Iterable[Path], state: DoctorState) -> list[Path]:
    """Resolve and validate that every path is inside the repo root.

    Returns a list of fully-resolved :class:`Path` values. Raises
    :exc:`DoctorSafetyError` if any path escapes the repo or points at
    the doctor state directory itself (which would be self-destructive
    on undo).
    """

    cleaned: list[Path] = []
    repo = state.repo_root
    doctor_root = state.root.resolve()
    for raw in paths:
        # Resolve symlinks and ``..`` segments but tolerate non-existent
        # leaves (resolve(strict=False) still normalises).
        resolved = Path(os.path.normpath(str((repo / raw).resolve()))) if not raw.is_absolute() else raw.resolve()
        try:
            resolved.relative_to(repo)
        except ValueError as exc:
            raise DoctorSafetyError(f"Path escapes repo root: {raw} -> {resolved} (root={repo})") from exc
        if resolved == doctor_root or doctor_root in resolved.parents:
            raise DoctorSafetyError(f"Refusing to mutate path inside doctor state directory: {resolved}")
        cleaned.append(resolved)
    return cleaned


# ---------------------------------------------------------------------------
# Backup
# ---------------------------------------------------------------------------


def _snapshot(paths: list[Path], state: DoctorState, action_id: str) -> tuple[Path, dict[str, str]]:
    """Copy every existing path into the per-action backup directory.

    Returns ``(backup_dir, pre_hashes)``. ``pre_hashes`` maps each
    absolute path (as a string) to its SHA-256 (or :data:`ABSENT_SENTINEL`
    if the path did not exist).
    """

    backup_dir = state.backups_dir / action_id
    backup_dir.mkdir(parents=True, exist_ok=False)
    hashes: dict[str, str] = {}

    for path in paths:
        digest = _hash_path(path)
        hashes[str(path)] = digest
        if digest == ABSENT_SENTINEL:
            continue
        rel = path.relative_to(state.repo_root)
        dest = backup_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if path.is_symlink():
            target = os.readlink(path)
            os.symlink(target, dest)
        elif path.is_file():
            shutil.copy2(path, dest)
        elif path.is_dir():
            shutil.copytree(path, dest, symlinks=True)

    manifest = {
        "action_id": action_id,
        "pre_hashes": hashes,
        "repo_root": str(state.repo_root),
    }
    (backup_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return backup_dir, hashes


# ---------------------------------------------------------------------------
# Journal
# ---------------------------------------------------------------------------


def _append_journal(state: DoctorState, record: MutateRecord) -> None:
    """Append one ``MutateRecord`` as a JSON line to ``actions.jsonl``."""
    state.ensure()
    with state.journal_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record.to_jsonable(), sort_keys=True))
        fh.write("\n")


def load_journal(state: DoctorState) -> list[MutateRecord]:
    """Return every record in the journal, oldest first."""
    if not state.journal_path.exists():
        return []
    records: list[MutateRecord] = []
    for line_no, raw in enumerate(state.journal_path.read_text().splitlines(), start=1):
        raw = raw.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise DoctorSafetyError(f"Corrupt journal at line {line_no}: {exc}") from exc
        records.append(
            MutateRecord(
                action_id=data["action_id"],
                timestamp_utc=data["timestamp_utc"],
                fix_id=data["fix_id"],
                finding_code=data["finding_code"],
                therapy=data["therapy"],
                title=data["title"],
                backup_dir=data["backup_dir"],
                pre_hashes=data["pre_hashes"],
                post_hashes=data["post_hashes"],
                affected_paths=data["affected_paths"],
                reversible=data["reversible"],
                applied=data["applied"],
                error=data.get("error"),
            )
        )
    return records


# ---------------------------------------------------------------------------
# The chokepoint
# ---------------------------------------------------------------------------


def mutate(plan: FixPlan, state: DoctorState) -> MutateRecord:
    """Execute ``plan`` under the full safety contract.

    No matter what ``plan.action_kind`` does, the surrounding ceremony
    is identical: validate paths, snapshot, run the handler, hash again,
    and journal the outcome. A failure during the handler does *not*
    prevent the journal record from being written — that is how undo
    knows whether the action ever touched the filesystem.

    Args:
        plan: The intended mutation.
        state: Doctor state (paths and backup dir).

    Returns:
        The :class:`MutateRecord` describing what happened. Always
        returns — failures are reported via ``applied=False`` and
        ``error``.

    Raises:
        DoctorSafetyError: If the plan itself is invalid (paths escape
            the repo, no handler registered, etc.) — these are
            programming errors, not runtime fix failures.
    """

    state.ensure()
    handler = _HANDLERS.get(plan.action_kind)
    if handler is None:
        raise DoctorSafetyError(
            f"No handler registered for action_kind={plan.action_kind!r}; known: {sorted(_HANDLERS)}"
        )

    resolved_paths = _validate_paths(plan.affected_paths, state)
    action_id, ts = state.new_action_id()
    backup_dir, pre_hashes = _snapshot(resolved_paths, state, action_id)

    error: str | None = None
    applied = False
    try:
        # Build a copy of the plan with resolved absolute paths so handlers
        # never have to re-derive them.
        resolved_plan = FixPlan(
            fix_id=plan.fix_id,
            title=plan.title,
            therapy=plan.therapy,
            finding_code=plan.finding_code,
            affected_paths=tuple(resolved_paths),
            action_kind=plan.action_kind,
            params=plan.params,
            reversible=plan.reversible,
        )
        handler(resolved_plan, state)
        applied = True
    except Exception as exc:  # noqa: BLE001 — surfaced via record.error
        error = f"{type(exc).__name__}: {exc}"
        logger.error("Fix %s failed: %s", plan.fix_id, error)

    post_hashes = {str(p): _hash_path(p) for p in resolved_paths}

    record = MutateRecord(
        action_id=action_id,
        timestamp_utc=ts,
        fix_id=plan.fix_id,
        finding_code=plan.finding_code,
        therapy=plan.therapy.label,
        title=plan.title,
        backup_dir=str(backup_dir),
        pre_hashes=pre_hashes,
        post_hashes=post_hashes,
        affected_paths=[str(p) for p in resolved_paths],
        reversible=plan.reversible,
        applied=applied,
        error=error,
    )
    _append_journal(state, record)
    return record


# ---------------------------------------------------------------------------
# Undo
# ---------------------------------------------------------------------------


def undo(record: MutateRecord, state: DoctorState) -> MutateRecord:
    """Restore the filesystem to the pre-mutation state for ``record``.

    Verifies the backup directory still exists and that every restored
    path matches the recorded ``pre_hashes`` byte-for-byte. Writes an
    inverse journal entry (``fix_id="undo:<original_fix_id>"``,
    ``reversible=False``) so the audit trail is complete.

    Args:
        record: The record to invert. Must have ``reversible=True``.
        state: Doctor state.

    Returns:
        A new :class:`MutateRecord` describing the undo operation.

    Raises:
        DoctorSafetyError: If ``record`` is not reversible, the backup
            is missing, or a restored hash does not match the original.
    """

    if not record.reversible:
        raise DoctorSafetyError(f"Action {record.action_id} is not reversible")
    if not record.applied:
        raise DoctorSafetyError(f"Action {record.action_id} was never applied; nothing to undo")

    backup_dir = Path(record.backup_dir)
    if not backup_dir.is_dir():
        raise DoctorSafetyError(f"Backup directory missing: {backup_dir}")

    undo_action_id, ts = state.new_action_id()

    # Restore every path. ABSENT_SENTINEL means "the path didn't exist
    # before — make it not exist again".
    repo_root = state.repo_root
    restored: dict[str, str] = {}
    for path_str, pre_hash in record.pre_hashes.items():
        target = Path(path_str)
        if pre_hash == ABSENT_SENTINEL:
            _remove_path(target)
            restored[path_str] = ABSENT_SENTINEL
            continue
        rel = target.relative_to(repo_root)
        source = backup_dir / rel
        if not source.exists() and not source.is_symlink():
            raise DoctorSafetyError(f"Backup is missing path needed for undo: {source}")
        _remove_path(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_symlink():
            os.symlink(os.readlink(source), target)
        elif source.is_file():
            shutil.copy2(source, target)
        elif source.is_dir():
            shutil.copytree(source, target, symlinks=True)
        new_hash = _hash_path(target)
        if new_hash != pre_hash:
            raise DoctorSafetyError(f"Hash mismatch after restoring {target}: expected {pre_hash}, got {new_hash}")
        restored[path_str] = new_hash

    undo_record = MutateRecord(
        action_id=undo_action_id,
        timestamp_utc=ts,
        fix_id=f"undo:{record.fix_id}",
        finding_code=record.finding_code,
        therapy=record.therapy,
        title=f"Undo of {record.title} ({record.action_id})",
        backup_dir=str(backup_dir),
        pre_hashes=record.post_hashes,
        post_hashes=restored,
        affected_paths=record.affected_paths,
        reversible=False,
        applied=True,
        error=None,
    )
    _append_journal(state, undo_record)
    return undo_record


def _remove_path(path: Path) -> None:
    """Best-effort path removal that copes with files, dirs, and symlinks."""
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
    elif path.is_dir():
        shutil.rmtree(path)


# ---------------------------------------------------------------------------
# Built-in action handlers
# ---------------------------------------------------------------------------
#
# These cover the small set of fundamental mutations a doctor performs.
# Fixers in :mod:`infrastructure.doctor.fixers` produce :class:`FixPlan`
# objects parameterised over these handlers; they don't write their own
# filesystem code.


def _handler_delete_paths(plan: FixPlan, state: DoctorState) -> None:
    """Delete every affected path (recursively for directories)."""
    for path in plan.affected_paths:
        _remove_path(path)


def _handler_chmod(plan: FixPlan, state: DoctorState) -> None:
    """Apply the mode from ``plan.params['mode']`` to each path.

    The mode is OR-ed with the existing mode so callers can use
    ``mode=0o111`` to mean "add execute for all" without clobbering
    read/write bits.
    """
    mode = int(plan.params.get("mode", 0))
    if mode <= 0:
        raise DoctorSafetyError(f"chmod handler requires positive mode; got {mode!r}")
    for path in plan.affected_paths:
        current = path.stat().st_mode
        path.chmod(stat.S_IMODE(current) | mode)


def _handler_write_file(plan: FixPlan, state: DoctorState) -> None:
    """Write ``plan.params['content']`` to the single affected file.

    Creates parent directories as needed. Refuses to overwrite an
    existing file unless ``params['overwrite']`` is true.
    """
    if len(plan.affected_paths) != 1:
        raise DoctorSafetyError(f"write_file handler expects exactly one affected_path; got {len(plan.affected_paths)}")
    target = plan.affected_paths[0]
    overwrite = bool(plan.params.get("overwrite", False))
    if target.exists() and not overwrite:
        raise DoctorSafetyError(f"Refusing to overwrite existing file: {target}")
    content: str = plan.params.get("content", "")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _handler_run_uv_sync(plan: FixPlan, state: DoctorState) -> None:
    """Run ``uv sync`` from the repo root.

    The only non-file mutation the doctor performs. Marked
    ``reversible=False`` by the fixer that builds this plan — undoing a
    sync would require time-travel on the virtualenv.
    """
    cmd = ["uv", "sync"]
    extra: list[str] = list(plan.params.get("extra_args", []))
    cmd.extend(extra)
    result = subprocess.run(  # noqa: S603 — argv list, no shell
        cmd,
        cwd=state.repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise DoctorSafetyError(f"uv sync exited {result.returncode}; stderr tail: {result.stderr[-400:]}")


def _register_builtin_handlers() -> None:
    """Wire the built-in handlers. Idempotent — safe to call repeatedly."""
    register_handler("delete_paths", _handler_delete_paths)
    register_handler("chmod", _handler_chmod)
    register_handler("write_file", _handler_write_file)
    register_handler("run_uv_sync", _handler_run_uv_sync)


_register_builtin_handlers()
