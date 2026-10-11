"""Real source declarations, artifacts and processes for required acceptance."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from infrastructure.core.pipeline.plan import compile_execution_plan
from infrastructure.core.pipeline.types import PipelineConfig
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.project.public_acceptance_evidence import runtime_identity
from infrastructure.publishing.root_release_contract import RUNTIME_VERSION_PROVIDER_SOURCE
from infrastructure.reporting.readiness_receipts import SCHEMA_VERSION, source_fingerprint
from infrastructure.reporting.release_readiness import collect_release_readiness, main
from infrastructure.reporting.release_readiness_pipeline import validate_pipeline
from infrastructure.reporting.release_readiness_profile import ARTIFACT_SCHEMA, Requirement, required_profile
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.reporting.release_readiness_validators import validate_acceptance


def _declarations(root: Path) -> None:
    (root / "pyproject.toml").write_text('[project]\nname="research-project-template"\nversion="4.0.1"\n')
    (root / ".python-version").write_text("3.14\n")
    (root / "CHANGELOG.md").write_text("## [4.0.1] — intended candidate\n")
    (root / "infrastructure").mkdir()
    (root / "infrastructure/_version.py").write_text(RUNTIME_VERSION_PROVIDER_SOURCE)
    for project in PUBLIC_PROJECT_NAMES:
        path = root / "projects" / project
        (path / "manuscript").mkdir(parents=True)
        (path / "src").mkdir()
        (path / "src/model.py").write_text("def score():\n    return 1\n")
        (path / "tests").mkdir()
        (path / "tests/test_model.py").write_text("def test_one():\n    assert 1\ndef test_two():\n    assert 2\n")
        (path / "pyproject.toml").write_text(
            '[project]\nname="exemplar"\nversion="2.0.0"\n'
            '[tool.template]\nplatform_version="4.0.1"\n'
            'tested_python_versions=["3.12","3.13","3.14"]\nrequired_unpaid_capabilities=[]\n'
        )
        (path / "manuscript/config.yaml").write_text(
            'publication:\n  intended_version: "2.0.0"\n  platform_version: "4.0.1"\n'
            "render:\n  formats:\n    pdf: true\n    html: false\n    slides: false\n    docx: false\n    epub: false\n"
        )


def _binding(root: Path, name: str, data: dict) -> dict[str, str]:
    path = root / "output/readiness" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, sort_keys=True))
    return {"path": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def _receipt(
    root: Path,
    requirement: Requirement,
    *,
    status: str = "pass",
    details: dict | None = None,
    blockers: list | None = None,
) -> Path:
    fingerprint = source_fingerprint(root)
    payload = {
        "schema_version": ARTIFACT_SCHEMA,
        "gate": requirement.id,
        "status": status,
        "version": requirement.version,
        "platform_version": requirement.platform_version,
        "scope": requirement.scope,
        "source_fingerprint": fingerprint,
        "source_identity": requirement.source_identity,
        "details": details or {},
        "blockers": blockers,
    }
    if requirement.scope != "root":
        payload["deliverables_identity"] = requirement.deliverables_identity
    artifact = _binding(root, "acceptance.json", payload)
    receipt = root / "output/readiness/receipt.json"
    receipt.write_text(
        json.dumps(
            {
                "schema_version": SCHEMA_VERSION,
                "platform_version": "4.0.1",
                "source_fingerprint": fingerprint,
                "roster": list(PUBLIC_PROJECT_NAMES),
                "gates": {
                    requirement.id: {
                        "status": status,
                        "command": [sys.executable, "check.py"],
                        "artifact": artifact["path"],
                        "artifact_sha256": artifact["sha256"],
                    }
                },
            }
        )
    )
    return receipt


def _requirements(root: Path) -> tuple[Requirement, ...]:
    requirements, faults = required_profile(root, SnapshotReader(root), source_fingerprint(root))
    assert not faults
    return requirements


def test_source_owned_profile_requires_every_project_runtime_and_capability(tmp_path: Path) -> None:
    _declarations(tmp_path)
    project = PUBLIC_PROJECT_NAMES[0]
    meta = tmp_path / "projects" / project / "pyproject.toml"
    meta.write_text(
        meta.read_text().replace("required_unpaid_capabilities=[]", 'required_unpaid_capabilities=["local-review"]')
    )
    requirements = _requirements(tmp_path)
    assert {req.scope for req in requirements} == {"root", *PUBLIC_PROJECT_NAMES}
    for project in PUBLIC_PROJECT_NAMES:
        assert {req.python_version for req in requirements if req.scope == project and req.kind == "runtime"} == {
            "3.12",
            "3.13",
            "3.14",
        }
        assert {req.kind for req in requirements if req.scope == project} >= {
            "coverage",
            "pipeline",
            "formats",
            "domain",
            "installed",
            "export",
            "publication",
        }
    assert any(req.capability == "local-review" for req in requirements)
    report = collect_release_readiness(tmp_path)
    assert report.status == "unknown"
    assert not report.candidate_ready


@pytest.mark.parametrize(
    "provider",
    [
        '__version__ = "4.0.1"\n',
        RUNTIME_VERSION_PROVIDER_SOURCE + "raise RuntimeError('untrusted')\n",
        RUNTIME_VERSION_PROVIDER_SOURCE.replace("research-project-template", "other-package"),
    ],
)
def test_runtime_provider_is_validated_from_snapshot_without_execution(tmp_path: Path, provider: str) -> None:
    _declarations(tmp_path)
    (tmp_path / "infrastructure/_version.py").write_text(provider)
    requirements, faults = required_profile(tmp_path, SnapshotReader(tmp_path), source_fingerprint(tmp_path))
    assert not requirements
    assert len(faults) == 1 and faults[0].id == "root:metadata" and faults[0].state == "fail"


def test_one_asserted_project_without_case_evidence_cannot_complete_the_required_roster(tmp_path: Path) -> None:
    _declarations(tmp_path)
    requirement = next(
        req
        for req in _requirements(tmp_path)
        if req.kind == "runtime"
        and req.scope != "root"
        and req.python_version == f"{sys.version_info.major}.{sys.version_info.minor}"
    )
    probe = _binding(tmp_path, "runtime-probe.json", dict(runtime_identity(), execution_exit_code=0))
    receipt = _receipt(
        tmp_path,
        requirement,
        details={
            "execution_exit_code": 0,
            "python_version": requirement.python_version,
            "collected": 2,
            "passed": 2,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
            "deselected": 0,
            "test_files": list(requirement.test_files),
            "interpreter": sys.executable,
            "implementation": platform.python_implementation(),
            "python_full_version": platform.python_version(),
            "runtime_artifact": probe,
        },
    )
    report = collect_release_readiness(tmp_path, readiness_receipt=receipt)
    assert report.status == "fail"
    assert any(gate.id == requirement.id and gate.state == "fail" for gate in report.evidence.gates)
    assert not report.overall_ready and not report.candidate_ready


def test_explicit_required_tool_blocker_remains_blocked(tmp_path: Path, capsys) -> None:
    _declarations(tmp_path)
    requirement = next(req for req in _requirements(tmp_path) if req.id == "root:macos:rendering")
    receipt = _receipt(
        tmp_path, requirement, status="blocked", blockers=[{"tool": "xelatex", "reason": "not installed"}]
    )
    report = collect_release_readiness(tmp_path, readiness_receipt=receipt)
    assert report.status == "blocked"
    assert (
        main(["--repo-root", str(tmp_path), "--readiness-receipt", str(receipt), "--strict", "--format", "json"]) == 75
    )
    assert json.loads(capsys.readouterr().out)["production_authorized"] is False


@pytest.mark.parametrize("mutation", ["hash", "absolute", "private", "status", "version", "roster"])
def test_invalid_required_evidence_fails_instead_of_becoming_missing(tmp_path: Path, mutation: str) -> None:
    _declarations(tmp_path)
    requirement = _requirements(tmp_path)[0]
    receipt = _receipt(tmp_path, requirement, status="unknown")
    payload = json.loads(receipt.read_text())
    entry = payload["gates"][requirement.id]
    if mutation == "hash":
        entry["artifact_sha256"] = "0" * 64
    elif mutation == "absolute":
        entry["artifact"] = str(tmp_path / entry["artifact"])
    elif mutation == "private":
        entry["artifact"] = "projects/working/private/receipt.json"
    elif mutation == "status":
        entry["status"] = True
    elif mutation == "version":
        payload["platform_version"] = "3.2.0"
    else:
        payload["roster"] = list(PUBLIC_PROJECT_NAMES[:-1])
    receipt.write_text(json.dumps(payload))
    assert collect_release_readiness(tmp_path, readiness_receipt=receipt).status == "fail"


def test_raw_singleton_summary_and_tag_hint_cannot_grant_release(tmp_path: Path) -> None:
    _declarations(tmp_path)
    report_path = tmp_path / "output" / PUBLIC_PROJECT_NAMES[0] / "reports/pipeline_report.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_text('{"stages":[{"status":"passed","exit_code":0}]}')
    report = collect_release_readiness(tmp_path, latest_tag="v4.0.1")
    assert report.pipeline.available and not report.pipeline.ready
    assert report.release.latest_tag == "v4.0.1"
    assert report.evidence.verified_tag is None and report.status == "unknown"


@pytest.mark.timeout(120)
def test_actual_plan_completion_rejects_singletons_duplicates_skips_and_wrong_order(tmp_path: Path) -> None:
    project = "templates/template_code_project"
    project_root = tmp_path / "projects" / project
    project_root.mkdir(parents=True)
    script = tmp_path / "scripts/step.py"
    script.parent.mkdir()
    script.write_text('import sys\nassert "--project" in sys.argv\nprint("step completed")\n')
    pipeline = project_root / "pipeline.yaml"
    pipeline.write_text(
        "stages:\n  - key: first\n    name: First\n    script: scripts/step.py\n"
        "  - key: second\n    name: Second\n    script: scripts/step.py\n    depends_on: [First]\n"
    )
    config = PipelineConfig(project, tmp_path, clean=False, skip_infra=True)
    plan = compile_execution_plan(config)
    outcomes = []
    for stage in plan.stages:
        child = subprocess.run(
            [sys.executable, str(tmp_path / stage.script), *stage.arguments],
            capture_output=True,
            timeout=5,
            check=False,
        )
        assert child.returncode == 0
        outcomes.append({"stage_key": stage.key, "status": "succeeded", "child_exit_code": child.returncode})
    details = {
        "mode": "core",
        "run_id": "real-control",
        "selection": {"skip_clean": True, "skip_infra": True},
        "plan": json.loads(json.dumps(plan.to_dict())),
        "plan_digest": plan.digest,
        "expected_stage_keys": list(plan.expected_stage_keys),
        "outcomes": outcomes,
    }
    validate_pipeline(project, details, tmp_path)
    for invalid in [
        outcomes[:1],
        outcomes[::-1],
        outcomes + outcomes[:1],
        [dict(outcomes[0], status="skipped"), outcomes[1]],
        [dict(outcomes[0], child_exit_code=False), outcomes[1]],
    ]:
        with pytest.raises(ValueError):
            validate_pipeline(project, dict(details, outcomes=invalid), tmp_path)
    invented = dict(
        details,
        expected_stage_keys=["invented"],
        outcomes=[{"stage_key": "invented", "status": "succeeded", "child_exit_code": 0}],
    )
    with pytest.raises(ValueError):
        validate_pipeline(project, invented, tmp_path)


def test_paid_or_transport_only_live_receipt_cannot_pass(tmp_path: Path) -> None:
    requirement = Requirement(
        "project:live:local-review",
        "live",
        "templates/template_code_project",
        "2.0.0",
        "4.0.1",
        "a" * 64,
        capability="local-review",
    )
    binding = _binding(tmp_path, "controlled.json", {"execution_kind": "controlled"})
    details = {
        "execution_exit_code": 0,
        "capability": "local-review",
        "paid": False,
        "execution_kind": "actual",
        "execution_artifact": binding,
    }
    with pytest.raises(ValueError, match="actual capability"):
        validate_acceptance(requirement, {"details": details}, SnapshotReader(tmp_path))
    with pytest.raises(ValueError, match="unpaid"):
        validate_acceptance(requirement, {"details": dict(details, paid=True)}, SnapshotReader(tmp_path))


def test_source_declared_draft_does_not_require_fabricated_publication(tmp_path: Path) -> None:
    requirement = Requirement(
        "project:publication",
        "publication",
        "templates/template_code_project",
        "2.0.0",
        "4.0.1",
        "a" * 64,
        profile="released",
        draft=True,
    )
    details = {
        "execution_exit_code": 0,
        "unpublished": True,
        "intended_version": "2.0.0",
        "doi": None,
        "actual_tag": None,
        "published_version": None,
    }
    validate_acceptance(requirement, {"details": details}, SnapshotReader(tmp_path))
    with pytest.raises(ValueError, match="unpublished"):
        validate_acceptance(requirement, {"details": dict(details, actual_tag="v2.0.0")}, SnapshotReader(tmp_path))
    with pytest.raises(ValueError):
        validate_acceptance(replace(requirement, draft=False), {"details": details}, SnapshotReader(tmp_path))


@pytest.mark.parametrize("kind", ["docs", "roster"])
def test_platform_four_auxiliary_flags_require_original_process_and_raw_evidence(tmp_path: Path, kind: str) -> None:
    details = {"execution_exit_code": 0}
    if kind == "docs":
        details.update(mermaid=[], broken_links=[], consistency=[], doc_pairs=[])
    else:
        details["projects"] = list(PUBLIC_PROJECT_NAMES)
    requirement = Requirement("root:" + kind, kind, "root", "4.0.1", "4.0.1", "a" * 64)
    payload = {"source_fingerprint": "b" * 64, "details": details}
    with pytest.raises(ValueError, match="exact artifact binding"):
        validate_acceptance(requirement, payload, SnapshotReader(tmp_path))
    legacy = replace(requirement, platform_version="3.8.0")
    validate_acceptance(legacy, payload, SnapshotReader(tmp_path))
    with pytest.raises(ValueError, match="exact artifact binding"):
        validate_acceptance(
            legacy, {**payload, "details": {**details, "process_artifact": None}}, SnapshotReader(tmp_path)
        )
