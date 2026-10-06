"""A real timestamp-valid poisoned project cache cannot replace reviewed source."""

from __future__ import annotations

import hashlib
import json
import os
import py_compile
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests.infra_tests.core.test_local_review_custody_review import _manuscript, _provider


@pytest.mark.timeout(120)
def test_real_prose_launcher_ignores_timestamp_valid_poisoned_project_bytecode(tmp_path: Path) -> None:
    repository = Path(__file__).resolve().parents[3]
    exemplar = repository / "projects/templates/template_prose_project"
    project = tmp_path / "project"
    shutil.copytree(exemplar / "src", project / "src")
    script = project / "scripts/_run_local_review.py"
    script.parent.mkdir()
    shutil.copyfile(exemplar / "scripts/_run_local_review.py", script)
    shutil.copyfile(exemplar / "pyproject.toml", project / "pyproject.toml")
    _manuscript(project)
    source = project / "src/template_prose_project/pipeline/llm_review.py"
    original = source.read_bytes()
    prefix = b"raise SystemExit(77)\n#"
    assert len(original) > len(prefix)
    source.write_bytes(prefix + b"x" * (len(original) - len(prefix)))
    py_compile.compile(str(source), doraise=True)
    poisoned_stat = source.stat()
    source.write_bytes(original)
    os.utime(source, ns=(poisoned_stat.st_atime_ns, poisoned_stat.st_mtime_ns))
    bootstrap = "import sys;sys.path.insert(0,sys.argv[1]);import template_prose_project.pipeline.llm_review"
    ordinary = subprocess.run(
        [sys.executable, "-I", "-c", bootstrap, str(project / "src")],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert ordinary.returncode == 77, ordinary.stderr
    with _provider() as (endpoint, consumed):
        fresh = subprocess.run(
            [
                sys.executable,
                "-I",
                str(script),
                "--mode",
                "live",
                "--model",
                "custody:fixture",
                "--endpoint",
                endpoint,
                "--timeout",
                "60",
            ],
            cwd=project,
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )
    assert fresh.returncode == 0, fresh.stderr
    assert len(consumed) == 1
    receipt = json.loads((project / "output/.pipeline/prose_review/execution.json").read_text())
    assert receipt["status"] == "succeeded" and receipt["child_exit_code"] == 0
    assert receipt["custody"]["producer_source"]["template_prose_project/pipeline/llm_review.py"] == (
        hashlib.sha256(original).hexdigest()
    )
    assert receipt["custody"]["implementation"]["bytecode_binding"] == "fresh-owned-prefix"
