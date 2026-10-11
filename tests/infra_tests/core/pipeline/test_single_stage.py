#!/usr/bin/env python3
"""Tests for infrastructure.core.pipeline.single_stage."""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.core.pipeline.single_stage import execute_single_stage
from infrastructure.core.pipeline.stages import PIPELINE_STAGE_TIMEOUT_SECONDS
from infrastructure.reporting.project_verifier import DEFAULT_PROJECT_VERIFIER_TIMEOUT_SECONDS


def test_single_stage_deadline_exceeds_declared_verifier_deadline() -> None:
    assert PIPELINE_STAGE_TIMEOUT_SECONDS > DEFAULT_PROJECT_VERIFIER_TIMEOUT_SECONDS


def test_unknown_stage_returns_invocation_error(tmp_path: Path) -> None:
    assert execute_single_stage("not_a_real_stage", "demo", tmp_path) == 2


def test_known_stage_key_is_mapped() -> None:
    from infrastructure.core.pipeline.stage_registry import known_stage_keys

    assert "render_pdf" in known_stage_keys()


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


def test_retired_bare_script_shape_is_rejected_before_execution(tmp_path: Path) -> None:
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
        "stages:\n  - name: Custom stage\n    key: custom\n    script: custom_stage.py\n",
        encoding="utf-8",
    )

    assert execute_single_stage("custom", "demo", tmp_path) == 2
    assert not (tmp_path / "bare-stage-ran.txt").exists()


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
    contract:
      definition_of_done: Publication evidence verified
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


@pytest.mark.parametrize(("allow_skip", "expected"), [(True, 1), (False, 1)])
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
