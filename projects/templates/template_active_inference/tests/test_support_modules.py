"""RunLogger and small support-module tests."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from orchestration import full_verification
from ontology.bindings import load_section_ontology, validate_gnn_ontology
from simulation.logging_utils import RunLogger


def test_run_logger_emit_and_records(tmp_path: Path) -> None:
    log = RunLogger(tmp_path / "runs.jsonl")
    log.fresh()
    log.emit({"event": "test", "value": 1})
    records = log.records()
    assert len(records) == 1
    assert records[0]["event"] == "test"


def test_run_logger_emit_recreates_missing_parent_after_fresh(tmp_path: Path) -> None:
    log = RunLogger(tmp_path / "logs" / "runs.jsonl")
    log.fresh()
    shutil.rmtree(log.path.parent)

    log.emit({"event": "test", "value": 2})

    assert log.records()[0]["value"] == 2


def test_sheaf_package_exports_public_symbols() -> None:
    from manuscript.sheaf import (
        GENERATED_RENDERERS,
        ImradBlock,
        SectionKind,
        coverage_cell_symbol,
        resolve_track_body,
    )

    assert coverage_cell_symbol("black") == "P"
    assert "section_figures" in GENERATED_RENDERERS
    assert resolve_track_body.__name__ == "resolve_track_body"
    assert ImradBlock is not None
    assert SectionKind is not None


def test_ontology_helpers() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "manuscript" / "sections" / "imrad" / "intro_contributions" / "ontology.yaml"
    terms = load_section_ontology(path)
    assert "location" in terms
    discussion = root / "manuscript" / "sections" / "imrad" / "discussion_outlook" / "ontology.yaml"
    discussion_terms = load_section_ontology(discussion)
    assert discussion_terms["pedagogical_scope"] == "Pedagogical scope"
    gnn = root / "gnn" / "bernoulli_toy.gnn.md"
    assert not validate_gnn_ontology(gnn)


def test_full_verification_run_sets_defaults(tmp_path: Path, capsys) -> None:
    calls: list[dict] = []

    class Result:
        returncode = 0

    def fake_run(cmd, *, cwd, env, text, check):
        calls.append({"cmd": cmd, "cwd": cwd, "env": env, "text": text, "check": check})
        return Result()

    ticks = iter((10.0, 12.5))
    full_verification._run(
        tmp_path,
        ["uv", "run", "pytest", "-q"],
        "Smoke",
        env={"EXTRA_FLAG": "1"},
        process_runner=fake_run,
        clock=lambda: next(ticks),
    )

    assert calls[0]["cmd"] == ["uv", "run", "pytest", "-q"]
    assert calls[0]["cwd"] == tmp_path
    assert calls[0]["env"]["MPLBACKEND"] == "Agg"
    assert calls[0]["env"]["PYTHONUNBUFFERED"] == "1"
    assert calls[0]["env"]["TEMPLATE_ACTIVE_INFERENCE_FIXED_POINT_PASSES"] == "2"
    assert calls[0]["env"]["EXTRA_FLAG"] == "1"
    assert "Smoke" in capsys.readouterr().out


def test_full_verification_run_raises_on_failure(tmp_path: Path) -> None:
    class Result:
        returncode = 7

    with pytest.raises(RuntimeError, match="Explode failed"):
        full_verification._run(
            tmp_path,
            ["false"],
            "Explode",
            process_runner=lambda *args, **kwargs: Result(),
            clock=lambda: 1.0,
        )


def test_coverage_command_defers_threshold_until_final_chunk() -> None:
    partial = full_verification._coverage_command(["tests/test_one.py"], append=False, final=False)
    final = full_verification._coverage_command(["tests/test_two.py"], append=True, final=True)

    assert "--cov-fail-under=0" in partial
    assert "--cov-fail-under=90" not in partial
    assert "--cov-fail-under=90" in final


def test_profile_args_are_additive_and_keep_live_services_opt_in() -> None:
    quick = full_verification._profile_marker_args("quick")
    release = full_verification._profile_marker_args("release")
    exhaustive = full_verification._profile_marker_args("exhaustive")

    assert quick[0] == release[0] == exhaustive[0] == "-m"
    assert "not slow" in quick[1]
    assert "not slow" not in release[1]
    assert "not long_running" in release[1]
    assert "not long_running" not in exhaustive[1]
    assert all("not requires_ollama" in expression[1] for expression in (quick, release, exhaustive))


def test_run_verification_skip_chunks_orders_preflight_and_postflight(tmp_path: Path) -> None:
    calls: list[tuple[str, list[str]]] = []
    full_verification.run_verification(
        tmp_path,
        skip_chunks=True,
        command_runner=lambda project_root, cmd, label, env=None: calls.append((label, cmd)),
    )

    labels = [label for label, _ in calls]
    assert labels[0] == "Compose manuscript sections"
    assert "Simulate SI T-maze" in labels
    assert "Generate validation spine" in labels
    assert "Generate canonical sheaf tracks" in labels
    assert "Focused contract and infrastructure checks" not in labels
    assert "Full suite coverage pass" not in labels
    assert "Coverage pass: Focused contract and infrastructure checks" in labels
    first_coverage_cmd = dict(calls)["Coverage pass: Focused contract and infrastructure checks"]
    second_coverage_cmd = dict(calls)["Coverage pass: Gate and manuscript-focused checks"]
    assert "--cov=src" in first_coverage_cmd
    assert "--cov-append" not in first_coverage_cmd
    assert "--cov-append" in second_coverage_cmd


def test_run_verification_can_use_legacy_monolithic_coverage(tmp_path: Path) -> None:
    calls: list[tuple[str, list[str]]] = []
    full_verification.run_verification(
        tmp_path,
        skip_chunks=True,
        monolithic_coverage=True,
        command_runner=lambda project_root, cmd, label, env=None: calls.append((label, cmd)),
    )

    labels = [label for label, _ in calls]
    assert "Coverage pass: Focused contract and infrastructure checks" not in labels
    assert "Full suite coverage pass" in labels
    coverage_cmd = dict(calls)["Full suite coverage pass"]
    assert coverage_cmd[-1] == "--maxfail=1"


def test_run_verification_includes_chunked_sheaf_modules(tmp_path: Path) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    sheaf_path = tests_dir / "test_sheaf_alpha.py"
    sheaf_path.write_text("", encoding="utf-8")
    calls: list[tuple[str, list[str]]] = []
    full_verification.run_verification(
        tmp_path,
        skip_chunks=False,
        command_runner=lambda project_root, cmd, label, env=None: calls.append((label, cmd)),
    )

    chunks = dict(calls)
    assert "Focused contract and infrastructure checks" in chunks
    assert "Gate and manuscript-focused checks" in chunks
    roadmap_cmd = chunks["Roadmap and sheaf consolidation checks"]
    assert str(sheaf_path.relative_to(tmp_path)) in roadmap_cmd


def test_refresh_cache_skips_an_unchanged_generator_fixed_point(tmp_path: Path) -> None:
    calls: list[str] = []
    cache = full_verification._RefreshCache()
    command = ["uv", "run", "python", "scripts", "compose_manuscript.py"]

    def run(_root: Path, _cmd: list[str], label: str) -> None:
        calls.append(label)

    cache.run(tmp_path, command, "first", run)
    cache.run(tmp_path, command, "second", run)

    assert calls == ["first"]


def test_refresh_cache_invalidates_after_a_generator_input_or_output_changes(tmp_path: Path) -> None:
    calls: list[str] = []
    cache = full_verification._RefreshCache()
    command = ["uv", "run", "python", "scripts", "z_generate_manuscript_variables.py"]

    def run(root: Path, _cmd: list[str], label: str) -> None:
        calls.append(label)
        target = root / "output" / "data" / "variables.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(str(len(calls)), encoding="utf-8")

    cache.run(tmp_path, command, "first", run)
    (tmp_path / "input.txt").write_text("changed", encoding="utf-8")
    cache.run(tmp_path, command, "second", run)
    cache.run(tmp_path, command, "third", run)

    assert calls == ["first", "second"]
