#!/usr/bin/env python3
"""Tests for infrastructure.publishing.executable_bundle."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.publishing.executable_bundle import bundle_project, verify_bundle_receipt
import shutil

from tests._support.projects import make_project, write_doc


def _scaffold_bundle_project(root: Path, name: str) -> None:
    project = make_project(root, name, program="templates", with_manuscript=True, with_scripts=True)
    (project / "src" / "demo.py").write_text("def run() -> int:\n    return 0\n")
    (project / "manuscript" / "config.yaml").write_text(
        "publication:\n  doi: '10.5281/zenodo.12345678'\n",
        encoding="utf-8",
    )
    write_doc(root / "pyproject.toml", "[project]\nname = 'demo'\n")
    write_doc(root / "uv.lock", "# lock\n")
    pinned = root / "tests" / "regression" / "pinned_values"
    pinned.mkdir(parents=True)
    (pinned / f"{name}.json").write_text(json.dumps({"claims": []}))
    # Minimal real Layer-1 tree; the bundle vendors it into source/.
    infrastructure = root / "infrastructure"
    infrastructure.mkdir()
    (infrastructure / "__init__.py").write_text("", encoding="utf-8")


def test_bundle_project_writes_manifest_and_dockerfile(tmp_path: Path) -> None:
    name = "template_code_project"
    qualified = f"templates/{name}"
    _scaffold_bundle_project(tmp_path, name)

    out_dir = bundle_project(tmp_path, qualified)

    assert out_dir == tmp_path / "output" / qualified / "executable_bundle"
    assert (out_dir / "manifest.json").is_file()
    assert (out_dir / "Dockerfile").is_file()
    assert (out_dir / "docker-compose.yml").is_file()
    assert (out_dir / "bundle_receipt.json").is_file()
    assert (out_dir / "source" / "src" / "demo.py").is_file()
    verify_bundle_receipt(out_dir)
    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["archival_receipts"]["zenodo_doi"] == "10.5281/zenodo.12345678"
    readme = (out_dir / "README.md").read_text(encoding="utf-8")
    # EXECUTABLE-BUNDLE-MAJ-2 contract: self-contained vendored payload with
    # fail-closed full-pipeline services.
    assert "vendored ``infrastructure/`` copy" in readme
    assert "FAIL CLOSED" in readme
    assert (out_dir / "source" / "infrastructure").is_dir()
    compose = (out_dir / "docker-compose.yml").read_text(encoding="utf-8")
    import yaml as _yaml

    services = _yaml.safe_load(compose)["services"]
    assert "python -m pytest tests -q" in str(services["tests"]["command"])
    assert services["render"]["command"][2].startswith("echo 'EXECUTABLE-BUNDLE UNAVAILABLE-DEPENDENCY RECEIPT")
    assert "No combined PDF was bundled" in readme


def test_bundle_refuses_missing_or_symlinked_infrastructure_tree(tmp_path: Path) -> None:
    """Negative control: the vendored Layer-1 copy is required and must be real."""
    name = "template_code_project"
    qualified = f"templates/{name}"
    _scaffold_bundle_project(tmp_path, name)
    infrastructure = tmp_path / "infrastructure"

    shutil.rmtree(infrastructure)

    # A symlinked Layer-1 tree cannot be vendored (would leak private mirroring)
    external = tmp_path / "external_infrastructure"
    external.mkdir()
    (external / "__init__.py").write_text("", encoding="utf-8")
    infrastructure.symlink_to(external)
    with pytest.raises(ValueError, match="requires a real infrastructure/ tree"):
        bundle_project(tmp_path, qualified)


def test_compose_full_pipeline_services_fail_closed() -> None:
    """Negative control: compose services needing the absent repo root exit non-zero with a receipt."""
    from infrastructure.rendering.dockerfile_gen import build_compose_yaml
    import yaml as _yaml

    services = _yaml.safe_load(build_compose_yaml("templates/template_code_project"))["services"]
    for service in ("reproduce", "render"):
        command = services[service]["command"][2]
        assert "UNAVAILABLE-DEPENDENCY RECEIPT" in command
        assert "exit 3" in command


def test_bundle_project_copies_combined_pdf_when_present(tmp_path: Path) -> None:
    name = "template_code_project"
    qualified = f"templates/{name}"
    _scaffold_bundle_project(tmp_path, name)
    pdf_dir = tmp_path / "output" / qualified / "pdf"
    pdf_dir.mkdir(parents=True)
    pdf_name = f"{name}_combined.pdf"
    pdf_dir.joinpath(pdf_name).write_bytes(b"%PDF-1.4 demo")

    out_dir = bundle_project(tmp_path, qualified)

    copied = out_dir / "artifacts" / "pdf" / pdf_name
    assert copied.is_file()
    assert copied.read_bytes() == b"%PDF-1.4 demo"
    readme = (out_dir / "README.md").read_text(encoding="utf-8")
    assert f"artifacts/pdf/{pdf_name}" in readme


def test_bundle_project_refuses_non_public_project(tmp_path: Path) -> None:
    _scaffold_bundle_project(tmp_path, "template_code_project")
    with pytest.raises(ValueError, match="canonical public"):
        bundle_project(tmp_path, "working/private")


def test_bundle_project_refuses_symlinked_source(tmp_path: Path) -> None:
    name = "template_code_project"
    qualified = f"templates/{name}"
    _scaffold_bundle_project(tmp_path, name)
    project = tmp_path / "projects" / "templates" / name
    external = tmp_path / "private.py"
    external.write_text("secret = True\n", encoding="utf-8")
    (project / "src" / "private.py").symlink_to(external)

    with pytest.raises(ValueError, match="symlinked source"):
        bundle_project(tmp_path, qualified)


def test_bundle_project_ignores_excluded_local_venv_symlinks(tmp_path: Path) -> None:
    """Excluded local interpreter links are not part of the public payload."""
    name = "template_code_project"
    qualified = f"templates/{name}"
    _scaffold_bundle_project(tmp_path, name)
    local_bin = tmp_path / "projects" / "templates" / name / ".venv" / "bin"
    local_bin.mkdir(parents=True)
    (local_bin / "python3").symlink_to("/usr/bin/python3")

    project = tmp_path / "projects" / "templates" / name
    (project / "src" / "__pycache__").mkdir(parents=True)
    (project / "src" / "__pycache__" / "demo.cpython-312.pyc").write_bytes(b"cache")
    (project / "src" / "template_code_project.egg-info").mkdir()
    (project / "src" / "template_code_project.egg-info" / "PKG-INFO").write_text("generated\n", encoding="utf-8")

    out_dir = bundle_project(tmp_path, qualified)

    assert not (out_dir / "source" / ".venv").exists()
    assert not (out_dir / "source" / "src" / "__pycache__").exists()
    assert not (out_dir / "source" / "src" / "template_code_project.egg-info").exists()
    verify_bundle_receipt(out_dir)


def test_bundle_receipt_rejects_changed_payload(tmp_path: Path) -> None:
    """Negative control: changing a bundled file after assembly must fail."""
    name = "template_code_project"
    qualified = f"templates/{name}"
    _scaffold_bundle_project(tmp_path, name)
    out_dir = bundle_project(tmp_path, qualified)
    (out_dir / "source" / "src" / "demo.py").write_text("def run() -> int:\n    return 1\n", encoding="utf-8")

    with pytest.raises(ValueError, match="content changed"):
        verify_bundle_receipt(out_dir)


def test_bundle_receipt_rejects_unexpected_payload(tmp_path: Path) -> None:
    """Negative control: an extra file cannot be published through a stale receipt."""
    name = "template_code_project"
    qualified = f"templates/{name}"
    _scaffold_bundle_project(tmp_path, name)
    out_dir = bundle_project(tmp_path, qualified)
    (out_dir / "unexpected.txt").write_text("not in the receipt\n", encoding="utf-8")

    with pytest.raises(ValueError, match="payload differs"):
        verify_bundle_receipt(out_dir)


def test_bundle_receipt_rejects_traversal_and_duplicate_entries(tmp_path: Path) -> None:
    """Negative controls: receipt paths must be unique and confined."""
    name = "template_code_project"
    qualified = f"templates/{name}"
    _scaffold_bundle_project(tmp_path, name)
    out_dir = bundle_project(tmp_path, qualified)
    receipt_path = out_dir / "bundle_receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    receipt["files"][0]["path"] = "../escape.txt"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(ValueError, match="unsafe path"):
        verify_bundle_receipt(out_dir)

    out_dir = bundle_project(tmp_path, qualified)
    receipt_path = out_dir / "bundle_receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["files"].append(dict(receipt["files"][0]))
    receipt["file_count"] += 1
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate path"):
        verify_bundle_receipt(out_dir)


def test_bundle_receipt_rejects_payload_symlink(tmp_path: Path) -> None:
    """Negative control: a post-build symlink escape must fail closed."""
    name = "template_code_project"
    qualified = f"templates/{name}"
    _scaffold_bundle_project(tmp_path, name)
    out_dir = bundle_project(tmp_path, qualified)
    target = out_dir / "source" / "src" / "demo.py"
    target.unlink()
    target.symlink_to(tmp_path / "private.py")
    (tmp_path / "private.py").write_text("secret = True\n", encoding="utf-8")

    with pytest.raises(ValueError, match="symlinked"):
        verify_bundle_receipt(out_dir)
