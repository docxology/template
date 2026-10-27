"""Closed policy controls use genuine collection with no case/fixture execution."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

from infrastructure.core.implementation_custody import bytecode_audit_bootstrap
from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy
from infrastructure.project.public_acceptance_case_policy import POLICY_SCHEMA, RootCasePolicy, compile_case_plan

_ROOT = Path(__file__).resolve().parents[3]
pytestmark = pytest.mark.timeout(180)

_WORKER = r"""
import json,sys
from pathlib import Path
sdk,root,fault=Path(sys.argv[1]),Path(sys.argv[2]),sys.argv[3]
sys.path.insert(0,str(sdk))
from infrastructure.core.implementation_custody import verify_fresh_module_bytecode
from infrastructure.project.public_acceptance_case_observer import RootCaseObserver
from infrastructure.project.public_acceptance_case_policy import digest
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
import pytest
reader=SnapshotReader(root)
hashes={path.relative_to(root).as_posix():reader.read(path.relative_to(root).as_posix()).sha256
    for path in sorted((root/'tests').rglob('*.py'))}
observer=RootCaseObserver(reader,hashes)
argv=['-c',str(root/'pytest.ini'),'--rootdir',str(root),'--confcutdir',str(root),'-o','addopts=',
    '--import-mode=importlib','--assert=plain','--collect-only','--no-cov','-p','no:cacheprovider','-q',str(root/'tests')]
if fault=='filtered': argv+=['-k','test_core']
code=int(pytest.main(argv,plugins=[observer]))
assert observer.executed_reports==0
identity=digest({'owned_python':hashes,'config_sha256':__import__('hashlib').sha256((root/'pytest.ini').read_bytes()).hexdigest()})
if fault=='source-mutated':
    with (root/'tests/test_owned.py').open('a') as stream: stream.write('\n# genuine source edit after collection\n')
census=None; diagnostic=''
try:
    census=observer.census(source_identity=identity,
        runtime=f'{sys.version_info.major}.{sys.version_info.minor}',platform=sys.platform)
except ValueError as error: diagnostic=str(error)
verify_fresh_module_bytecode(sdk/'infrastructure',Path(sys.pycache_prefix))
if fault!='source-mutated': verify_fresh_module_bytecode(root/'tests',Path(sys.pycache_prefix))
(root/'census.json').write_text(json.dumps({'census':census,'cases':observer.cases,'original_pytest_exit_code':code,'diagnostic':diagnostic,
    'collection_errors':observer.collection_errors,'collection_skips':observer.collection_skips,
    'deselected':observer.deselected,'executed_reports':observer.executed_reports}))
