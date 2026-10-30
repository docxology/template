"""Actual ordinary-CI partition, pytest/xdist selection and coverage union controls."""

from __future__ import annotations

import configparser
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import pytest
import yaml

from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy
from infrastructure.core.testing.ci_infra_coverage import (
    ARTIFACT_DIRECTORY,
    merge_shards,
)
from infrastructure.core.testing.ci_infra_partition import (
    INFRA_MARKERS,
    RESERVED_MODULES,
    SCHEMA,
    SHARD_COUNT,
    ci_matrix,
    module_shard,
    partition,
    read_receipt,
    receipt_path,
    selected_runtime,
    selection_source,
    validate_receipts,
)
from infrastructure.project.public_capabilities import CANONICAL_CI_PYTHON_VERSIONS
from infrastructure.project.public_reference_git import (
    _PINNED_SUBMODULE,
    _PINNED_SUBMODULE_URL,
    native_git,
)

SDK_ROOT = Path(__file__).resolve().parents[3]


def _fixture(tmp_path: Path) -> Path:
    """Own actual test/source files, without manufacturing an installed SDK."""
    root = tmp_path / "ordinary-ci-fixture"
    root.mkdir()
    (root / "scripts").mkdir()
    (root / "infrastructure").mkdir()
    (root / ".github/workflows").mkdir(parents=True)
    (root / ".github/workflows/ci.yml").write_text("name: owned fixture\n")
    (root / "uv.lock").write_text("version = 1\n")
    (root / "tests/helpers").mkdir(parents=True)
    (root / "tests/helpers/owned_fixture.py").write_text("def fixture_value():\n    return 19\n")
    (root / "conftest.py").write_text(
        "import importlib.util\nfrom pathlib import Path\nimport pytest\n"
        f"ROOT = Path({str(root)!r})\n"
        "spec = importlib.util.spec_from_file_location('owned_fixture_helper', ROOT/'tests/helpers/owned_fixture.py')\n"
        "helper = importlib.util.module_from_spec(spec)\nspec.loader.exec_module(helper)\n"
        "@pytest.fixture(autouse=True)\ndef actual_root_fixture():\n    assert helper.fixture_value() == 19\n"
    )
    (root / "tests/conftest.py").write_text("OWNED_TEST_FIXTURE = 17\n")
    (root / "pyproject.toml").write_text(
        '[tool.pytest.ini_options]\naddopts = "--import-mode=importlib"\n'
        'markers = ["requires_ollama", "requires_docker", "network", "slow", "bench", "benchmark", "performance"]\n'
        "[tool.coverage.run]\nbranch = true\nomit = []\n"
        "[tool.coverage.report]\nfail_under = 60\n"
    )
    (root / "infrastructure/arithmetic.py").write_text(
        "".join(
            f"def calculation_{index}(left, right):\n"
            "    if left < 0:\n        return left + right - 1\n"
            "    return left + right + 1\n"
            for index in range(SHARD_COUNT)
        )
    )
    # The four actual collected modules fill every declared shard. Their test
    # bodies execute owned arithmetic and append actual observed case names.
    for index, module in enumerate(RESERVED_MODULES):
        path = root / module
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "import importlib.util\nfrom pathlib import Path\nimport pytest\n"
            f"ROOT = Path({str(root)!r})\n"
            "spec = importlib.util.spec_from_file_location('owned_calculation', ROOT/'infrastructure/arithmetic.py')\n"
            "calculation = importlib.util.module_from_spec(spec)\nspec.loader.exec_module(calculation)\n"
            f"def test_actual_case_{index}():\n"
            f"    assert calculation.calculation_{index}(1, 3) == 5\n"
            f"    assert calculation.calculation_{index}(-1, 3) == 1\n"
            f"    with (ROOT/'executed.txt').open('a') as output: output.write('case-{index}\\n')\n"
            "@pytest.mark.slow\ndef test_deferred_case():\n"
            "    raise AssertionError('the original marker exclusion must remain')\n"
        )
    return root


