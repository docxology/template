"""Real native assets must precede project hydration's visualization seal."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import matplotlib
import pytest

from infrastructure.rendering.pipeline import execute_render_pipeline
from infrastructure.transmission.transmission_bookends import write_transmission_bookends
from tests.infra_tests.publishing.test_transmission_bookends import _write_project

_REPO = Path(__file__).resolve().parents[3]


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "projects" / "templates" / "transmission_order"
    _write_project(project)
    for name in ("src", "tests", "scripts"):
        (project / name).mkdir()
    (project / "scripts/z_generate_manuscript_variables.py").write_text(
        'raise AssertionError("invalid hydration budget must refuse before child launch")\n'
    )
    return project


def _font(directory: Path, name: str) -> None:
    source = Path(matplotlib.get_data_path()) / "fonts" / "ttf" / name
    shutil.copyfile(source, directory / "Arial.ttf")


def test_real_pipeline_prepares_native_assets_before_hydration_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A genuine invalid hydration budget stops after native asset preparation."""
    project = _project(tmp_path)
    monkeypatch.chdir(tmp_path)
    target = project / "output/figures/transmission_pairing.png"
    _font(tmp_path, "DejaVuSans.ttf")
    write_transmission_bookends(project, "templates/transmission_order", repo_root=tmp_path)
    previous = target.read_bytes()
    _font(tmp_path, "DejaVuSerif.ttf")
    write_transmission_bookends(project, "templates/transmission_order", repo_root=tmp_path)
    expected = target.read_bytes()
    assert previous != expected
    target.write_bytes(previous)
    monkeypatch.setenv("MANUSCRIPT_HYDRATION_TIMEOUT", "0")
    assert execute_render_pipeline("templates/transmission_order", repo_root=tmp_path) == 2
    assert target.read_bytes() == expected


def test_preparation_preserves_explicit_consumed_paper_layout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project = _project(tmp_path)
    monkeypatch.chdir(tmp_path)
    _font(tmp_path, "DejaVuSans.ttf")
    write_transmission_bookends(project, "templates/transmission_order", repo_root=tmp_path)
    target = project / "output/figures/transmission_pairing.png"
    previous = target.read_bytes()
    consumed = project / "output/manuscript"
    (consumed / "config.yaml").write_text("# Project-resolved config\npaper:\n  frontmatter: [plate.md]\n")
    _font(tmp_path, "DejaVuSerif.ttf")
    monkeypatch.setenv("MANUSCRIPT_HYDRATION_TIMEOUT", "0")
    assert execute_render_pipeline("templates/transmission_order", repo_root=tmp_path) == 2
    assert target.read_bytes() == previous


def test_provisional_layout_does_not_replace_hydration_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _project(tmp_path)
    config = project / "manuscript/config.yaml"
    config.write_text(config.read_text().replace("paper:", "paper:\n  frontmatter: '{{PAGES}}'"))
    monkeypatch.setenv("MANUSCRIPT_HYDRATION_TIMEOUT", "0")
    assert execute_render_pipeline("templates/transmission_order", repo_root=tmp_path) == 2
    assert not (project / "output/figures/transmission_pairing.png").exists()


def test_skipped_hydration_does_not_prepare_assets_before_existing_config_guard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _project(tmp_path)
    monkeypatch.chdir(tmp_path)
    _font(tmp_path, "DejaVuSans.ttf")
    write_transmission_bookends(project, "templates/transmission_order", repo_root=tmp_path)
    target = project / "output/figures/transmission_pairing.png"
    previous = target.read_bytes()
    source = project / "manuscript/config.yaml"
    source.write_text(source.read_text().replace("Transmission Demo", "{{UNRESOLVED_TITLE}}"))
    _font(tmp_path, "DejaVuSerif.ttf")
    assert (
        execute_render_pipeline("templates/transmission_order", repo_root=tmp_path, skip_manuscript_hydration=True) == 1
    )
    assert target.read_bytes() == previous


def test_real_font_provider_change_rejects_late_audit_and_accepts_prepared_repeat(tmp_path: Path) -> None:
    """Use actual Root image producers and Active's read-only auxiliary validator."""
    script = r"""
import json, os, shutil, sys
from pathlib import Path
import matplotlib
repo, workspace = map(Path, sys.argv[1:])
project = repo / "projects/templates/template_active_inference"
sys.path[:0] = [str(project / "src"), str(project / "tests")]
from direct_recompute_support import copy_project_tree
from roadmap_tracks.visualization_audit import write_visualization_quality_audit, validate_visualization_quality_audit
from roadmap_tracks.visualization_contract import build_auxiliary_visualization_inventory, auxiliary_visualization_rows_match
from infrastructure.rendering.pipeline import _prepare_bookends_before_hydration, RenderPipelineDependencies
from infrastructure.transmission.transmission_bookends import write_transmission_bookends
root = copy_project_tree(workspace / "project")
os.chdir(workspace)
fonts = Path(matplotlib.get_data_path()) / "fonts/ttf"
shutil.copyfile(fonts / "DejaVuSans.ttf", workspace / "Arial.ttf")
write_transmission_bookends(root, "templates/template_active_inference", repo_root=repo)
write_visualization_quality_audit(root)
before = build_auxiliary_visualization_inventory(root)["rows"]
shutil.copyfile(fonts / "DejaVuSerif.ttf", workspace / "Arial.ttf")
write_transmission_bookends(root, "templates/template_active_inference", repo_root=repo)
late = [issue for issue in validate_visualization_quality_audit(root) if "auxiliary visualizations" in issue]
after = build_auxiliary_visualization_inventory(root)["rows"]
assert late and not auxiliary_visualization_rows_match(before, after)
_prepare_bookends_before_hydration(root, "templates/template_active_inference", repo, RenderPipelineDependencies())
write_visualization_quality_audit(root)
sealed = build_auxiliary_visualization_inventory(root)["rows"]
write_transmission_bookends(root, "templates/template_active_inference", repo_root=repo)
repeated = build_auxiliary_visualization_inventory(root)["rows"]
fresh = [issue for issue in validate_visualization_quality_audit(root) if "auxiliary visualizations" in issue]
assert auxiliary_visualization_rows_match(sealed, repeated) and not fresh
print(json.dumps({"late_issues": late, "prepared_repeat_issues": fresh}))
"""
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", script, str(_REPO), str(tmp_path)],
        cwd=_REPO,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    evidence = json.loads(result.stdout.splitlines()[-1])
    assert evidence["late_issues"]
    assert evidence["prepared_repeat_issues"] == []
