"""Actual valid-PDF semantic, geometry and localized visibility controls."""

from __future__ import annotations

import base64
import copy
import json
import sys
import time
from pathlib import Path
from typing import Any

import pytest

from infrastructure.core.execution_boundary import build_bounded_env, run_bounded_subprocess
from infrastructure.core.implementation_custody import bytecode_audit_bootstrap
from infrastructure.project.public_acceptance_evidence import read_json, write_json, runtime_identity
from infrastructure.core.pipeline.fingerprints import paths_digest
from infrastructure.reporting.native_format_portable_custody import producer_custody, validate_producer_custody
from infrastructure.reporting.native_format_acceptance_checks import native_tool_record, parse_native_bytes
from infrastructure.reporting.native_format_acceptance_contracts import (
    create_private_native_directory,
    native_environment,
)
from infrastructure.reporting.native_format_acceptance_validation import _pdf_controls, _tool
from infrastructure.reporting.native_format_acceptance_worker import _pdf_oracle_control
from infrastructure.reporting.native_format_content_contracts import content_contract_from_bytes, text_tokens
from infrastructure.reporting.native_format_pdf_oracles import (
    PDF_CONTROL_CODES,
    inspect_pdf_content,
    pdf_control_bytes,
    pdf_control_contract,
    require_pdf_control_result,
)
from infrastructure.reporting.native_projection_contracts import ProjectionSourceUnsupported
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

REPO = Path(__file__).resolve().parents[3]
# Strict replay authenticates every retained native tool receipt against the
# externally admitted Source and original launch custodian. Receipt DATA and a
# bare SnapshotReader never hold them, so replay refuses before reconstruction.
UNADMITTED = "externally admitted source and original launch custody"
pytestmark = pytest.mark.timeout(600)


def test_actual_pdf_bytes_are_independent_of_epoch_in_separate_processes(tmp_path: Path) -> None:
    """Reproduce the worker/reader clock difference without changing parent state."""
    observed: list[dict[str, bytes]] = []
    deadline = time.monotonic() + 120
    for index, epoch in enumerate((None, "1700000000", "946684800")):
        prefix = tmp_path / f"epoch-{index}-bytecode"
        prefix.mkdir()
        environment = build_bounded_env()
        environment.pop("SOURCE_DATE_EPOCH", None)
        if epoch is not None:
            environment["SOURCE_DATE_EPOCH"] = epoch
        code = bytecode_audit_bootstrap((REPO / "infrastructure",), prefix)
        code += (
            "import base64,json,os,sys\nfrom pathlib import Path\n"
            "sys.path.insert(0,sys.argv[1])\n"
            "from infrastructure.reporting.native_format_pdf_oracles import PDF_CONTROL_CODES,pdf_control_bytes\n"
            "before=os.environ.get('SOURCE_DATE_EPOCH')\n"
            "documents={name:base64.b64encode(pdf_control_bytes(name)).decode('ascii') for name in PDF_CONTROL_CODES}\n"
            "_audit_scope['verify_executed_source_code'](Path(sys.argv[1])/'infrastructure',Path(sys.pycache_prefix))\n"
            "print(json.dumps({'epoch_before':before,'epoch_after':os.environ.get('SOURCE_DATE_EPOCH'),"
            "'documents':documents},sort_keys=True))\n"
        )
        result = run_bounded_subprocess(
            (sys.executable, "-I", "-X", f"pycache_prefix={prefix}", "-c", code, str(REPO)),
            cwd=tmp_path,
            env=environment,
            timeout=min(40, deadline - time.monotonic()),
        )
        assert result.returncode == result.original_returncode == 0, result.stderr
        assert result.timed_out is result.custody_refused is False
        payload = json.loads(result.stdout)
        assert payload["epoch_before"] == payload["epoch_after"] == epoch
        assert set(payload["documents"]) == set(PDF_CONTROL_CODES)
        documents = {name: base64.b64decode(raw, validate=True) for name, raw in payload["documents"].items()}
        for raw in documents.values():
            assert parse_native_bytes("pdf", raw)["pages"] == 1
        assert len(set(documents.values())) == len(PDF_CONTROL_CODES)
        observed.append(documents)
    assert observed[0] == observed[1] == observed[2]
    assert observed[0] == {name: pdf_control_bytes(name) for name in PDF_CONTROL_CODES}


