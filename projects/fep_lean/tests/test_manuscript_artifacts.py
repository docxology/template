"""manuscript_vars structure from catalogue. All real methods, no mocks."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from catalogue.topics import FEPTopicCatalogue
from output.manuscript import (
    _get_latest_verification_manifest,
    _hermes_block_from_summary,
    _read_toolchain_vars,
    _verify_block_from_manifest,
    build_full_topic_lean_catalogue_markdown,
    build_manuscript_vars,
    write_full_topic_lean_catalogue_markdown,
    write_manuscript_vars,
)

PROJ = Path(__file__).resolve().parent.parent


def test_build_manuscript_vars_shape() -> None:
    c = FEPTopicCatalogue.from_yaml(PROJ / "config" / "topics.yaml")
    v = build_manuscript_vars(c, PROJ)
    assert v["total_topics"] == 50
    assert v["total_areas"] == 5
    assert len(v["topic_ids"]) == 50
    t035 = next(t for t in c.topics if t.id == "fep-035")
    row035 = v["topics"]["fep-035"]
    assert row035["area"] == "FEP"
    assert row035["maturity"] == "real"
    assert row035["maturity_icon"] == "✅"
    assert row035["mathlib_status"] == "real"
    assert int(row035["lean_chars"]) == t035.lean_chars
    assert row035["nl_statement"] == t035.nl
    assert row035["lean_sketch"] == t035.lean_sketch
    assert "maturity_icon" in v["topics"]["fep-035"]
    assert "lean_chars" in v["topics"]["fep-035"]
    assert "verify" in v
    assert v["lean_toolchain"] == (PROJ / "lean" / "lean-toolchain").read_text(
        encoding="utf-8"
    ).strip().splitlines()[0]
    assert v["lean_version"] == "4.29.0"
    assert v["mathlib_tag"] == "v4.29.0"


def test_read_toolchain_vars_matches_disk(tmp_path: Path) -> None:
    lean = tmp_path / "lean"
    lean.mkdir(parents=True)
    (lean / "lean-toolchain").write_text("leanprover/lean4:v4.29.0\n", encoding="utf-8")
    (lean / "lakefile.lean").write_text(
        'require mathlib from git\n  "https://github.com/leanprover-community/mathlib4.git" @ "v4.29.0"\n',
        encoding="utf-8",
    )
    t = _read_toolchain_vars(tmp_path)
    assert t["lean_toolchain"] == "leanprover/lean4:v4.29.0"
    assert t["lean_version"] == "4.29.0"
    assert t["mathlib_tag"] == "v4.29.0"


def test_read_toolchain_vars_fallback_lake_manifest(tmp_path: Path) -> None:
    lean = tmp_path / "lean"
    lean.mkdir(parents=True)
    (lean / "lean-toolchain").write_text("leanprover/lean4:v4.29.0\n", encoding="utf-8")
    (lean / "lakefile.lean").write_text("package foo\n", encoding="utf-8")
    (lean / "lake-manifest.json").write_text(
        '{"packages": [{"name": "mathlib", "inputRev": "v4.29.0"}]}',
        encoding="utf-8",
    )
    t = _read_toolchain_vars(tmp_path)
    assert t["mathlib_tag"] == "v4.29.0"


def test_build_full_topic_lean_catalogue_markdown_matches_topics() -> None:
    c = FEPTopicCatalogue.from_yaml(PROJ / "config" / "topics.yaml")
    md = build_full_topic_lean_catalogue_markdown(c)
    assert md.count("\n```lean\n") == 50
    assert "**Version**:" not in md
    assert "**Status**: Generated" not in md
    assert "**Source**: `src/output/manuscript.py`" not in md
    for t in c.topics:
        assert t.id in md
        assert t.lean_sketch.strip() in md


def test_write_full_topic_lean_catalogue_markdown_roundtrip(tmp_path: Path) -> None:
    import shutil

    shutil.copytree(PROJ / "config", tmp_path / "config")
    (tmp_path / "manuscript").mkdir(parents=True, exist_ok=True)
    c = FEPTopicCatalogue.from_yaml(tmp_path / "config" / "topics.yaml")
    out = write_full_topic_lean_catalogue_markdown(tmp_path, c)
    assert out.is_file()
    text = out.read_text(encoding="utf-8")
    assert text.count("```lean") == 50
    assert "## fep-001 —" in text
    assert "## fep-050 —" in text
    assert "**Version**:" not in text
    assert "**Status**: Generated" not in text
    assert "**Source**: `src/output/manuscript.py`" not in text


def test_verify_block_from_manifest_missing() -> None:
    b = _verify_block_from_manifest(None)
    assert b["manifest_present"] is False


def test_verify_block_from_manifest_invalid_json(tmp_path: Path) -> None:
    p = tmp_path / "verification_manifest.json"
    p.write_text("{not json", encoding="utf-8")
    b = _verify_block_from_manifest(p)
    assert b["manifest_present"] is True
    assert b["verify_lean_ran"] is False


def test_verify_block_from_manifest_topics_fallback(tmp_path: Path) -> None:
    p = tmp_path / "verification_manifest.json"
    p.write_text('{"results": [{"x": 1}, {"x": 2}]}', encoding="utf-8")
    b = _verify_block_from_manifest(p)
    assert b["topics_with_result"] == 2


def test_latest_verification_manifest_newest(tmp_path: Path) -> None:
    base = tmp_path / "output" / "reports"
    old = base / "run_old"
    new = base / "run_new"
    old.mkdir(parents=True)
    new.mkdir(parents=True)
    (old / "verification_manifest.json").write_text("{}", encoding="utf-8")
    (new / "verification_manifest.json").write_text("{}", encoding="utf-8")
    import os
    import time

    os.utime(new / "verification_manifest.json", (time.time() + 10, time.time() + 10))
    picked = _get_latest_verification_manifest(tmp_path)
    assert picked is not None
    assert "run_new" in str(picked)


def test_verify_block_from_manifest_json(tmp_path: Path) -> None:
    p = tmp_path / "verification_manifest.json"
    p.write_text(
        json.dumps(
            {
                "verify_lean_ran": True,
                "topics_with_result": 3,
                "compiles_true": 1,
                "compiles_false": 2,
            }
        ),
        encoding="utf-8",
    )
    b = _verify_block_from_manifest(p)
    assert b["manifest_present"] is True
    assert b["verify_lean_ran"] is True
    assert b["topics_with_result"] == 3


def test_hermes_block_missing_summary_returns_zeros() -> None:
    block = _hermes_block_from_summary(None)
    assert block["summary_present"] is False
    assert block["processed"] == 0
    assert block["success_count"] == 0
    assert block["tokens_total"] == 0
    assert block["primary_model"] == ""
    assert block["models_used"] == ""


def test_hermes_block_aggregates_from_summary(tmp_path: Path) -> None:
    summary_path = tmp_path / "summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "run_id": "20260420_111111",
                "topics": [
                    {
                        "topic_id": "fep-001",
                        "hermes_success": True,
                        "lean_compiles": True,
                        "hermes_lean_compiles": True,
                        "cache_hit": True,
                        "tokens_used": 1000,
                        "hermes_model": "z-ai/glm-5.1",
                    },
                    {
                        "topic_id": "fep-002",
                        "hermes_success": True,
                        "lean_compiles": True,
                        "hermes_lean_compiles": False,  # fallback path
                        "cache_hit": False,
                        "tokens_used": 2000,
                        "hermes_model": "z-ai/glm-5.1",
                    },
                    {
                        "topic_id": "fep-003",
                        "hermes_success": False,
                        "lean_compiles": False,
                        "cache_hit": False,
                        "tokens_used": 0,
                        "hermes_model": "",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    block = _hermes_block_from_summary(summary_path)
    assert block["summary_present"] is True
    assert block["run_id"] == "run_20260420_111111"
    assert block["processed"] == 3
    assert block["success_count"] == 2
    assert block["cache_hits"] == 1
    assert block["tokens_total"] == 3000
    assert block["tokens_mean"] == 1500
    assert block["hermes_lean_compiles_count"] == 1
    assert block["fallback_count"] == 1
    assert block["primary_model"] == "z-ai/glm-5.1"
    assert "z-ai/glm-5.1" in block["models_used"]


def test_build_manuscript_vars_exposes_hermes_block(tmp_path: Path) -> None:
    """``build_manuscript_vars`` must expose a top-level ``hermes`` block when a
    sibling ``summary.json`` is present alongside the verification manifest."""
    import shutil

    shutil.copytree(PROJ / "config", tmp_path / "config")
    (tmp_path / "manuscript").mkdir()
    # _read_toolchain_vars only reads ``lean-toolchain``, ``lakefile.lean``,
    # ``lake-manifest.json``; skip the multi-GB ``.lake`` build cache and the
    # transient FepSketches verification scratch dir.
    shutil.copytree(
        PROJ / "lean",
        tmp_path / "lean",
        ignore=shutil.ignore_patterns(".lake", "FepSketches"),
    )
    run_dir = tmp_path / "output" / "reports" / "run_test_hermes_block"
    run_dir.mkdir(parents=True)
    (run_dir / "verification_manifest.json").write_text(
        json.dumps(
            {
                "verify_lean_ran": True,
                "topics_with_result": 2,
                "compiles_true": 2,
                "compiles_false": 0,
                "results": [
                    {"topic_id": "fep-001", "compiles": True, "lean_has_sorry": False},
                    {"topic_id": "fep-002", "compiles": True, "lean_has_sorry": False},
                ],
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "summary.json").write_text(
        json.dumps(
            {
                "run_id": "test_hermes_block",
                "topics": [
                    {
                        "topic_id": "fep-001",
                        "hermes_success": True,
                        "lean_compiles": True,
                        "hermes_lean_compiles": True,
                        "cache_hit": False,
                        "tokens_used": 500,
                        "hermes_model": "z-ai/glm-5.1",
                    },
                    {
                        "topic_id": "fep-002",
                        "hermes_success": True,
                        "lean_compiles": True,
                        "hermes_lean_compiles": True,
                        "cache_hit": True,
                        "tokens_used": 1500,
                        "hermes_model": "z-ai/glm-5.1",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    c = FEPTopicCatalogue.from_yaml(tmp_path / "config" / "topics.yaml")
    v = build_manuscript_vars(c, tmp_path)
    assert "hermes" in v
    assert v["hermes"]["summary_present"] is True
    assert v["hermes"]["processed"] == 2
    assert v["hermes"]["success_count"] == 2
    assert v["hermes"]["cache_hits"] == 1
    assert v["hermes"]["tokens_mean"] == 1000
    assert v["hermes"]["primary_model"] == "z-ai/glm-5.1"
    assert v["hermes"]["hermes_lean_compiles_count"] == 2
    assert v["hermes"]["fallback_count"] == 0
    assert "tests" in v
    assert isinstance(v["tests"]["collected"], int)


def test_write_manuscript_vars_roundtrip(tmp_path: Path) -> None:
    import shutil

    shutil.copytree(PROJ / "config", tmp_path / "config")
    (tmp_path / "manuscript").mkdir()
    (tmp_path / "manuscript" / "config.yaml").write_text("paper:\n  title: t\n", encoding="utf-8")
    for d in ("scripts", "tests", "src", "output"):
        (tmp_path / d).mkdir()
    (tmp_path / "src" / "__init__.py").write_text('"""x"""\n', encoding="utf-8")
    shutil.copytree(
        PROJ / "lean",
        tmp_path / "lean",
        ignore=shutil.ignore_patterns(".lake", "FepSketches"),
    )

    c = FEPTopicCatalogue.from_yaml(tmp_path / "config" / "topics.yaml")
    out = write_manuscript_vars(tmp_path, c)
    assert out.is_file()
    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert data["total_topics"] == len(c.topics)
    assert data["lean_version"] == "4.29.0"
    assert data["mathlib_tag"] == "v4.29.0"
    assert data["lean_toolchain"].startswith("leanprover/lean4:")
