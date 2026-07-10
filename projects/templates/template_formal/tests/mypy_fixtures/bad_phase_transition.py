"""Known-bad fixture: calling an Established-only method on Idle (ISC-18).

`mypy --strict` MUST reject this file: `send` is defined only on
`EstablishedSession`, not on `IdleSession` -- the method is genuinely
absent from the Idle class (illegal-state-unrepresentable), not merely
runtime-guarded. Never imported or executed -- only type-checked in
isolation by tests/test_mypy_oracle.py.
"""

from template_formal.protocol.session import IdleSession
from template_formal.types.ids import new_agent_id


def bad_usage() -> None:
    idle = IdleSession(local_id=new_agent_id())
    # error: "IdleSession" has no attribute "send"
    idle.send(b"illegal payload on an idle session")
