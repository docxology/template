"""Tests for the shared CLI scaffold and argparse schema introspection (no mocks)."""

from __future__ import annotations

import argparse
import json

from infrastructure.core.cli_scaffold import (
    add_format_arg,
    add_repo_root_arg,
    add_schema_flag,
    emit_schema,
    parser_schema,
)
from infrastructure.core.pipeline.cli import main as pipeline_cli_main


def _sample_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="sample", description="A sample CLI.")
    add_repo_root_arg(p)
    sub = p.add_subparsers(dest="command")
    run = sub.add_parser("run", help="Run it")
    run.add_argument("target", help="What to run")
    run.add_argument("--count", type=int, default=3, help="How many")
    add_format_arg(run)
    return p


class TestSharedFlags:
    def test_repo_root_default(self) -> None:
        p = argparse.ArgumentParser()
        add_repo_root_arg(p)
        assert p.parse_args([]).repo_root == "."

    def test_format_choices(self) -> None:
        p = argparse.ArgumentParser()
        add_format_arg(p)
        assert p.parse_args([]).format == "json"
        assert p.parse_args(["--format", "table"]).format == "table"

    def test_schema_flag(self) -> None:
        p = argparse.ArgumentParser()
        add_schema_flag(p)
        assert p.parse_args(["--schema"]).schema is True


class TestParserSchema:
    def test_top_level_options_and_subcommands(self) -> None:
        schema = parser_schema(_sample_parser())
        assert schema["prog"] == "sample"
        assert any(o["name"] == "repo_root" for o in schema["options"])
        assert "run" in schema["subcommands"]

    def test_subcommand_arg_details(self) -> None:
        schema = parser_schema(_sample_parser())
        run = schema["subcommands"]["run"]
        by_name = {o["name"]: o for o in run["options"]}
        assert by_name["target"]["positional"] is True
        assert by_name["target"]["required"] is True
        assert by_name["count"]["type"] == "integer"
        assert by_name["count"]["default"] == 3
        assert by_name["format"]["choices"] == ["json", "table"]

    def test_help_action_excluded(self) -> None:
        schema = parser_schema(_sample_parser())
        assert all(o["name"] != "help" for o in schema["options"])

    def test_emit_schema(self, capsys) -> None:
        rc = emit_schema(_sample_parser())
        assert rc == 0
        parsed = json.loads(capsys.readouterr().out)
        assert parsed["prog"] == "sample"


class TestPipelineSchemaAdopter:
    def test_pipeline_schema_flag(self, capsys) -> None:
        rc = pipeline_cli_main(["describe-pipeline", "--schema"])
        assert rc == 0
        schema = json.loads(capsys.readouterr().out)
        # describe-pipeline exposes --format/--core-only/--yaml/--project/--repo-root
        sub = schema["subcommands"]["describe-pipeline"]
        names = {o["name"] for o in sub["options"]}
        assert {"format", "core_only", "yaml", "project", "repo_root"} <= names
