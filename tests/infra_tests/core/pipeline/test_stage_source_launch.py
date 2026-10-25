"""Real fresh stage launches preserve exits and refuse missing custody receipts."""

from __future__ import annotations

import os
import py_compile
import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.core.pipeline.outcomes import RunResult, StageStatus
from infrastructure.core.pipeline.stage_launch import launch_python_stage
from infrastructure.core.pipeline.skip_receipts import validate_skip_receipt
from tests.infra_tests.core.test_execution_contract import _executor
from tests.infra_tests.core.test_bounded_run_guardian import _run_copy

pytestmark = pytest.mark.timeout(90)


def test_fresh_worker_uses_shared_protocol_without_importing_launch_controller() -> None:
    root = Path(launch_python_stage.__code__.co_filename).absolute().parents[3]
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            "-c",
            "import sys;sys.path.insert(0,sys.argv[1]);"
            "from infrastructure.core.pipeline import stage_worker;"
            "assert 'infrastructure.core.pipeline.stage_launch' not in sys.modules;"
            "from infrastructure.core.pipeline import stage_launch;"
            "assert stage_worker.SCHEMA == stage_launch.SCHEMA == 'template-python-stage/3';"
            "assert stage_worker.ANALYSIS_SCHEMA == stage_launch.ANALYSIS_SCHEMA == 'template-python-analysis/4';"
            "print('actual-worker-controller-protocol-agrees')",
            str(root),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "actual-worker-controller-protocol-agrees"


def test_actual_stage_ignores_timestamp_valid_poisoned_domain_cache(tmp_path: Path) -> None:
    executor = _executor(tmp_path, "from calculation import VALUE\nprint(VALUE)\n")
    source = executor.config.project_dir / "src/calculation.py"
    original = b"VALUE = 42\n" + b"#" * 100
    poisoned = b"raise SystemExit(77)\n#"
    source.write_bytes(poisoned + b"x" * (len(original) - len(poisoned)))
    assert len(source.read_bytes()) == len(original)
    cache = source.parent / "__pycache__" / f"{source.stem}.{sys.implementation.cache_tag}.pyc"
    py_compile.compile(
        str(source), cfile=str(cache), doraise=True, invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP
    )
    cached_stat = source.stat()
    source.write_bytes(original)
    os.utime(source, ns=(cached_stat.st_atime_ns, cached_stat.st_mtime_ns))
    ordinary = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            "-c",
            "import sys;sys.path.insert(0,sys.argv[1]);import calculation",
            str(source.parent),
        ],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert ordinary.returncode == 77
    result = executor._run_script("scripts/child.py")
    assert result.status is StageStatus.SUCCEEDED and result.child_exit_code == 0


def test_actual_stage_refuses_restored_repository_script_helper_code(tmp_path: Path) -> None:
    executor = _executor(
        tmp_path,
        "import os\nfrom pathlib import Path\n"
        "helper=Path(__file__).with_name('script_helper.py')\n"
        "original=helper.read_bytes()\nobserved=helper.stat()\n"
        'helper.write_text("from pathlib import Path\\nPath(__file__).parents[1]'
        ".joinpath('projects/demo/output/aba-ran').write_text('actual')\\nVALUE=17\\n\")\n"
        "import script_helper\nassert script_helper.VALUE == 17\n"
        "helper.write_bytes(original)\nos.utime(helper,ns=(observed.st_atime_ns,observed.st_mtime_ns))\n",
    )
    helper = executor.config.repo_root / "scripts/script_helper.py"
    helper.write_text("VALUE=17\n")
    original = helper.read_bytes()
    result = executor._run_script("scripts/child.py")
    assert (executor.config.project_dir / "output/aba-ran").read_text() == "actual"
    assert helper.read_bytes() == original
    assert result.status is StageStatus.BLOCKED and result.child_exit_code == 0
    assert "executed public module differs" in result.diagnostic


@pytest.mark.parametrize(
    "code,expected",
    [(0, StageStatus.SUCCEEDED), (2, StageStatus.FAILED), (7, StageStatus.FAILED), (75, StageStatus.BLOCKED)],
)
def test_actual_worker_preserves_declared_child_exit(tmp_path: Path, code: int, expected: StageStatus) -> None:
    executor = _executor(tmp_path, f"raise SystemExit({code})\n")
    result = executor._run_script("scripts/child.py", allow_skip_code=True)
    assert result.status is expected and result.child_exit_code == code


def test_zero_exit_without_worker_receipt_never_authorizes_success(tmp_path: Path) -> None:
    executor = _executor(tmp_path, "import os\nos._exit(0)\n")
    result = executor._run_script("scripts/child.py")
    assert result.status is StageStatus.FAILED and result.child_exit_code == 0
    assert "no valid completion receipt" in result.diagnostic


