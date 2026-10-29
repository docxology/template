"""Exact lock artifact and confined dependency-export controls."""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.project import locked_dependency_export as exporter

DIGEST = "sha256:" + "a" * 64
URL = "https://files.pythonhosted.org/packages/00/11/source/control_package-1.2.3.tar.gz"


def _lock(
    *, url: str = URL, digest: str = DIGEST, registry: str = "https://pypi.org/simple", wheels: bool = False
) -> bytes:
    wheel_table = (
        '\nwheels = [{ url = "https://files.pythonhosted.org/packages/control_package-1.2.3-py3-none-any.whl" }]\n'
        if wheels
        else ""
    )
    return (
        'version = 1\n[[package]]\nname = "control-package"\nversion = "1.2.3"\n'
        f'source = {{ registry = "{registry}" }}\nsdist = {{ url = "{url}", hash = "{digest}" }}\n' + wheel_table
    ).encode()


def _lock_with_wheels(*wheels: str) -> bytes:
    table = "\nwheels = [" + "".join(f'\n    {{ url = "{wheel}" }},' for wheel in wheels) + "\n]\n" if wheels else ""
    return (
        'version = 1\n[[package]]\nname = "control-package"\nversion = "1.2.3"\n'
        f'source = {{ registry = "https://pypi.org/simple" }}\nsdist = {{ url = "{URL}", hash = "{DIGEST}" }}' + table
    ).encode()


def _requirements(header: str = "control-package==1.2.3", digest: str = DIGEST) -> bytes:
    return f"{header} \\\n    --hash={digest}\n".encode()


def test_exact_artifact_keeps_marker_extras_hash_and_unrelated_wheel_bytes() -> None:
    unchanged = b"other-package==5.0 \\\n    --hash=sha256:" + b"b" * 64 + b"\n"
    original = _requirements('control_package[extra]==1.2.3 ; python_version < "3.15"') + unchanged
    normalized = exporter.normalize_locked_sdist_requirements(_lock(), original)
    assert normalized == (
        f'control_package[extra] @ {URL} ; python_version < "3.15" --hash={DIGEST}\n'.encode() + unchanged
    )
    assert exporter.normalize_locked_sdist_requirements(_lock(), normalized) == normalized


def test_locked_registry_wheel_requirement_is_not_redirected_to_sdist() -> None:
    original = _requirements()
    assert exporter.normalize_locked_sdist_requirements(_lock(wheels=True), original) == original


@pytest.mark.parametrize("header", ["control-package==1.2.2", "control-package>=1.2.3", "control-package==1.2.*"])
def test_different_or_unpinned_version_cannot_be_rebound(header: str) -> None:
    with pytest.raises(ValueError, match="version"):
        exporter.normalize_locked_sdist_requirements(_lock(), _requirements(header))


@pytest.mark.parametrize(
    "suffix", ["", " --hash=sha256:" + "b" * 64, " --hash=" + DIGEST, " --trusted-host=example.com"]
)
def test_missing_duplicate_extra_and_option_hash_tails_refused(suffix: str) -> None:
    original = f"control-package==1.2.3 --hash={DIGEST}{suffix}\n".encode() if suffix else b"control-package==1.2.3\n"
    with pytest.raises(ValueError, match="hash"):
        exporter.normalize_locked_sdist_requirements(_lock(), original)


def test_wrong_archive_hash_cannot_use_the_nominated_source() -> None:
    with pytest.raises(ValueError, match="hash"):
        exporter.normalize_locked_sdist_requirements(_lock(), _requirements(digest="sha256:" + "b" * 64))


@pytest.mark.parametrize(
    "url",
    [
        URL.replace("https:", "http:"),
        URL.replace("files.pythonhosted.org", "example.com"),
        URL.replace("files.pythonhosted.org", "user@files.pythonhosted.org"),
        URL.replace("files.pythonhosted.org", "files.pythonhosted.org:444"),
        URL.replace("/packages/", "/other/"),
        URL + "?candidate=alternate",
        URL + "#fragment",
        URL.replace("1.2.3", "1.2.2"),
    ],
)
def test_source_url_provider_credentials_identity_and_aliases_refused(url: str) -> None:
    with pytest.raises(ValueError):
        exporter.normalize_locked_sdist_requirements(_lock(url=url), _requirements())


