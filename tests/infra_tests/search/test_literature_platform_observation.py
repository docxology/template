"""One real current observation per boundary, with unchanged custody refusals."""

from __future__ import annotations

import copy
import json
import os
import shutil
import sys
from pathlib import Path

import pytest

from infrastructure.core import implementation_custody as custody_module
from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy
from infrastructure.search.literature import live_contract

pytestmark = pytest.mark.timeout(180)


def _projection(observed: dict) -> dict[str, str]:
    """Independent reconstruction of the complete original manifest payload."""
    result = {"platform/" + key: value for key, value in observed["files"].items()}
    distribution = observed["distribution"]
    if distribution is not None:
        result["platform/distribution/METADATA"] = distribution["metadata_sha256"]
        result["platform/distribution/RECORD"] = distribution["record_sha256"]
    return result


def test_each_verification_boundary_captures_once_and_preserves_the_full_original_oracle():
    prefix = Path(sys.pycache_prefix) if sys.pycache_prefix is not None else None
    admitted = live_contract.implementation_custody()
    manifest = _projection(admitted)
    environment = admitted["runtime_environment"]
    assert live_contract.platform_manifest() == manifest
    assert live_contract.environment_identity() == environment
    # Keep the unchanged shared verifier as the actual full-record oracle.
    custody_module.verify_implementation_custody(admitted, fresh_pycache_prefix=prefix)
    actual_code = custody_module.capture_implementation_custody.__code__
    prior = sys.getprofile()
    calls = 0

    def observe(frame, event, argument):
        nonlocal calls
        if event == "call" and frame.f_code is actual_code:
            calls += 1
        if prior is not None:
            prior(frame, event, argument)

    try:
        sys.setprofile(observe)
        assert live_contract.verify_platform(manifest, environment, admitted) is None
        assert calls == 1
        assert live_contract.verify_platform(manifest, environment, admitted) is None
        assert calls == 2  # The second boundary must obtain its own new observation.
        assert live_contract.verify_platform(manifest, environment) is None
        assert calls == 3
    finally:
        sys.setprofile(prior)
    assert sys.getprofile() is prior
    assert live_contract.implementation_custody() == admitted


@pytest.mark.parametrize("plane", ["schema_version", "binding_kind", "files", "distribution", "runtime_environment"])
def test_full_contract_plane_refusals_match_the_original_shared_verifier(plane):
    prefix = Path(sys.pycache_prefix) if sys.pycache_prefix is not None else None
    admitted = live_contract.implementation_custody()
    wrong = copy.deepcopy(admitted)
    wrong[plane] = {"different": True} if isinstance(wrong[plane], dict) or wrong[plane] is None else "different"
    with pytest.raises(ValueError) as original:
        custody_module.verify_implementation_custody(wrong, fresh_pycache_prefix=prefix)
    with pytest.raises(ValueError) as actual:
        live_contract.verify_platform(_projection(admitted), admitted["runtime_environment"], wrong)
    assert str(actual.value) == str(original.value)


def test_bytecode_label_normalization_remains_exactly_the_shared_verifier_contract():
    prefix = Path(sys.pycache_prefix) if sys.pycache_prefix is not None else None
    admitted = live_contract.implementation_custody()
    wrong = dict(admitted, bytecode_binding="different-controller-label")
    if prefix is None:
        with pytest.raises(ValueError) as original:
            custody_module.verify_implementation_custody(wrong)
        with pytest.raises(ValueError) as actual:
            live_contract.verify_platform(_projection(admitted), admitted["runtime_environment"], wrong)
        assert str(actual.value) == str(original.value)
    else:
        assert custody_module.verify_implementation_custody(wrong, fresh_pycache_prefix=prefix) is None
        assert live_contract.verify_platform(_projection(admitted), admitted["runtime_environment"], wrong) is None


