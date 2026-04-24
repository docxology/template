"""Tests for ``projects_in_progress/cogant/tools/check_coverage_table.py`` parse helpers.

Loads the script by path so the COGANT staging tree stays the single source of truth
without packaging the tool as an importable package.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SCRIPT = _REPO_ROOT / "projects_in_progress/cogant/tools/check_coverage_table.py"


def _load_check_coverage_module():
    if not _SCRIPT.is_file():
        pytest.skip(f"COGANT staging script not present: {_SCRIPT}")
    spec = importlib.util.spec_from_file_location("check_coverage_table", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_parse_coverage_report_maps_file_paths_to_modules() -> None:
    mod = _load_check_coverage_module()
    text = """Name                              Stmts   Miss  Cover
-------------------------------------------------------------
cogant/translate/engine.py          208     35    83%
cogant/simulate/free_energy.py      165      0   100%
TOTAL                              9999   1111    89%
"""
    out = mod._parse_coverage_report(text)
    assert out["cogant.translate.engine"] == (208, 83)
    assert out["cogant.simulate.free_energy"] == (165, 100)


def test_parse_table_extracts_backtick_module_rows(tmp_path) -> None:
    mod = _load_check_coverage_module()
    md = tmp_path / "06_04.md"
    md.write_text(
        """# x

| Module | Stmts | Cover |
|--------|------:|------:|
| `cogant.translate.engine` | 208 | 83% |
| `cogant.simulate.free_energy` | 165 | 100% |

: Table 9 — example. {#tbl:coverage-stmt-modules}
""",
        encoding="utf-8",
    )
    rows = mod._parse_table(md)
    assert rows == [("cogant.translate.engine", 208, 83), ("cogant.simulate.free_energy", 165, 100)]


def test_file_to_module() -> None:
    mod = _load_check_coverage_module()
    assert mod._file_to_module("cogant/x/y.py") == "cogant.x.y"
    assert mod._file_to_module("nopy") == ""
