"""Actual public collection is independent of unrelated local source trees."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from infrastructure.core.implementation_custody import bytecode_audit_bootstrap
from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

_ROOT = Path(__file__).resolve().parents[3]
pytestmark = pytest.mark.timeout(180)

_PROBE = r"""
import importlib,json,sys
from pathlib import Path
sdk,layout=Path(sys.argv[1]),Path(sys.argv[2])
sys.path.insert(0,str(sdk))
import infrastructure
from infrastructure.core.implementation_custody import verify_fresh_module_bytecode
from infrastructure.project.public_acceptance_pytest import CollectionEvidence
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
import pytest
markers=[]
for poison in sorted(layout.glob('projects/*/owned_local_fixture/src')):
    marker=poison/'poison-ran'
    sys.path.insert(0,str(poison))
    live=importlib.import_module('public_fixture_template_code_project')
    assert live.VALUE=='owned local poison' and marker.read_text()=='actual poison import'
    sys.modules.pop(live.__name__)
    sys.path.remove(str(poison))
    marker.unlink()
    markers.append(marker)
observer=CollectionEvidence()
original=int(pytest.main([
    '-c',str(layout/'pytest.ini'),'--assert=plain','--rootdir',str(layout),
    '--confcutdir',str(layout),'--import-mode=importlib',
    str(layout/'tests/test_owned_collection.py'),'--collect-only','-q',
],plugins=[observer]))
assert original==0 and not observer.collection_errors and not observer.collection_skips
assert observer.nodeids==['tests/test_owned_collection.py::test_owned_public_source']
assert not observer.deselected and not observer.reports
expected=[str(layout/'projects'/name/'src') for name in PUBLIC_PROJECT_NAMES]
assert sys.path[:len(expected)]==expected
loaded=importlib.import_module('public_fixture_template_code_project')
assert loaded.VALUE=='canonical public source'
expected_module=layout/'projects/templates/template_code_project/src/public_fixture_template_code_project.py'
assert Path(loaded.__file__).resolve()==expected_module
assert not any(marker.exists() for marker in markers)
verify_fresh_module_bytecode(sdk/'infrastructure',Path(sys.pycache_prefix))
verify_fresh_module_bytecode(layout,Path(sys.pycache_prefix))
print('PUBLIC_PATH_RECEIPT:'+json.dumps({
    'nodeids':observer.nodeids,'original_pytest_exit_code':original,
    'provider_version':infrastructure.__version__,
    'provider_origin':str(Path(infrastructure.__file__).resolve()),
    'canonical_source_count':len(expected),'poison_controls_proved_live':len(markers),
    'poison_after_public_collection':False,
},sort_keys=True))
"""


def _collect_layout(tmp_path: Path, *, local_trees: bool) -> dict[str, object]:
    layout = tmp_path / ("with-local-trees" if local_trees else "public-only")
    (layout / "tests").mkdir(parents=True)
    (layout / "tests/conftest.py").write_bytes((_ROOT / "tests/conftest.py").read_bytes())
    (layout / "pytest.ini").write_text("[pytest]\naddopts=\n", encoding="utf-8")
    (layout / "tests/test_owned_collection.py").write_text(
        "from public_fixture_template_code_project import VALUE\n"
        "assert VALUE=='canonical public source'\n"
        "def test_owned_public_source():\n    assert VALUE=='canonical public source'\n",
        encoding="utf-8",
    )
    for name in PUBLIC_PROJECT_NAMES:
        source = layout / "projects" / name / "src"
        source.mkdir(parents=True)
    (layout / "projects/templates/template_code_project/src/public_fixture_template_code_project.py").write_text(
        "VALUE='canonical public source'\n", encoding="utf-8"
    )
    if local_trees:
        for lifecycle in ("active", "working", "ongoing", "archive", "unlisted"):
            source = layout / "projects" / lifecycle / "owned_local_fixture/src"
            source.mkdir(parents=True)
            (source / "public_fixture_template_code_project.py").write_text(
                "from pathlib import Path\n"
                "Path(__file__).with_name('poison-ran').write_text('actual poison import')\n"
                "VALUE='owned local poison'\n",
                encoding="utf-8",
            )
    prefix = tmp_path / (layout.name + "-cache")
    prefix.mkdir()
    bootstrap = bytecode_audit_bootstrap((_ROOT / "infrastructure", layout), prefix)
    outcome = run_with_policy(
        [sys.executable, "-I", "-X", f"pycache_prefix={prefix}", "-c", bootstrap + _PROBE, str(_ROOT), str(layout)],
        cwd=layout,
        env=None,
        policy=SubprocessPolicy(
            policy_id="public-collection-path-isolation-control",
            source_path="tests/infra_tests/project/test_public_collection_paths.py",
            timeout_seconds=120,
            credential_free=True,
        ),
    )
    assert outcome.returncode == outcome.original_returncode == 0, outcome.stdout + outcome.stderr
    assert not outcome.timed_out and not outcome.custody_refused
    lines = [line for line in outcome.stdout.splitlines() if line.startswith("PUBLIC_PATH_RECEIPT:")]
    assert len(lines) == 1, outcome.stdout
    return json.loads(lines[0].removeprefix("PUBLIC_PATH_RECEIPT:"))


def test_actual_root_conftest_collects_same_public_cases_without_local_imports(tmp_path: Path) -> None:
    public = _collect_layout(tmp_path, local_trees=False)
    local = _collect_layout(tmp_path, local_trees=True)
    assert public["poison_controls_proved_live"] == 0 and local["poison_controls_proved_live"] == 5
    for receipt in (public, local):
        assert receipt["original_pytest_exit_code"] == 0
        assert receipt["canonical_source_count"] == len(PUBLIC_PROJECT_NAMES)
        assert receipt["poison_after_public_collection"] is False
    assert {key: value for key, value in public.items() if key != "poison_controls_proved_live"} == {
        key: value for key, value in local.items() if key != "poison_controls_proved_live"
    }
