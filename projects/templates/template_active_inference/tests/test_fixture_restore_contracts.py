"""Actual owned pytest sessions qualify lazy shared-copy restoration."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def _run_owned_pytest(tmp_path: Path, tests: str) -> None:
    root = tmp_path / "owned-project"
    directory = root / "tests"
    directory.mkdir(parents=True)
    source = Path(__file__).parent
    for name in ("conftest.py", "direct_recompute_support.py"):
        shutil.copyfile(source / name, directory / name)
    for relative in ("manuscript/probe.md", "output/data/probe.json"):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("alpha")
    (root / "pyproject.toml").write_text('[tool.pytest.ini_options]\nmarkers = ["requires_gate_artifacts", "slow"]\n')
    (directory / "test_owned.py").write_text(
        "import os\nimport sys\nfrom pathlib import Path\nfrom types import SimpleNamespace\nimport pytest\n"
        "def plugin(config):\n"
        "    return config.pluginmanager.get_plugin(str(Path(__file__).with_name('conftest.py')))\n" + tests
    )
    environment = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONDONTWRITEBYTECODE="1")
    environment.pop("PYTEST_ADDOPTS", None)
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-c",
            str(root / "pyproject.toml"),
            "--confcutdir",
            str(root),
            "-q",
            str(directory),
        ],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "skipped" not in completed.stdout and "deselected" not in completed.stdout
    assert (root / "manuscript/probe.md").read_text() == "alpha"
    assert (root / "output/data/probe.json").read_text() == "alpha"


def test_actual_static_transitive_private_and_pure_fixture_ownership(tmp_path: Path) -> None:
    _run_owned_pytest(
        tmp_path,
        """
_roots = set()
_scans = []
_pure_scan_count = None
def observe(event, args):
    if event == "pathlib.Path.glob" and str(args[0]) in _roots:
        _scans.append((str(args[0]), args[1]))
sys.addaudithook(observe)

def test_00_pure_does_not_create_shared_copy(pytestconfig):
    owner = plugin(pytestconfig)
    assert owner._PROJECT_COPY not in pytestconfig.stash
    assert owner._PROJECT_STATE not in pytestconfig.stash

def test_01_direct_mutator(project_root):
    _roots.add(str(project_root))
    for relative in ("manuscript/probe.md", "output/data/probe.json"):
        path = project_root / relative
        before = path.stat()
        path.write_text("bravo")
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
        assert path.stat().st_size == before.st_size
        assert path.stat().st_mtime_ns == before.st_mtime_ns
        assert path.stat().st_ctime_ns != before.st_ctime_ns
    (project_root / "output/data/added.json").write_text("new")

def test_02_pure_after_mutator(pytestconfig):
    global _pure_scan_count
    owner = plugin(pytestconfig)
    root = pytestconfig.stash[owner._PROJECT_COPY]
    assert (root / "manuscript/probe.md").read_text() == "alpha"
    assert (root / "output/data/probe.json").read_text() == "alpha"
    assert not (root / "output/data/added.json").exists()
    assert _scans
    _pure_scan_count = len(_scans)

@pytest.fixture
def nested_root(project_root):
    return project_root

def test_03_transitive_mutator(nested_root):
    assert len(_scans) == _pure_scan_count
    (nested_root / "manuscript/probe.md").write_text("delta")

def test_04_private_fixture_consumer(_mutable_project_source_snapshots, _mutable_project_source_stats):
    paths, snapshots = _mutable_project_source_snapshots
    path = next(path for path in paths if path.name == "probe.md")
    assert path.read_text() == "alpha"
    assert snapshots[path] == b"alpha"
    assert len(_mutable_project_source_stats[path]) == 5
    path.write_text("again")

def test_05_later_consumer_sees_restored_bytes(project_root):
    assert (project_root / "manuscript/probe.md").read_text() == "alpha"
""",
    )


def test_actual_dynamic_first_request_captures_baseline_before_mutation(tmp_path: Path) -> None:
    _run_owned_pytest(
        tmp_path,
        """
def test_00_dynamic_first(request, pytestconfig):
    owner = plugin(pytestconfig)
    assert owner._PROJECT_STATE not in pytestconfig.stash
    root = request.getfixturevalue("project_root")
    (root / "manuscript/probe.md").write_text("changed")
    (root / "output/data/added.json").write_text("new")

def test_01_following_consumer(project_root):
    assert (project_root / "manuscript/probe.md").read_text() == "alpha"
    assert not (project_root / "output/data/added.json").exists()
""",
    )


def test_unknown_request_ownership_uses_real_conservative_restoration(tmp_path: Path) -> None:
    _run_owned_pytest(
        tmp_path,
        """
def test_00_unknown_metadata(pytestconfig):
    owner = plugin(pytestconfig)
    assert owner._PROJECT_STATE not in pytestconfig.stash
    unknown = SimpleNamespace(config=pytestconfig, node=object(), fixturenames=[])
    restore = owner._restore_mutable_project_state.__wrapped__(unknown)
    next(restore)
    root = pytestconfig.stash[owner._PROJECT_STATE][0]
    (root / "manuscript/probe.md").write_text("changed")
    (root / "output/data/added.json").write_text("new")
    with pytest.raises(StopIteration):
        next(restore)
    assert (root / "manuscript/probe.md").read_text() == "alpha"
    assert not (root / "output/data/added.json").exists()

def test_01_normal_consumer(project_root):
    assert (project_root / "manuscript/probe.md").read_text() == "alpha"
""",
    )
