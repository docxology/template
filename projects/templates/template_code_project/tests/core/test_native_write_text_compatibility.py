"""The observed byte route preserves the original platform text encoding."""

import json
from pathlib import Path

from template_code_project.core.manuscript_variables import save_variables


def test_variable_bytes_match_utf8_json_text_writer(tmp_path: Path) -> None:
    variables = {"value": "résumé", "formatted": "a\nb", "nested": "α"}
    expected = tmp_path / "expected.json"
    expected.write_text(json.dumps(variables, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
    actual = tmp_path / "actual.json"
    assert save_variables(variables, actual) == actual
    assert actual.read_bytes() == expected.read_bytes()
    assert json.loads(actual.read_bytes()) == variables
