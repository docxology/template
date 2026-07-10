"""Known-bad fixture: an arbitrary string where an isolation Literal is required (ISC-15).

`mypy --strict` MUST reject this file. It is never imported or executed —
only type-checked in isolation by tests/test_mypy_oracle.py.
"""

from pathlib import Path

from template_formal.storage.db import open_database


def bad_usage() -> None:
    # error: Argument "isolation_level" to "open_database" has incompatible type "str"; expected "Literal['deferred', 'immediate', 'exclusive']"
    open_database(Path("agent.db"), isolation_level="bogus")
