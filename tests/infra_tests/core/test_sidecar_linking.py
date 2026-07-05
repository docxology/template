from pathlib import Path

from infrastructure.core.sidecar_linking import SidecarLinkConfig, sync_private_links
from infrastructure.project.linking import PROJECT_LINK_CONFIG


def test_sync_private_links_creates_managed_symlink(tmp_path: Path) -> None:
    repo = tmp_path / "template"
    (repo / "projects").mkdir(parents=True)
    private = tmp_path / "projects"
    (private / "working" / "demo").mkdir(parents=True)
    result = sync_private_links(repo, PROJECT_LINK_CONFIG, private)
    link = repo / "projects" / "working" / "demo"
    assert link.is_symlink()
    assert link.resolve() == (private / "working" / "demo").resolve()
    assert any("projects/working/demo" in name for name in result.created)


def test_sync_private_links_no_private_root_is_noop(tmp_path: Path) -> None:
    repo = tmp_path / "template"
    (repo / "projects").mkdir(parents=True)
    config = SidecarLinkConfig(
        protected_names=frozenset(),
        lifecycle_subdirs=("working",),
        required_private_root_subdirs=("working",),
        lifecycle_link_dirs={"working": "demo/working"},
        config_filename=".demo_root",
        env_var="DEMO_ROOT",
        skip_env_var="DEMO_SKIP",
    )
    result = sync_private_links(repo, config, private_root=None)
    assert result.private_root is None
    assert not result.changed
