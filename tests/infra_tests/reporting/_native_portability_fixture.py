"""Small honest native fixture inheriting the public template's scaffolding.

Only native conformance is tested. Publication ancestry metadata is copied from
its public template; this fixture does not establish scientific/domain/release
acceptance or publish a new release.
"""

from __future__ import annotations

import shutil
import tomllib
from pathlib import Path

import yaml


def create_native_fixture(source: Path, root: Path) -> None:
    root.mkdir()
    for lane in ("infrastructure", "scripts"):
        shutil.copytree(source / lane, root / lane, ignore=shutil.ignore_patterns("__pycache__"))
    for name in (
        "pyproject.toml",
        "uv.lock",
        ".python-version",
        ".gitignore",
        "README.md",
        "LICENSE",
        "CHANGELOG.md",
        "pipeline.yaml",
    ):
        path = source / name
        if path.is_file():
            shutil.copyfile(path, root / name)
    inherited = source / "projects/templates/template_code_project"
    project = root / "projects/templates/template_code_project"
    for lane in ("src", "tests", "scripts", "manuscript"):
        (project / lane).mkdir(parents=True)
    scaffold = (
        ".agents",
        ".gitignore",
        "AGENTS.md",
        "LICENSE",
        "README.md",
        "TODO.md",
        "domain_profile.yaml",
        "experiment_plan.yaml",
        "STANDALONE.md",
        ".zenodo.json",
        "CITATION.cff",
        "codemeta.json",
        "manuscript/config.yaml.example",
        "manuscript/preamble.md",
        "manuscript/references.bib",
    )
    for name in scaffold:
        selected, target = inherited / name, project / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if selected.is_dir():
            shutil.copytree(selected, target)
        else:
            shutil.copyfile(selected, target)
    (project / "src/__init__.py").write_text('"""Independent native portability fixture."""\n')
    (project / "src/model.py").write_text("def measure():\n    return 42\n")
    (project / "tests/conftest.py").write_text(
        'import sys\nfrom pathlib import Path\nsys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))\n'
    )
    (project / "tests/test_model.py").write_text(
        "from model import measure\ndef test_measure():\n    assert measure() == 42\n"
    )
    (project / "scripts/analyze.py").write_text(
        "from pathlib import Path\nimport sys\np=Path(__file__).resolve().parents[1]\n"
        'sys.path.insert(0,str(p/"src"))\nfrom model import measure\n'
        '(p/"output/data").mkdir(parents=True,exist_ok=True)\n'
        '(p/"output/data/measurement.txt").write_text(str(measure()))\n'
    )
    ancestor_version = tomllib.loads((inherited / "pyproject.toml").read_text())["project"]["version"]
    (project / "pyproject.toml").write_text(
        f'[project]\nname="portable-native-fixture"\nversion="{ancestor_version}"\nrequires-python=">=3.12"\n'
    )
    (project / "manuscript/01_intro.md").write_text(
        "# Portable Native Observation\n\nThis independent document records a measured value of forty two.\n"
    )
    (project / "manuscript/02_methods.md").write_text(
        "# Methods\n\nThe analysis evaluates a deterministic integer measurement with a verified value of forty two.\n"
    )
    origin = yaml.safe_load((inherited / "manuscript/config.yaml").read_text())
    config = {
        "paper": {"title": "Portable Native Observation", "version": "3.0.0", "date": "2026-10-06"},
        "authors": origin["authors"],
        "metadata": origin["metadata"],
        "publication": {**origin["publication"], "transmission_bookends": {"enabled": False}},
        "render": {"formats": {"pdf": True, "html": False, "slides": False, "docx": False, "epub": False}},
    }
    (project / "manuscript/config.yaml").write_text(yaml.safe_dump(config))

    (project / "AGENTS.md").write_text(
        "# Native fixture contract\n\nSource of truth is manuscript/config.yaml. "
        "Run the canonical pipeline with uv run Python. Do not claim scientific, domain or publication acceptance.\n"
    )
    (project / "README.md").write_text(
        "# Native portability fixture\n\nUse this template for independent native conformance controls. "
        "Configuration entry points are manuscript/config.yaml and manuscript/config.yaml.example. "
        "Fork instructions are in STANDALONE.md. Run via the template monorepo with "
        "uv run python scripts/pipeline/stage_01_test.py --project templates/template_code_project --project-only. "
        "Project tests exercise the model. Validate output through canonical Stage 04. "
        "Publication ancestry metadata is inherited; this fixture does not publish a new release.\n"
    )
    header = "| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |\n"
    separator = "| --- | --- | --- | --- | --- | --- | --- | --- |\n"
    (project / "TODO.md").write_text(
        "# Fixture backlog\n\nThis backlog contains future work only and is future-only.\n\n"
        + "\n".join(f"## {size} upcoming\n\n{header}{separator}" for size in ("Major", "Medium", "Minor"))
    )