def test_an_undeclared_registry_cannot_nominate_the_pypi_artifact() -> None:
    with pytest.raises(ValueError, match="public PyPI"):
        exporter.normalize_locked_sdist_requirements(_lock(registry="https://example.com/simple"), _requirements())


def test_duplicate_locked_identity_is_ambiguous() -> None:
    duplicate = _lock().split(b"[[package]]", 1)[1]
    with pytest.raises(ValueError, match="ambiguous"):
        exporter.normalize_locked_sdist_requirements(_lock() + b"[[package]]" + duplicate, _requirements())


def test_inconsistent_direct_artifact_cannot_be_rebound() -> None:
    with pytest.raises(ValueError, match="URL"):
        exporter.normalize_locked_sdist_requirements(_lock(), _requirements(f"control-package @ {URL}?alias=changed"))


def test_cli_normalization_uses_actual_confined_files_and_preserves_lock(tmp_path: Path) -> None:
    metadata = tmp_path / "metadata"
    metadata.mkdir()
    (metadata / "uv.lock").write_bytes(_lock())
    requirements = tmp_path / "requirements.txt"
    requirements.write_bytes(_requirements())
    assert exporter.main(["--metadata-root", str(metadata), "--requirements", str(requirements)]) == 0
    assert requirements.read_bytes() == f"control-package @ {URL} --hash={DIGEST}\n".encode()
    assert (metadata / "uv.lock").read_bytes() == _lock()


def test_symlinked_lock_and_output_refused_without_modifying_target(tmp_path: Path) -> None:
    actual = tmp_path / "actual.lock"
    actual.write_bytes(_lock())
    metadata = tmp_path / "metadata"
    metadata.mkdir()
    (metadata / "uv.lock").symlink_to(actual)
    requirements = tmp_path / "requirements.txt"
    requirements.write_bytes(_requirements())
    with pytest.raises((ValueError, OSError)):
        exporter.normalize_locked_dependency_export(metadata, requirements)
    assert requirements.read_bytes() == _requirements()
    (metadata / "uv.lock").unlink()
    (metadata / "uv.lock").write_bytes(_lock())
    linked = tmp_path / "linked.txt"
    linked.symlink_to(requirements)
    with pytest.raises((ValueError, OSError)):
        exporter.normalize_locked_dependency_export(metadata, linked)
    assert requirements.read_bytes() == _requirements()


def test_locked_wheel_for_another_minor_is_nominated_per_target() -> None:
    lock = _lock_with_wheels(
        "https://files.pythonhosted.org/packages/control_package-1.2.3-cp314-cp314-macosx_11_0_arm64.whl"
    )
    original = _requirements()
    assert exporter.normalize_locked_sdist_requirements(lock, original, minor="3.15") == (
        f"control-package @ {URL} --hash={DIGEST}\n".encode()
    )
    assert exporter.normalize_locked_sdist_requirements(lock, original, minor="3.14") == original


def test_pure_and_abi3_wheels_still_serve_later_minors() -> None:
    pure = _lock_with_wheels("https://files.pythonhosted.org/packages/control_package-1.2.3-py3-none-any.whl")
    abi3 = _lock_with_wheels(
        "https://files.pythonhosted.org/packages/control_package-1.2.3-cp314-abi3-macosx_11_0_arm64.whl"
    )
    original = _requirements()
    assert exporter.normalize_locked_sdist_requirements(pure, original, minor="3.15") == original
    assert exporter.normalize_locked_sdist_requirements(abi3, original, minor="3.15") == original
    assert exporter.normalize_locked_sdist_requirements(abi3, original, minor="3.13") == (
        f"control-package @ {URL} --hash={DIGEST}\n".encode()
    )


def test_target_minor_must_be_a_cpython_minor() -> None:
    with pytest.raises(ValueError, match="minor"):
        exporter.normalize_locked_sdist_requirements(_lock(), _requirements(), minor="3.x")
