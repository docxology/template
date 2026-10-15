"""Actual bounded child execution and retained-code DATA controls; no mocks."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.project.acceptance_payload import (
    MAX_LOADER_BYTES,
    format_acceptance_payload_loader,
    validate_acceptance_payload,
    write_acceptance_payload,
)


def _payload(tmp_path: Path, body: bytes):
    source = tmp_path / "Source"
    source.mkdir()
    scratch = tmp_path / "scratch"
    scratch.mkdir(mode=0o700)
    outside = scratch / "outside"
    outside.mkdir(mode=0o700)
    path = outside / "payload.py"
    metadata = write_acceptance_payload(scratch, path, body, forbidden_roots=(source,))
    return path, metadata, outside


def _run(path: Path, metadata: dict, outside: Path) -> subprocess.CompletedProcess:
    prefix = outside / "fresh-bytecode"
    prefix.mkdir(exist_ok=True)
    command = (
        sys.executable,
        "-I",
        "-X",
        "pycache_prefix=" + str(prefix),
        "-c",
        format_acceptance_payload_loader(metadata),
        str(outside / "spec.json"),
        str(outside / "observation.json"),
    )
    assert len(command) == 8
    assert max(len(os.fsencode(arg)) for arg in command) <= MAX_LOADER_BYTES
    return subprocess.run(command, cwd=outside, capture_output=True, text=True, timeout=20)


def test_actual_large_payload_executes_with_bounded_argv_and_original_main_globals(tmp_path: Path) -> None:
    body = (
        b"#"
        + b"x" * 210_000
        + b"\n"
        + b"""
import json,pathlib,sys
assert sys._getframe().f_code.co_filename == '<string>'
assert __name__ == '__main__' and '__file__' not in globals()
assert sys.flags.isolated and sys.pycache_prefix
pathlib.Path(sys.argv[2]).write_text(json.dumps({'argc':len(sys.argv),'result':123}))
"""
    )
    path, metadata, outside = _payload(tmp_path, body)
    validate_acceptance_payload(body, metadata, expected_path=path)
    result = _run(path, metadata, outside)
    assert result.returncode == 0, result.stderr
    assert json.loads((outside / "observation.json").read_text()) == {"argc": 3, "result": 123}


@pytest.mark.parametrize("mutation", ["body", "aba", "alias", "mode", "link", "hash"])
def test_actual_loader_refuses_physical_and_hash_changes_before_payload_execution(
    tmp_path: Path, mutation: str
) -> None:
    body = b"import pathlib,sys\npathlib.Path(sys.argv[2]).write_text('must not execute')\n"
    path, metadata, outside = _payload(tmp_path, body)
    if mutation == "hash":
        metadata = {**metadata, "sha256": "0" * 64}
    else:
        path.chmod(0o600)
        if mutation == "body":
            path.write_bytes(body + b"#different\n")
        elif mutation == "aba":
            path.write_bytes(body + b"#transient\n")
            path.write_bytes(body)
        elif mutation == "alias":
            other = outside / "other.py"
            other.write_bytes(body)
            path.unlink()
            path.symlink_to(other)
        elif mutation == "link":
            os.link(path, outside / "second-name.py")
        if mutation != "mode" and not path.is_symlink():
            path.chmod(0o400)
    result = _run(path, metadata, outside)
    assert result.returncode != 0 and "acceptance payload" in result.stderr
    assert not (outside / "observation.json").exists()


@pytest.mark.parametrize("outcome", ["normal", "zero", "nonzero", "interrupt"])
def test_closing_physical_guard_runs_on_zero_and_preserves_actual_negative_exit(tmp_path: Path, outcome: str) -> None:
    suffix = {
        "normal": "",
        "zero": "raise SystemExit(0)",
        "nonzero": "raise SystemExit(7)",
        "interrupt": "raise KeyboardInterrupt",
    }[outcome]
    body = (
        "import pathlib,sys\np=pathlib.Path(sys.argv[1]).with_name('payload.py')\np.chmod(0o600)\np.write_bytes(p.read_bytes()+b'#actual changed payload\\n')\n"
        + suffix
    ).encode()
    path, metadata, outside = _payload(tmp_path, body)
    result = _run(path, metadata, outside)
    if outcome in {"normal", "zero"}:
        assert result.returncode != 0 and "physical identity changed" in result.stderr
    elif outcome == "nonzero":
        assert result.returncode == 7
    else:
        assert result.returncode in {-2, 130} and "KeyboardInterrupt" in result.stderr


@pytest.mark.parametrize("change", ["hash", "path", "body", "size", "extra"])
def test_independent_payload_admission_requires_exact_regenerated_body_and_fixed_path(
    tmp_path: Path, change: str
) -> None:
    body = b"VALUE=1\n"
    path, metadata, _ = _payload(tmp_path, body)
    expected_body, expected_path = body, path
    if change == "hash":
        metadata = {**metadata, "sha256": "0" * 64}
    elif change == "path":
        expected_path = path.with_name("foreign.py")
    elif change == "body":
        expected_body = b"VALUE=2\n"
    elif change == "size":
        metadata = {**metadata, "identity": {**metadata["identity"], "size": len(body) + 1}}
    else:
        metadata = {**metadata, "unchecked": True}
    with pytest.raises(ValueError):
        validate_acceptance_payload(expected_body, metadata, expected_path=expected_path)


def test_payload_writer_refuses_source_placement_and_existing_files(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    path = source / "payload.py"
    with pytest.raises(ValueError, match="outside-Source"):
        write_acceptance_payload(tmp_path, path, b"VALUE=1\n", forbidden_roots=(source,))
    path.write_bytes(b"retained foreign file\n")
    with pytest.raises(ValueError, match="fresh owned"):
        write_acceptance_payload(tmp_path, path, b"VALUE=1\n", forbidden_roots=())
    assert path.read_bytes() == b"retained foreign file\n"
