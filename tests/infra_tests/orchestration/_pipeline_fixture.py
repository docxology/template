"""Small real child-process DAGs for orchestration contract tests."""

from pathlib import Path

import yaml


def scaffold_pipeline(
    root: Path, names: tuple[str, ...] = ("demo",), *, infra_exit: int = 0, canonical_gate: bool = True
) -> Path:
    """Scaffold an owned repository with recording stage children.

    By default the shared ``infra_tests`` stage uses the canonical lexical
    target ``scripts/pipeline/stage_01_test.py --infra-only`` as a thin adapter
    to the same recording child, so the once-only shared gate can actually run.
    With ``canonical_gate=False`` it is an ordinary project script, which
    multi-project execution must refuse as a shared gate.
    """
    for name in names:
        project = root / "projects" / name
        for directory in ("src", "tests", "manuscript", "output/data"):
            (project / directory).mkdir(parents=True, exist_ok=True)
        (project / "src" / "__init__.py").write_text("", encoding="utf-8")
        (project / "tests" / "test_source.py").write_text(
            "def test_source():\n    assert 2 + 2 == 4\n", encoding="utf-8"
        )
        (project / "manuscript" / "02_methods.md").write_text("# Methods\n\nA measured process.\n", encoding="utf-8")
    script = root / "scripts" / "stage.py"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(
        "import json, os, sys\nfrom pathlib import Path\n"
        "step = sys.argv[1]\nproject = sys.argv[sys.argv.index('--project') + 1]\n"
        "with Path('process_order.log').open('a') as stream: stream.write(project + ':' + step + '\\n')\n"
        f"if step == 'infra': sys.exit({infra_exit})\n"
        "if project.endswith('fail'): sys.exit(2)\n"
        "output = Path('projects') / project / 'output/data'\noutput.mkdir(parents=True, exist_ok=True)\n"
        "(output / (step + '.json')).write_text(json.dumps({'step': step, 'pid': os.getpid()}))\n",
        encoding="utf-8",
    )
    stages = []
    for name, key, step, tags in (
        ("Infrastructure Tests", "infra_tests", "infra", ["core"]),
        ("Project Analysis", "analysis", "analysis", ["core"]),
        ("Live Review", "llm_reviews", "live", ["llm", "live"]),
    ):
        stages.append(
            {
                "name": name,
                "key": key,
                "script": "scripts/stage.py",
                "args": [step],
                "tags": tags,
                "contract": {
                    "output_artifacts": ["projects/{project}/output/data/"],
                    "definition_of_done": "The child process completes and records its result.",
                    "failure_code": "CHILD_FAILED",
                },
            }
        )
    if canonical_gate:
        gate = root / "scripts" / "pipeline" / "stage_01_test.py"
        gate.parent.mkdir(parents=True, exist_ok=True)
        gate.write_text(
            "import sys\nfrom pathlib import Path\n"
            "assert '--infra-only' in sys.argv, sys.argv\n"
            "project = sys.argv[sys.argv.index('--project') + 1] if '--project' in sys.argv else 'root'\n"
            "with Path('process_order.log').open('a') as stream: stream.write(project + ':infra\\n')\n"
            f"sys.exit({infra_exit})\n",
            encoding="utf-8",
        )
        shared = next(stage for stage in stages if stage["key"] == "infra_tests")
        shared.update(script="scripts/pipeline/stage_01_test.py", args=["--infra-only"])
    path = root / "infrastructure" / "core" / "pipeline" / "pipeline.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump({"stages": stages, "telemetry": {"enabled": False}}), encoding="utf-8")
    return root
