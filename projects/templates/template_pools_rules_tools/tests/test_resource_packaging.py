"""Actual public resource admission for standalone wheel builds."""

from pathlib import Path

import pytest

from template_pools_rules_tools.resource_paths import bundle_public_resources, public_resource_root


def _resources(root: Path) -> None:
    for kind in ("fonds", "rules", "tools"):
        target = root / kind / "templates" / "public-example"
        target.mkdir(parents=True)
        (target / "manifest.yaml").write_text(f"kind: {kind}\n")
        private = root / kind / "working"
        private.mkdir()
        (private / "private.txt").write_text("private sentinel")


def test_canonical_and_exported_builds_bundle_only_public_templates(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    _resources(repository)
    project = repository / "projects/templates/template_pools_rules_tools"
    project.mkdir(parents=True)
    destination = tmp_path / "built-package"
    copied = bundle_public_resources(project, destination)
    assert len(copied) == 3
    assert all("/templates/" in name for name in copied)
    assert not list(destination.rglob("private.txt"))
    export = tmp_path / "export"
    export.mkdir()
    (export / "_template_resources").mkdir()
    _resources(export / "_template_resources")
    other = tmp_path / "other-built-package"
    assert bundle_public_resources(export, other) == copied
    assert sorted(path.read_bytes() for path in other.rglob("manifest.yaml")) == sorted(
        path.read_bytes() for path in destination.rglob("manifest.yaml")
    )


@pytest.mark.parametrize("unsafe", ["symlink", "credential", "missing-root"])
def test_unowned_or_private_resources_cannot_enter_a_wheel(tmp_path: Path, unsafe: str) -> None:
    project = tmp_path / "export"
    project.mkdir()
    resources = project / "_template_resources"
    resources.mkdir()
    _resources(resources)
    if unsafe == "symlink":
        (resources / "fonds/templates/private-link").symlink_to(
            resources / "fonds/working", target_is_directory=True
        )
    elif unsafe == "credential":
        (resources / "fonds/templates/.env").write_text("private sentinel")
    else:
        (resources / "tools/templates/public-example/manifest.yaml").unlink()
        (resources / "tools/templates/public-example").rmdir()
        (resources / "tools/templates").rmdir()
    with pytest.raises(ValueError):
        bundle_public_resources(project, tmp_path / "built")


def test_absent_standalone_bundle_does_not_infer_arbitrary_ancestor_resources(
    tmp_path: Path,
) -> None:
    project = tmp_path / "standalone"
    project.mkdir()
    with pytest.raises(ValueError, match="requires"):
        bundle_public_resources(project, tmp_path / "built")
    assert public_resource_root("fonds").parts[-2:] == ("fonds", "templates")
    with pytest.raises(ValueError, match="outside"):
        public_resource_root("private")


@pytest.mark.parametrize("boundary", ["source", "destination"])
def test_resource_bundle_refuses_ancestor_redirection(tmp_path: Path, boundary: str) -> None:
    project = tmp_path / "source" / "project"
    project.mkdir(parents=True)
    _resources(project / "_template_resources")
    external = tmp_path / "external"
    external.mkdir()
    sentinel = external / "private.txt"
    sentinel.write_text("private sentinel")
    link = tmp_path / "linked"
    if boundary == "source":
        link.symlink_to(project.parent, target_is_directory=True)
        project = link / "project"
        destination = tmp_path / "built"
    else:
        link.symlink_to(external, target_is_directory=True)
        destination = link / "nested/built"
    with pytest.raises(ValueError, match="ancestor symlink"):
        bundle_public_resources(project, destination)
    assert sentinel.read_text() == "private sentinel"
    assert {path.name for path in external.iterdir()} == {sentinel.name}
