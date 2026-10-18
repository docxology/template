"""Private project-runner controls that leave actual pytest selection intact."""

from __future__ import annotations

from typing import Any

import pytest


def pytest_addoption(parser: Any) -> None:
    parser.addoption(
        "--template-benchmark-storage",
        default=None,
        help="Default benchmark storage nominated by the owning project runner.",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: Any) -> None:
    """Relocate only the loaded plugin's default before its session is built.

    The runner nominates its already confined, ignored output directory. An
    absent/disabled benchmark plugin has no option to change. Explicit user
    destinations remain theirs; the hook changes no benchmark workload or
    test selection and emits no execution receipts.
    """
    destination = config.getoption("template_benchmark_storage")
    current = getattr(config.option, "benchmark_storage", None)
    if destination is not None and current == "file://./.benchmarks":
        config.option.benchmark_storage = "file://" + destination
