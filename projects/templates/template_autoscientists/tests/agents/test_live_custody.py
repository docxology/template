"""Real custody observations, without replacing implementation dependencies."""

from __future__ import annotations

import copy
import json
import shutil
import sys
from pathlib import Path

import pytest

from infrastructure.core import implementation_custody as platform_custody
from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy
from template_autoscientists.agents.live_custody import (
    environment_identity,
    implementation_custody,
    platform_sources,
    verify_custody,
)


@pytest.fixture(scope="module")
def expected_observation():
    return implementation_custody(), platform_sources(), environment_identity()


def test_each_custody_boundary_captures_platform_and_runtime_exactly_once(expected_observation) -> None:
    """Observe actual function calls; no capture/runtime implementation is replaced."""
    implementation, sources, environment = expected_observation
    counts = {"platform": 0, "runtime": 0}
    code_labels = {
        platform_custody.capture_implementation_custody.__code__: "platform",
        platform_custody.runtime_identity.__code__: "runtime",
    }
    original_profile = sys.getprofile()

    def observe(frame, event, argument):
        if event == "call" and frame.f_code in code_labels:
            counts[code_labels[frame.f_code]] += 1
        if original_profile is not None:
            original_profile(frame, event, argument)

    try:
        sys.setprofile(observe)
        verify_custody(sources, environment, implementation)
        verify_custody(sources, environment)
    finally:
        sys.setprofile(original_profile)
    assert counts == {"platform": 2, "runtime": 2}


@pytest.mark.parametrize("plane", ["schema", "files", "distribution", "runtime"])
def test_changed_implementation_plane_is_rejected(expected_observation, plane) -> None:
    implementation, sources, environment = expected_observation
    changed = copy.deepcopy(implementation)
    if plane == "schema":
        changed["schema_version"] = "unrecognized"
    elif plane == "files":
        changed["files"].pop("infrastructure/core/subprocess_policy.py")
    elif plane == "distribution":
        changed["distribution"] = {"name": "forged"}
    else:
        changed["runtime_environment"]["python_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="implementation, distribution, bytecode binding or runtime changed"):
        verify_custody(sources, environment, changed)


def test_unselected_owned_bytecode_prefix_is_rejected(tmp_path, expected_observation) -> None:
    implementation, sources, environment = expected_observation
    prefix = tmp_path.resolve() / "unselected-cache"
    prefix.mkdir()
    with pytest.raises(ValueError, match="worker did not use its launcher's fresh bytecode prefix"):
        verify_custody(sources, environment, implementation, fresh_prefix=prefix)


def test_audited_worker_rechecks_owned_source_after_earlier_success(tmp_path, expected_observation) -> None:
    """A fresh worker normalizes launcher evidence and observes a later addition."""
    implementation, sources, environment = expected_observation
    project = Path(__file__).resolve().parents[2]
    root = Path(platform_custody.__file__).resolve().parents[2]
    source = tmp_path.resolve() / "src"
    package = source / "template_autoscientists"
    shutil.copytree(project / "src/template_autoscientists", package, ignore=shutil.ignore_patterns("__pycache__"))
    prefix = tmp_path.resolve() / "cache"
    prefix.mkdir()
    invocation = tmp_path.resolve() / "custody.json"
    invocation.write_text(
        json.dumps(
            {
                "implementation": dict(implementation, bytecode_binding="loaded-baseline"),
                "sources": sources,
                "environment": environment,
            }
        ),
        encoding="utf-8",
    )
    bootstrap = platform_custody.bytecode_audit_bootstrap((package, root / "infrastructure", root / "scripts"), prefix)
    worker = "\n".join(
        (
            "import json,sys",
            "from pathlib import Path",
            "sys.path[:0]=[sys.argv.pop(1),sys.argv.pop(1)]",
            "from template_autoscientists.agents.live_custody import verify_custody",
            "request=json.loads(Path(sys.argv[1]).read_text())",
            "prefix=Path(sys.pycache_prefix)",
            "verify_custody(request['sources'],request['environment'],request['implementation'],fresh_prefix=prefix)",
            "(Path(sys.argv[2])/'added_after_verification.py').write_text('value = 1\\n')",
            "try:",
            "    verify_custody(request['sources'],request['environment'],request['implementation'],fresh_prefix=prefix)",
            "except ValueError as error:",
            "    assert 'source or runtime environment changed' in str(error), str(error)",
            "    print('fresh worker rejected source added after its first successful boundary')",
            "else:",
            "    raise AssertionError('later source change was accepted')",
        )
    )
    result = run_with_policy(
        [
            sys.executable,
            "-I",
            "-X",
            f"pycache_prefix={prefix}",
            "-c",
            bootstrap + worker,
            str(source),
            str(root),
            str(invocation),
            str(package),
        ],
        cwd=tmp_path.resolve(),
        env=None,
        policy=SubprocessPolicy(
            policy_id="autoscientists-custody-boundary-control",
            source_path="projects/templates/template_autoscientists/tests/agents/test_live_custody.py",
            timeout_seconds=90,
            credential_free=True,
            capture_output=True,
        ),
    )
    assert not result.timed_out
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "fresh worker rejected source added after its first successful boundary"
    assert (package / "added_after_verification.py").is_file()
    assert not (project / "src/template_autoscientists/added_after_verification.py").exists()
