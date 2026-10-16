"""Overlap only owned subprocess supervision; resume Source controllers serially."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Generator, Sequence
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass
import math
from pathlib import Path
import time
from typing import Any

from infrastructure.project.public_acceptance_auxiliary_supervision import supervise


@dataclass(frozen=True)
class AuxiliaryProcess:
    """One fully prepared original child, using its unchanged enclosing deadline."""

    command: list[str]
    root: Path
    directory: Path
    deadline: float
    bootstrap_payload: dict[str, Any] | None = None


AuxiliaryResult = tuple[str, dict[str, Any]]
AuxiliaryOperation = Generator[AuxiliaryProcess, dict[str, Any], AuxiliaryResult]


def execute_auxiliary_operations(
    operations: Sequence[tuple[str, AuxiliaryOperation]], *, workers: int, deadline: float
) -> list[AuxiliaryResult]:
    """Keep each scope serial and import/admit/write only on the calling thread.

    Only the existing actual subprocess supervisor runs on worker threads.
    A positive child and its negative control keep the same scope slot until
    the controller has admitted and written that gate's final observation.
    """
    if type(workers) is not int or workers not in (1, 2, 3):
        raise ValueError("auxiliary workers must be one, two or three")
    if type(deadline) not in (int, float) or not math.isfinite(deadline):
        raise ValueError("auxiliary controller requires its original finite deadline")

    def remaining() -> None:
        if time.monotonic() >= deadline:
            raise TimeoutError("original auxiliary deadline exhausted during controller admission")

    remaining()
    if any(not isinstance(scope, str) or not scope for scope, _ in operations):
        raise ValueError("auxiliary operations require explicit nonempty scope ownership")
    if len({id(operation) for _, operation in operations}) != len(operations):
        raise ValueError("auxiliary operation cannot be scheduled more than once")
    queues: dict[str, deque[tuple[int, AuxiliaryOperation]]] = defaultdict(deque)
    for index, (scope, operation) in enumerate(operations):
        # The default must retain the exact original serial execution order,
        # including interleaved scopes in an explicit caller selection.
        queue = str(index) if workers == 1 else scope
        queues[queue].append((index, operation))
    ready = deque(queues)
    results: list[AuxiliaryResult | None] = [None] * len(operations)
    pending: dict[Future[dict[str, Any]], tuple[str, int, AuxiliaryOperation]] = {}

    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="auxiliary-child") as executor:

        def advance(
            scope: str,
            index: int,
            operation: AuxiliaryOperation,
            observation: dict[str, Any] | None = None,
        ) -> None:
            remaining()
            try:
                request = next(operation) if observation is None else operation.send(observation)
            except StopIteration as completed:
                remaining()
                results[index] = completed.value
                if queues[scope]:
                    ready.append(scope)
                return
            remaining()
            if request.deadline != deadline:
                raise ValueError("auxiliary child changed the original controller deadline")
            future = executor.submit(
                supervise,
                list(request.command),
                request.root,
                request.directory,
                request.deadline,
                bootstrap_payload=request.bootstrap_payload,
            )
            pending[future] = (scope, index, operation)

        while ready or pending:
            while ready and len(pending) < workers:
                scope = ready.popleft()
                index, operation = queues[scope].popleft()
                advance(scope, index, operation)
            if pending:
                completed, _ = wait(pending, return_when=FIRST_COMPLETED)
                for future in sorted(completed, key=lambda item: pending[item][1]):
                    scope, index, operation = pending.pop(future)
                    advance(scope, index, operation, future.result())
    if any(result is None for result in results):
        raise ValueError("auxiliary controller omitted an original operation result")
    remaining()
    return [result for result in results if result is not None]