def _native(root: Path, program: str, *, seconds: float = 90.0):
    bootstrap = (
        "import json, pathlib, sys\n"
        "sys.path.insert(0, "
        f"{str(SDK_ROOT)!r}"
        ")\n"
        "import pytest\n"
        "import infrastructure.core.testing.ci_infra_shard_plugin as plugin\n"
        "from infrastructure.core.testing.ci_infra_partition import INFRA_MARKERS\n"
        "from infrastructure.core.testing.ci_infra_coverage import export_shard, mer"
        "ge_shards\n"
        "assert pathlib.Path(plugin.__file__).resolve() == pathlib.Path("
        f"{str(SDK_ROOT)!r}"
        ")/'infrastructure/core/testing/ci_infra_shard_plugin.py'\n"
        "root = pathlib.Path("
        f"{str(root)!r}"
        ")\n"
        "def command(shard):\n"
        "    return ['-c', str(root/'pyproject.toml'), str(root/'tests/infra_tests')"
        ", '-q', '-p', plugin.__name__, '--infra-ci-shard', str(shard), '-m', INFRA_"
        "MARKERS]\n"
    ) + program
    return run_with_policy(
        [sys.executable, "-I", "-c", bootstrap],
        cwd=root,
        env={
            **{
                key: value
                for key, value in os.environ.items()
                if not key.startswith("COV_CORE_") and key != "COVERAGE_PROCESS_START"
            },
            "PYTEST_ADDOPTS": "",
            "PYTHONPATH": "",
            "COVERAGE_FILE": str(root / ".coverage.infra"),
        },
        policy=SubprocessPolicy(
            policy_id="ordinary-infra-ci-owned-fixture",
            source_path="tests/infra_tests/core/test_ci_infra_partition.py",
            timeout_seconds=seconds,
        ),
    )


def test_declared_matrix_retains_every_environment_and_shard() -> None:
    cells = ci_matrix()["include"]
    expected = {
        (runner, version, shard)
        for runner, versions in (
            ("ubuntu-latest", CANONICAL_CI_PYTHON_VERSIONS),
            ("macos-latest", ("3.15",)),
        )
        for version in versions
        for shard in range(SHARD_COUNT)
    }
    actual = {(cell["os"], cell["python-version"], cell["shard"]) for cell in cells}
    assert actual == expected and len(cells) == len(actual) == 12


def test_partition_covers_future_modules_and_every_parameter_without_overlap() -> None:
    ids = [f"{module}::test_actual[param-{parameter}]" for module in RESERVED_MODULES for parameter in range(3)]
    ids.extend(f"tests/infra_tests/new_family/test_future_{index}.py::test_case" for index in range(20))
    assignments = partition(ids)
    assert sorted(node for assigned in assignments for node in assigned) == sorted(ids)
    assert len({node for assigned in assignments for node in assigned}) == len(ids)
    assert partition(list(reversed(ids))) == assignments
    for module, shard in RESERVED_MODULES.items():
        assert module_shard(module) == shard


def test_partition_admits_escaped_parametrization_ids_from_actual_collection() -> None:
    """Real pytest IDs escape bytes/newlines; only the module path must be canonical."""
    ids = [
        "tests/infra_tests/core/test_bytecode_audit.py::test_fields[co_code-\\x97\\x00d\\x00S\\x00]",
        "tests/infra_tests/core/test_health.py::TestSubset::test_table[print('')\\n-False]",
    ]
    assignments = partition(ids)
    assert sorted(node for assigned in assignments for node in assigned) == sorted(ids)


@pytest.mark.parametrize(
    "ids",
    [
        [],
        ["tests/infra_tests/core/test_x.py::test_a"] * 2,
        ["../private/test_x.py::test_a"],
        ["tests/infra_tests/test_x.py"],
        ["tests/infra_tests/../test_x.py::test_a"],
        ["tests\\infra_tests\\core\\test_x.py::test_a"],
        ["tests/infra_tests/core/test_x.py::test_a[\0]"],
    ],
)
def test_partition_refuses_empty_duplicate_or_noncanonical_collection(
    ids: list[str],
) -> None:
    with pytest.raises(ValueError):
        partition(ids)


