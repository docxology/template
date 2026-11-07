"""Project and shared outcomes validated for multi-project reporting."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING

from infrastructure.core.pipeline.multi_project import validated_project_run
from infrastructure.core.pipeline.multi_project_support import validated_shared_run

if TYPE_CHECKING:
    from infrastructure.core.pipeline.multi_project import MultiProjectResult
    from infrastructure.core.pipeline.outcomes import RunResult


@dataclass(frozen=True)
class ProjectRunReadback:
    """A requested project and its validated run, when one is available."""

    qualified_name: str
    run: RunResult | None

    @property
    def complete(self) -> bool:
        return self.run is not None and self.run.complete


def iter_project_runs(result: MultiProjectResult, project_names: Iterable[str]) -> Iterator[ProjectRunReadback]:
    """Keep the caller's project order and preserve repeated names."""
    for name in project_names:
        yield ProjectRunReadback(name, validated_project_run(result, name))


def shared_infrastructure_run(result: MultiProjectResult) -> RunResult | None:
    """Read a validated shared run whose exit agrees with the aggregate."""
    return validated_shared_run(result.shared_infrastructure_result, result.shared_infrastructure_exit_code)