def test_actual_wrong_launcher_prefix_is_refused_by_both_full_contract_verifiers(tmp_path):
    admitted = live_contract.implementation_custody()
    wrong = tmp_path.resolve() / "not-the-launcher-prefix"
    wrong.mkdir()
    with pytest.raises(ValueError) as original:
        custody_module.verify_implementation_custody(admitted, fresh_pycache_prefix=wrong)
    with pytest.raises(ValueError) as actual:
        live_contract.verify_platform(
            _projection(admitted), admitted["runtime_environment"], admitted, fresh_prefix=wrong
        )
    assert str(actual.value) == str(original.value)


@pytest.mark.parametrize("fault", ["source", "lock", "metadata", "bytecode"])
def test_fresh_verification_refuses_real_owned_provider_mutation_after_success(tmp_path, fault):
    provider = Path(__file__).resolve().parents[3]
    assert all((provider / name).is_file() for name in ("pyproject.toml", "uv.lock", ".python-version"))
    copied = tmp_path.resolve() / "actual-provider-copy"
    # This copies the genuine canonical Root test source, not installed-wheel proof.
    # Preserve every real source byte; only bytecode/control artifacts are omitted.
    for directory in ("infrastructure", "scripts"):
        shutil.copytree(provider / directory, copied / directory, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name in ("pyproject.toml", "uv.lock", ".python-version"):
        shutil.copyfile(provider / name, copied / name)
    cache = tmp_path.resolve() / "fresh-owned-cache"
    cache.mkdir()
    code = custody_module.bytecode_audit_bootstrap((copied / "infrastructure", copied / "scripts"), cache)
    code += """
import json
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from infrastructure.search.literature import live_contract
from infrastructure.core.implementation_custody import verify_implementation_custody
observed = live_contract.implementation_custody()
assert observed['binding_kind'] == 'source-checkout'
assert observed['bytecode_binding'] == 'fresh-owned-prefix'
manifest = live_contract.platform_manifest()
environment = live_contract.environment_identity()
verify_implementation_custody(observed, fresh_pycache_prefix=Path(sys.pycache_prefix))
live_contract.verify_platform(manifest, environment, observed)
print('actual-admitted-provider', flush=True)
root = Path(sys.argv[1])
fault = sys.argv[2]
if fault == 'source':
    target = root / 'infrastructure/search/literature/live_contract.py'
    target.write_bytes(target.read_bytes() + b'\\n# owned source mutation\\n')
elif fault == 'lock':
    target = root / 'uv.lock'
    target.write_bytes(target.read_bytes() + b'\\n# owned lock mutation\\n')
elif fault == 'metadata':
    target = root / 'pyproject.toml'
    raw = target.read_text()
    assert 'name = "research-project-template"' in raw
    target.write_text(raw.replace('name = "research-project-template"', 'name = "owned-invalid-provider"'))
else:
    target = Path(live_contract.__cached__)
    assert target.is_relative_to(Path(sys.pycache_prefix))
    target.write_bytes(target.read_bytes() + b'owned bytecode mutation')
try:
    live_contract.verify_platform(manifest, environment, observed)
except ValueError as error:
    print(json.dumps({'fault': fault, 'refused': True, 'diagnostic': str(error)}))
else:
    raise AssertionError('a later boundary reused stale provider evidence')
"""
    result = run_with_policy(
        [sys.executable, "-I", "-X", f"pycache_prefix={cache}", "-c", code, str(copied), fault],
        cwd=tmp_path.resolve(),
        env=os.environ.copy(),
        policy=SubprocessPolicy(
            policy_id="literature-platform-observation-control",
            source_path="tests/infra_tests/search/test_literature_platform_observation.py",
            timeout_seconds=150,
            credential_free=True,
        ),
    )
    assert result.returncode == 0 and not result.timed_out, result.stderr
    lines = result.stdout.strip().splitlines()
    assert lines[0] == "actual-admitted-provider"
    record = json.loads(lines[1])
    assert record["fault"] == fault and record["refused"] is True and record["diagnostic"]