@pytest.mark.timeout(120)
def test_actual_serial_shards_execute_exact_union_and_enforce_real_branch_coverage(
    tmp_path: Path,
) -> None:
    root = _fixture(tmp_path)
    result = _native(
        root,
        (
            "for shard in range(4):\n"
            "    status = pytest.main(command(shard) + ['--cov='+str(root/'infrastructur"
            "e'), '--cov-report=', '--cov-fail-under=0'])\n"
            "    assert status == 0, status\n"
            "    export_shard(root, shard)\n"
            "assert merge_shards(root) >= 60.0\n"
            "from coverage import Coverage\n"
            "import hashlib, importlib.util\n"
            "foreign = root.parent/'foreign-owned-source.py'\n"
            "foreign.write_text('def selected(value):\\n    if value: return 19\\n    retu"
            "rn 23\\n')\n"
            "capture = Coverage(data_file=str(root/'foreign.coverage'), branch=True, sou"
            "rce=[str(root.parent)])\n"
            "capture.start()\n"
            "spec = importlib.util.spec_from_file_location('owned_foreign_calculation', "
            "foreign)\n"
            "calculation = importlib.util.module_from_spec(spec); spec.loader.exec_modul"
            "e(calculation)\n"
            "assert calculation.selected(True)==19 and calculation.selected(False)==23\n"
            "capture.stop(); capture.save()\n"
            "artifact = root/'output/readiness/ordinary-infra-ci/coverage-data/infra-cov"
            "erage-shard-0'\n"
            "original_data = (artifact/'coverage.data').read_bytes(); original_record = "
            "(artifact/'selection.json').read_bytes()\n"
            "data = (root/'foreign.coverage').read_bytes(); (artifact/'coverage.data').w"
            "rite_bytes(data)\n"
            "record = json.loads(original_record); record['coverage_sha256']=hashlib.sha"
            "256(data).hexdigest()\n"
            "(artifact/'selection.json').write_text(json.dumps(record))\n"
            "def foreign_open_guard(event, arguments):\n"
            "    if event == 'open' and arguments and isinstance(arguments[0], str) and "
            "pathlib.Path(arguments[0]) == foreign:\n"
            "        raise AssertionError('merge attempted to read foreign source')\n"
            "sys.addaudithook(foreign_open_guard)\n"
            "try: foreign.read_text()\n"
            "except AssertionError as error: assert 'read foreign source' in str(error)\n"
            "else: raise AssertionError('genuine open audit control was not active')\n"
            "try: merge_shards(root)\n"
            "except ValueError as error: assert 'foreign source path' in str(error), str"
            "(error)\n"
            "else: raise AssertionError('foreign recorded source authorized coverage mer"
            "ge')\n"
            "(artifact/'coverage.data').write_bytes(original_data); (artifact/'selection"
            ".json').write_bytes(original_record)\n"
        ),
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert sorted((root / "executed.txt").read_text().splitlines()) == [f"case-{index}" for index in range(4)]
    records = [read_receipt(root, receipt_path(root, shard)) for shard in range(SHARD_COUNT)]
    assert (
        len(
            validate_receipts(
                records,
                expected_source=selection_source(root),
                expected_runtime=selected_runtime(),
            )
        )
        == 4
    )
    union = read_receipt(root, root / "output/readiness/ordinary-infra-ci/union.json")
    assert union["totals"]["percent_covered"] >= 60 and union["meta"]["branch_coverage"] is True
    # Actual transferred bytes, not substituted Coverage behavior.
    path = root / ARTIFACT_DIRECTORY / "infra-coverage-shard-0/coverage.data"
    original_data = path.read_bytes()
    path.write_bytes(original_data + b"tamper")
    with pytest.raises(ValueError, match="hash"):
        merge_shards(root)
    path.write_bytes(original_data)
    extra = root / ARTIFACT_DIRECTORY / "unexpected-transfer.txt"
    extra.write_text("genuine undeclared transfer")
    with pytest.raises(ValueError, match="inventory"):
        merge_shards(root)
    extra.unlink()
    outsider = tmp_path / "owned-outsider-data"
    outsider.write_bytes(b"owned sentinel, must not be read or modified")
    path.unlink()
    path.symlink_to(outsider)
    with pytest.raises(ValueError, match="symlink"):
        merge_shards(root)
    assert outsider.read_bytes() == b"owned sentinel, must not be read or modified"
    path.unlink()
    path.write_bytes(original_data)
    # Genuine measured data from one shard cannot substitute for the complete
    # union. Even a matching transfer hash cannot waive the 60% measurement.
    for shard in range(1, SHARD_COUNT):
        directory = root / ARTIFACT_DIRECTORY / f"infra-coverage-shard-{shard}"
        (directory / "coverage.data").write_bytes(original_data)
        selection = read_receipt(root, directory / "selection.json")
        selection["coverage_sha256"] = hashlib.sha256(original_data).hexdigest()
        (directory / "selection.json").write_text(json.dumps(selection))
    with pytest.raises(ValueError, match="below"):
        merge_shards(root)


@pytest.mark.timeout(120)
def test_actual_xdist_workers_agree_and_only_execute_the_assigned_cases(
    tmp_path: Path,
) -> None:
    root = _fixture(tmp_path)
    module = root / next(iter(RESERVED_MODULES))
    module.write_text(
        module.read_text()
        + "\n@pytest.mark.parametrize('private_value', [str(ROOT/'PRIVATE_PARAMETER_SENTINEL')])\n"
        + "def test_actual_parameter_privacy(private_value):\n"
        + "    assert private_value.endswith('PRIVATE_PARAMETER_SENTINEL')\n"
    )
    result = _native(
        root,
        "raise SystemExit(pytest.main(command(0) + ['-n', '2', '--dist', 'loadscope']))\n",
    )
    assert result.returncode == 0, result.stderr + result.stdout
    record = read_receipt(root, receipt_path(root, 0))
    assert record["original_pytest_exit_code"] == record["exit_code"] == 0
    assert record["complete"] is True and record["diagnostics"] == []
    assert record["completed_node_ids"] == record["assigned_node_ids"]
    assert (root / "executed.txt").read_text().splitlines() == ["case-0"]
    diagnostics = _diagnostic_record(root, "0")
    assert diagnostics["active_cases"] == []
    assert diagnostics["first_failure_events"] == []
    assert diagnostics["recent_events"][-1]["event"] == "session_finish"
    assert any(event.get("last_observed_report_phase") == "teardown" for event in diagnostics["recent_events"])
    serialized = json.dumps(diagnostics)
    assert str(root) not in serialized and "PRIVATE_PARAMETER_SENTINEL" not in serialized
    member = next(node for node in record["assigned_node_ids"] if "test_actual_parameter_privacy[" in node)
    assert "PRIVATE_PARAMETER_SENTINEL" in member
    assert any(
        event.get("case_identity_sha256") == hashlib.sha256(member.encode()).hexdigest()
        for event in diagnostics["recent_events"]
    )


@pytest.mark.timeout(120)
@pytest.mark.parametrize("fault", ["invalid-shard", "wrong-markers", "collection-only"])
def test_actual_invalid_partition_invocation_refuses_before_any_body(tmp_path: Path, fault: str) -> None:
    root = _fixture(tmp_path)
    change = {
        "invalid-shard": "args[args.index('--infra-ci-shard')+1] = '99'",
        "wrong-markers": "args[args.index('-m')+1] = 'slow'",
        "collection-only": "args.append('--collect-only')",
    }[fault]
    result = _native(root, "args = command(0)\n" + change + "\nraise SystemExit(pytest.main(args))\n")
    assert result.returncode == 2, result.stderr + result.stdout
    assert not (root / "executed.txt").exists()
    assert not receipt_path(root, 0).exists()


@pytest.mark.timeout(120)
def test_actual_failure_preserves_original_pytest_one(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    module = root / next(iter(RESERVED_MODULES))
    module.write_text(module.read_text() + "\ndef test_actual_failure():\n    assert 0 == 1\n")
    result = _native(root, "raise SystemExit(pytest.main(command(0)))\n")
    assert result.returncode == 1
    record = read_receipt(root, receipt_path(root, 0))
    assert record["original_pytest_exit_code"] == record["exit_code"] == 1
    assert record["complete"] is False
    diagnostics = _diagnostic_record(root, "0")
    assert any(
        event.get("public_family", "").endswith("::test_actual_failure") and event.get("observed_outcome") == "failed"
        for event in diagnostics["first_failure_events"]
    )


@pytest.mark.timeout(120)
@pytest.mark.parametrize(
    "consumed_source",
    [
        "infrastructure/arithmetic.py",
        "conftest.py",
        "tests/conftest.py",
        "tests/helpers/owned_fixture.py",
    ],
)
def test_actual_source_edit_during_execution_refuses_completion(tmp_path: Path, consumed_source: str) -> None:
    root = _fixture(tmp_path)
    module = root / next(iter(RESERVED_MODULES))
    module.write_text(
        module.read_text()
        + "\ndef test_actual_source_mutation():\n"
        + f"    (ROOT/{consumed_source!r}).write_text('CHANGED_CONSUMED_SOURCE = 20\\n')\n"
    )
    result = _native(root, "raise SystemExit(pytest.main(command(0)))\n")
    assert result.returncode == 1
    record = read_receipt(root, receipt_path(root, 0))
    assert record["original_pytest_exit_code"] == 0 and record["exit_code"] == 1
    assert record["complete"] is False and any("source changed" in item for item in record["diagnostics"])


def _records() -> list[dict[str, object]]:
    nodes = [f"{module}::test_actual" for module in RESERVED_MODULES]
    return [
        {
            "schema_version": SCHEMA,
            "shard_count": SHARD_COUNT,
            "shard": shard,
            "all_node_ids": sorted(nodes),
            "assigned_node_ids": list(assigned),
            "completed_node_ids": list(assigned),
            "source_sha256": "actual-fixture-source",
            "python_minor": selected_runtime(),
            "marker_expression": INFRA_MARKERS,
            "original_pytest_exit_code": 0,
            "exit_code": 0,
            "complete": True,
            "diagnostics": [],
        }
        for shard, assigned in enumerate(partition(nodes))
    ]


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "duplicate",
        "wrong-source",
        "wrong-runtime",
        "omitted-case",
        "wrong-assignment",
        "incomplete",
        "failed",
        "marker-change",
    ],
)
def test_complete_merge_admission_refuses_invalid_selection_records(fault: str) -> None:
    records = _records()
    if fault == "missing":
        records.pop()
    elif fault == "duplicate":
        records[1] = records[0].copy()
    elif fault == "wrong-source":
        records[0]["source_sha256"] = "wrong"
    elif fault == "wrong-runtime":
        records[0]["python_minor"] = "0.0"
    elif fault == "omitted-case":
        records[0]["all_node_ids"] = list(records[0]["all_node_ids"])[1:]
    elif fault == "wrong-assignment":
        records[0]["assigned_node_ids"] = records[1]["assigned_node_ids"]
    elif fault == "incomplete":
        records[0]["completed_node_ids"] = []
    elif fault == "failed":
        records[0]["original_pytest_exit_code"] = 1
    else:
        records[0]["marker_expression"] = "slow"
    with pytest.raises(ValueError):
        validate_receipts(
            records,
            expected_source="actual-fixture-source",
            expected_runtime=selected_runtime(),
        )