@pytest.fixture(scope="module")
def actual_pdf_controls(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    """All five actual children share one finite source-independent fixture clock."""
    root = tmp_path_factory.mktemp("actual-native-pdf")
    directory = root / "output/readiness/controls"
    create_private_native_directory(root, directory)
    nonce = "c" * 32
    deadline = time.monotonic() + 450
    env = native_environment(REPO, Path(sys.executable), directory)
    runtime = runtime_identity()
    source_digest = paths_digest((REPO / "infrastructure",), source=True)
    custody = validate_producer_custody(producer_custody(root, runtime, source_digest), runtime, source_digest)
    versions = {
        name: native_tool_record(
            root, directory, name, ["-v"], env=env, deadline=deadline, run_id=nonce, purpose=f"version-{name}"
        )
        for name in ("pdftoppm", "pdffonts")
    }
    controls = [_pdf_oracle_control(root, directory, nonce, name, env, deadline) for name in PDF_CONTROL_CODES]
    # The positive baseline must have completed before the mutated valid inputs.
    assert controls[0]["expected_exit_code"] == controls[0]["observed_exit_code"] == 0
    return {
        "root": root,
        "directory": directory,
        "nonce": nonce,
        "deadline": deadline,
        "controls": controls,
        "versions": versions,
        "runtime": runtime,
        "custody": custody,
    }


def test_source_tokens_preserve_signs_numeric_units_and_punctuation() -> None:
    assert text_tokens("offset -3.25 mV; +4% ≠ 5.0 ms") == (
        "offset",
        "-",
        "3",
        ".",
        "25",
        "mV",
        ";",
        "+",
        "4",
        "%",
        "≠",
        "5",
        ".",
        "0",
        "ms",
    )
    assert text_tokens("e\u0301  ﬁ") == ("é", "fi")
    assert text_tokens("-3.25 mV") != text_tokens("3.25 mv")


def test_source_contract_keeps_order_occurrences_and_current_hashes() -> None:
    raw = b"# Observation\n\nOffset -3.25 mV.\n\n- Offset -3.25 mV.\n"
    first = content_contract_from_bytes("manuscript:pdf", (("01.md", raw),))
    changed = content_contract_from_bytes("manuscript:pdf", (("01.md", raw.replace(b"-3.25", b"-8.25")),))
    assert [block.id for block in first.blocks] == ["01.md:1", "01.md:3", "01.md:5"]
    assert [block.kind for block in first.blocks] == ["heading", "body", "body"]
    assert first.blocks[1].tokens == first.blocks[2].tokens
    assert first.digest != changed.digest and first.sources != changed.sources
    assert first.blockers == ()


def test_math_markup_and_zero_collection_stay_explicitly_blocked() -> None:
    contract = content_contract_from_bytes("manuscript:pdf", (("math.md", b"$x=-3.25$ [@citation]\n"),))
    assert contract.blocks == ()
    assert any("math/citation" in reason for reason in contract.blockers)
    assert "no supported source-text obligations collected" in contract.blockers
    with pytest.raises(ValueError, match="source-byte budget"):
        content_contract_from_bytes("manuscript:pdf", (("oversized.md", b"a" * (4 * 1024 * 1024 + 1)),))
    metadata = content_contract_from_bytes(
        "manuscript:pdf", (("metadata.md", b"---\ntitle: Private metadata projection\n---\n\nVisible body.\n"),)
    )
    assert len(metadata.blocks) == 1 and metadata.blocks[0].tokens == ("Visible", "body", ".")
    assert any("metadata-frontmatter" in reason for reason in metadata.blockers)


@pytest.mark.parametrize("name", tuple(PDF_CONTROL_CODES))
def test_actual_valid_pdf_reaches_exact_intended_observer(name: str, actual_pdf_controls: dict[str, Any]) -> None:
    fixture = actual_pdf_controls
    control = next(row for row in fixture["controls"] if row["name"] == name)
    raw = read_json(fixture["root"], fixture["root"] / control["artifact"]["path"])
    artifact = raw["artifact"]
    reader = SnapshotReader(fixture["root"])
    pdf = reader.read(artifact["path"])
    assert pdf.content == pdf_control_bytes(name)
    assert parse_native_bytes("pdf", pdf.content)["pages"] == 1
    pixels = tuple(reader.read(item["path"]).content for item in artifact["raster"]["rasters"])
    oracle = inspect_pdf_content(pdf.content, pixels, pdf_control_contract(), deadline=time.monotonic() + 30)
    assert raw["pdf_content"] == oracle
    assert {finding["code"] for finding in oracle["findings"]} == (
        {PDF_CONTROL_CODES[name]} if PDF_CONTROL_CODES[name] else set()
    )
    code = require_pdf_control_result(name, oracle)
    process = read_json(fixture["root"], fixture["root"] / control["process_artifact"]["path"])
    assert raw["exit_code"] == process["exit_code"] == process["original_exit_code"] == code
    assert process["timed_out"] is process["custody_refused"] is False
    assert reader.unchanged()


def _replay_controls(fixture: dict[str, Any], controls: list[dict[str, Any]]) -> dict[str, Any]:
    """Run the strict control replay with only retained DATA and a bare reader."""
    reader = SnapshotReader(fixture["root"])
    versions = {
        name: read_json(fixture["root"], fixture["root"] / record["artifact"]["path"])
        for name, record in fixture["versions"].items()
    }
    return _pdf_controls(
        {"pdf_negative_controls": controls},
        reader,
        fixture["directory"],
        fixture["nonce"],
        fixture["runtime"],
        {"deadline_monotonic": fixture["deadline"]},
        versions,
        True,
        fixture["custody"],
        deadline=fixture["deadline"],
    )


def _independent_oracle(fixture: dict[str, Any], control: dict[str, Any]) -> dict[str, Any]:
    raw = read_json(fixture["root"], fixture["root"] / control["artifact"]["path"])
    reader = SnapshotReader(fixture["root"])
    pdf = reader.read(raw["artifact"]["path"])
    pixels = tuple(reader.read(item["path"]).content for item in raw["artifact"]["raster"]["rasters"])
    return inspect_pdf_content(pdf.content, pixels, pdf_control_contract(), deadline=time.monotonic() + 30)


def test_strict_reader_reconstructs_actual_pdf_controls(actual_pdf_controls: dict[str, Any]) -> None:
    """Reconstruction needs original launch custody; bare DATA never admits it."""
    fixture = actual_pdf_controls
    reader = SnapshotReader(fixture["root"])
    for name, record in fixture["versions"].items():
        with pytest.raises(ProjectionSourceUnsupported, match=UNADMITTED):
            _tool(record["artifact"], reader, fixture["nonce"], name, f"version-{name}", ["-v"])
    with pytest.raises(ProjectionSourceUnsupported, match=UNADMITTED):
        _replay_controls(fixture, fixture["controls"])
    assert reader.unchanged()


def test_strict_reader_refuses_forged_observer_bytes(actual_pdf_controls: dict[str, Any]) -> None:
    fixture = actual_pdf_controls
    controls = copy.deepcopy(fixture["controls"])
    path = fixture["root"] / controls[1]["artifact"]["path"]
    original = path.read_bytes()
    payload = read_json(fixture["root"], path)
    payload["pdf_content"]["pdf_sha256"] = "0" * 64
    try:
        controls[1]["artifact"] = write_json(fixture["root"], path, payload)
        # The forged observation cannot equal an independent recomputation
        # from the retained PDF and raster bytes, and it cannot be admitted.
        assert _independent_oracle(fixture, controls[1]) != payload["pdf_content"]
        with pytest.raises(ProjectionSourceUnsupported, match=UNADMITTED):
            _replay_controls(fixture, controls)
    finally:
        path.write_bytes(original)


def test_missing_baseline_and_wrong_process_code_cannot_count(actual_pdf_controls: dict[str, Any]) -> None:
    fixture = actual_pdf_controls
    with pytest.raises(ValueError, match="absent or duplicated"):
        _replay_controls(fixture, fixture["controls"][1:])
    controls = copy.deepcopy(fixture["controls"])
    path = fixture["root"] / controls[1]["process_artifact"]["path"]
    original = path.read_bytes()
    process = read_json(fixture["root"], path)
    process["original_exit_code"] = 7
    try:
        controls[1]["process_artifact"] = write_json(fixture["root"], path, process)
        with pytest.raises(ProjectionSourceUnsupported, match=UNADMITTED):
            _replay_controls(fixture, controls)
    finally:
        path.write_bytes(original)


def test_changed_consumed_source_cannot_reuse_positive_observation(actual_pdf_controls: dict[str, Any]) -> None:
    fixture = actual_pdf_controls
    raw = read_json(fixture["root"], fixture["root"] / fixture["controls"][0]["artifact"]["path"])
    reader = SnapshotReader(fixture["root"])
    pdf = reader.read(raw["artifact"]["path"])
    pixels = tuple(reader.read(item["path"]).content for item in raw["artifact"]["raster"]["rasters"])
    changed = content_contract_from_bytes(
        "invented-control:pdf",
        (("invented-public-control.md", b"# Invented public measurement\n\nMeasured offset -8.25 mV.\n"),),
    )
    observation = inspect_pdf_content(pdf.content, pixels, changed, deadline=time.monotonic() + 30)
    assert observation["status"] == "fail"
    assert {item["code"] for item in observation["findings"]} == {"pdf.content.missing"}
    assert observation["contract_digest"] != raw["pdf_content"]["contract_digest"]
    with pytest.raises(TimeoutError, match="finite deadline"):
        inspect_pdf_content(pdf.content, pixels, changed, deadline=time.monotonic() - 1)


def test_infrastructure_refusal_is_not_a_valid_pdf_negative() -> None:
    with pytest.raises(ValueError, match="exact intended diagnostic"):
        require_pdf_control_result(
            "changed-number",
            {"status": "fail", "blockers": [], "findings": [{"code": "infrastructure.launch-refused"}]},
        )
