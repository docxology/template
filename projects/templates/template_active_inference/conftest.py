"""Project pytest configuration — ensure local src and pymdp env."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent
SRC = PROJECT_ROOT / "src"
TESTS = PROJECT_ROOT / "tests"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

os.environ.setdefault("MPLBACKEND", "Agg")


class _TestEvidencePlugin:
    """Write real warning/discovery counts for a receipt-bearing pytest pass."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.warning_count = 0
        self.deselected_count = 0
        self.selected_count = 0

    def pytest_warning_recorded(
        self,
        warning_message: Any,
        when: str,
        nodeid: str,
        location: tuple[str, int, str] | None,
    ) -> None:
        del warning_message, when, nodeid, location
        self.warning_count += 1

    def pytest_deselected(self, items: list[Any]) -> None:
        self.deselected_count += len(items)

    def pytest_collection_finish(self, session: Any) -> None:
        self.selected_count = len(session.items)

    def pytest_sessionfinish(self, session: Any, exitstatus: int) -> None:
        del session, exitstatus
        payload = {
            "schema_version": "template-active-inference/pytest-evidence/1",
            "warnings": self.warning_count,
            "discovery_count": self.selected_count + self.deselected_count,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(f".{self.path.name}.tmp")
        temporary.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, self.path)


def pytest_addoption(parser: Any) -> None:
    """Register the private machine-readable evidence sidecar option."""
    parser.addoption(
        "--template-test-evidence",
        action="store",
        default="",
        help="write warning and discovery counts for the Stage-01 verifier",
    )


def pytest_configure(config: Any) -> None:
    """Enable evidence capture only when the verifier supplies a path."""
    raw_path = str(config.getoption("--template-test-evidence") or "").strip()
    if not raw_path:
        return
    path = Path(raw_path)
    if not path.is_absolute():
        raise ValueError("--template-test-evidence must be an absolute path")
    config.pluginmanager.register(_TestEvidencePlugin(path), "template-test-evidence")


# Prefer this project's venv site-packages when root pytest delegates here.
# Only add a site-packages directory built for the *running* interpreter's
# Python version; a venv built for a different version (e.g. a standalone
# 3.14 venv picked up by a 3.12 repo run) ships incompatible C-extensions
# (numpy's _multiarray_umath) and would break import on a version mismatch.
VENV_SITE = PROJECT_ROOT / ".venv" / "lib"
if VENV_SITE.is_dir():
    _pyver = f"python{sys.version_info.major}.{sys.version_info.minor}"
    site = VENV_SITE / _pyver / "site-packages"
    if site.is_dir():
        site_str = str(site)
        if site_str not in sys.path:
            sys.path.insert(0, site_str)