def test_ci_workflow_consumes_partition_and_keeps_the_union_gate_required() -> None:
    workflow = yaml.safe_load((SDK_ROOT / ".github/workflows/hardening.yml").read_text())
    jobs = workflow["jobs"]
    emit = next(step["run"] for step in jobs["detect-projects"]["steps"] if step.get("id") == "matrix")
    assert "scripts/gates/infra_ci_partition.py --matrix" in emit
    infra = jobs["test-infra"]
    assert infra["timeout-minutes"] == 90 and infra["strategy"]["fail-fast"] is False
    execution = next(step for step in infra["steps"] if step.get("name") == "Run infrastructure tests")
    assert "--infra-ci-shard" in execution["run"] and "--dist loadscope" in execution["run"]
    assert INFRA_MARKERS in execution["run"] and "--timeout=120" in execution["run"]
    assert "--cov-fail-under=0" in execution["env"]["INFRA_COV_FLAGS"]
    assert jobs["coverage-infra"]["needs"] == ["test-infra"]
    assert any("--merge-coverage" in step.get("run", "") for step in jobs["coverage-infra"]["steps"])
    assert "coverage-infra" in jobs["ci-gate"]["needs"]
    assert set(jobs["ci-gate"]["needs"]) == set(jobs) - {"ci-gate"}
    diagnostics = next(
        step for step in infra["steps"] if step.get("name") == "Preserve partial infrastructure controller diagnostics"
    )
    assert diagnostics["if"] == "${{ always() }}" and diagnostics["continue-on-error"] is True
    assert diagnostics["with"]["if-no-files-found"] == "warn"
    assert "/diagnostics/" in diagnostics["with"]["path"]
    slow = jobs["test-infra-slow"]
    slow_execution = next(step for step in slow["steps"] if step.get("name") == "Run slow-marked infrastructure tests")
    assert slow["timeout-minutes"] == 90
    assert "--timeout=1200" in slow_execution["run"] and "-n auto" in slow_execution["run"]
    assert "-m slow" in slow_execution["run"] and "--dist loadscope" in slow_execution["run"]
    assert "--infra-ci-observer-only slow" in slow_execution["run"] and "--infra-ci-shard" not in slow_execution["run"]
    slow_diagnostics = next(
        step for step in slow["steps"] if step.get("name") == "Preserve partial slow-lane controller diagnostics"
    )
    assert slow_diagnostics["if"] == "${{ always() }}" and slow_diagnostics["continue-on-error"] is True
    assert slow_diagnostics["with"]["if-no-files-found"] == "warn"


