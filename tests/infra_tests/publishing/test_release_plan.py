"""Real owned Git metadata transactions; no fabricated runtime acceptance."""

from __future__ import annotations

from pathlib import Path
import os
import json
import subprocess
import shutil
import sys
import tomllib

import jsonschema
import pytest
import yaml

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.publishing.release_plan import (
    CONTRACT,
    CONTRACT_VALUE,
    build_release_plan,
    canonical,
    check_release_plan,
    sha256,
)
from infrastructure.publishing.release_plan_transaction import apply_release_plan, rollback_release_plan
from infrastructure.publishing.root_release_contract import RUNTIME_VERSION_PROVIDER_SOURCE


def _git(root: Path, *arguments: str) -> bytes:
    return subprocess.check_output(
        [
            "git",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "user.name=Owned Release Test",
            "-c",
            "user.email=release@example.invalid",
            "-C",
            str(root),
            *arguments,
        ],
        stderr=subprocess.PIPE,
    )


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    root = tmp_path / "owned"
    root.mkdir()
    roster = f"PUBLIC_PROJECT_NAMES: tuple[str, ...] = {PUBLIC_PROJECT_NAMES!r}\n".encode()
    fixed = {
        CONTRACT: canonical(CONTRACT_VALUE),
        "infrastructure/_version.py": RUNTIME_VERSION_PROVIDER_SOURCE.encode(),
        "infrastructure/project/public_scope.py": roster,
    }
    for path, body in fixed.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
    for scope in ("root", *PUBLIC_PROJECT_NAMES):
        base = root if scope == "root" else root / "projects" / scope
        base.mkdir(parents=True, exist_ok=True)
        package = "research-project-template" if scope == "root" else Path(scope).name.replace("_", "-")
        own_version = "4.0.1" if scope == "root" else "2.1.3"
        metadata = f'[project]\nname = "{package}"\nversion = "{own_version}"\n'
        if scope != "root":
            metadata += 'dependencies = ["research-project-template==4.0.1"]\n[tool.template]\nplatform_version = "4.0.1"\n[tool.uv.sources]\nresearch-project-template = { path = "../../..", editable = true }\n'
        if scope == "templates/template_advanced_literature_review":
            metadata += 'template-literature-meta-analysis = { path = "../template_literature_meta_analysis", editable = true }\n'
        (base / "pyproject.toml").write_text(metadata)
        if scope != "root":
            publication = base / "manuscript/config.yaml"
            publication.parent.mkdir()
            publication.write_text(
                'publication:\n  platform_version: "4.0.1" # Keep comment\n'
                '  intended_version: "2.1.3"\n  doi: "10.example/owned"\n'
            )
        editable = "." if scope == "root" else "../../.."
        (base / "uv.lock").write_text(
            f'version = 1\n[[package]]\nname = "research-project-template"\nversion = "4.0.1"\nsource = {{ editable = "{editable}" }}\n[[package]]\nname = "third-party"\nversion = "4.0.1"\nsource = {{ registry = "https://example.invalid" }}\n'
        )
    _git(root, "init", "-q")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "Owned miniature release metadata DATA")
    return root


def _plan(root: Path) -> dict:
    return build_release_plan(root, "4.0.2", expected_current="4.0.1")


def test_real_git_plan_apply_and_exact_rollback_preserve_own_versions_and_locks(
    repository: Path, tmp_path: Path
) -> None:
    plan = _plan(repository)
    assert plan == _plan(repository)
    check_release_plan(repository, plan)
    assert len(plan["inputs"]) == 80 and len(plan["changes"]) == 77
    assert plan["provider_order"].index("templates/template_literature_meta_analysis") < plan["provider_order"].index(
        "templates/template_advanced_literature_review"
    )
    original = {row["path"]: (repository / row["path"]).read_bytes() for row in plan["inputs"]}
    review = sha256(canonical(plan))
    journal = tmp_path / "private-review"
    result = apply_release_plan(repository, plan, reviewed_sha256=review, journal=journal)
    assert result["role"] == "metadata-preparation-only"
    assert len(result["required_followup"]) == 7
    for scope in PUBLIC_PROJECT_NAMES:
        metadata = tomllib.loads((repository / "projects" / scope / "pyproject.toml").read_text())
        assert metadata["project"]["version"] == "2.1.3"
        assert metadata["tool"]["template"]["platform_version"] == "4.0.2"
        publication = repository / "projects" / scope / "manuscript/config.yaml"
        assert yaml.safe_load(publication.read_text()) == {
            "publication": {"platform_version": "4.0.2", "intended_version": "2.1.3", "doi": "10.example/owned"}
        }
        assert "# Keep comment" in publication.read_text()
    for path in ("uv.lock", *(f"projects/{scope}/uv.lock" for scope in PUBLIC_PROJECT_NAMES)):
        rows = tomllib.loads((repository / path).read_text())["package"]
        assert [row["version"] for row in rows] == ["4.0.2", "4.0.1"]
    rollback_release_plan(repository, journal, reviewed_sha256=review)
    assert all((repository / path).read_bytes() == body for path, body in original.items())
    assert _git(repository, "diff", "--exit-code") == b""


