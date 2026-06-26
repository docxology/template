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


def test_full_verification_run_sets_defaults(monkeypatch, tmp_path: Path, capsys) -> None:
    calls: list[dict] = []

    class Result:
        returncode = 0

    def fake_run(cmd, *, cwd, env, text, check):
        calls.append({"cmd": cmd, "cwd": cwd, "env": env, "text": text, "check": check})
        return Result()

    ticks = iter((10.0, 12.5))
    monkeypatch.setattr(full_verification.subprocess, "run", fake_run)
    monkeypatch.setattr(full_verification.time, "perf_counter", lambda: next(ticks))

    full_verification._run(tmp_path, ["uv", "run", "pytest", "-q"], "Smoke", env={"EXTRA_FLAG": "1"})

    assert calls[0]["cmd"] == ["uv", "run", "pytest", "-q"]
    assert calls[0]["cwd"] == tmp_path
    assert calls[0]["env"]["MPLBACKEND"] == "Agg"
    assert calls[0]["env"]["PYTHONUNBUFFERED"] == "1"
    assert calls[0]["env"]["TEMPLATE_ACTIVE_INFERENCE_FIXED_POINT_PASSES"] == "2"
    assert calls[0]["env"]["EXTRA_FLAG"] == "1"
    assert "Smoke" in capsys.readouterr().out


def test_full_verification_run_raises_on_failure(monkeypatch, tmp_path: Path) -> None:
    class Result:
        returncode = 7

    monkeypatch.setattr(full_verification.subprocess, "run", lambda *args, **kwargs: Result())
    monkeypatch.setattr(full_verification.time, "perf_counter", lambda: 1.0)

    with pytest.raises(RuntimeError, match="Explode failed"):
        full_verification._run(tmp_path, ["false"], "Explode")


def test_run_verification_skip_chunks_orders_preflight_and_postflight(monkeypatch, tmp_path: Path) -> None:
    calls: list[tuple[str, list[str]]] = []
    monkeypatch.setattr(
        full_verification,
        "_run",
        lambda project_root, cmd, label, env=None: calls.append((label, cmd)),
    )

    full_verification.run_verification(tmp_path, skip_chunks=True)

    labels = [label for label, _ in calls]
    assert labels[0] == "Run analytical sweep"
    assert "Focused contract and infrastructure checks" not in labels
    assert "Full suite coverage pass" not in labels
    assert "Coverage pass: Focused contract and infrastructure checks" in labels
    first_coverage_cmd = dict(calls)["Coverage pass: Focused contract and infrastructure checks"]
    second_coverage_cmd = dict(calls)["Coverage pass: Gate and manuscript-focused checks"]
    assert "--cov=src" in first_coverage_cmd
    assert "--cov-append" not in first_coverage_cmd
    assert "--cov-append" in second_coverage_cmd


def test_run_verification_can_use_legacy_monolithic_coverage(monkeypatch, tmp_path: Path) -> None:
    calls: list[tuple[str, list[str]]] = []
    monkeypatch.setattr(
        full_verification,
        "_run",
        lambda project_root, cmd, label, env=None: calls.append((label, cmd)),
    )

    full_verification.run_verification(tmp_path, skip_chunks=True, monolithic_coverage=True)

    labels = [label for label, _ in calls]
    assert "Coverage pass: Focused contract and infrastructure checks" not in labels
    assert "Full suite coverage pass" in labels
    coverage_cmd = dict(calls)["Full suite coverage pass"]
    assert coverage_cmd[-1] == "--maxfail=1"


def test_run_verification_includes_chunked_sheaf_modules(monkeypatch, tmp_path: Path) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    sheaf_path = tests_dir / "test_sheaf_alpha.py"
    sheaf_path.write_text("", encoding="utf-8")
    calls: list[tuple[str, list[str]]] = []
    monkeypatch.setattr(
        full_verification,
        "_run",
        lambda project_root, cmd, label, env=None: calls.append((label, cmd)),
    )

    full_verification.run_verification(tmp_path, skip_chunks=False)

    chunks = dict(calls)
    assert "Focused contract and infrastructure checks" in chunks
    assert "Gate and manuscript-focused checks" in chunks
    roadmap_cmd = chunks["Roadmap and sheaf consolidation checks"]
    assert str(sheaf_path.relative_to(tmp_path)) in roadmap_cmd
