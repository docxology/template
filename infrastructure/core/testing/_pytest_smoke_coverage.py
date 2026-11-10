"""Keep the audited pipeline smoke pytest process free of coverage."""

from collections.abc import Iterator
from typing import Any

import pytest


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_load_initial_conftests(early_config: pytest.Config, args: list[str]) -> Iterator[None]:
    """Disable the registered coverage plugin before its controller can start."""
    options: Any = early_config.known_args_namespace
    if hasattr(options, "no_cov") and not options.no_cov:
        # pytest-cov reads the early namespace, then pytest reparses argv.
        options.no_cov = True
        option_end = args.index("--") if "--" in args else len(args)
        args.insert(option_end, "--no-cov")
    yield