"""


def _collect_fixture(tmp_path_factory: pytest.TempPathFactory, fault: str = "healthy") -> dict:
    root = tmp_path_factory.mktemp("actual-root-case-census").resolve()
    (root / "tests").mkdir()
    marker = root / "case-or-fixture-executed"
    (root / "pytest.ini").write_text(
        "[pytest]\naddopts=\nmarkers=\n    requires_ollama: explicit local model contract\n",
        encoding="utf-8",
    )
    (root / "tests/conftest.py").write_text(
        "from pathlib import Path\nimport pytest\n"
        "@pytest.fixture\ndef owned_fixture():\n"
        f"    Path({str(marker)!r}).write_text('actual fixture executed')\n",
        encoding="utf-8",
    )
    (root / "tests/test_owned.py").write_text(
        "from pathlib import Path\nimport pytest\n"
        "@pytest.mark.usefixtures('owned_fixture')\n"
        "@pytest.mark.parametrize('number',[1,2],ids=['one','two'])\n"
        "def test_core(number):\n"
        f"    Path({str(marker)!r}).write_text('actual case executed')\n"
        "    assert number>0\n"
        "@pytest.mark.usefixtures('owned_fixture')\n"
        "@pytest.mark.requires_ollama\n"
        "class TestInheritedLive:\n"
        "    def test_model(self):\n        raise AssertionError('collection must not execute this case')\n",
        encoding="utf-8",
    )
    if fault == "collection-error":
        (root / "tests/test_owned.py").write_text("raise RuntimeError('genuine collection import failure')\n")
    elif fault == "collection-skip":
        (root / "tests/test_owned.py").write_text(
            "import pytest\npytest.importorskip('root_case_fixture_genuinely_missing')\n"
        )
    elif fault == "empty":
        (root / "tests/test_owned.py").write_text("VALUE = 1\n")
    elif fault == "unsupported-item":
        with (root / "tests/conftest.py").open("a") as stream:
            stream.write(
                "class GenuineItem(pytest.Item):\n"
                f"    def runtest(self): Path({str(marker)!r}).write_text('unsupported case executed')\n"
                "class GenuineFile(pytest.File):\n"
                "    def collect(self): yield GenuineItem.from_parent(self, name='unsupported')\n"
                "def pytest_collect_file(file_path, parent):\n"
                "    if file_path.name == 'test_owned.py': return GenuineFile.from_parent(parent, path=file_path)\n"
            )
    prefix = root / "cache"
    prefix.mkdir()
    bootstrap = bytecode_audit_bootstrap((_ROOT / "infrastructure", root / "tests"), prefix)
    observed = run_with_policy(
        [
            sys.executable,
            "-I",
            "-X",
            f"pycache_prefix={prefix}",
            "-c",
            bootstrap + _WORKER,
            str(_ROOT),
            str(root),
            fault,
        ],
        cwd=root,
        env=None,
        policy=SubprocessPolicy(
            policy_id="root-case-policy-genuine-census-control",
            source_path="tests/infra_tests/project/test_root_case_policy.py",
            timeout_seconds=120,
            credential_free=True,
        ),
    )
    assert observed.returncode == observed.original_returncode == 0, observed.stdout + observed.stderr
    assert not observed.timed_out and not observed.custody_refused
    assert not marker.exists(), "collect-only must invoke neither fixture nor test body"
    result = json.loads((root / "census.json").read_text())
    assert result["executed_reports"] == 0
    return result


@pytest.fixture(scope="module")
def actual_census(tmp_path_factory: pytest.TempPathFactory) -> dict:
    result = _collect_fixture(tmp_path_factory)
    assert result["original_pytest_exit_code"] == 0 and result["diagnostic"] == ""
    return result


def _policy(census: dict) -> dict:
    families = []
    for family in census["families"]:
        live = "requires_ollama" in family["markers"]
        families.append(
            {
                **{key: copy.deepcopy(family[key]) for key in ("id", "members", "source_sha256", "metadata_sha256")},
                "lane": "live-unpaid" if live else "core",
                "obligations": ["local-model:owned"] if live else [],
            }
        )
    return {
        "schema_version": POLICY_SCHEMA,
        "runtimes": ["3.14", "3.15"],
        "platforms": ["darwin", "linux"],
        "families": families,
        "obligations": [{"id": "local-model:owned", "kind": "local-model", "eligibility": None}],
    }


def test_actual_collection_preserves_parameter_ids_class_marks_and_fixture_sources(actual_census: dict) -> None:
    census = actual_census["census"]
    assert len(census["nodeids"]) == 3 and len(census["families"]) == 2
    policy = RootCasePolicy.parse(_policy(census))
    plan = compile_case_plan(policy, census, source_identity=census["source_identity"])
    assert {lane.id: len(lane.nodeids) for lane in plan.lanes} == {"core": 2, "live-unpaid": 1}
    assert set(plan.nodeids) == set(census["nodeids"])
    live = next(case for case in actual_census["cases"] if case["family"].endswith("::test_model"))
    markers = {row["name"]: row for row in live["markers"]}
    assert markers["requires_ollama"]["inherited_from"].endswith("::TestInheritedLive")
    assert markers["usefixtures"]["inherited_from"].endswith("::TestInheritedLive")
    assert markers["usefixtures"]["args"] == [{"type": "source-bound-string"}]
    assert all("usefixtures" in family["markers"] for family in census["families"])
    source = live["fixtures"]["owned_fixture"][0]["origin"]
    assert source["scope"] == "public-owned" and source["path"] == "tests/conftest.py"
    assert len(source["sha256"]) == 64


@pytest.mark.parametrize(
    "fault",
    [
        "missing-family",
        "duplicate-family",
        "missing-runtime",
        "missing-platform",
        "unknown-field",
        "unknown-schema",
        "unknown-obligation",
        "unused-obligation",
        "empty-members",
        "duplicate-member",
        "wrong-parameter",
    ],
)
def test_policy_cannot_invent_or_waive_its_closed_contract(actual_census: dict, fault: str) -> None:
    value = _policy(actual_census["census"])
    if fault == "missing-family":
        value["families"] = []
    elif fault == "duplicate-family":
        value["families"].append(copy.deepcopy(value["families"][0]))
    elif fault == "missing-runtime":
        value["runtimes"].pop()
    elif fault == "missing-platform":
        value["platforms"].pop()
    elif fault == "unknown-field":
        value["allow_skips"] = True
    elif fault == "unknown-schema":
        value["schema_version"] = 1
    elif fault == "unknown-obligation":
        value["families"][0]["obligations"] = ["unknown:provider"]
    elif fault == "unused-obligation":
        value["obligations"].append({"id": "tool:unused", "kind": "tool", "eligibility": None})
    elif fault == "empty-members":
        value["families"][0]["members"] = []
    elif fault == "duplicate-member":
        value["families"][0]["members"].append(copy.deepcopy(value["families"][0]["members"][0]))
    else:
        value["families"][0]["members"][0]["parameter_id"] = "wrong"
    with pytest.raises(ValueError):
        RootCasePolicy.parse(value)


@pytest.mark.parametrize(
    "fault",
    [
        "missing-case",
        "duplicate-case",
        "new-case",
        "new-family",
        "parameter",
        "source",
        "metadata",
        "unknown-marker",
        "nonpublic-origin",
        "wrong-runtime",
        "wrong-platform",
        "stale-source",
    ],
)
def test_actual_census_drift_cannot_authorize_reuse(actual_census: dict, fault: str) -> None:
    original = actual_census["census"]
    policy = RootCasePolicy.parse(_policy(original))
    value = copy.deepcopy(original)
    if fault == "missing-case":
        value["nodeids"].pop()
    elif fault == "duplicate-case":
        value["nodeids"].append(value["nodeids"][0])
    elif fault == "new-case":
        value["nodeids"].append("tests/test_owned.py::test_unreviewed")
    elif fault == "new-family":
        value["families"].append(copy.deepcopy(value["families"][0]))
    elif fault == "parameter":
        value["families"][0]["members"][0]["parameter_id"] = "wrong"
    elif fault == "source":
        value["families"][0]["source_sha256"] = "b" * 64
    elif fault == "metadata":
        value["families"][0]["metadata_sha256"] = "b" * 64
    elif fault == "unknown-marker":
        value["families"][0]["markers"].append("unreviewed_network_provider")
    elif fault == "nonpublic-origin":
        value["families"][0]["public_closure"] = False
    elif fault == "wrong-runtime":
        value["runtime"] = "3.11"
    elif fault == "wrong-platform":
        value["platform"] = "unreviewed"
    else:
        value["source_identity"] = "b" * 64
    with pytest.raises(ValueError):
        compile_case_plan(policy, value, source_identity=original["source_identity"])


def test_live_capability_cannot_be_dropped_or_reclassified_as_core(actual_census: dict) -> None:
    census = actual_census["census"]
    for fault in ("drop", "core"):
        value = _policy(census)
        live = next(family for family in value["families"] if family["obligations"])
        if fault == "drop":
            value["obligations"] = []
            live["obligations"] = []
        else:
            live["lane"] = "core"
        with pytest.raises(ValueError):
            compile_case_plan(RootCasePolicy.parse(value), census, source_identity=census["source_identity"])


@pytest.mark.parametrize(
    "fault", ["collection-error", "collection-skip", "empty", "filtered", "source-mutated", "unsupported-item"]
)
def test_real_partial_or_mutated_collection_refuses_census(
    tmp_path_factory: pytest.TempPathFactory, fault: str
) -> None:
    result = _collect_fixture(tmp_path_factory, fault)
    assert result["census"] is None and result["diagnostic"]
    if fault == "collection-error":
        assert result["original_pytest_exit_code"] == 2 and result["collection_errors"]
    elif fault == "collection-skip":
        assert result["original_pytest_exit_code"] == 5 and result["collection_skips"]
    elif fault == "empty":
        assert result["original_pytest_exit_code"] == 5
    elif fault == "filtered":
        assert result["original_pytest_exit_code"] == 0 and len(result["deselected"]) == 1
    elif fault == "unsupported-item":
        assert result["original_pytest_exit_code"] == 3
    else:
        assert result["original_pytest_exit_code"] == 0


@pytest.mark.parametrize("fault", ["missing", "paid", "empty-operation", "private-reference", "bad-reference-hash"])
def test_network_marker_never_authorizes_unreviewed_or_paid_operation(actual_census: dict, fault: str) -> None:
    value = _policy(actual_census["census"])
    obligation = {
        "id": "network:owned-discover",
        "kind": "network-unpaid",
        "eligibility": {
            "provider": "public-provider",
            "operation": "discover",
            "billing": "unpaid",
            "public_reference": "docs/maintenance/provider-eligibility.md",
            "reference_sha256": "a" * 64,
        },
    }
    if fault == "missing":
        obligation["eligibility"] = None
    elif fault == "paid":
        obligation["eligibility"]["billing"] = "paid"
    elif fault == "empty-operation":
        obligation["eligibility"]["operation"] = ""
    elif fault == "private-reference":
        obligation["eligibility"]["public_reference"] = "projects/working/private/provider.md"
    else:
        obligation["eligibility"]["reference_sha256"] = "wrong"
    value["obligations"].append(obligation)
    value["families"][0]["obligations"] = [obligation["id"]]
    with pytest.raises(ValueError):
        RootCasePolicy.parse(value)


def test_explicit_live_obligation_cannot_be_smuggled_into_unmarked_core(actual_census: dict) -> None:
    census = actual_census["census"]
    value = _policy(census)
    core = next(family for family in value["families"] if family["lane"] == "core")
    core["obligations"] = ["local-model:owned"]
    with pytest.raises(ValueError):
        compile_case_plan(RootCasePolicy.parse(value), census, source_identity=census["source_identity"])


@pytest.mark.parametrize("kind", ["tool", "platform"])
def test_explicit_offline_tool_or_platform_obligation_is_required_in_core(actual_census: dict, kind: str) -> None:
    census = actual_census["census"]
    value = _policy(census)
    identity = kind + ":owned"
    core = next(family for family in value["families"] if family["lane"] == "core")
    core["obligations"] = [identity]
    value["obligations"].append({"id": identity, "kind": kind, "eligibility": None})
    plan = compile_case_plan(RootCasePolicy.parse(value), census, source_identity=census["source_identity"])
    assert next(lane for lane in plan.lanes if lane.id == "core").obligations == (identity,)
