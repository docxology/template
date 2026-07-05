from pathlib import Path

from infrastructure.core.lifecycle_discovery import LifecycleDiscoveryConfig, discover_program_entries


def test_discover_program_entries_finds_program_and_standalone(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    templates = repo / "projects" / "templates"
    project = templates / "demo"
    (project / "src").mkdir(parents=True)
    (project / "src" / "demo.py").write_text("VALUE = 1\n", encoding="utf-8")
    (project / "tests").mkdir()
    config = LifecycleDiscoveryConfig(non_rendered_subdirs=frozenset())

    top_level = discover_program_entries(repo / "projects", config)
    assert len(top_level) == 1
    assert top_level[0].name == "templates"
    assert top_level[0].kind == "program"

    nested = discover_program_entries(templates, config)
    assert len(nested) == 1
    assert nested[0].name == "demo"
    assert nested[0].path == project
    assert nested[0].kind == "standalone"
