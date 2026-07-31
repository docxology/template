import os
import shutil
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

os.environ.setdefault("MPLBACKEND", "Agg")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPO_ROOT = os.path.abspath(os.path.join(ROOT, "..", "..", ".."))
for _path in (REPO_ROOT, ROOT):
    if _path not in sys.path:
        sys.path.insert(0, _path)


@pytest.fixture(scope="session", autouse=True)
def _preserve_project_output(
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[None]:
    """Restore real generated output after the suite exercises the pipeline."""
    output = Path(ROOT) / "output"
    snapshot = tmp_path_factory.mktemp("madlib-output") / "output"
    existed = output.is_dir()
    if existed:
        shutil.copytree(output, snapshot, symlinks=True)

    yield

    if output.exists():
        shutil.rmtree(output)
    if existed:
        shutil.copytree(snapshot, output, symlinks=True)
