"""Tests for COGANT ``check_coverage_table.py`` parse helpers.

Loads the script by path from staging when present, otherwise from the
committed ``tests/fixtures/private_project/cogant`` fallback.
"""

from __future__ import annotations

import importlib.util

import pytest

from tests.infra_tests._cogant_paths import cogant_root

pytestmark = pytest.mark.private_project

_SCRIPT = cogant_root() / "tools/check_coverage_table.py"


def _load_check_coverage_module():
    if not _SCRIPT.is_file():
        pytest.fail(f"COGANT check_coverage_table script not present: {_SCRIPT}")
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
