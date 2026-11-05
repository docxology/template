"""A raising worker must still record why it raised.

Hosted run 41954325668 (head `125ef4d91576`): all 25 native cells exited 1 with
`native Source reference lacks strict published rendered evidence` and empty
`formats`. The retained `receipt.json` recorded
`worker_outcome: {"class": "SystemExit", "kind": "raised", "system_exit_code": 1}`
and every worker stderr held only `NATIVE_WORKER_STARTUP_V1` markers.

`SystemExit` inherits from `BaseException`, not `Exception`, so the worker's
`except Exception` clause could not see it: the worker died, recorded no
diagnostic and emitted no traceback. These controls pin that the escape is now
recorded, and they assert the *wiring* rather than the predicate alone — a
handler that exists but is not reached by `SystemExit` would leave the same
vacuum the hosted run produced.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
WORKER = ROOT / "infrastructure/reporting/native_format_acceptance_worker.py"


def _handler_names() -> list[str]:
    """Return the exception type named by each `except` clause, in source order."""
    tree = ast.parse(WORKER.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is not None:
            names.append(ast.unparse(node.type))
    return names


def test_worker_handles_baseexception_after_exception() -> None:
    """`SystemExit` must reach a handler: it is BaseException, not Exception."""
    assert issubclass(SystemExit, BaseException)
    assert not issubclass(SystemExit, Exception)

    handlers = _handler_names()
    assert "BaseException" in handlers, (
        "the worker must catch BaseException: `SystemExit`, `GeneratorExit` and any "
        f"other BaseException subclass bypass `except Exception`. Found: {handlers}"
    )
    # Ordering is load-bearing: a broader handler placed first would shadow the
    # specific `NativeToolUnavailable` (75) and `TimeoutError` (124) branches and
    # silently relabel blocked and timed-out workers as generic failures.
    assert handlers.index("Exception") < handlers.index("BaseException"), handlers


def test_baseexception_handler_records_then_reraises() -> None:
    """The handler must write a diagnostic and re-raise, never swallow."""
    tree = ast.parse(WORKER.read_text(encoding="utf-8"))
    handler = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ExceptHandler) and node.type is not None and ast.unparse(node.type) == "BaseException"
    )
    body = ast.unparse(handler)
    # `ast.unparse` renders subscripts with single quotes, so match loosely.
    assert "diagnostic" in body, body
    assert "__name__" in body, body
    # Re-raised: a worker that converted SystemExit into a partial pass would be
    # a worse defect than the missing diagnostic this clause exists to fix.
    assert any(isinstance(node, ast.Raise) and node.exc is None for node in ast.walk(handler)), (
        "the BaseException handler must re-raise so the worker still fails"
    )
    # The exception class and exit code are retained for the receipt reader.
    assert "worker_outcome" in body, body
    assert "system_exit_code" in body, body


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (SystemExit(1), "SystemExit"),
        (SystemExit(None), "SystemExit"),
        (SystemExit("refused"), "SystemExit"),
        (GeneratorExit(), "GeneratorExit"),
        (KeyboardInterrupt(), "KeyboardInterrupt"),
    ],
)
def test_baseexception_subclasses_are_not_exception(error: BaseException, expected: str) -> None:
    """Negative control: these are precisely the values `except Exception` misses."""
    assert not isinstance(error, Exception)
    assert isinstance(error, BaseException)
    assert type(error).__name__ == expected


def test_system_exit_escapes_except_exception() -> None:
    """Negative control for the defect itself, restated as executable proof."""
    recorded: list[str] = []
    try:
        try:
            raise SystemExit(1)
        except Exception:  # the pre-fix worker's only generic clause
            recorded.append("exception-handler")  # pragma: no cover - must not run
    except BaseException:
        recorded.append("baseexception-handler")
    assert recorded == ["baseexception-handler"], (
        "if this ever reads ['exception-handler'] the language changed and the BaseException clause is no longer needed"
    )


def test_no_statement_between_raw_and_the_handler_sits_outside_a_try() -> None:
    """The handler must begin as soon as `raw` exists.

    Before this was pinned, `env = native_environment(...)` sat between `raw`
    being constructed and the protected `try:`, inside no `try` at all. A
    `SystemExit` raised there escaped with an empty diagnostic -- the exact
    failure the BaseException clause exists to prevent -- and nothing caught
    it because the clause is attached to a `try` that had not started yet.
    """
    tree = ast.parse(WORKER.read_text(encoding="utf-8"))
    function = next(
        node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "_run_native_worker"
    )
    handler_try = next(
        statement
        for statement in function.body
        if isinstance(statement, ast.Try)
        and any(
            clause.type is not None and ast.unparse(clause.type) == "BaseException" for clause in statement.handlers
        )
    )
    raw_index = next(
        index
        for index, statement in enumerate(function.body)
        if isinstance(statement, (ast.AnnAssign, ast.Assign))
        and "raw" in ast.unparse(statement.targets if isinstance(statement, ast.Assign) else [statement.target])
    )
    between = function.body[raw_index + 1 : function.body.index(handler_try)]
    assert between == [], (
        "statements between `raw` and the protected try: run outside the "
        f"BaseException handler. Offending lines: {[s.lineno for s in between]}"
    )
