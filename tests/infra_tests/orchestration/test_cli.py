"""Tests for infrastructure.orchestration.cli."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.orchestration.cli import (
    _cmd_list_projects,
    _cmd_menu,
    _resolve_repo_root,
    build_parser,
    main,
)


def test_build_parser_help_works() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit) as info:
        parser.parse_args(["--help"])
    assert info.value.code == 0


def test_build_parser_recognizes_pipeline_subcommand() -> None:
    parser = build_parser()
    ns = parser.parse_args(["pipeline", "--project", "template_code_project", "--core-only"])
    assert ns.command == "pipeline"
    assert ns.project == "template_code_project"
    assert ns.core_only is True


def test_build_parser_recognizes_secure_subcommand() -> None:
    parser = build_parser()
    ns = parser.parse_args(["secure", "--steganography-only"])
    assert ns.command == "secure"
    assert ns.steganography_only is True


def test_build_parser_unknown_subcommand_raises() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["bogus_subcommand"])


def test_resolve_repo_root_default_points_to_repo() -> None:
    parser = build_parser()
    ns = parser.parse_args([])
    root = _resolve_repo_root(ns)
    # Default points 2 parents up from the orchestration package, which
    # must contain an `infrastructure/` directory.
    assert (root / "infrastructure").is_dir()


def test_resolve_repo_root_respects_override(tmp_path: Path) -> None:
    parser = build_parser()
    ns = parser.parse_args(["--repo-root", str(tmp_path), "list-projects"])
    assert _resolve_repo_root(ns) == tmp_path


def test_cmd_menu_prints_to_stdout(fake_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    parser = build_parser()
    ns = parser.parse_args(["--repo-root", str(fake_repo), "menu", "--project", "template_code_project"])
    rc = _cmd_menu(ns)
    captured = capsys.readouterr()
    assert rc == 0
    assert "MANUSCRIPT PIPELINE" in captured.out
    assert "template_code_project" in captured.out


def test_cmd_list_projects(fake_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    parser = build_parser()
    ns = parser.parse_args(["--repo-root", str(fake_repo), "list-projects"])
    rc = _cmd_list_projects(ns)
    captured = capsys.readouterr()
    assert rc == 0
    assert "template_code_project" in captured.out
    assert "template_prose_project" in captured.out
    assert "template_search_project" in captured.out


def test_main_with_list_projects(fake_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["--repo-root", str(fake_repo), "list-projects"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "template_code_project" in captured.out


def test_main_with_menu(fake_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["--repo-root", str(fake_repo), "menu"])
    assert rc == 0


def test_main_pipeline_rejects_invalid_project(fake_repo: Path) -> None:
    """Path-traversal slugs raise ValueError before any executor is invoked."""
    with pytest.raises(ValueError, match=r"\.\."):
        main(
            [
                "--repo-root",
                str(fake_repo),
                "pipeline",
                "--project",
                "../etc/passwd",
            ]
        )


def test_module_help_via_subprocess() -> None:
    """End-to-end check: ``python -m infrastructure.orchestration --help`` exits 0."""
    repo_root = Path(__file__).resolve().parents[3]
    result = subprocess.run(
        [sys.executable, "-m", "infrastructure.orchestration", "--help"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "pipeline" in result.stdout
    assert "secure" in result.stdout


def test_module_list_projects_via_subprocess(fake_repo: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "infrastructure.orchestration",
            "--repo-root",
            str(fake_repo),
            "list-projects",
        ],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "template_code_project" in result.stdout


# ---------------------------------------------------------------------------
# Subcommand dispatch via patched runners
# ---------------------------------------------------------------------------


class _SpyRunner:
    """Simple recording stand-in for PipelineRunner."""

    def __init__(self, repo_root, stream=None):
        self.repo_root = repo_root
        self.runs: list = []
        self.multi_runs: list = []

    def run(self, invocation):
        self.runs.append(invocation)
        return 0

    def run_multi(self, invocation):
        self.multi_runs.append(invocation)
        return 0


@pytest.fixture
def patch_runner(monkeypatch: pytest.MonkeyPatch):
    holder: dict[str, _SpyRunner] = {}

    def _factory(repo_root, stream=None):
        spy = _SpyRunner(repo_root, stream)
        holder["last"] = spy
        return spy

    monkeypatch.setattr("infrastructure.orchestration.cli.PipelineRunner", _factory)
    return holder


def test_cmd_pipeline_with_explicit_project(fake_repo: Path, patch_runner) -> None:
    rc = main(
        [
            "--repo-root",
            str(fake_repo),
            "pipeline",
            "--project",
            "template_code_project",
        ]
    )
    assert rc == 0
    spy = patch_runner["last"]
    assert len(spy.runs) == 1
    assert spy.runs[0].project == "template_code_project"
    assert spy.runs[0].core_only is False


def test_cmd_pipeline_default_project(fake_repo: Path, patch_runner) -> None:
    rc = main(["--repo-root", str(fake_repo), "pipeline"])
    assert rc == 0
    spy = patch_runner["last"]
    assert spy.runs[0].project == "template_code_project"


def test_cmd_pipeline_default_no_canonical(monkeypatch, tmp_path: Path, patch_runner) -> None:
    """When template_code_project absent, default to first discovered."""
    proj = tmp_path / "projects" / "rotating_alpha"
    (proj / "src").mkdir(parents=True)
    (proj / "tests").mkdir()
    (proj / "src" / "__init__.py").write_text("", encoding="utf-8")
    (proj / "tests" / "__init__.py").write_text("", encoding="utf-8")
    rc = main(["--repo-root", str(tmp_path), "pipeline"])
    assert rc == 0
    spy = patch_runner["last"]
    assert spy.runs[0].project == "rotating_alpha"


def test_cmd_pipeline_no_projects(tmp_path: Path, patch_runner) -> None:
    (tmp_path / "projects").mkdir()
    rc = main(["--repo-root", str(tmp_path), "pipeline"])
    assert rc == 1


def test_cmd_pipeline_all_projects_routes_to_multi(fake_repo: Path, patch_runner) -> None:
    rc = main(["--repo-root", str(fake_repo), "pipeline", "--all-projects", "--core-only"])
    assert rc == 0
    spy = patch_runner["last"]
    assert len(spy.multi_runs) == 1
    assert spy.multi_runs[0].skip_llm is True


def test_cmd_pipeline_core_only(fake_repo: Path, patch_runner) -> None:
    rc = main(
        [
            "--repo-root",
            str(fake_repo),
            "pipeline",
            "--project",
            "template_code_project",
            "--core-only",
            "--skip-infra",
            "--resume",
        ]
    )
    assert rc == 0
    inv = patch_runner["last"].runs[0]
    assert inv.core_only is True
    assert inv.skip_infra is True
    assert inv.resume is True


def test_cmd_multi(fake_repo: Path, patch_runner) -> None:
    rc = main(["--repo-root", str(fake_repo), "multi", "--core-only", "--skip-infra"])
    assert rc == 0
    inv = patch_runner["last"].multi_runs[0]
    assert inv.skip_infra is True
    assert inv.skip_llm is True


def test_cmd_multi_no_executive_report(fake_repo: Path, patch_runner) -> None:
    rc = main(["--repo-root", str(fake_repo), "multi", "--no-executive-report"])
    assert rc == 0
    assert patch_runner["last"].multi_runs[0].run_executive_report is False


def test_cmd_secure_steg_only(fake_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    def _fake_run_secure(repo_root, options):
        captured["repo_root"] = repo_root
        captured["options"] = options
        return 0

    monkeypatch.setattr("infrastructure.orchestration.cli.run_secure_pipeline", _fake_run_secure)
    rc = main(["--repo-root", str(fake_repo), "secure", "--steganography-only"])
    assert rc == 0
    assert captured["options"].steganography_only is True


def test_cmd_secure_deterministic_flag_sets_env_var(
    fake_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--deterministic must set STEGANOGRAPHY_DETERMINISTIC=1 before run_secure_pipeline."""
    monkeypatch.delenv("STEGANOGRAPHY_DETERMINISTIC", raising=False)
    observed: dict[str, str | None] = {}

    def _fake_run_secure(repo_root, options):
        import os as _os

        observed["env"] = _os.environ.get("STEGANOGRAPHY_DETERMINISTIC")
        return 0

    monkeypatch.setattr("infrastructure.orchestration.cli.run_secure_pipeline", _fake_run_secure)
    rc = main(
        [
            "--repo-root",
            str(fake_repo),
            "secure",
            "--steganography-only",
            "--deterministic",
        ]
    )
    assert rc == 0
    assert observed["env"] == "1"


