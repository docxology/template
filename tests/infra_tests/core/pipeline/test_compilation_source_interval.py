"""Actual file mutation at compilation reads cannot bind policy to other bytes."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.infra_tests.core.test_bounded_run_guardian import _run_copy

pytestmark = pytest.mark.timeout(120)


def test_actual_plugin_compilation_preserves_clean_json_and_has_no_execution_side_effects(tmp_path: Path) -> None:
    result = _run_copy(
        tmp_path,
        r"""
import json
from pathlib import Path
from infrastructure.core.pipeline.plan import compile_execution_plan
from infrastructure.core.pipeline.types import PipelineConfig
repo = Path.cwd() / 'owned-repository'
project = repo / 'projects/template_test'
project.mkdir(parents=True)
(repo / 'scripts').mkdir()
(repo / 'scripts/child.py').write_text("from pathlib import Path\nPath('actual-stage-marker').write_text('ran')\n")
(project / 'pipeline.yaml').write_text('stages:\n- name: Child\n  key: child\n  script: scripts/child.py\n')
(project / 'pipeline_plugins.yaml').write_text(
    'plugins:\n- name: Plugin\n  key: plugin\n  script: scripts/child.py\n'
    '  depends_on: [Child]\n  contract:\n    output_artifacts: [output/plugin.txt]\n'
    '    definition_of_done: Plugin produces its admitted result\n    failure_code: PLUGIN_FAILED\n')
plan = compile_execution_plan(PipelineConfig('template_test', repo, clean=False))
assert not (repo / 'actual-stage-marker').exists()
assert not (project / 'output').exists()
print(json.dumps({'keys': plan.expected_stage_keys,
                  'dependencies': [stage.dependencies for stage in plan.stages],
                  'stage_executed': False}))
""",
        observer_timeout=90,
    )
    assert result == {"keys": ["child", "plugin"], "dependencies": [[], ["child"]], "stage_executed": False}


@pytest.mark.parametrize("restore_original", [False, True])
def test_real_plugin_mutation_inside_compile_refuses_plan(tmp_path: Path, restore_original: bool) -> None:
    result = _run_copy(
        tmp_path,
        r"""
import json, os
from pathlib import Path
from infrastructure.core.pipeline.plan import compile_execution_plan
from infrastructure.core.pipeline.types import PipelineConfig
repo = Path.cwd() / 'owned-repository'
project = repo / 'projects/template_test'
project.mkdir(parents=True)
(repo / 'scripts').mkdir()
(repo / 'scripts/child.py').write_text("from pathlib import Path\nPath('actual-stage-marker').write_text('ran')\n")
(project / 'pipeline.yaml').write_text('stages:\n- name: Child\n  key: child\n  script: scripts/child.py\n')
plugin = project / 'pipeline_plugins.yaml'
original = ('plugins:\n- name: Original plugin\n  key: original_plugin\n  script: scripts/child.py\n'
            '  depends_on: [Child]\n  contract:\n    output_artifacts: [output/plugin.txt]\n'
            '    definition_of_done: Plugin produces its admitted result\n    failure_code: PLUGIN_FAILED\n')
changed = original.replace('original_plugin', 'changed_plugin')
plugin.write_text(original)
restore = sys.argv[1] == 'true'
events = 0
mutating = False
def mutate_actual_file(event, args):
    global events, mutating
    if event != 'open' or mutating or not isinstance(args[0], (str, bytes, os.PathLike)):
        return
    if Path(os.fsdecode(args[0])).name != plugin.name:
        return
    events += 1
    if events == 2 or (restore and events == 3):
        mutating = True
        try:
            plugin.write_text(changed if events == 2 else original)
        finally:
            mutating = False
sys.addaudithook(mutate_actual_file)
refused = False
try:
    compile_execution_plan(PipelineConfig('template_test', repo, clean=False))
except ValueError as exc:
    refused = 'changed during compilation' in str(exc)
assert events >= 3 and refused
assert plugin.read_text() == (original if restore else changed)
assert not (repo / 'actual-stage-marker').exists()
print(json.dumps({'refused':refused, 'restored_original':restore, 'stage_executed':False}))
""",
        "true" if restore_original else "false",
        observer_timeout=90,
    )
    assert result == {"refused": True, "restored_original": restore_original, "stage_executed": False}
