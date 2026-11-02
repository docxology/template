"""Real locked selection and filesystem DATA controls, without network grants."""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

import pytest
import yaml
from packaging.tags import sys_tags
from packaging.utils import parse_wheel_filename

from infrastructure.project.pdfium_fixture_preparation import (
    LIMIT,
    WheelFixture,
    admit_fixture_scratch,
    require_bounded_curl,
    select_pdfium_wheel,
    verify_download,
)

ROOT = Path(__file__).resolve().parents[3]
NAME = "pypdfium2-0.0.0-py3-none-any.whl"
BODY = b"Owned fixture selection DATA, never installed or imported.\n"


def _lock(*, url: str | None = None, digest: str | None = None, size: int = len(BODY)) -> bytes:
    return (
        '[[package]]\nname = "pypdfium2"\nversion = "0.0.0"\n'
        f'wheels = [{{url = "{url or "https://files.pythonhosted.org/packages/" + NAME}", '
        f'hash = "{digest or "sha256:" + hashlib.sha256(BODY).hexdigest()}", size = {size}}}]\n'
    ).encode()


def test_actual_lock_selects_a_current_platform_wheel() -> None:
    selected = select_pdfium_wheel((ROOT / "uv.lock").read_bytes())
    name, _, _, tags = parse_wheel_filename(selected.filename)
    assert name == "pypdfium2"
    assert set(sys_tags()) & tags
    assert selected.url.endswith("/" + selected.filename)
    assert len(selected.sha256) == 64


@pytest.mark.parametrize(
    "url",
    [
        "http://files.pythonhosted.org/packages/" + NAME,
        "https://other.invalid/packages/" + NAME,
        "https://user:secret@files.pythonhosted.org/packages/" + NAME,
        "https://files.pythonhosted.org/packages/" + NAME + "?token=private",
        "https://files.pythonhosted.org/packages/" + NAME + "#fragment",
        "https://files.pythonhosted.org/packages/pypdfium2-1.0.0-py3-none-any.whl",
        "https://files.pythonhosted.org/packages/{first,second}/" + NAME,
        "https://files.pythonhosted.org/packages/[1-9]/" + NAME,
        "https://files.pythonhosted.org/packages/../" + NAME,
        "https://files.pythonhosted.org/packages/%7Bfirst,second%7D/" + NAME,
    ],
)
def test_refuse_noncanonical_public_wheel_locator(url: str) -> None:
    with pytest.raises(ValueError):
        select_pdfium_wheel(_lock(url=url))


@pytest.mark.parametrize("fault", ["missing", "duplicate", "hash", "empty", "oversize", "incompatible"])
def test_refuse_incomplete_or_ambiguous_lock(fault: str) -> None:
    lock = _lock()
    if fault == "missing":
        lock = lock.replace(b'pypdfium2"', b'unrelated"', 1)
    elif fault == "duplicate":
        lock += lock
    elif fault == "hash":
        lock = _lock(digest="sha256:bad")
    elif fault == "empty":
        lock = _lock(size=0)
    elif fault == "oversize":
        lock = _lock(size=64 * 1024 * 1024 + 1)
    else:
        lock = lock.replace(b"py3-none-any", b"cp20-cp20-unsupported_platform")
    with pytest.raises(ValueError):
        select_pdfium_wheel(lock)


@pytest.mark.parametrize("fault", ["none", "bytes", "long", "short", "alias", "name"])
def test_verify_exact_real_file(tmp_path: Path, fault: str) -> None:
    directory = tmp_path.resolve()
    selected = select_pdfium_wheel(_lock())
    assert selected == WheelFixture(selected.url, NAME, hashlib.sha256(BODY).hexdigest(), len(BODY))
    target = directory / NAME
    target.write_bytes(BODY)
    if fault == "bytes":
        target.write_bytes(b"X" + BODY[1:])
    elif fault == "long":
        target.write_bytes(BODY + b"X")
    elif fault == "short":
        target.write_bytes(BODY[:-1])
    elif fault == "alias":
        actual = directory / "actual"
        target.rename(actual)
        target.symlink_to(actual)
    elif fault == "name":
        replacement = directory / "different.whl"
        target.rename(replacement)
        target = replacement
    if fault == "none":
        verify_download(target, selected)
    else:
        with pytest.raises(ValueError):
            verify_download(target, selected)


@pytest.mark.parametrize("body", [b"curl 8.3.0 data", b"curl 7.88.1 data", b"not curl", b"x" * 4097])
def test_curl_unknown_length_bound_is_required(body: bytes) -> None:
    with pytest.raises(ValueError):
        require_bounded_curl(body)


@pytest.mark.parametrize("body", [b"curl 8.4.0 data", b"curl 8.7.1 data", b"curl 9.0.0 data"])
def test_curl_bounded_versions_are_eligible_data(body: bytes) -> None:
    require_bounded_curl(body)


