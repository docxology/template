"""A reused Python worker cannot bind new source bytes to stale loaded code."""

from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from infrastructure.core.pipeline import fingerprints


@pytest.mark.parametrize("changed", ["infrastructure", "scripts"])
def test_loaded_implementation_change_refuses_new_plan(tmp_path: Path, changed: str) -> None:
    target = tmp_path / "infrastructure" / "core" / "pipeline" / "fingerprints.py"
    target.parent.mkdir(parents=True)
    shutil.copyfile(fingerprints.__file__, target)
    (tmp_path / "scripts").mkdir()
    probe = (
        "import importlib.util\nfrom pathlib import Path\n"
        f"spec=importlib.util.spec_from_file_location('consumed_fingerprints', {str(target)!r})\n"
        "module=importlib.util.module_from_spec(spec)\nspec.loader.exec_module(module)\n"
        "module.verify_loaded_implementation()\n"
        f"Path({str(tmp_path / changed / 'changed.py')!r}).write_text('new source bytes')\n"
        "try:\n module.verify_loaded_implementation()\n"
        "except ValueError as exc:\n assert 'restart the worker' in str(exc)\n"
        "else:\n raise AssertionError('stale worker authorized new source')\n"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", probe], cwd=tmp_path, capture_output=True, text=True, timeout=15
    )
    assert result.returncode == 0, result.stderr
