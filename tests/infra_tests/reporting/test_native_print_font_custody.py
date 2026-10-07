"""Actual installed font selections and transported original record controls."""

from __future__ import annotations
import copy
import json
import subprocess
import sys
from pathlib import Path
import pytest
from infrastructure.reporting.native_print_font_custody import observe_print_fonts, validate_print_fonts

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module", params=("storybook", "newspaper"))
def original(request):
    kind = request.param
    project = ROOT / f"projects/templates/template_{kind}"
    record = observe_print_fonts(project, kind)
    validate_print_fonts(record, kind, project)
    return kind, project, record


@pytest.mark.parametrize(
    "fault",
    (
        "omitted-role",
        "duplicate-role",
        "source",
        "selector",
        "bytes",
        "digest",
        "identity",
        "escape",
        "face",
        "index",
        "cross-provider",
        "extra",
    ),
)
def test_actual_original_font_record_refuses_incomplete_or_changed_custody(original, fault):
    kind, project, record = original
    changed = copy.deepcopy(record)
    row = next((item for item in changed["roles"] if item["kind"] == "system-file"), changed["roles"][0])
    if fault in {"bytes", "digest", "identity", "escape"} and row["resource"] is None:
        row["resource"] = {"bytes": 1, "sha256": "0" * 64}

    if fault == "omitted-role":
        changed["roles"].pop()
    elif fault == "duplicate-role":
        changed["roles"][1] = changed["roles"][0]
    elif fault == "source":
        changed["source_identity"] = "0" * 64
    elif fault == "selector":
        changed["selector_sha256"] = "0" * 64
    elif fault == "bytes":
        row["resource"]["bytes"] = 64 * 1024 * 1024 + 1
    elif fault == "digest":
        row["resource"]["sha256"] = "not-a-digest"
    elif fault == "identity":
        if "identity" in row["resource"]:
            row["resource"]["identity"][2] += 1
        else:
            row["resource"]["identity"] = [0, 0, 2, 0, 0]
    elif fault == "escape":
        row["resource"]["path"] = "/System/Library/Fonts/../private/font.ttf"
    elif fault == "face":
        row["native_face"] = [""]
    elif fault == "index":
        row["index"] = True
    elif fault == "cross-provider":
        row["kind"] = "embedded-provider" if kind == "newspaper" else "builtin-provider"
    elif fault == "extra":
        row["extra"] = True
    with pytest.raises(ValueError):
        validate_print_fonts(changed, kind, project)


def test_reader_replays_actual_original_font_record_without_opening_installed_fonts(original, tmp_path):
    kind, project, record = original
    retained = tmp_path / "fonts.json"
    retained.write_text(json.dumps(record))
    script = """import json,sys,pathlib
from infrastructure.reporting.native_print_font_custody import validate_print_fonts
record=json.loads(pathlib.Path(sys.argv[1]).read_text())
def audit(event,args):
    if event=='open' and isinstance(args[0],str) and args[0].startswith(('/System/Library/Fonts/','/Library/Fonts/','/usr/share/fonts/','/usr/local/share/fonts/')):
        raise RuntimeError('reader reopened an original installed font')
sys.addaudithook(audit)
validate_print_fonts(record,sys.argv[2],pathlib.Path(sys.argv[3]))
"""
    process = subprocess.run(
        [sys.executable, "-c", script, str(retained), kind, str(project)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert process.returncode == 0, process.stderr