def test_cmd_secure_without_deterministic_does_not_set_env_var(
    fake_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Omitting --deterministic must leave STEGANOGRAPHY_DETERMINISTIC unset."""
    monkeypatch.delenv("STEGANOGRAPHY_DETERMINISTIC", raising=False)
    observed: dict[str, str | None] = {}

    def _fake_run_secure(repo_root, options):
        import os as _os

        observed["env"] = _os.environ.get("STEGANOGRAPHY_DETERMINISTIC")
        return 0

    monkeypatch.setattr("infrastructure.orchestration.cli.run_secure_pipeline", _fake_run_secure)
    rc = main(["--repo-root", str(fake_repo), "secure", "--steganography-only"])
    assert rc == 0
    assert observed["env"] is None


def test_secure_help_advertises_both_modes() -> None:
    """`secure --help` must document both modes plus --deterministic."""
    parser = build_parser()
    subparsers_action = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))
    secure_parser = subparsers_action.choices["secure"]
    text = secure_parser.format_help()
    # Mode advertisement
    assert "--steganography-only" in text
    assert "--project" in text
    # Examples in epilog
    assert "Examples:" in text
    # New flag documented
    assert "--deterministic" in text
    assert "STEGANOGRAPHY_DETERMINISTIC" in text


def test_cmd_menu_default_project_no_canonical(tmp_path: Path, capsys) -> None:
    proj = tmp_path / "projects" / "rotating_a"
    (proj / "src").mkdir(parents=True)
    (proj / "tests").mkdir()
    (proj / "src" / "__init__.py").write_text("", encoding="utf-8")
    (proj / "tests" / "__init__.py").write_text("", encoding="utf-8")
    rc = main(["--repo-root", str(tmp_path), "menu"])
    assert rc == 0
    assert "rotating_a" in capsys.readouterr().out


def test_cmd_menu_no_projects(tmp_path: Path, capsys) -> None:
    (tmp_path / "projects").mkdir()
    rc = main(["--repo-root", str(tmp_path), "menu"])
    assert rc == 0
    assert "(none)" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Interactive loop (driven by canned input queue)
# ---------------------------------------------------------------------------


def test_interactive_quit_immediate(fake_repo: Path, patch_runner) -> None:
    from infrastructure.orchestration.cli import _interactive

    rc = _interactive(fake_repo, reader=lambda: "q")
    assert rc == 0


def test_interactive_eof_returns_zero(fake_repo: Path, patch_runner) -> None:
    from infrastructure.orchestration.cli import _interactive

    def _reader() -> str:
        raise EOFError

    assert _interactive(fake_repo, reader=_reader) == 0


def test_interactive_no_projects_returns_one(tmp_path: Path) -> None:
    from infrastructure.orchestration.cli import _interactive

    (tmp_path / "projects").mkdir()
    assert _interactive(tmp_path, reader=lambda: "q") == 1


def test_interactive_show_info_then_quit(fake_repo: Path, capsys) -> None:
    from infrastructure.orchestration.cli import _interactive

    answers = iter(["i", "q"])
    rc = _interactive(fake_repo, reader=lambda: next(answers))
    assert rc == 0
    assert "Current project" in capsys.readouterr().out


def test_interactive_change_project_then_quit(fake_repo: Path) -> None:
    from infrastructure.orchestration.cli import _interactive

    # 'p' opens picker, '0' selects first, then 'q' quits
    answers = iter(["p", "0", "q"])
    rc = _interactive(fake_repo, reader=lambda: next(answers))
    assert rc == 0


def test_interactive_invalid_then_quit(fake_repo: Path, capsys) -> None:
    from infrastructure.orchestration.cli import _interactive

    answers = iter(["zzz", "q"])
    rc = _interactive(fake_repo, reader=lambda: next(answers))
    assert rc == 0
    assert "Invalid input" in capsys.readouterr().err


def test_interactive_runs_full_pipeline_via_key_9(fake_repo: Path) -> None:
    from infrastructure.orchestration.cli import _interactive

    spy = _SpyRunner(fake_repo)
    answers = iter(["9", "q"])
    rc = _interactive(fake_repo, reader=lambda: next(answers), runner=spy)
    assert rc == 0
    assert len(spy.runs) == 1


def test_interactive_failed_op_breaks_sequence(fake_repo: Path) -> None:
    from infrastructure.orchestration.cli import _interactive

    class _Failing(_SpyRunner):
        def run(self, invocation):
            super().run(invocation)
            return 1

    spy = _Failing(fake_repo)
    answers = iter(["89", "q"])  # chained: core then full; first should fail
    rc = _interactive(fake_repo, reader=lambda: next(answers), runner=spy)
    assert rc == 0
    # Only the first invocation runs because of failure-break.
    assert len(spy.runs) == 1


def test_interactive_dispatches_stage_keys(fake_repo: Path) -> None:
    from infrastructure.orchestration.cli import _interactive

    received: list[str] = []

    def _stage_runner(stage_key: str, project: str, repo_root: Path) -> int:
        received.append(stage_key)
        return 0

    spy = _SpyRunner(fake_repo)
    answers = iter(["234", "q"])  # chained: 2,3,4
    _interactive(
        fake_repo,
        reader=lambda: next(answers),
        runner=spy,
        stage_runner=_stage_runner,
    )
    assert received == ["analysis", "render_pdf", "validate"]


def test_interactive_dispatch_multi_keys(fake_repo: Path) -> None:
    from infrastructure.orchestration.cli import _interactive

    spy = _SpyRunner(fake_repo)
    answers = iter(["a", "b", "c", "d", "q"])
    _interactive(fake_repo, reader=lambda: next(answers), runner=spy)
    assert len(spy.multi_runs) == 4
    # a: full ; b: skip infra; c: skip llm; d: skip both
    assert spy.multi_runs[0].skip_infra is False
    assert spy.multi_runs[0].skip_llm is False
    assert spy.multi_runs[1].skip_infra is True
    assert spy.multi_runs[2].skip_llm is True
    assert spy.multi_runs[3].skip_infra is True
    assert spy.multi_runs[3].skip_llm is True


def test_interactive_multi_d_alone_exits_without_second_prompt(fake_repo: Path, capsys) -> None:
    """Successful sole menu key ``d`` ends the interactive session (no menu redraw)."""
    from infrastructure.orchestration.cli import _interactive

    spy = _SpyRunner(fake_repo)
    rc = _interactive(fake_repo, reader=lambda: "d", runner=spy)
    assert rc == 0
    assert len(spy.multi_runs) == 1
    assert spy.multi_runs[0].skip_infra is True
    assert spy.multi_runs[0].skip_llm is True
    out = capsys.readouterr().out
    # One menu banner only — second iteration would print a second "=" * 64 block opener.
    assert out.count("MANUSCRIPT PIPELINE") == 1


def test_interactive_p_quit_returns_zero(fake_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    from infrastructure.orchestration.cli import _interactive

    # 'p' opens picker, then 'q' inside picker => returns None => loop returns 0
    answers = iter(["p", "q"])
    rc = _interactive(fake_repo, reader=lambda: next(answers))
    assert rc == 0
    out = capsys.readouterr().out
    assert "Available projects:" in out
    assert "Choice [index / a=all / q=quit]:" in out


def test_interactive_p_all_keeps_loop(fake_repo: Path) -> None:
    from infrastructure.orchestration.cli import _interactive

    answers = iter(["p", "a", "q"])
    rc = _interactive(fake_repo, reader=lambda: next(answers))
    assert rc == 0


def test_dispatch_menu_key_unknown_returns_one(fake_repo: Path) -> None:
    from infrastructure.orchestration.cli import _dispatch_menu_key

    spy = _SpyRunner(fake_repo)
    rc = _dispatch_menu_key("zzz", "template_code_project", fake_repo, spy)
    assert rc == 1


def test_dispatch_menu_key_f_skips_infra(fake_repo: Path) -> None:
    from infrastructure.orchestration.cli import _dispatch_menu_key

    spy = _SpyRunner(fake_repo)
    rc = _dispatch_menu_key("f", "template_code_project", fake_repo, spy)
    assert rc == 0
    assert spy.runs[0].skip_infra is True


def test_interactive_empty_input_loops(fake_repo: Path) -> None:
    """An empty enter cycles back to the menu without dispatch."""
    from infrastructure.orchestration.cli import _interactive

    answers = iter(["", "q"])
    rc = _interactive(fake_repo, reader=lambda: next(answers))
    assert rc == 0


def test_main_no_subcommand_runs_interactive(fake_repo: Path, monkeypatch) -> None:
    """Bare invocation (no subcommand) routes to _interactive."""
    captured = {}

    def _fake_interactive(repo_root, **kwargs):
        captured["repo_root"] = repo_root
        return 0

    monkeypatch.setattr("infrastructure.orchestration.cli._interactive", _fake_interactive)
    rc = main(["--repo-root", str(fake_repo)])
    assert rc == 0
    assert captured["repo_root"] == fake_repo
