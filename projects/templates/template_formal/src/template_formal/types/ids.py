"""Nominal identifier types for the ant-robot colony.

Each identifier wraps ``uuid.UUID`` via ``typing.NewType``. This buys
structural-typing safety mypy --strict actually enforces: an ``AgentId``
cannot be passed where a ``MessageId`` is expected, even though both are
UUIDs at runtime, because ``NewType`` creates a distinct nominal type at
the type-checker level. This is *not* a runtime guarantee — at runtime an
``AgentId`` and a ``MessageId`` are indistinguishable ``UUID`` values. The
guarantee is edit-time/CI-time only. See ``manuscript`` §"What mypy proves"
for the exact scoping of this claim.
"""

from __future__ import annotations

from typing import NewType
from uuid import UUID, uuid4

AgentId = NewType("AgentId", UUID)
MessageId = NewType("MessageId", UUID)
TxnId = NewType("TxnId", UUID)


def new_agent_id() -> AgentId:
    """Construct a fresh, random :class:`AgentId`."""
    return AgentId(uuid4())


def new_message_id() -> MessageId:
    """Construct a fresh, random :class:`MessageId`."""
    return MessageId(uuid4())


def new_txn_id() -> TxnId:
    """Construct a fresh, random :class:`TxnId`."""
    return TxnId(uuid4())
