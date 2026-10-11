"""Real print artifacts and original subprocess exits; no mocks."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]
CHILD = Path(__file__).with_name("_special_native_control_child.py")


def _source(tmp_path: Path, kind: str) -> Path:
    source = ROOT / "projects/templates" / ("template_" + kind)
    project = tmp_path / kind
    shutil.copytree(source / "src", project / "src")
    (project / "content").mkdir()
    if kind == "storybook":
        raw = yaml.safe_load((source / "content/story.yaml").read_bytes())
        raw["pages"] = raw["pages"][:2]
        (project / "content/story.yaml").write_text(yaml.safe_dump(raw, sort_keys=False))
    else:
        raw = yaml.safe_load((source / "content/edition.yaml").read_bytes())
        raw["pages"] = ["first.yaml", "second.yaml"]
        (project / "content/edition.yaml").write_text(yaml.safe_dump(raw, sort_keys=False))
        (project / "content/pages").mkdir()
        for index, leaf in enumerate(raw["pages"], 1):
            page = {
                "number": index,
                "section": "A",
                "department": f"Public measurement {index}",
                "template": "standard",
                "columns": 4,
                "rail_enabled": False,
                "main": [
                    {
                        "headline": f"Measured offset {index}",
                        "level": "primary",
                        "body": [f"Independent station {index} measured a stable offset of 42 millivolts."],
                    }
                ],
            }
            (project / "content/pages" / leaf).write_text(yaml.safe_dump(page, sort_keys=False))
    return project


@pytest.mark.skipif(shutil.which("pdftoppm") is None, reason="actual Poppler raster tool unavailable")
@pytest.mark.timeout(60)
@pytest.mark.parametrize(
    "kind,mode",
    [
        (kind, mode)
        for kind in ("storybook", "newspaper")
        for mode in ("baseline", "altered", "omitted", "reordered", "hidden", "clipped", "geometry", "font", "image")
    ]
    + [
        ("storybook", "contact-order"),
        ("storybook", "transparency"),
        ("storybook", "png-transparency"),
        ("newspaper", "font-resource"),
    ],
)
def test_actual_special_print_controls(tmp_path: Path, kind: str, mode: str) -> None:
    project = _source(tmp_path, kind)
    directory = tmp_path / f"{kind}-{mode}"
    command = [sys.executable, str(CHILD), kind, mode, str(project), str(directory)]
    environment = dict(os.environ, PYTHONPATH=str(ROOT), MPLCONFIGDIR=str(tmp_path.parent / "matplotlib"))
    child = subprocess.run(command, capture_output=True, text=True, env=environment, timeout=55)
    record = {
        "command": command,
        "original_exit_code": child.returncode,
        "stdout": child.stdout,
        "stderr": child.stderr,
    }
    (tmp_path / f"{kind}-{mode}-original-process.json").write_text(json.dumps(record, indent=2))
    assert child.returncode == (0 if mode == "baseline" else 1), record
    assert (directory / "observation.json").is_file()
    if kind == "newspaper" and mode in {"hidden", "image"}:
        observation = json.loads((directory / "observation.json").read_bytes())
        assert observation["refused"].startswith("newspaper rendered pixels differ"), observation
        rasters = json.loads((directory / "readback/raster-processes.json").read_bytes())
        assert len(rasters) == 2 and all(row["original_exit_code"] == 0 for row in rasters)


def test_unknown_source_forms_refused(tmp_path: Path) -> None:
    from infrastructure.reporting.native_storybook_source import build_storybook_reference
    from infrastructure.reporting.native_newspaper_source import build_newspaper_reference
    import time

    for kind, build, leaf in [
        ("storybook", build_storybook_reference, "story.yaml"),
        ("newspaper", build_newspaper_reference, "edition.yaml"),
    ]:
        project = _source(tmp_path, kind)
        path = project / "content" / leaf
        raw = yaml.safe_load(path.read_bytes())
        raw["unrecognized_future_layout"] = True
        path.write_text(yaml.safe_dump(raw))
        with pytest.raises(ValueError, match="unsupported"):
            build(project, tmp_path / f"unknown-{kind}", deadline=time.monotonic() + 10)
