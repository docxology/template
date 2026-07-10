"""Known-good fixture: the flagship generic instantiation must type-check.

`mypy --strict` MUST accept this file cleanly (exit 0). It exists because
a prior revision of `GaussianBelief` declared `mean`/`variance` as plain
mutable attributes, which a `frozen=True` dataclass (`BeliefState`) can
never satisfy under mypy --strict -- and because `src/` itself never
instantiates `Agent[StateT]` with a concrete type argument, the src-only
mypy run was blind to the break (Forge cross-vendor audit finding,
CRITICAL-1; see ISA.md Changelog). This fixture is the regression guard:
`Agent[BeliefState]` (and a `list[...]` of them) must keep type-checking.
"""

from pathlib import Path

from template_formal.agent.agent import Agent, BeliefState
from template_formal.types.ids import new_agent_id


def build_one_agent(db_dir: Path) -> Agent[BeliefState]:
    return Agent(
        agent_id=new_agent_id(),
        db_path=db_dir / "agent.sqlite3",
        preference=BeliefState(mean=10.0, variance=1.0),
    )


def build_several_agents(db_dir: Path) -> list[Agent[BeliefState]]:
    return [build_one_agent(db_dir) for _ in range(3)]
