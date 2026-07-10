"""Known-bad fixture: mixing distinct NewType identifiers (ISC-2).

`mypy --strict` MUST reject this file. It is never imported or executed —
only type-checked in isolation by tests/test_mypy_oracle.py.
"""

from template_formal.types.ids import AgentId, MessageId, new_agent_id


def wants_a_message_id(message_id: MessageId) -> None:
    print(message_id)


def bad_usage() -> None:
    agent_id: AgentId = new_agent_id()
    # error: Argument 1 to "wants_a_message_id" has incompatible type "AgentId"; expected "MessageId"
    wants_a_message_id(agent_id)