def test_source_edit_during_stage_blocks_and_preserves_original_zero(tmp_path: Path) -> None:
    executor = _executor(tmp_path, "from pathlib import Path\nPath(__file__).write_text('changed')\n")
    result = executor._run_script("scripts/child.py")
    assert result.status is StageStatus.BLOCKED and result.child_exit_code == 0
    assert "Consumed source" in result.diagnostic


@pytest.mark.parametrize(
    "code,state,aggregate",
    [
        (130, StageStatus.INTERRUPTED, 130),
        (124, StageStatus.TIMED_OUT, 124),
        (2, StageStatus.FAILED, 1),
        (7, StageStatus.FAILED, 1),
        (75, StageStatus.BLOCKED, 75),
    ],
)
def test_source_refusal_preserves_executed_exit_precedence(
    tmp_path: Path, code: int, state: StageStatus, aggregate: int
) -> None:
    executor = _executor(
        tmp_path,
        f"from pathlib import Path\nPath(__file__).write_text('changed')\nraise SystemExit({code})\n",
    )
    result = executor._run_script("scripts/child.py", allow_skip_code=True)
    assert result.status is state and result.child_exit_code == code
    assert not result.complete and not result.receipt_validated
    assert "Consumed source" in result.diagnostic
    assert RunResult((result.stage_key,), (result,)).exit_code == aggregate


@pytest.mark.parametrize("code,expected", [(130, "interrupted"), (124, "timed_out")])
@pytest.mark.timeout(150)
def test_late_supervisor_refusal_retains_original_exit_and_diagnostic(tmp_path: Path, code: int, expected: str) -> None:
    observed = _run_copy(
        tmp_path.resolve(),
        r"""
import json, os, time
from pathlib import Path
repo = Path(sys.path[0]).resolve()
project = repo / 'projects' / 'demo'
for name in ('src', 'scripts', 'tests', 'manuscript'):
    (project / name).mkdir(parents=True)
(repo / 'scripts').mkdir()
target = repo / 'infrastructure' / 'core' / '_bounded_kill.py'
script = repo / 'scripts' / 'child.py'
code = int(sys.argv[1])
script.write_text(
    'import atexit\nfrom pathlib import Path\n'
    + f'_target = Path({str(target)!r})\n'
    + "atexit.register(lambda: _target.write_bytes(_target.read_bytes() + b'\\n# late-source-change\\n'))\n"
    + f'raise SystemExit({code})\n'
)
from infrastructure.core.pipeline.fingerprints import source_fingerprint
from infrastructure.core.pipeline.stage_launch import launch_python_stage
from infrastructure.core.pipeline.outcomes import RunResult
outcome = launch_python_stage(
    repo=repo, project=project, argv=[sys.executable, str(script)], env=dict(os.environ),
    deadline=time.monotonic()+60, stage_key='late', run_id='late-custody-case',
    source_digest=source_fingerprint(repo, project), definition=None,
    skip_path=project/'output/skip.json', allow_skip=False,
)
print(json.dumps({'status':outcome.status, 'child':outcome.child_exit_code,
                  'aggregate':RunResult(('late',),(outcome,)).exit_code,
                  'diagnostic':outcome.diagnostic}))
""",
        str(code),
        observer_timeout=120,
    )
    assert observed["status"] == expected, observed
    assert observed["child"] == observed["aggregate"] == code
    assert "custody" in observed["diagnostic"].lower()


def test_skip_receipt_parent_link_cannot_admit_external_bytes(tmp_path: Path) -> None:
    external = tmp_path / "external"
    external.mkdir()
    sentinel = external / "receipt.json"
    sentinel.write_text("private sentinel")
    linked = tmp_path / "linked"
    linked.symlink_to(external, target_is_directory=True)
    assert validate_skip_receipt(linked / sentinel.name, env={}) is None
    assert sentinel.read_text() == "private sentinel"


@pytest.mark.parametrize("cwd_kind", ["string", "nested", "external", "traversal"])
def test_python_stage_refuses_unadmitted_working_directory_before_launch(tmp_path: Path, cwd_kind: str) -> None:
    repo = tmp_path / "repo"
    project = repo / "projects" / "demo"
    rejected = {
        "string": str(project),
        "nested": project / "src",
        "external": tmp_path / "external",
        "traversal": project / ".." / "demo",
    }[cwd_kind]
    with pytest.raises(ValueError, match="working directory"):
        launch_python_stage(
            repo=repo,
            project=project,
            argv=[sys.executable, "unexecuted.py"],
            env={},
            deadline=0,
            stage_key="cwd-admission",
            run_id="unexecuted",
            source_digest="",
            definition=None,
            skip_path=project / "output" / "skip.json",
            allow_skip=False,
            cwd=rejected,
        )
    assert not repo.exists()
