"""Tests for the pipeline-introspection CLI (no mocks; real YAML)."""

from __future__ import annotations

import json
from pathlib import Path

from infrastructure.core.pipeline.cli import (
    DEFAULT_PIPELINE_YAML,
    main as pipeline_cli_main,
    stage_rows,
)


class TestStageRows:
    def test_default_pipeline_has_twelve_stages(self) -> None:
        rows = stage_rows(DEFAULT_PIPELINE_YAML)
        assert len(rows) == 12
        names = [r["name"] for r in rows]
        assert names[0] == "Clean Output Directories"
        assert "LLM Scientific Review" in names

    def test_rows_are_topologically_ordered(self) -> None:
        rows = stage_rows(DEFAULT_PIPELINE_YAML)
        order_by_name = {r["name"]: r["order"] for r in rows}
        for row in rows:
            for dep in row["depends_on"]:
                assert order_by_name[dep] < row["order"]

    def test_core_only_excludes_llm(self) -> None:
        rows = stage_rows(DEFAULT_PIPELINE_YAML, exclude_tags={"llm"})
        assert len(rows) == 10
        assert all("llm" not in r["tags"] for r in rows)

    def test_rows_expose_contract_fields(self) -> None:
        rows = stage_rows(DEFAULT_PIPELINE_YAML)
        first = rows[0]
        assert set(["order", "name", "runner", "tags", "optional", "definition_of_done"]).issubset(first)

    def test_synthetic_yaml(self, tmp_path: Path) -> None:
        yaml_path = tmp_path / "pipeline.yaml"
        yaml_path.write_text(
            "stages:\n"
            "  - name: A\n"
            "    method: _a\n"
            "    tags: [core]\n"
            "  - name: B\n"
            "    script: b.py\n"
            "    depends_on: [A]\n"
            "    allow_skip: true\n"
            "    tags: [llm]\n",
            encoding="utf-8",
        )
        rows = stage_rows(yaml_path)
        assert [r["name"] for r in rows] == ["A", "B"]
        assert rows[1]["optional"] is True
        assert rows[1]["runner"] == "b.py"


class TestCli:
    def test_json_output_is_clean(self, capsys) -> None:
        rc = pipeline_cli_main(["describe-pipeline", "--format", "json"])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)  # must parse: no log pollution on stdout
        assert payload["version"] == 1
        assert len(payload["stages"]) == 12

    def test_list_stages_alias(self, capsys) -> None:
        rc = pipeline_cli_main(["list-stages", "--format", "json"])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert len(payload["stages"]) == 12

    def test_table_output(self, capsys) -> None:
        rc = pipeline_cli_main(["describe-pipeline", "--format", "table"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Clean Output Directories" in out
        assert "12 stage(s)" in out

    def test_core_only_flag(self, capsys) -> None:
        rc = pipeline_cli_main(["describe-pipeline", "--format", "json", "--core-only"])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert len(payload["stages"]) == 10

    def test_missing_yaml_returns_error(self, tmp_path: Path) -> None:
        rc = pipeline_cli_main(["describe-pipeline", "--yaml", str(tmp_path / "absent.yaml")])
        assert rc == 1
