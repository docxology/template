"""SIA-HARNESS-2: fixture-replay vs live-mode separation guardrails.

The public exemplar must demonstrate SIA mechanics *without* implying autonomous
live-code execution in CI. These tests pin the boundary:

* Default/replay runs read **recorded** generations and never invoke a live
  agent or the reference scaffold.
* Replay fails **closed** (raises) when fixtures are missing — it never silently
  fabricates a passing run.
* The ``live`` flag (explicit or config-driven) is the single switch between the
  two modes, and the two modes have distinct on-disk dependencies.

No mocks: every test runs the real loop over real recorded artifacts in a
sandbox copy of the project.
"""

from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path

import pytest

from infrastructure.core.exceptions import ValidationError
from infrastructure.sia import RunConfig, run_sia_loop
from src.loop import build_run_config, fixtures_dir, run_sia_loop_project

PROJECT_ROOT = Path(__file__).resolve().parent.parent

Copy = Callable[[Path], Path]


def _fresh_sandbox(tmp_path: Path, copy_project_sandbox: Copy) -> Path:
    project = tmp_path / "proj"
    copy_project_sandbox(project)
    if (project / "output").exists():
        shutil.rmtree(project / "output")
    return project


# --------------------------------------------------------------------------- #
# Mode selection: live flag is the single switch
# --------------------------------------------------------------------------- #


def test_replay_config_points_at_recorded_fixtures() -> None:
    config = build_run_config(PROJECT_ROOT, live=False)
    assert config.live is False
    assert config.fixtures_dir == fixtures_dir(PROJECT_ROOT)
    assert config.fixtures_dir is not None and config.fixtures_dir.is_dir()


def test_live_config_drops_fixtures_dir() -> None:
    config = build_run_config(PROJECT_ROOT, live=True)
    assert config.live is True
    assert config.fixtures_dir is None


def test_config_default_resolves_to_fixture_replay() -> None:
    """With no explicit override, the committed config (live: false) replays."""
    config = build_run_config(PROJECT_ROOT, live=None)
    assert config.live is False
    assert config.fixtures_dir == fixtures_dir(PROJECT_ROOT)


def test_config_live_true_resolves_to_live_mode(tmp_path: Path, copy_project_sandbox: Copy) -> None:
    """A project whose config sets ``sia.live: true`` resolves to live mode."""
    project = _fresh_sandbox(tmp_path, copy_project_sandbox)
    cfg_path = project / "manuscript" / "config.yaml"
    cfg_path.write_text(
        cfg_path.read_text(encoding="utf-8").replace("live: false", "live: true"),
        encoding="utf-8",
    )
    config = build_run_config(project, live=None)
    assert config.live is True
    assert config.fixtures_dir is None


# --------------------------------------------------------------------------- #
# Replay reads recorded artifacts only (no live execution)
# --------------------------------------------------------------------------- #


def test_replay_ignores_broken_reference_agent(tmp_path: Path, copy_project_sandbox: Copy) -> None:
    """Fixture replay must reconstruct generations from recorded artifacts only.

    The task layout requires the reference scaffold to *exist*, but replay must
    never *execute* it. Replacing the reference with a script that raises on
    execution still yields three replayed generations — proving the recorded
    fixtures, not the live agent, drive replay.
    """
    project = _fresh_sandbox(tmp_path, copy_project_sandbox)
    reference = project / "tasks" / "mini_classify" / "reference" / "reference_target_agent.py"
    reference.write_text(
        'raise RuntimeError("reference agent must not execute during fixture replay")\n',
        encoding="utf-8",
    )

    result = run_sia_loop_project(project, live=False)

    assert len(result.artifacts) == 3
    assert all(a.evaluation is not None for a in result.artifacts)


def test_replay_fails_closed_when_fixtures_missing(tmp_path: Path, copy_project_sandbox: Copy) -> None:
    """Replay must raise — never silently pass — when recorded fixtures are gone."""
    project = _fresh_sandbox(tmp_path, copy_project_sandbox)
    shutil.rmtree(fixtures_dir(project))

    with pytest.raises(ValidationError, match="(?i)fixture"):
        run_sia_loop_project(project, live=False)


def test_replay_fails_closed_when_one_generation_fixture_removed(tmp_path: Path, copy_project_sandbox: Copy) -> None:
    """Removing a single generation's fixture is also caught (no partial fabrication)."""
    project = _fresh_sandbox(tmp_path, copy_project_sandbox)
    shutil.rmtree(fixtures_dir(project) / "gen_2")

    with pytest.raises(ValidationError, match="(?i)fixture"):
        run_sia_loop_project(project, live=False)


def test_zero_generations_fails_closed_not_vacuous_pass(tmp_path: Path, copy_project_sandbox: Copy) -> None:
    """A non-positive max_generations must raise, not return an empty 'successful' run.

    Regression for the silent-pass hole: with ``max_generations=0`` the loop body
    never executes, so the fixture-presence checks inside it are never reached —
    a run over deleted fixtures would otherwise return ``[]`` with no error.
    """
    project = _fresh_sandbox(tmp_path, copy_project_sandbox)
    shutil.rmtree(fixtures_dir(project))  # even with NO fixtures it must fail closed
    config = RunConfig(
        task_dir=project / "tasks" / "mini_classify",
        output_dir=project / "output",
        run_id=42,
        max_generations=0,
        live=False,
        fixtures_dir=None,
        target_timeout_sec=60,
        llm_model="",
    )
    with pytest.raises(ValidationError, match="(?i)max_generations"):
        run_sia_loop(config)


# --------------------------------------------------------------------------- #
# Live mode has a distinct dependency surface
# --------------------------------------------------------------------------- #


def test_task_layout_requires_reference_agent(tmp_path: Path, copy_project_sandbox: Copy) -> None:
    """The harness fails closed if the reference scaffold is absent (either mode)."""
    project = _fresh_sandbox(tmp_path, copy_project_sandbox)
    (project / "tasks" / "mini_classify" / "reference" / "reference_target_agent.py").unlink()

    config = RunConfig(
        task_dir=project / "tasks" / "mini_classify",
        output_dir=project / "output",
        run_id=99,
        max_generations=1,
        live=True,
        fixtures_dir=None,
        target_timeout_sec=60,
        llm_model="",
    )
    with pytest.raises((ValidationError, FileNotFoundError)):
        run_sia_loop(config)
