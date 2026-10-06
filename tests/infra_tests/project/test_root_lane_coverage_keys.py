"""Root lane coverage reports key actual measured files by their SDK path."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]

# A separate interpreter owns its Coverage tracer, so the measurement cannot
# disturb (or be disturbed by) a pytest-cov session in this process.
_MEASURE = """
import json, sys
from pathlib import Path
from coverage import Coverage
sys.path.insert(0, sys.argv[1])
target = Path(sys.argv[2])
sys.path.insert(0, str(target.parent))
measured = Coverage(data_file=None, branch=True, source=[str(target.parent)])
measured.start()
__import__(target.stem)
measured.stop()
from infrastructure.project.public_root_lane_coverage import report
try:
    print(json.dumps({"files": sorted(report(measured)["files"])}))
except ValueError as error:
    print(json.dumps({"refused": str(error)}))
"""


def _measure(target: Path, cwd: Path, sdk_root: Path = REPO_ROOT) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, "-I", "-c", _MEASURE, str(sdk_root), str(target)],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout.strip().splitlines()[-1])


@pytest.mark.timeout(120)
def test_sdk_source_is_keyed_canonically_from_any_working_directory(tmp_path: Path) -> None:
    # Measure a probe inside a private SDK copy; the live tree is never written.
    sdk = tmp_path / "sdk"
    shutil.copytree(REPO_ROOT / "infrastructure", sdk / "infrastructure", ignore=shutil.ignore_patterns("__pycache__"))
    target = sdk / "infrastructure" / "project" / "lane_coverage_probe_target.py"
    target.write_text("VALUE = 1\n", encoding="utf-8")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    inside = _measure(target, sdk, sdk)
    outside = _measure(target, elsewhere, sdk)
    # Source-directory measurement also reports the package's unexecuted files;
    # every key must be the same canonical SDK path regardless of cwd.
    files = inside["files"]
    assert isinstance(files, list)
    assert "infrastructure/project/lane_coverage_probe_target.py" in files
    assert all(name.startswith("infrastructure/project/") for name in files)
    assert outside == inside


@pytest.mark.timeout(120)
def test_source_outside_the_selected_sdk_is_refused(tmp_path: Path) -> None:
    target = tmp_path / "foreign_module.py"
    target.write_text("VALUE = 2\n", encoding="utf-8")
    observed = _measure(target, tmp_path)
    assert observed == {"refused": "Root lane coverage report names a source outside the selected SDK"}