@pytest.mark.parametrize("fault", ["none", "source", "runtime", "alias", "file", "missing"])
def test_scratch_is_physical_and_outside_source_runtime(tmp_path: Path, fault: str) -> None:
    directory = tmp_path.resolve()
    root = directory / "source"
    root.mkdir()
    scratch = directory / "scratch"
    scratch.mkdir()
    if fault == "source":
        scratch = root
    elif fault == "runtime":
        scratch = Path(sys.prefix).resolve(strict=True)
    elif fault == "alias":
        alias = directory / "alias"
        alias.symlink_to(scratch, target_is_directory=True)
        scratch = alias
    elif fault == "file":
        scratch = directory / "file"
        scratch.write_bytes(b"Owned non-directory DATA")
    elif fault == "missing":
        scratch = directory / "missing"
    if fault == "none":
        assert admit_fixture_scratch(root, scratch) == scratch
    else:
        with pytest.raises((ValueError, FileNotFoundError)):
            admit_fixture_scratch(root, scratch)
    assert not tuple(root.iterdir())


@pytest.mark.parametrize("fault", ["missing", "directory", "parent-alias", "fifo"])
def test_nonregular_or_aliased_wheel_never_opens_stream(tmp_path: Path, fault: str) -> None:
    directory = tmp_path.resolve()
    selected = select_pdfium_wheel(_lock())
    target = directory / NAME
    if fault == "directory":
        target.mkdir()
    elif fault == "fifo":
        os.mkfifo(target)
    elif fault == "parent-alias":
        real = directory / "real"
        real.mkdir()
        (real / NAME).write_bytes(BODY)
        alias = directory / "alias"
        alias.symlink_to(real, target_is_directory=True)
        target = alias / NAME
    with pytest.raises((ValueError, FileNotFoundError)):
        verify_download(target, selected)


def test_locked_wheel_preference_and_duplicate_rows() -> None:
    actual = next(sys_tags())
    specific = f"https://files.pythonhosted.org/packages/pypdfium2-0.0.0-{actual}.whl"
    general = "https://files.pythonhosted.org/packages/" + NAME
    header = _lock().split(b"wheels = [", 1)[0]
    rows = [_lock(url=url).split(b"wheels = [", 1)[1].removesuffix(b"]\n") for url in (general, specific)]
    for sequence in (rows, rows[::-1]):
        selected = select_pdfium_wheel(header + b"wheels = [" + b", ".join(sequence) + b"]\n")
        assert selected.url == specific
    with pytest.raises(ValueError, match="ambiguous"):
        select_pdfium_wheel(header + b"wheels = [" + b", ".join([rows[1], rows[1]]) + b"]\n")


@pytest.mark.parametrize("fault", ["boolean", "negative", "lock-size", "distribution"])
def test_remaining_declared_bounds(fault: str) -> None:
    if fault == "boolean":
        lock = _lock().replace(f"size = {len(BODY)}".encode(), b"size = true")
    elif fault == "negative":
        lock = _lock(size=-1)
    elif fault == "lock-size":
        lock = b"x" * (LIMIT + 1)
    else:
        lock = _lock(url="https://files.pythonhosted.org/packages/unrelated-0.0.0-py3-none-any.whl")
    with pytest.raises(ValueError):
        select_pdfium_wheel(lock)


def test_hosted_fixture_precedes_execution_user_and_root_custody() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/platform-required-acceptance.yml").read_text())
    steps = workflow["jobs"]["root-original"]["steps"]
    sync = next(index for index, step in enumerate(steps) if step.get("name") == "Prepare selected locked environment")
    fixture = next(
        index
        for index, step in enumerate(steps)
        if step.get("name") == "Prepare exact Source-locked PDFium wheel fixture"
    )
    user = next(
        index for index, step in enumerate(steps) if step.get("uses") == "./.github/actions/setup-ci-execution-user"
    )
    original = next(
        index for index, step in enumerate(steps) if step.get("name") == "Original complete Root observation"
    )
    assert sync < fixture < user < original
    command = steps[fixture]["run"]
    assert "-m infrastructure.project.pdfium_fixture_preparation" in command
    assert "TEMPLATE_TEST_PDFIUM_WHEEL=$wheel" in command and "$GITHUB_ENV" in command


def test_hardening_infrastructure_prepares_source_wheel_fixture() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/hardening.yml").read_text())
    steps = workflow["jobs"]["test-infra"]["steps"]
    sync = next(
        index
        for index, step in enumerate(steps)
        if step.get("name") == "Sync dependencies (dev + optional test groups)"
    )
    fixture = next(
        index
        for index, step in enumerate(steps)
        if step.get("name") == "Prepare exact Source-locked PDFium wheel fixture"
    )
    execution = next(index for index, step in enumerate(steps) if step.get("name") == "Run infrastructure tests")
    assert sync < fixture < execution
    step = steps[fixture]
    assert step["shell"] == "bash" and "if" not in step and "continue-on-error" not in step
    command = step["run"]
    assert "set -euo pipefail" in command
    assert ".venv/bin/python -B -m infrastructure.project.pdfium_fixture_preparation" in command
    assert '--repo-root "$PWD" --temporary-root "$RUNNER_TEMP"' in command
    assert 'echo "TEMPLATE_TEST_PDFIUM_WHEEL=$wheel" >> "$GITHUB_ENV"' in command
    assert "pytest tests/infra_tests/" in steps[execution]["run"]
    assert "not external_fixture" not in steps[execution]["run"]
