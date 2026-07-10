"""Core type vocabulary: nominal IDs, the Result ADT, and phase markers."""

from template_formal.types.ids import AgentId, MessageId, TxnId, new_agent_id, new_message_id, new_txn_id
from template_formal.types.phase import Closed, Established, Handshaking, Idle, PhaseT
from template_formal.types.result import Err, Ok, Result, and_then, is_ok, map_result, unwrap_or

__all__ = [
    "AgentId",
    "MessageId",
    "TxnId",
    "new_agent_id",
    "new_message_id",
    "new_txn_id",
    "Idle",
    "Handshaking",
    "Established",
    "Closed",
    "PhaseT",
    "Ok",
    "Err",
    "Result",
    "is_ok",
    "map_result",
    "and_then",
    "unwrap_or",
]
