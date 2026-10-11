"""Ordinary filesystem controls for held lifecycle logging admission."""

from pathlib import Path

import pytest

from infrastructure.core.files.secure_write import append_text_confined
from infrastructure.orchestration._stage_log_links import admitted_lifecycle_log_root
from infrastructure.orchestration.stage_logger import setup_stage_log
from infrastructure.project.linking import sync_private_project_links


def _snapshot(directory: Path) -> dict[str, bytes | None]:
    return {
        path.relative_to(directory).as_posix(): path.read_bytes() if path.is_file() else None
        for path in directory.rglob("*")
    }


@pytest.mark.parametrize("lifecycle", ["active", "working", "ongoing", "archive", "working/_category"])
def test_managed_two_hop_lifecycle_links_preserve_append_and_permissions(tmp_path: Path, lifecycle: str) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    sidecar = tmp_path / "private"
    canonical = tmp_path / "self-versioned"
    (canonical / "src").mkdir(parents=True)
    (canonical / "sentinel").write_bytes(b"authored source\n")
    lifecycle_entry = sidecar / lifecycle / "demo"
    lifecycle_entry.parent.mkdir(parents=True)
    lifecycle_entry.symlink_to(canonical, target_is_directory=True)
    sync_private_project_links(repository, sidecar)
    lexical = repository / "projects" / lifecycle / "demo"
    assert lexical.readlink() == lifecycle_entry
    log = setup_stage_log(repository, f"{lifecycle}/demo", "First")
    first = log.read_bytes()
    setup_stage_log(repository, f"{lifecycle}/demo", "Second")
    assert log.read_bytes().startswith(first)
    assert "Starting: Second" in log.read_text()
    assert (canonical / "sentinel").read_bytes() == b"authored source\n"
    assert (canonical / "output/logs/pipeline.log").stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize("hop", ["mirror", "lifecycle"])
def test_relative_leaf_targets_are_refused_without_target_writes(tmp_path: Path, hop: str) -> None:
    repository = tmp_path / "repo"
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    (canonical / "sentinel").write_bytes(b"preserved\n")
    lexical = repository / "projects/working/demo"
    lexical.parent.mkdir(parents=True)
    if hop == "mirror":
        lexical.symlink_to("../../../canonical")
    else:
        lifecycle_entry = tmp_path / "private/working/demo"
        lifecycle_entry.parent.mkdir(parents=True)
        lifecycle_entry.symlink_to("../../canonical")
        lexical.symlink_to(lifecycle_entry)
    before = _snapshot(canonical)
    with pytest.raises(ValueError, match="absolute targets"):
        setup_stage_log(repository, "working/demo", "Refused")
    assert _snapshot(canonical) == before


def test_absolute_parent_traversal_target_is_refused_before_writes(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    (canonical / "sentinel").write_bytes(b"preserved\n")
    lexical = repository / "projects/working/demo"
    lexical.parent.mkdir(parents=True)
    lexical.symlink_to(canonical / ".." / canonical.name)
    before = _snapshot(canonical)
    with pytest.raises(ValueError, match="parent traversal"):
        setup_stage_log(repository, "working/demo", "Refused")
    assert _snapshot(canonical) == before


@pytest.mark.parametrize("component", ["mirror_parent", "target_parent"])
def test_lifecycle_target_ancestor_links_are_refused_without_external_writes(tmp_path: Path, component: str) -> None:
    repository = tmp_path / "repo"
    canonical = tmp_path / "external/demo"
    canonical.mkdir(parents=True)
    (canonical / "sentinel").write_bytes(b"preserved\n")
    lexical = repository / "projects/working/demo"
    if component == "mirror_parent":
        lexical.parent.parent.mkdir(parents=True)
        links = tmp_path / "links"
        links.mkdir()
        (links / "demo").symlink_to(canonical)
        lexical.parent.symlink_to(links)
    else:
        lexical.parent.mkdir(parents=True)
        alias = tmp_path / "alias"
        alias.symlink_to(canonical.parent)
        lexical.symlink_to(alias / "demo")
    before = _snapshot(canonical)
    with pytest.raises(ValueError, match="ancestor"):
        setup_stage_log(repository, "working/demo", "Refused")
    assert _snapshot(canonical) == before


def test_lifecycle_leaf_cycle_is_bounded_without_output_creation(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    lexical = repository / "projects/working/demo"
    lexical.parent.mkdir(parents=True)
    other = tmp_path / "other"
    lexical.symlink_to(other)
    other.symlink_to(lexical)
    with pytest.raises(ValueError, match="cycle"):
        setup_stage_log(repository, "working/demo", "Refused")
    assert not (repository / "output").exists()
    assert not (lexical.parent / "output").exists()


@pytest.mark.parametrize("links", [32, 33])
def test_lifecycle_hop_limit_has_exact_positive_and_refusal_boundary(tmp_path: Path, links: int) -> None:
    repository = tmp_path / "repo"
    lexical = repository / "projects/working/demo"
    lexical.parent.mkdir(parents=True)
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    (canonical / "sentinel").write_bytes(b"preserved\n")
    hops = [lexical, *(tmp_path / f"link-{number}" for number in range(links - 1))]
    for path, target in zip(hops, [*hops[1:], canonical], strict=True):
        path.symlink_to(target)
    if links == 32:
        setup_stage_log(repository, "working/demo", "Admitted")
        assert "Starting: Admitted" in (canonical / "output/logs/pipeline.log").read_text()
    else:
        before = _snapshot(canonical)
        with pytest.raises(ValueError, match="hop limit"):
            setup_stage_log(repository, "working/demo", "Refused")
        assert _snapshot(canonical) == before


@pytest.mark.parametrize("kind", ["missing", "regular"])
def test_lifecycle_final_target_requires_existing_directory(tmp_path: Path, kind: str) -> None:
    repository = tmp_path / "repo"
    lexical = repository / "projects/working/demo"
    lexical.parent.mkdir(parents=True)
    target = tmp_path / "target"
    if kind == "regular":
        target.write_bytes(b"preserved\n")
    lexical.symlink_to(target)
    with pytest.raises((ValueError, FileNotFoundError)):
        setup_stage_log(repository, "working/demo", "Refused")
    assert not (repository / "output").exists()
    if kind == "regular":
        assert target.read_bytes() == b"preserved\n"
    else:
        assert not target.exists()


def test_admitted_final_directory_replacement_refuses_before_output_mkdir(tmp_path: Path) -> None:
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    (canonical / "sentinel").write_bytes(b"original\n")
    lexical = tmp_path / "mirror"
    lexical.symlink_to(canonical)
    retired = tmp_path / "retired"
    with pytest.raises(ValueError, match="root changed after admission"):
        with admitted_lifecycle_log_root(lexical) as (root, identity):
            canonical.rename(retired)
            canonical.mkdir()
            (canonical / "sentinel").write_bytes(b"replacement\n")
            append_text_confined(root, root / "output/logs/pipeline.log", "Refused", expected_root_identity=identity)
    assert _snapshot(canonical) == {"sentinel": b"replacement\n"}
    assert _snapshot(retired) == {"sentinel": b"original\n"}
