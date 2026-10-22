"""Fixed stage DATA controls never stand in for genuine Source/Popen custody."""

from __future__ import annotations

import copy
import importlib.metadata
import hashlib
import json
import shutil
import time
import subprocess
import sys
import venv
from pathlib import Path
from typing import Any

import pytest

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_source_provider_bootstrap import format_selected_sdk_native_bootstrap
from infrastructure.reporting.native_stage_child import current_native_stage_directory, prepare_native_stage_child
from infrastructure.reporting.native_stage_child_contracts import (
    OBSERVATION_SCHEMA,
    SCHEMA,
    WORKER,
    audit_roots,
    binding,
    validate_specification,
    verify_stage_observation,
)
from infrastructure.reporting.native_stage_child_custody import NativeStageChildReaderOperation
from infrastructure.reporting.native_stage_child_scope import retain_native_stage_artifact
from infrastructure.reporting.native_tool_producer import _stage_scope_nomination
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader

SCOPE = "templates/template_code_project"


def test_ordinary_owner_query_imports_without_optional_rendering_dependencies(tmp_path: Path) -> None:
    """A real runtime with required PyYAML can query custody without a PDF provider."""
    environment = tmp_path / "empty-runtime"
    venv.EnvBuilder(with_pip=False).create(environment)
    python = environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    site = environment / (
        "Lib/site-packages"
        if sys.platform == "win32"
        else f"lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages"
    )
    # The SDK declares PyYAML as a required base dependency. Copy the actual
    # installed distribution into this same-ABI venv; no resolver or optional
    # PDF packages participate in the regression environment.
    distribution = importlib.metadata.distribution("PyYAML")
    assert distribution.files
    for member in distribution.files:
        relative = Path(str(member))
        assert not relative.is_absolute() and ".." not in relative.parts
        original = Path(distribution.locate_file(member))
        assert original.is_file() and not original.is_symlink()
        destination = site / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original, destination)
    root = Path(__file__).resolve().parents[3]
    result = subprocess.run(
        [
            str(python),
            "-I",
            "-c",
            "import importlib.metadata,importlib.util,sys;from pathlib import Path;"
            "assert importlib.util.find_spec('reportlab') is None;"
            "import yaml;"
            "assert Path(yaml.__file__).resolve().is_relative_to(Path(sys.prefix).resolve());"
            "assert importlib.metadata.version('PyYAML') == sys.argv[2];"
            "assert yaml.safe_load('provider: genuine') == {'provider':'genuine'};"
            "sys.path.insert(0,sys.argv[1]);"
            "from infrastructure.reporting.native_tool_producer import current_native_producer_operation;"
            "assert current_native_producer_operation() is None;"
            "assert 'infrastructure.reporting.native_source_external_admission' not in sys.modules;"
            "assert 'infrastructure.rendering' not in sys.modules;"
            "print('ordinary-query-without-native-provider')",
            str(root),
            distribution.version,
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "ordinary-query-without-native-provider"


def test_native_owner_construction_still_requires_actual_admitted_source() -> None:
    from infrastructure.reporting.native_tool_producer import NativeProducerOperation

    with pytest.raises(ValueError, match="genuine admitted Source"):
        NativeProducerOperation(object(), "actual-run", time.monotonic() + 30)


def _snapshot(root: Path, relative: str, value: dict[str, Any]) -> ArtifactSnapshot:
    raw = (json.dumps(value, sort_keys=True) + "\n").encode()
    return ArtifactSnapshot(root / relative, relative, raw, hashlib.sha256(raw).hexdigest(), (1, 2, len(raw), 3))


def _specification(root: Path) -> tuple[dict[str, Any], ArtifactSnapshot]:
    """Only normalized DATA fixtures; no fixture constructs Source or an owner."""
    parent_directory = "output/readiness/actual-original-scope"
    directory = parent_directory + "/native-stage/run/stage/attempt/child-" + "a" * 32
    request = _snapshot(
        root, directory + "/request.json", {"run_id": "actual-pipeline-run", "stage_key": "02_analysis"}
    )
    spec = {
        "schema_version": SCHEMA,
        "scope": SCOPE,
        "run_id": "b" * 32,
        "pipeline_run_id": "actual-pipeline-run",
        "stage_key": "02_analysis",
        "nonce": "a" * 32,
        "directory": directory,
        "source": {},
        "implementation": {"path": directory + "/implementation.json", "sha256": "c" * 64},
        "request": binding(request),
        "request_digest": canonical_digest(request.json_object()),
        "protocol": "stage",
        "script": {"path": "scripts/pipeline/stage_02_analysis.py", "sha256": "d" * 64},
        "cwd": str(root),
        "parent_pid": 7,
        "parent_directory": parent_directory,
        "parent_platform": "Darwin",
        "deadline_monotonic": 5000.0,
        "parent_deadline_monotonic": 6000.0,
        "closure_identity": [1, 10],
        "prefix_identity": [1, 11],
        "directory_identity": [1, 12],
        "source_audit_roots": [str(path) for path in audit_roots(root, root / "infrastructure", SCOPE)],
    }
    return spec, request


def _observation(spec: dict[str, Any], request: ArtifactSnapshot, returned: int | None) -> dict[str, Any]:
    return {
        "schema_version": OBSERVATION_SCHEMA,
        "scope": spec["scope"],
        "run_id": spec["run_id"],
        "pipeline_run_id": spec["pipeline_run_id"],
        "stage_key": spec["stage_key"],
        "nonce": spec["nonce"],
        "request": binding(request),
        "request_digest": spec["request_digest"],
        "worker_pid": 17,
        "parent_pid": 7,
        "stage_return_code": returned,
        "stage_exception": {"class": "OSError", "module": "builtins"} if returned is None else None,
        "result": None,
        "original_checkpoint": None,
        "nested_tool_artifacts": [],
        "stage_children": [],
        "stage_artifacts": [],
        "script_intent_authority": "Source stage worker only; child signed OS belongs to parent ToolAPI",
    }


def test_fixed_bootstrap_covers_all_actual_source_lanes_and_original_stage_deadline(tmp_path: Path) -> None:
    root, sdk = tmp_path / "mirror", tmp_path / "sdk/infrastructure"
    hook = b"# fixture is bootstrap DATA, not a Source audit or executable role\n"
    original_deadline = time.monotonic() + 7200
    command = format_selected_sdk_native_bootstrap(
        hook,
        sdk,
        audit_roots(root, sdk, SCOPE)[1:],
        root / "output/readiness/input.json",
        "a" * 64,
        root / "output/readiness/native-stage/run/stage/child/closure",
        (1, 20),
        original_deadline,
        required_worker_module=WORKER,
    )
    assert repr(original_deadline) in command
    for location in audit_roots(root, sdk, SCOPE):
        assert repr(str(location)) in command
    assert "native_stage_child_worker" in command
    assert "STAGE_CHILD_CLOSURE_V1 " in command
    assert "nullcontext" in command


def test_arbitrary_worker_module_is_refused_before_any_execution(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        format_selected_sdk_native_bootstrap(
            b"",
            tmp_path,
            (),
            tmp_path / "input",
            "a" * 64,
            tmp_path / "closure",
            (1, 2),
            time.monotonic() + 10,
            required_worker_module="arbitrary.module",
        )


@pytest.mark.parametrize("returned", [0, 1, 17, 75, 124, 130, 255, None])
def test_stage_script_conventions_are_data_with_distinct_pipeline_and_native_run_ids(
    tmp_path: Path, returned: int | None
) -> None:
    spec, request = _specification(tmp_path)
    assert spec["run_id"] != spec["pipeline_run_id"]
    validate_specification(spec)
    verify_stage_observation(spec, _observation(spec, request, returned), child_pid=17, request=request)


@pytest.mark.parametrize(
    "field,value",
    [
        ("run_id", "wrong"),
        ("pipeline_run_id", "wrong"),
        ("nonce", "wrong"),
        ("scope", "private"),
        ("parent_pid", True),
        ("deadline_monotonic", 6001.0),
        ("deadline_monotonic", float("nan")),
        ("parent_deadline_monotonic", float("inf")),
        ("directory", "../outside"),
        ("directory", "/absolute"),
        ("closure_identity", [1, True]),
        ("prefix_identity", [1]),
        ("source_audit_roots", ["/one"]),
        ("request_digest", "wrong"),
        ("cwd", "relative"),
        ("parent_directory", "output/readiness/different-original-scope"),
        ("parent_directory", "/absolute"),
        ("parent_directory", "output/readiness/../outside"),
    ],
)
def test_specification_controls_refuse_changed_identities_clocks_roots_and_held_directories(
    tmp_path: Path, field: str, value: Any
) -> None:
    spec, _ = _specification(tmp_path)
    if field == "pipeline_run_id":
        value = ""  # Nonempty pipeline identities are bound to the actual request later.
    spec[field] = value
    with pytest.raises(ValueError):
        validate_specification(spec)


@pytest.mark.parametrize("field", ["scope", "run_id", "pipeline_run_id", "stage_key", "nonce", "request_digest"])
def test_late_observation_identity_change_is_refused(tmp_path: Path, field: str) -> None:
    spec, request = _specification(tmp_path)
    value = _observation(spec, request, 17)
    value[field] = "late-change"
    with pytest.raises(ValueError):
        verify_stage_observation(spec, value, child_pid=17, request=request)


@pytest.mark.parametrize("returned", [-2, -15, 256, True, "0"])
def test_signed_os_status_cannot_be_misrepresented_as_script_intent(tmp_path: Path, returned: Any) -> None:
    spec, request = _specification(tmp_path)
    with pytest.raises(ValueError):
        verify_stage_observation(spec, _observation(spec, request, returned), child_pid=17, request=request)


def test_observation_cannot_claim_completion_authority_or_replace_request_bytes(tmp_path: Path) -> None:
    spec, request = _specification(tmp_path)
    value = _observation(spec, request, 0)
    value["script_intent_authority"] = "OS success"
    with pytest.raises(ValueError):
        verify_stage_observation(spec, value, child_pid=17, request=request)
    value = _observation(spec, request, 0)
    changed = _snapshot(tmp_path, request.relative, {"run_id": "late"})
    with pytest.raises(ValueError):
        verify_stage_observation(spec, value, child_pid=17, request=changed)
    with pytest.raises(ValueError):
        verify_stage_observation(spec, value, child_pid=18, request=request)


def test_returned_intent_and_exception_are_mutually_consistent(tmp_path: Path) -> None:
    spec, request = _specification(tmp_path)
    value = _observation(spec, request, 17)
    value["stage_exception"] = {"class": "OSError", "module": "builtins"}
    with pytest.raises(ValueError):
        verify_stage_observation(spec, value, child_pid=17, request=request)
    value = _observation(spec, request, None)
    value["stage_exception"]["caller_expected_status"] = 0
    with pytest.raises(ValueError):
        verify_stage_observation(spec, value, child_pid=17, request=request)


@pytest.mark.parametrize("field", ["nested_tool_artifacts", "stage_children", "stage_artifacts"])
@pytest.mark.parametrize("damage", ["repeat", "absolute", "traversal", "extra-status", "wrong-hash"])
def test_late_retained_roster_row_refuses_repeats_paths_and_status_minting(
    tmp_path: Path, field: str, damage: str
) -> None:
    spec, request = _specification(tmp_path)
    value = _observation(spec, request, 0)
    rows = [{"path": f"output/readiness/native-stage/tool-{index}.json", "sha256": "e" * 64} for index in range(20)]
    if damage == "repeat":
        rows[-1] = dict(rows[0])
    elif damage == "absolute":
        rows[-1]["path"] = "/absolute/tool.json"
    elif damage == "traversal":
        rows[-1]["path"] = "output/readiness/../tool.json"
    elif damage == "extra-status":
        rows[-1]["expected_status"] = 0
    else:
        rows[-1]["sha256"] = "wrong"
    value[field] = rows
    with pytest.raises(ValueError):
        verify_stage_observation(spec, value, child_pid=17, request=request)


def test_data_packet_cannot_open_a_source_owner_stage_directory_or_reader(tmp_path: Path) -> None:
    from infrastructure.reporting.native_stage_child_completion import observe_native_stage_child

    spec, request = _specification(tmp_path)
    with pytest.raises(ValueError, match="actual fixed parent preparation call"):
        observe_native_stage_child(spec, {})
    assert current_native_stage_directory() is None
    with pytest.raises(ValueError, match="actual live Source owner"):
        prepare_native_stage_child(spec, SCOPE, request, tmp_path, deadline=time.monotonic() + 10)
    with pytest.raises(ValueError, match="exact Source-owned concrete role"):
        NativeStageChildReaderOperation(
            copy.deepcopy(spec),
            SnapshotReader(tmp_path),
            [],
            scope=SCOPE,
            run_id="b" * 32,
            deadline=time.monotonic() + 10,
        )
    with pytest.raises(ValueError, match="actual admitted fixed child scope"):
        retain_native_stage_artifact(request, tool_artifacts=[])
    assert not (tmp_path / "output").exists()


def test_stage_scope_nomination_is_optional_paired_data_and_preserves_physical_identity(tmp_path: Path) -> None:
    assert _stage_scope_nomination(tmp_path, None, None) is None
    directory = tmp_path / "output/readiness/actual-original-scope"
    directory.mkdir(parents=True)
    observed = _stage_scope_nomination(tmp_path, SCOPE, directory)
    assert observed is not None and observed[:2] == (SCOPE, directory)
    directory.rename(directory.with_name("retained-original-scope"))
    directory.mkdir()
    replacement = _stage_scope_nomination(tmp_path, SCOPE, directory)
    assert replacement is not None and replacement[2] != observed[2]


@pytest.mark.parametrize(
    "scope,relative",
    [(None, "output/readiness/scope"), (SCOPE, None), ("private", "output/readiness/scope"), (SCOPE, "outside")],
)
def test_stage_scope_data_nomination_refuses_missing_pair_unknown_scope_and_outside_lane(
    tmp_path: Path, scope: str | None, relative: str | None
) -> None:
    directory = tmp_path / relative if relative is not None else None
    if directory is not None:
        directory.mkdir(parents=True)
    with pytest.raises(ValueError):
        _stage_scope_nomination(tmp_path, scope, directory)


def test_stage_scope_nomination_refuses_symbolic_parent_directory(tmp_path: Path) -> None:
    real = tmp_path / "output/readiness/actual-original-scope"
    real.mkdir(parents=True)
    alias = real.with_name("alias-scope")
    alias.symlink_to(real, target_is_directory=True)
    with pytest.raises(ValueError):
        _stage_scope_nomination(tmp_path, SCOPE, alias)


def test_specification_refuses_root_lane_sibling_and_wrong_nonce_child(tmp_path: Path) -> None:
    for directory in (
        "output/readiness/native-stage/run/stage/attempt/child-" + "a" * 32,
        "output/readiness/sibling-scope/native-stage/run/stage/attempt/child-" + "a" * 32,
        "output/readiness/actual-original-scope/native-stage/run/stage/attempt/child-" + "b" * 32,
    ):
        spec, _ = _specification(tmp_path)
        spec["directory"] = directory
        spec["request"]["path"] = directory + "/request.json"
        with pytest.raises(ValueError):
            validate_specification(spec)
