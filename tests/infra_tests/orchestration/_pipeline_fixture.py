"""Small real child-process DAGs for orchestration contract tests."""

from pathlib import Path

import yaml


def scaffold_pipeline(root: Path, names: tuple[str, ...] = ("demo",), *, infra_exit: int = 0) -> Path:
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
    path = root / "infrastructure" / "core" / "pipeline" / "pipeline.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump({"stages": stages, "telemetry": {"enabled": False}}), encoding="utf-8")
    return root
