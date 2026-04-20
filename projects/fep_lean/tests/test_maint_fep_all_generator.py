"""Tests for ``scripts/_maint_build_fep_all_lean.py``.

The generator is the single source of truth for ``lean/FepSketches/fep_all.lean``
(which is gitignored). These tests guard the same invariants that
:mod:`tests.test_fep_all_lean_ssot` enforces on the materialized file, so a
SKETCHES edit that breaks the SSOT contract fails fast in unit tests rather
than only at the project-wide ``test_fep_all_lean_*`` gate.
"""

from __future__ import annotations

import importlib
import importlib.util
import re
import sys
from pathlib import Path

import pytest
import yaml

PROJ = Path(__file__).resolve().parent.parent
SCRIPTS = PROJ / "scripts"
TOPICS_YAML = PROJ / "config" / "topics.yaml"

_NS_RE = re.compile(r"^namespace fep_fep(\d+)", re.MULTILINE)


@pytest.fixture(scope="module")
def generator_module():
    """Import the generator module by file path so tests stay decoupled from
    package layout (``scripts/`` is not a package)."""
    spec = importlib.util.spec_from_file_location(
        "_maint_build_fep_all_lean",
        SCRIPTS / "_maint_build_fep_all_lean.py",
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _yaml_topic_ids() -> set[str]:
    data = yaml.safe_load(TOPICS_YAML.read_text(encoding="utf-8"))
    return {t["id"] for t in data["topics"]}


def test_write_aggregate_emits_50_topic_namespaces(tmp_path: Path, generator_module) -> None:
    fep_all_path, basic_path, n = generator_module.write_aggregate(out_dir=tmp_path)
    assert n == 50, f"expected 50 SKETCHES, got {n}"
    assert fep_all_path.is_file()
    assert basic_path.is_file()

    text = fep_all_path.read_text(encoding="utf-8")
    namespaces = {f"fep-{m.group(1)}" for m in _NS_RE.finditer(text)}
    assert len(namespaces) == 50, (
        f"expected 50 fep_fepNNN namespaces, got {len(namespaces)}: "
        f"{sorted(namespaces)}"
    )


def test_write_aggregate_covers_every_yaml_topic(tmp_path: Path, generator_module) -> None:
    fep_all_path, _, _ = generator_module.write_aggregate(out_dir=tmp_path)
    text = fep_all_path.read_text(encoding="utf-8")
    lean_ids = {f"fep-{m.group(1)}" for m in _NS_RE.finditer(text)}
    yaml_ids = _yaml_topic_ids()

    missing_from_lean = yaml_ids - lean_ids
    extra_in_lean = lean_ids - yaml_ids
    assert not missing_from_lean, (
        f"in topics.yaml but not in regenerated fep_all.lean: {sorted(missing_from_lean)}"
    )
    assert not extra_in_lean, (
        f"in regenerated fep_all.lean but not in topics.yaml: {sorted(extra_in_lean)}"
    )


def test_write_aggregate_no_non_comment_sorry(tmp_path: Path, generator_module) -> None:
    fep_all_path, _, _ = generator_module.write_aggregate(out_dir=tmp_path)
    text = fep_all_path.read_text(encoding="utf-8")
    offending: list[str] = []
    for i, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("--"):
            continue
        if re.search(r"\bsorry\b", line):
            offending.append(f"line {i}: {line.rstrip()}")
    assert not offending, "non-comment sorry leaked into generated fep_all.lean:\n" + "\n".join(
        offending
    )


def test_write_aggregate_hoists_single_top_level_import(tmp_path: Path, generator_module) -> None:
    """Per-sketch ``import Mathlib.*`` lines must be stripped; only the file-level
    ``import Mathlib`` should remain. Avoids duplicate imports that would
    otherwise litter the aggregate after every regeneration."""
    fep_all_path, _, _ = generator_module.write_aggregate(out_dir=tmp_path)
    text = fep_all_path.read_text(encoding="utf-8")
    import_lines = [ln for ln in text.splitlines() if ln.startswith("import ")]
    assert import_lines == ["import Mathlib"], (
        f"expected exactly one top-level `import Mathlib`, got: {import_lines}"
    )


def test_basic_lean_stub_compiles_grep_target(tmp_path: Path, generator_module) -> None:
    """Basic.lean is the second target of the CI ``grep ... fep_all.lean Basic.lean``
    sorry-gate; verify the stub is non-empty, sorry-free, and references Mathlib."""
    _, basic_path, _ = generator_module.write_aggregate(out_dir=tmp_path)
    text = basic_path.read_text(encoding="utf-8")
    assert "import Mathlib" in text
    assert not re.search(r"^(?!\s*--).*\bsorry\b", text, flags=re.MULTILINE), (
        "Basic.lean stub contains a non-comment sorry"
    )


def test_topic_id_to_namespace_round_trips(generator_module) -> None:
    assert generator_module._topic_id_to_namespace("fep-001") == "fep_fep001"
    assert generator_module._topic_id_to_namespace("fep-050") == "fep_fep050"
    with pytest.raises(ValueError):
        generator_module._topic_id_to_namespace("not-a-topic")
    with pytest.raises(ValueError):
        generator_module._topic_id_to_namespace("fep-xyz")


def test_build_aggregate_rejects_empty_sketches(generator_module) -> None:
    with pytest.raises(ValueError, match="SKETCHES is empty"):
        generator_module._build_aggregate({})
