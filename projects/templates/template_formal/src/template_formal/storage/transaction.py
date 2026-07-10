"""Affine-discipline ``TransactionHandle`` — a runtime-guarded resource, not a proof.

Python has no linear or affine type system (per ``Out of Scope`` /
``Principles``: no code comment here may claim otherwise). mypy --strict
cannot reject a program that calls ``handle.commit()`` twice on the same
``TransactionHandle`` instance — nothing about that second call is
ill-typed. What this module *can* do is make the reuse fail loudly and
immediately at runtime: :class:`TransactionHandle` is ``frozen`` +
``__slots__`` and carries a private ``_consumed`` flag that every
consuming method checks first, raising :class:`ConsumedHandleError` on a
second use. This is the runtime half of the paired static+dynamic proof
referenced by ISC-11/12/13: the *type* only promises "a transaction
handle"; the *discipline* — checked here, every call, not merely
documented — promises "used at most once".
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field

from template_formal.storage.db import Database, IsolationLevel, StorageError
from template_formal.types.ids import TxnId, new_txn_id
from template_formal.types.result import Err, Ok, Result

_BEGIN_SQL: dict[IsolationLevel, str] = {
    "deferred": "BEGIN DEFERRED",
    "immediate": "BEGIN IMMEDIATE",
    "exclusive": "BEGIN EXCLUSIVE",
}


class ConsumedHandleError(RuntimeError):
    """Raised when an already-committed/rolled-back ``TransactionHandle`` is reused.

    This is a programmer-error condition (per repo convention: only
    affine-handle-reuse and similar misuse may raise instead of returning
    ``Result.Err``) — reusing a consumed transaction handle is a bug in
    the calling code, not an expected outcome the caller should branch on.
    """


@dataclass(frozen=True, slots=True)
class TransactionHandle:
    """A single-use handle over one SQLite transaction on one agent's database.

    Attributes:
        txn_id: The nominal, ``NewType``-wrapped identity of this
            transaction (distinct from ``AgentId``/``MessageId`` at the
            type level; see ``types/ids.py``).
        connection: The underlying ``sqlite3.Connection`` this handle's
            transaction was opened on.
        isolation_level: The isolation level this transaction began with.
    """

    txn_id: TxnId
    connection: sqlite3.Connection
    isolation_level: IsolationLevel
    _consumed: bool = field(default=False, init=False)

    def commit(self) -> Result[None, StorageError]:
        """Commit this transaction. Consumes the handle.

        Raises:
            ConsumedHandleError: If this handle was already committed or
                rolled back.
        """
        self._mark_consumed()
        try:
            self.connection.commit()
        except sqlite3.Error as exc:
            return Err(StorageError(kind="connection_error", message=str(exc)))
        return Ok(None)

    def rollback(self) -> Result[None, StorageError]:
        """Roll back this transaction, restoring the pre-transaction state. Consumes the handle.

        Raises:
            ConsumedHandleError: If this handle was already committed or
                rolled back.
        """
        self._mark_consumed()
        try:
            self.connection.rollback()
        except sqlite3.Error as exc:
            return Err(StorageError(kind="connection_error", message=str(exc)))
        return Ok(None)

    def _mark_consumed(self) -> None:
        """Raise if already consumed; otherwise mark consumed before the SQL call.

        Marking consumed *before* issuing the underlying commit/rollback
        (rather than after) guarantees a second call always hits the
        raise, even if the first call's ``sqlite3`` operation itself
        failed — a partially-failed commit/rollback still ends this
        handle's single use.
        """
        if self._consumed:
            raise ConsumedHandleError(
                f"TransactionHandle {self.txn_id} was already committed or rolled back "
                "and cannot be reused (affine-discipline runtime guard, not a compile-time proof)"
            )
        object.__setattr__(self, "_consumed", True)


def begin_transaction(database: Database) -> TransactionHandle:
    """Begin a new transaction on ``database`` using its configured isolation level.

    Args:
        database: The :class:`~template_formal.storage.db.Database` to
            begin a transaction on.

    Returns:
        A fresh, unconsumed :class:`TransactionHandle`.
    """
    database.connection.execute(_BEGIN_SQL[database.isolation_level])
    return TransactionHandle(
        txn_id=new_txn_id(),
        connection=database.connection,
        isolation_level=database.isolation_level,
    )
