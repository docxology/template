#!/usr/bin/env python3
"""Structured-logging contract for infrastructure.core.cache_gate.

CACHE-GATE-LOGGING-1 negative control: gate diagnostics must flow through the
shared ``get_logger`` (surviving non-TTY pipeline log aggregation), not bare
``print()`` calls. On the pre-change code this test failed because the failure
path emitted nothing via the logging framework.
"""

from __future__ import annotations

import logging
import os

import pytest

from infrastructure.core.cache_gate import run_cache_gate

_GATE_LOGGER = "infrastructure.core.cache_gate"


def test_cache_gate_failure_logs_error(caplog: pytest.LogCaptureFixture) -> None:
    """A gate failure records an ERROR-level log record, not just a print()."""
    prior = os.environ.pop("HERMES_HOME", None)
    try:
        with caplog.at_level(logging.INFO, logger=_GATE_LOGGER):
            assert run_cache_gate() == 1
    finally:
        if prior is not None:
            os.environ["HERMES_HOME"] = prior

    error_records = [r for r in caplog.records if r.name == _GATE_LOGGER and r.levelno == logging.ERROR]
    assert error_records, "cache-gate failure path must log at ERROR level"
    assert any("HERMES_HOME" in r.getMessage() for r in error_records)
