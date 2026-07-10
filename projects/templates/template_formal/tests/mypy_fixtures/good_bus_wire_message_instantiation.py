"""Known-good fixture: ``InProcessBus[WireMessage]`` binds and type-checks cleanly (ISC-20/26).

`mypy --strict` MUST accept this file (exit 0). It exists as a
positive-control regression guard: `src/` itself never instantiates
`InProcessBus[MsgT]` with a concrete type argument -- every real binding to
`WireMessage` (via `encode_wire_message`/`decode_wire_message`) lives in
`tests/network/test_bus.py` and `tests/network/test_handshake_over_bus.py`,
neither of which `tests/test_mypy_oracle.py` type-checks. A `src/`-only
mypy gate is therefore structurally blind to a broken generic binding
between `InProcessBus` and its `encode`/`decode` callables (the same class
of blind spot documented for `Agent[BeliefState]` in ISA.md's Changelog).
This fixture is the permanent guard against that blind spot recurring for
the network-bus module.
"""

from template_formal.network.bus import FaultConfig, InProcessBus
from template_formal.protocol.session import WireMessage, decode_wire_message, encode_wire_message
from template_formal.types.ids import new_agent_id, new_message_id


def build_and_exercise_bus() -> int:
    bus: InProcessBus[WireMessage] = InProcessBus(
        encode=encode_wire_message,
        decode=decode_wire_message,
        fault_config=FaultConfig(seed=0),
    )
    sender_id = new_agent_id()
    recipient_id = new_agent_id()
    bus.register(sender_id)
    bus.register(recipient_id)
    message = WireMessage(msg_id=new_message_id(), sender=sender_id, kind="data", payload=b"x")
    bus.send(recipient_id, message)
    bus.flush()
    return bus.inbox_count(recipient_id)
