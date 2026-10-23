"""Real filesystem transport of producer diagnostics grants no capability admission."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import pytest

from infrastructure.core.testing._ci_execution_files import _export
from infrastructure.project.public_acceptance_evidence import read_json
from infrastructure.project.public_acceptance_literature_diagnostics import (
    _read_retained_literature_receipt,
    literature_failure_context,
    retain_literature_originals,
)


def producer_files(tmp_path: Path, status: str):
    root = tmp_path.resolve()
    project = root / "projects/templates/template_test"
    directory = project / "output/.pipeline/literature_acceptance/original"
    directory.mkdir(parents=True)
    native = {
        "status": status,
        "source_unchanged": True,
        "consumed_unchanged": True,
        "producer_results": {},
        "issues": ["actual responding producer rejected its bounded annotation"],
    }
    files = {
        "receipt.json": (json.dumps(native, indent=2) + "\n").encode(),
        "model_1/request.json": b'{"model":"controlled","prompt":"public source"}\n',
        "model_1/response.json": b'{"response":"invalid annotation"}\n',
        "model_1/execution.json": b'{"returncode":1,"timed_out":false}\n',
        "phase_0_retrieval/body.bin": b"public provider original bytes\x00\xff",
    }
    for name, body in files.items():
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
    cell = root / "output/readiness/auxiliary/002"
    return root, project, directory, cell, native, files


@pytest.mark.parametrize("status", ["failed", "blocked", "passed"])
def test_every_original_is_exported_before_any_status_admission(tmp_path, status):
    root, project, source, cell, native, files = producer_files(tmp_path, status)
    observed, receipt, originals = retain_literature_originals(
        root, project, source / "receipt.json", cell, time.monotonic() + 30
    )
    assert observed == native
    assert json.loads((root / receipt["path"]).read_bytes()) == native
    manifest = json.loads((root / originals["path"]).read_bytes())
    assert manifest["acceptance_granted"] is False
    assert set(manifest["files"]) == set(files)
    assert manifest["bytes"] == sum(map(len, files.values()))
    assert manifest["original_receipt"]["sha256"] == hashlib.sha256(files["receipt.json"]).hexdigest()
    for name, body in files.items():
        binding = manifest["files"][name]
        assert (root / binding["path"]).read_bytes() == body
        assert binding["sha256"] == hashlib.sha256(body).hexdigest()
        assert binding["bytes"] == len(body)
    (source / "model_1/response.json").write_bytes(b"later replacement")
    assert (cell / "literature-originals/model_1/response.json").read_bytes() == files["model_1/response.json"]
    assert observed["status"] == status


def test_symlink_original_refuses_even_a_passing_receipt(tmp_path):
    root, project, source, cell, _, _ = producer_files(tmp_path, "passed")
    outside = root / "outside.bin"
    outside.write_bytes(b"must not be exported")
    (source / "escaped.bin").symlink_to(outside)
    with pytest.raises(ValueError, match="link/special"):
        retain_literature_originals(root, project, source / "receipt.json", cell, time.monotonic() + 30)
    assert not (cell / "literature-native.json").exists()
    assert not (cell / "literature-originals.json").exists()
    assert not (cell / "literature-originals/escaped.bin").exists()


def test_receipt_outside_selected_producer_directory_is_refused(tmp_path):
    root, project, source, cell, _, _ = producer_files(tmp_path, "failed")
    outside = root / "foreign/receipt.json"
    outside.parent.mkdir()
    outside.write_bytes((source / "receipt.json").read_bytes())
    with pytest.raises(ValueError, match="fresh child"):
        retain_literature_originals(root, project, outside, cell, time.monotonic() + 30)
    assert not cell.exists()


def test_original_expired_deadline_cannot_complete_transport(tmp_path):
    root, project, source, cell, _, _ = producer_files(tmp_path, "failed")
    with pytest.raises(ValueError, match="deadline exhausted"):
        retain_literature_originals(root, project, source / "receipt.json", cell, time.monotonic() - 1)
    assert not (cell / "literature-originals.json").exists()


def test_failure_context_is_bounded_and_omits_headers_and_environment(tmp_path):
    root, project, source, cell, native, _ = producer_files(tmp_path, "failed")
    observed, receipt, originals = retain_literature_originals(
        root, project, source / "receipt.json", cell, time.monotonic() + 30
    )
    native.update(issues=["native issue " * 1000] * 1000, headers={"secret": "private-header-marker"})
    native["environment"] = {"token": "private-environment-marker"}
    context = literature_failure_context(native, "retrieval", receipt, originals)
    assert len(context) < 1800
    assert "native issue" in context and receipt["sha256"] in context and originals["sha256"] in context
    assert "private-header-marker" not in context and "private-environment-marker" not in context
    assert observed["status"] == "failed"


def test_retained_receipt_join_ignores_the_pre_copy_observation_after_real_mutation(tmp_path):
    root, _, source, cell, _, _ = producer_files(tmp_path, "passed")
    prior_observation = read_json(root, source / "receipt.json")
    assert prior_observation["status"] == "passed"
    replacement = dict(prior_observation, status="failed", issues=["responding producer failed after initial read"])
    replacement_bytes = (json.dumps(replacement) + "\n").encode()
    (source / "receipt.json").write_bytes(replacement_bytes)
    retained = cell / "literature-originals"
    retained.mkdir(parents=True)
    _export(source, retained, time.monotonic() + 30)
    observed, bound, original = _read_retained_literature_receipt(root, retained, cell)
    assert observed == replacement and observed["status"] == "failed"
    assert original["sha256"] == hashlib.sha256(replacement_bytes).hexdigest()
    assert (retained / "receipt.json").read_bytes() == replacement_bytes
    assert json.loads((root / bound["path"]).read_bytes()) == replacement
    assert bound["sha256"] == hashlib.sha256((root / bound["path"]).read_bytes()).hexdigest()
