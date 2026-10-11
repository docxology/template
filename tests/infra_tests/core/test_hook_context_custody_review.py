"""Independent real-filesystem controls for local hook-context confidentiality."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.core.pipeline.hooks import StageHookContext, _write_context_file


def test_hook_context_is_private_and_confined(tmp_path: Path) -> None:
    output = tmp_path / "project/output"
    output.mkdir(parents=True)
    context = StageHookContext("private-fixture-project", "Analysis", 2, output, "running")
    path = _write_context_file(context)
    assert path.is_relative_to(output)
    assert json.loads(path.read_text()) == context.to_dict()
    assert path.stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize("linked_parent", ["hooks", "output-ancestor"])
def test_hook_context_refuses_linked_ancestors_without_external_writes(tmp_path: Path, linked_parent: str) -> None:
    external = tmp_path / "external"
    external.mkdir()
    project = tmp_path / "project"
    if linked_parent == "output-ancestor":
        (external / "output").mkdir()
        project.symlink_to(external, target_is_directory=True)
        output = project / "output"
    else:
        output = project / "output"
        controls = output / ".pipeline"
        controls.mkdir(parents=True)
        (controls / "hooks").symlink_to(external, target_is_directory=True)
    before = set(external.rglob("*"))
    context = StageHookContext("private-fixture-project", "Analysis", 2, output, "running")
    with pytest.raises(ValueError, match="[Ss]ymlink|[Ss]ymbolic"):
        _write_context_file(context)
    assert set(external.rglob("*")) == before