def test_ci_infra_checkouts_prepare_the_declared_public_pin_before_source_observation() -> None:
    """Both real workflow jobs nominate the same initialized, credential-free source."""
    declarations = configparser.ConfigParser(interpolation=None, strict=True)
    declarations.read_string((SDK_ROOT / ".gitmodules").read_text())
    section = 'submodule "' + _PINNED_SUBMODULE + '"'
    assert not declarations.defaults() and declarations.sections() == [section]
    assert declarations.get(section, "path") == _PINNED_SUBMODULE
    assert declarations.get(section, "url") == _PINNED_SUBMODULE_URL
    # Actual index metadata, rather than a fabricated directory or guessed pin.
    index = native_git(SDK_ROOT, time.monotonic() + 30.0, "ls-files", "--stage", "-z")
    links = []
    for row in index.split(b"\0"):
        if row:
            metadata, path = row.rsplit(b"\t", 1)
            if metadata.startswith(b"160000 "):
                assert metadata.split()[2] == b"0"
                links.append(path.decode("utf-8"))
    assert links == [_PINNED_SUBMODULE]
    jobs = yaml.safe_load((SDK_ROOT / ".github/workflows/hardening.yml").read_text())["jobs"]
    checkouts = []
    for job_name in ("test-infra", "coverage-infra"):
        steps = jobs[job_name]["steps"]
        checkout = steps[0]
        assert checkout["uses"].startswith("actions/checkout@")
        assert len(checkout["uses"].split("@", 1)[1]) == 40
        # Exactly the declared pinned, credential-free setup: no token, key,
        # ref or depth override can substitute a different source.
        assert checkout["with"] == {"submodules": True, "persist-credentials": False}
        assert steps[1]["uses"] == "./.github/actions/setup-python-env"
        assert sum(step.get("uses", "").startswith("actions/checkout@") for step in steps) == 1
        checkouts.append(checkout["uses"])
    assert checkouts[0] == checkouts[1]