@pytest.mark.parametrize(
    "change",
    ["unknown-scope", "wrong-sha", "stale-input", "new-head", "alias", "compatibility", "provider-outside", "legacy"],
)
def test_real_git_plan_refuses_unreviewed_or_mismatched_inputs(repository: Path, tmp_path: Path, change: str) -> None:
    plan = _plan(repository)
    review = sha256(canonical(plan))
    root_metadata = repository / "pyproject.toml"
    if change == "unknown-scope":
        plan["public_roster"].append("working/private")
    elif change == "wrong-sha":
        review = "0" * 64
    elif change == "stale-input":
        root_metadata.write_text(root_metadata.read_text() + "\n# Later unrelated edit\n")
    elif change == "new-head":
        _git(repository, "commit", "--allow-empty", "-qm", "Later commit")
    elif change == "alias":
        body = root_metadata.read_bytes()
        root_metadata.unlink()
        elsewhere = tmp_path / "outside.toml"
        elsewhere.write_bytes(body)
        root_metadata.symlink_to(elsewhere)
    elif change == "legacy":
        root_metadata.write_text(root_metadata.read_text().replace("4.0.1", "3.9.0"))
    else:
        target = repository / "projects" / PUBLIC_PROJECT_NAMES[0] / "pyproject.toml"
        target.write_text(
            target.read_text().replace('platform_version = "4.0.1"', 'platform_version = "4.0.0"')
            if change == "compatibility"
            else target.read_text().replace('path = "../../.."', 'path = "../../../../private"')
        )
    with pytest.raises((ValueError, OSError)):
        apply_release_plan(repository, plan, reviewed_sha256=review, journal=tmp_path / "refused")
    assert not (tmp_path / "refused").exists()


def test_partial_transaction_rollback_and_foreign_edit_refusal(repository: Path, tmp_path: Path) -> None:
    plan = _plan(repository)
    review = sha256(canonical(plan))
    journal = tmp_path / "journal"
    apply_release_plan(repository, plan, reviewed_sha256=review, journal=journal)
    # Reproduce an interruption after only some actual metadata replacements.
    row = plan["changes"][0]
    (repository / row["path"]).write_bytes((journal / "0000.before").read_bytes())
    rollback_release_plan(repository, journal, reviewed_sha256=review)
    assert _git(repository, "diff", "--exit-code") == b""
    # Journal is retained; an unrelated later edit must never be overwritten.
    target = repository / "projects" / PUBLIC_PROJECT_NAMES[0] / "manuscript/config.yaml"
    target.write_bytes(target.read_bytes() + b"\n# Foreign edit\n")
    with pytest.raises(ValueError, match="unrelated current bytes"):
        rollback_release_plan(repository, journal, reviewed_sha256=review)
    assert target.read_bytes().endswith(b"# Foreign edit\n")


@pytest.mark.parametrize(
    "change",
    [
        "old-binding",
        "duplicate-field",
        "duplicate-publication",
        "alias",
        "mapping-alias",
        "publication-alias",
        "untracked",
    ],
)
def test_publication_binding_refuses_ambiguous_or_unowned_inputs(repository: Path, change: str) -> None:
    relative = f"projects/{PUBLIC_PROJECT_NAMES[0]}/manuscript/config.yaml"
    target = repository / relative
    if change == "old-binding":
        target.write_text(target.read_text().replace('"4.0.1"', '"4.0.0"'))
    elif change == "duplicate-field":
        target.write_text(target.read_text() + '  platform_version: "4.0.1"\n')
    elif change == "duplicate-publication":
        target.write_text(target.read_text() + 'publication:\n  platform_version: "4.0.1"\n')
    elif change == "alias":
        target.write_text('sdk: &version "4.0.1"\npublication:\n  platform_version: *version\n')
    elif change == "mapping-alias":
        target.write_text('defaults: &pub\n  platform_version: "4.0.1"\npublication: *pub\n')
    elif change == "publication-alias":
        target.write_text('publication: &pub\n  platform_version: "4.0.1"\nelsewhere: *pub\n')
    else:
        _git(repository, "rm", "--cached", "--", relative)
    with pytest.raises((ValueError, subprocess.CalledProcessError)):
        _plan(repository)


@pytest.mark.skipif(os.name != "posix" or os.getuid() == 0, reason="requires real unprivileged POSIX permissions")
def test_real_atomic_write_failure_rolls_back_prior_replacements(repository: Path, tmp_path: Path) -> None:
    plan = _plan(repository)
    journal = tmp_path / "real-failure-journal"
    # Project metadata parents remain writable. Root metadata is encountered
    # later, where the genuine no-follow atomic writer must fail on permissions.
    repository.chmod(0o555)
    try:
        with pytest.raises(PermissionError):
            apply_release_plan(repository, plan, reviewed_sha256=sha256(canonical(plan)), journal=journal)
    finally:
        repository.chmod(0o755)
    assert (journal / "rolled-back.json").is_file()
    assert not (journal / "applied.json").exists()
    assert _git(repository, "diff", "--exit-code") == b""


