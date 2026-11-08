"""Private project-runner controls that leave actual pytest selection intact."""

from __future__ import annotations

from argparse import Namespace
from typing import Any

import pytest

from infrastructure.core.testing.pytest_marker_exprs import repository_marker_expression


def pytest_addoption(parser: Any) -> None:
    parser.addoption(
        "--template-benchmark-storage",
        default=None,
        help="Default benchmark storage nominated by the owning project runner.",
    )
    parser.addoption(
        "--template-profile-exclude",
        action="append",
        default=None,
        choices=[clause.removeprefix("not ") for clause in repository_marker_expression().split(" and ")],
        help="Canonical engine-generated project profile exclusion (not a user marker expression).",
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


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config: Any, items: list[Any]) -> None:
    """Resolve generated exclusions against the actual native collection.

    Explicit user expressions are never rewritten. Registration is read after
    plugins configure themselves; observed undeclared marks still count in
    non-strict projects. Strict annotation errors remain pytest's own errors.
    """
    exclusions = config.getoption("template_profile_exclude")
    if exclusions is None or config.getoption("collectonly"):
        return
    # Parse only invocation arguments with pytest's already configured parser:
    # project addopts must not mask the generated policy, while explicit -m
    # (including attached/clustered forms and the empty expression) stays raw.
    invocation = config._parser.parse_known_args(config.invocation_params.args, namespace=Namespace(markexpr=None))
    if invocation.markexpr is not None:
        return
    names = {row.split(":", 1)[0].split("(", 1)[0].strip() for row in config.getini("markers")}
    names.update(mark.name for item in items for mark in item.iter_markers())
    # Set the real effective option before pytest's own marker deselection.
    # Even an empty intersection supersedes project addopts, just as the
    # original generated -m policy did; receipts observe this same expression.
    config.option.markexpr = " and ".join(f"not {name}" for name in exclusions if name in names)