@pytest.mark.timeout(120)
def test_actual_zero_collection_refuses_vacuous_success(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    for module in RESERVED_MODULES:
        (root / module).write_text("VALUE = 1\n")
    result = _native(root, "raise SystemExit(pytest.main(command(0)))\n")
    assert result.returncode == 2, result.stdout + result.stderr
    record = read_receipt(root, receipt_path(root, 0))
    assert record["original_pytest_exit_code"] == record["exit_code"] == 2
    assert record["complete"] is False and "nonempty" in result.stderr + result.stdout
    assert any("nonempty" in diagnostic for diagnostic in record["diagnostics"])


@pytest.mark.timeout(120)
def test_actual_xdist_zero_collection_refuses_without_worker_restarts(
    tmp_path: Path,
) -> None:
    """Under xdist the refusal travels through workeroutput; workers never crash."""
    root = _fixture(tmp_path)
    for module in RESERVED_MODULES:
        (root / module).write_text("VALUE = 1\n")
    result = _native(
        root,
        "raise SystemExit(pytest.main(command(0) + ['-n', '2', '--dist', 'loadscope']))\n",
    )
    assert result.returncode == 2, result.stdout + result.stderr
    record = read_receipt(root, receipt_path(root, 0))
    assert record["exit_code"] == 2 and record["complete"] is False
    assert any("nonempty" in diagnostic for diagnostic in record["diagnostics"])
    assert not any("worker failed" in diagnostic for diagnostic in record["diagnostics"])
    assert not (root / "executed.txt").exists()


@pytest.mark.timeout(120)
def test_actual_root_replacement_cannot_publish_into_the_replacement(
    tmp_path: Path,
) -> None:
    root = _fixture(tmp_path)
    module = root / next(iter(RESERVED_MODULES))
    original = tmp_path / "original-owned-root"
    module.write_text(
        module.read_text() + "\ndef test_actual_root_replacement():\n"
        "    import shutil\n"
        f"    ROOT.rename(Path({str(original)!r}))\n"
        f"    shutil.copytree(Path({str(original)!r}), ROOT)\n"
    )
    result = _native(root, "raise SystemExit(pytest.main(command(0)))\n")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "confinement root changed" in result.stdout + result.stderr
    assert original.is_dir() and root.is_dir()
    assert not receipt_path(root, 0).exists() and not receipt_path(original, 0).exists()


def _diagnostic_record(root: Path, lane: str) -> dict[str, object]:
    path = root / "output/readiness/ordinary-infra-ci/diagnostics" / f"shard-{lane}.json"
    assert path.stat().st_mode & 0o777 == 0o600
    value = json.loads(path.read_text())
    assert value["schema_version"] == "template-ordinary-infra-ci-controller-diagnostics-v1"
    assert value["diagnostics_only"] is True
    assert "complete" not in value and "completed_node_ids" not in value and "exit_code" not in value
    assert len(value["recent_events"]) <= value["recent_event_limit"]
    assert len(value["first_failure_events"]) <= value["first_failure_limit"]
    assert len(value["active_cases"]) <= value["active_case_limit"]
    return value


def _lane_program(lane: str) -> str:
    if lane == "ordinary":
        return "args = command(0)\n"
    return (
        "args = command(0)\n"
        "at = args.index('--infra-ci-shard'); del args[at:at+2]\n"
        "args[args.index('-m')+1] = 'slow'\n"
        "args += ['--infra-ci-observer-only', 'slow']\n"
    )


@pytest.mark.timeout(120)
@pytest.mark.parametrize("lane", ["ordinary", "slow"])
def test_actual_xdist_crash_retains_partial_controller_diagnostics(tmp_path: Path, lane: str) -> None:
    root = _fixture(tmp_path)
    if lane == "slow":
        for name in RESERVED_MODULES:
            module = root / name
            module.write_text(
                module.read_text().replace(
                    "raise AssertionError('the original marker exclusion must remain')",
                    "assert 19 == 19",
                )
            )
    module = root / next(iter(RESERVED_MODULES))
    module.write_text(
        module.read_text()
        + "\n"
        + ("@pytest.mark.slow\n" if lane == "slow" else "")
        + "def test_actual_worker_exit():\n    import os\n    os._exit(19)\n"
    )
    supervision = ""
    if lane == "slow":
        # The existing last-case worker-crash mechanics can leave xdist waiting
        # for its replacement worker. Observe the real partial failure, then
        # explicitly terminate only this owned controller within five seconds.
        # Missing failure DATA still fails the assertions below.
        supervision = (
            "import os, signal, threading, time\n"
            "def interrupt_owned_controller():\n"
            "    deadline = time.monotonic() + 20.0\n"
            "    diagnostic = root/'output/readiness/ordinary-infra-ci/diagnostics/shard-slow.json'\n"
            "    while time.monotonic() < deadline:\n"
            "        if diagnostic.exists():\n"
            "            failures = json.loads(diagnostic.read_text())['first_failure_events']\n"
            "            crashed = any(event.get('worker_error_present') is True for event in failures)\n"
            "            reported = any(event.get('public_family', '').endswith('::test_actual_worker_exit') and event.get('observed_outcome') == 'failed' for event in failures)\n"
            "            if crashed and reported: break\n"
            "        time.sleep(0.01)\n"
            "    os.kill(os.getpid(), signal.SIGTERM)\n"
            "threading.Thread(target=interrupt_owned_controller, daemon=True).start()\n"
        )
    result = _native(
        root,
        _lane_program(lane)
        + supervision
        + "raise SystemExit(pytest.main(args + ['-n', '2', '--dist', 'loadscope']))\n",
    )
    assert result.returncode == (1 if lane == "ordinary" else -15), result.stdout + result.stderr
    assert "node down" in result.stdout + result.stderr
    diagnostics = _diagnostic_record(root, "0" if lane == "ordinary" else "slow")
    assert any(event.get("worker_error_present") is True for event in diagnostics["first_failure_events"])
    assert any(
        event.get("public_family", "").endswith("::test_actual_worker_exit")
        and event.get("observed_outcome") == "failed"
        for event in diagnostics["first_failure_events"]
    )
    assert "test_actual_worker_exit" in result.stdout + result.stderr
    if lane == "ordinary":
        selection = read_receipt(root, receipt_path(root, 0))
        assert selection["complete"] is False and selection["exit_code"] == 1
    else:
        assert not any(receipt_path(root, shard).exists() for shard in range(SHARD_COUNT))


@pytest.mark.timeout(120)
@pytest.mark.parametrize("lane", ["ordinary", "slow"])
def test_actual_controller_interruption_retains_started_case(tmp_path: Path, lane: str) -> None:
    root = _fixture(tmp_path)
    if lane == "slow":
        for name in RESERVED_MODULES:
            module = root / name
            module.write_text(
                module.read_text().replace(
                    "raise AssertionError('the original marker exclusion must remain')",
                    "assert 19 == 19",
                )
            )
    module = root / next(iter(RESERVED_MODULES))
    module.write_text(
        module.read_text()
        + "\n"
        + ("@pytest.mark.slow\n" if lane == "slow" else "")
        + "def test_actual_controller_interrupt():\n"
        + "    import os, signal, time\n"
        + "    controller = int((ROOT/'controller.pid').read_text())\n"
        + "    assert controller == os.getppid() and controller != os.getpid()\n"
        + "    import json\n"
        + "    diagnostic = ROOT/'output/readiness/ordinary-infra-ci/diagnostics'/"
        + repr("shard-0.json" if lane == "ordinary" else "shard-slow.json")
        + "\n"
        + "    deadline = time.monotonic() + 5.0\n"
        + "    observed = False\n"
        + "    while time.monotonic() < deadline:\n"
        + "        events = json.loads(diagnostic.read_text())['active_cases']\n"
        + "        observed = any(event.get('public_family', '').endswith('::test_actual_controller_interrupt') and event.get('last_observed_report_phase') == 'setup' for event in events)\n"
        + "        if observed: break\n"
        + "        time.sleep(0.01)\n"
        + "    assert observed, 'owned controller did not retain actual setup within original fixture observation deadline'\n"
        + "    os.kill(controller, signal.SIGTERM)\n"
        + "    time.sleep(60)\n"
    )
    result = _native(
        root,
        "import os\n(root/'controller.pid').write_text(str(os.getpid()))\n"
        + _lane_program(lane)
        + "raise SystemExit(pytest.main(args + ['-n', '2', '--dist', 'loadscope']))\n",
    )
    assert result.returncode == -15, result.stdout + result.stderr
    diagnostics = _diagnostic_record(root, "0" if lane == "ordinary" else "slow")
    active = [
        event
        for event in diagnostics["active_cases"]
        if event.get("public_family", "").endswith("::test_actual_controller_interrupt")
    ]
    assert len(active) == 1 and active[0].get("last_observed_report_phase") == "setup"
    assert not any(event["event"] == "session_finish" for event in diagnostics["recent_events"])
    assert not any(receipt_path(root, shard).exists() for shard in range(SHARD_COUNT))


@pytest.mark.timeout(120)
@pytest.mark.parametrize("outcome", ["passed", "failed"])
def test_actual_slow_observer_only_retains_original_behavior(tmp_path: Path, outcome: str) -> None:
    root = _fixture(tmp_path)
    if outcome == "passed":
        for name in RESERVED_MODULES:
            module = root / name
            module.write_text(
                module.read_text().replace(
                    "raise AssertionError('the original marker exclusion must remain')",
                    "assert 19 == 19",
                )
            )
    program = (
        "invalid = command(0); invalid[invalid.index('-m')+1] = 'slow'\n"
        "invalid += ['--infra-ci-observer-only', 'slow']\n"
        "assert pytest.main(invalid) == 2\n"
        "assert not (root/'executed.txt').exists()\n"
        + _lane_program("slow")
        + "raise SystemExit(pytest.main(args + ['-n', '2', '--dist', 'loadscope']))\n"
    )
    result = _native(root, program)
    assert result.returncode == (0 if outcome == "passed" else 1), result.stdout + result.stderr
    assert not (root / "executed.txt").exists()
    assert not any(receipt_path(root, shard).exists() for shard in range(SHARD_COUNT))
    diagnostics = _diagnostic_record(root, "slow")
    assert diagnostics["recent_events"][-1]["observed_pytest_exit_code"] == result.returncode
    assert diagnostics["active_cases"] == []
    assert bool(diagnostics["first_failure_events"]) is (outcome == "failed")


@pytest.mark.timeout(120)
def test_actual_diagnostic_sink_refusal_preserves_test_outcome(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    outside = tmp_path / "owned-outside-diagnostics"
    outside.mkdir()
    sentinel = outside / "sentinel.txt"
    sentinel.write_bytes(b"retained private fixture sentinel")
    parent = root / "output/readiness/ordinary-infra-ci"
    parent.mkdir(parents=True)
    (parent / "diagnostics").symlink_to(outside, target_is_directory=True)
    result = _native(root, "raise SystemExit(pytest.main(command(0)))\n")
    assert result.returncode == 0, result.stdout + result.stderr
    selection = read_receipt(root, receipt_path(root, 0))
    assert selection["complete"] is True and selection["exit_code"] == 0
    assert "Infrastructure CI" in result.stdout + result.stderr and "diagnostics" in result.stdout + result.stderr
    assert sentinel.read_bytes() == b"retained private fixture sentinel"
    assert sorted(path.name for path in outside.iterdir()) == ["sentinel.txt"]