@pytest.mark.parametrize(
    "current,target", [("3.9.0", "3.9.1"), ("4.0.1", "4.1.0"), ("4.0.1", "4.0.1"), ("4.0.1", "4.0.2rc1")]
)
def test_release_plan_refuses_legacy_or_nonpatch_version_transitions(
    repository: Path, current: str, target: str
) -> None:
    with pytest.raises(ValueError, match="next patch"):
        build_release_plan(repository, target, expected_current=current)


def test_actual_public_metadata_plan_preserves_every_nonroot_lock_record(tmp_path: Path) -> None:
    """Copy only actual metadata DATA, not the large Source/SDK/output census."""
    source = Path(__file__).resolve().parents[3]
    owned = tmp_path / "actual-metadata-only"
    owned.mkdir()
    paths = [CONTRACT, "infrastructure/_version.py", "infrastructure/project/public_scope.py"]
    paths.extend(
        prefix + name
        for scope in ("root", *PUBLIC_PROJECT_NAMES)
        for prefix in ["" if scope == "root" else f"projects/{scope}/"]
        for name in ("pyproject.toml", "uv.lock")
    )
    paths.extend(f"projects/{scope}/manuscript/config.yaml" for scope in PUBLIC_PROJECT_NAMES)
    for path in paths:
        target = owned / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((source / path).read_bytes())
    _git(owned, "init", "-q")
    _git(owned, "add", ".")
    _git(owned, "commit", "-qm", "Owned actual public metadata DATA")
    old = tomllib.loads((owned / "pyproject.toml").read_text())["project"]["version"]
    major, minor, patch = map(int, old.split("."))
    plan = build_release_plan(owned, f"{major}.{minor}.{patch + 1}", expected_current=old)
    schema = json.loads((source / "infrastructure/publishing/release_plan.schema.json").read_bytes())
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(plan, schema)
    before = {
        row["path"]: tomllib.loads((owned / row["path"]).read_text())
        for row in plan["inputs"]
        if row["path"].endswith("uv.lock")
    }
    publications = {
        scope: yaml.safe_load((owned / "projects" / scope / "manuscript/config.yaml").read_text())
        for scope in PUBLIC_PROJECT_NAMES
    }
    apply_release_plan(owned, plan, reviewed_sha256=sha256(canonical(plan)), journal=tmp_path / "actual-journal")
    for scope, original in publications.items():
        original["publication"]["platform_version"] = plan["root_after"]
        assert yaml.safe_load((owned / "projects" / scope / "manuscript/config.yaml").read_text()) == original
    for path, original in before.items():
        updated = tomllib.loads((owned / path).read_text())
        expected = original.copy()
        expected["package"] = [row for row in original["package"] if row["name"] != "research-project-template"]
        updated["package"] = [row for row in updated["package"] if row["name"] != "research-project-template"]
        assert updated == expected
    uv = shutil.which("uv")
    assert uv is not None, "the declared uv toolchain is required"
    for scope in ("root", *PUBLIC_PROJECT_NAMES):
        base = owned if scope == "root" else owned / "projects" / scope
        exported = subprocess.run(
            [
                uv,
                "export",
                "--directory",
                str(base),
                "--locked",
                "--offline",
                "--no-default-groups",
                "--no-emit-project",
                "--no-emit-local",
                "--no-header",
                "--no-annotate",
                "--no-python-downloads",
                "--python",
                sys.executable,
            ],
            capture_output=True,
            check=False,
            timeout=30,
        )
        assert exported.returncode == 0, (scope, exported.stderr.decode(errors="replace"))
    # The actual exporter must accept the existing resolution without rewriting
    # either authored metadata or lock bytes after the planned transformation.
    for row in plan["changes"]:
        assert sha256((owned / row["path"]).read_bytes()) == row["after_sha256"]


def test_thin_cli_dry_run_and_check_match_library_plan(repository: Path, tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[3] / "scripts/maintenance/coordinated_release.py"
    command = [sys.executable, str(script), "--repo-root", str(repository)]
    emitted = subprocess.check_output(
        [*command, "plan", "--from-version", "4.0.1", "--to-version", "4.0.2"], timeout=30
    )
    assert json.loads(emitted) == _plan(repository)
    plan_file = tmp_path / "reviewed.json"
    plan_file.write_bytes(emitted)
    result = subprocess.check_output([*command, "check", "--plan", str(plan_file)], timeout=30)
    assert json.loads(result)["status"] == "current"
    assert _git(repository, "diff", "--exit-code") == b""
