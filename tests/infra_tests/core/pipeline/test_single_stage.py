#!/usr/bin/env python3
"""Tests for infrastructure.core.pipeline.single_stage."""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.core.pipeline.single_stage import execute_single_stage


def test_unknown_stage_exits_with_message() -> None:
    with pytest.raises(SystemExit, match="Unknown stage"):
        execute_single_stage("not_a_real_stage", "template_code_project", Path("."))


def test_known_stage_key_is_mapped() -> None:
    from infrastructure.core.pipeline.stage_registry import STAGE_DISPATCH

    assert "render_pdf" in STAGE_DISPATCH
    assert STAGE_DISPATCH["render_pdf"].script.endswith("stage_03_render.py")


def test_project_custom_stage_executes_by_key_and_display_name(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "demo"
    script = project / "scripts" / "custom_stage.py"
    script.parent.mkdir(parents=True)
    script.write_text(
        """from pathlib import Path
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--project", required=True)
args = parser.parse_args()
Path("custom-stage-ran.txt").write_text(args.project, encoding="utf-8")
""",
        encoding="utf-8",
    )
    (project / "pipeline.yaml").write_text(
        """stages:
  - name: Custom Research Stage
    key: custom_research
    script: projects/demo/scripts/custom_stage.py
""",
        encoding="utf-8",
    )

    assert execute_single_stage("custom_research", "demo", tmp_path) == 0
    marker = tmp_path / "custom-stage-ran.txt"
    assert marker.read_text(encoding="utf-8") == "demo"
    marker.unlink()
    assert execute_single_stage("Custom Research Stage", "demo", tmp_path) == 0
    assert marker.read_text(encoding="utf-8") == "demo"


def test_project_pipeline_legacy_bare_script_uses_repository_scripts_dir(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "demo"
    project.mkdir(parents=True)
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "custom_stage.py").write_text(
        "from pathlib import Path\n"
        "import argparse\n"
        "parser = argparse.ArgumentParser()\n"
        "parser.add_argument('--project', required=True)\n"
        "args = parser.parse_args()\n"
        "Path('bare-stage-ran.txt').write_text(args.project, encoding='utf-8')\n",
        encoding="utf-8",
    )
    (project / "pipeline.yaml").write_text(
        "stages:\n  - name: Legacy custom stage\n    key: legacy_custom\n    script: custom_stage.py\n",
        encoding="utf-8",
    )

    assert execute_single_stage("legacy_custom", "demo", tmp_path) == 0
    assert (tmp_path / "bare-stage-ran.txt").read_text(encoding="utf-8") == "demo"


def test_builtin_clean_stage_executes_from_project_dag(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "demo"
    output = project / "output"
    output.mkdir(parents=True)
    stale = output / "stale.txt"
    stale.write_text("stale", encoding="utf-8")
    (project / "pipeline.yaml").write_text(
        """stages:
  - name: Clean Output Directories
    key: clean
    method: _run_clean_outputs
""",
        encoding="utf-8",
    )

    assert execute_single_stage("clean", "demo", tmp_path) == 0
    assert not stale.exists()
    assert (output / "logs" / "pipeline.log").is_file()


def test_explicit_pipeline_executes_custom_script_stage(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "demo"
    script = project / "scripts" / "publish.py"
    script.parent.mkdir(parents=True)
    script.write_text(
        """from pathlib import Path
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--project", required=True)
args = parser.parse_args()
Path("explicit-pipeline-ran.txt").write_text(args.project, encoding="utf-8")
""",
        encoding="utf-8",
    )
    pipeline = project / "methods_pipeline.yaml"
    pipeline.write_text(
        """stages:
  - name: Publication Validation
    key: publication_validation
    script: projects/demo/scripts/publish.py
    method: descriptive methods evidence label
""",
        encoding="utf-8",
    )

    assert (
        execute_single_stage(
            "publication_validation",
            "demo",
            tmp_path,
            pipeline_path=pipeline,
        )
        == 0
    )
    assert (tmp_path / "explicit-pipeline-ran.txt").read_text(encoding="utf-8") == "demo"


@pytest.mark.parametrize(("allow_skip", "expected"), [(True, 0), (False, 2)])
def test_single_stage_matches_dag_allow_skip_exit_semantics(
    tmp_path: Path,
    allow_skip: bool,
    expected: int,
) -> None:
    project = tmp_path / "projects" / "demo"
    script = project / "scripts" / "optional.py"
    script.parent.mkdir(parents=True)
    script.write_text("raise SystemExit(2)\n", encoding="utf-8")
    (project / "pipeline.yaml").write_text(
        "stages:\n"
        "  - name: Optional Stage\n"
        "    key: optional\n"
        "    script: projects/demo/scripts/optional.py\n"
        f"    allow_skip: {'true' if allow_skip else 'false'}\n",
        encoding="utf-8",
    )

    assert execute_single_stage("optional", "demo", tmp_path) == expected
