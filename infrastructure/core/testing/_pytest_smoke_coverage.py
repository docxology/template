"""Keep smoke and metadata pytest processes free of coverage."""

import sys
from collections.abc import Iterator
from typing import Any

import pytest

from infrastructure.core.testing.coverage_policy import _METADATA_OPTION, _METADATA_RESULT


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(_METADATA_OPTION, choices=("capability", "discovery"), default=None)


def _metadata_mode(config: pytest.Config, options: Any) -> str | None:
    arguments = config.invocation_params.args
    option_end = arguments.index("--") if "--" in arguments else len(arguments)
    for argument in reversed(arguments[:option_end]):
        if argument in (f"{_METADATA_OPTION}=capability", f"{_METADATA_OPTION}=discovery"):
            mode = argument.split("=", 1)[1]
            if getattr(options, "template_pytest_metadata", None) != mode:
                raise pytest.UsageError("Could not admit the pytest metadata mode")
            return mode
    return None


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_load_initial_conftests(early_config: pytest.Config, args: list[str]) -> Iterator[None]:
    """Read the admitted parser or disable coverage before its controller starts."""
    options: Any = early_config.known_args_namespace
    if _metadata_mode(early_config, options) == "capability":
        absent = object()
        supported = early_config.getoption("--cov-datafile", absent) is not absent
        sys.stdout.write(f"\n{_METADATA_RESULT}capability:{'yes' if supported else 'no'}\n")
        sys.stdout.flush()
        raise SystemExit(0)
    if hasattr(options, "no_cov") and not options.no_cov:
        # pytest-cov reads the early namespace, then pytest reparses argv.
        options.no_cov = True
        option_end = args.index("--") if "--" in args else len(args)
        args.insert(option_end, "--no-cov")
    yield


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_cmdline_main(config: pytest.Config) -> Iterator[None]:
    """Keep diagnostic collection out of worker and loop-on-failure modes."""
    options: Any = config.option
    if _metadata_mode(config, options) == "discovery":
        if not options.collectonly:
            raise pytest.UsageError("Diagnostic pytest invocation requires collection-only mode")
        if hasattr(options, "numprocesses"):
            options.numprocesses = 0
        if hasattr(options, "looponfail"):
            options.looponfail = False
    yield


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Report the selected item count from the successful diagnostic session."""
    config = session.config
    count = session.testscollected
    if (
        exitstatus == 0
        and config.option.collectonly
        and _metadata_mode(config, config.option) == "discovery"
        and count > 0
        and count == len(session.items)
    ):
        sys.stdout.write(f"\n{_METADATA_RESULT}discovery:{count}\n")
        sys.stdout.flush()
