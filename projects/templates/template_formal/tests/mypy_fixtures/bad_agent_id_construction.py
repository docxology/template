"""Known-bad fixture: Agent construction must reject a bare UUID, not AgentId (ISC-31).

`mypy --strict` MUST reject this file: `Agent.__init__` requires
`agent_id: AgentId`, a `NewType`-wrapped `UUID` -- a bare `uuid.UUID`
(returned by `uuid4()`, never wrapped via `AgentId(...)`) is a distinct,
incompatible type at the type-checker level, even though both are `UUID`
values at runtime. Never imported or executed -- only type-checked in
isolation by tests/test_mypy_oracle.py.
"""

from pathlib import Path
from uuid import uuid4

from template_formal.agent.agent import Agent, BeliefState


def bad_usage() -> None:
    preference = BeliefState(mean=0.0, variance=1.0)
    # error: Argument 1 to "Agent" has incompatible type "UUID"; expected "AgentId"
    Agent(uuid4(), Path("/tmp/bad-agent.sqlite3"), preference)
