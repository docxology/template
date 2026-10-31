from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
from pathlib import Path

import pytest
from PIL import Image

from infrastructure.rendering import _mermaid_v11

from infrastructure.rendering._pdf_mermaid import _resolve_chrome_executable, replace_inline_mermaid


def _write_executable(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


def _write_shell_executable(path: Path, body: str) -> Path:
    return _write_executable(path, "#!/bin/sh\nset -eu\n" + body)


def _fake_manuscript_dir(tmp_path: Path) -> Path:
    manuscript_dir = tmp_path / "project" / "manuscript"
    manuscript_dir.mkdir(parents=True, exist_ok=True)
    return manuscript_dir


def _sample_mermaid_block(source: str) -> str:
    return f"```mermaid\n{source}\n```\n*Sample Caption*\n"


def test_resolve_chrome_prefers_env_path_over_cache_and_system(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_chrome = _write_shell_executable(tmp_path / "env" / "chrome-env", "exit 0\n")
    cache_chrome = _write_shell_executable(
        tmp_path / ".cache" / "puppeteer" / "chrome" / "linux-200.0.0" / "chrome",
        "exit 0\n",
    )
    system_chrome = _write_shell_executable(tmp_path / "bin" / "google-chrome", "exit 0\n")

    monkeypatch.setenv("PUPPETEER_EXECUTABLE_PATH", str(env_chrome))
    monkeypatch.setenv("CHROME_EXECUTABLE_PATH", str(tmp_path / "env" / "chrome-secondary"))
    monkeypatch.setenv("PUPPETEER_CACHE_DIR", str(cache_chrome.parents[3]))
    monkeypatch.setenv("PATH", str(system_chrome.parent))
    assert _resolve_chrome_executable(home=tmp_path) == env_chrome


def test_resolve_chrome_uses_newest_cache_executable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache_dir = tmp_path / ".cache" / "puppeteer"
    older = _write_shell_executable(
        cache_dir
        / "chrome"
        / "mac_arm-148.0.7778.97"
        / "chrome-mac-arm64"
        / "Google Chrome for Testing.app"
        / "Contents"
        / "MacOS"
        / "Google Chrome for Testing",
        "exit 0\n",
    )
    newest = _write_shell_executable(
        cache_dir / "chrome-headless-shell" / "linux-149.1.2.3" / "chrome-headless-shell",
        "exit 0\n",
    )

    monkeypatch.delenv("PUPPETEER_EXECUTABLE_PATH", raising=False)
    monkeypatch.delenv("CHROME_EXECUTABLE_PATH", raising=False)
    monkeypatch.setenv("PUPPETEER_CACHE_DIR", str(cache_dir))
    monkeypatch.setenv("PATH", "")
    resolved = _resolve_chrome_executable(home=tmp_path)

    assert older.exists()
    assert resolved == newest


def test_resolve_chrome_prefers_headless_shell_at_same_version(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache_dir = tmp_path / ".cache" / "puppeteer"
    version = "mac_arm-150.0.7871.24"
    _write_shell_executable(
        cache_dir
        / "chrome"
        / version
        / "chrome-mac-arm64"
        / "Google Chrome for Testing.app"
        / "Contents"
        / "MacOS"
        / "Google Chrome for Testing",
        "exit 0\n",
    )
    headless = _write_shell_executable(
        cache_dir / "chrome-headless-shell" / version / "chrome-headless-shell-mac-arm64" / "chrome-headless-shell",
        "exit 0\n",
    )

    monkeypatch.delenv("PUPPETEER_EXECUTABLE_PATH", raising=False)
    monkeypatch.delenv("CHROME_EXECUTABLE_PATH", raising=False)
    monkeypatch.setenv("PUPPETEER_CACHE_DIR", str(cache_dir))
    monkeypatch.setenv("PATH", "")
    assert _resolve_chrome_executable(home=tmp_path) == headless


def test_resolve_chrome_uses_system_candidates_then_none(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    system_chrome = _write_shell_executable(tmp_path / "bin" / "chromium-browser", "exit 0\n")

    monkeypatch.delenv("PUPPETEER_EXECUTABLE_PATH", raising=False)
    monkeypatch.delenv("CHROME_EXECUTABLE_PATH", raising=False)
    monkeypatch.delenv("PUPPETEER_CACHE_DIR", raising=False)
    monkeypatch.setenv("PATH", str(system_chrome.parent))
    missing_home = tmp_path / "missing-home"
    assert _resolve_chrome_executable(home=missing_home) == system_chrome

    monkeypatch.setenv("PATH", "")
    assert _resolve_chrome_executable(home=missing_home) is None


@pytest.fixture
def mermaid_runtime(monkeypatch: pytest.MonkeyPatch) -> Path:
    """Select installed real producer/browser inputs without replacing execution."""
    local_mmdc = Path(__file__).resolve().parents[3] / "node_modules" / ".bin" / "mmdc"
    mmdc = shutil.which("mmdc") or (str(local_mmdc) if local_mmdc.is_file() else None)
    if mmdc is None or shutil.which("node") is None:
        pytest.skip("real Mermaid11.16 and Node runtime are not installed")
    _mermaid_v11.selected_package(mmdc)
    chrome = _resolve_chrome_executable()
    if chrome is None:
        pytest.skip("real Chrome runtime is not installed")
    monkeypatch.setenv("PATH", os.pathsep.join((str(Path(mmdc).parent), os.environ.get("PATH", ""))))
    monkeypatch.setenv("PUPPETEER_EXECUTABLE_PATH", str(chrome))
    return chrome


def _render_evidence(manuscript_dir: Path, *, success: bool) -> tuple[Path, dict]:
    directory = manuscript_dir.parent / "output" / "figures" / "mermaid_inline"
    records = list(directory.glob("*.mermaid-process.json"))
    assert len(records) == 1
    process = json.loads(records[0].read_bytes())
    assert process["invocation_policy"] == _mermaid_v11.POLICY
    assert process["pid"] > 0
    assert (process["original_exit_code"] == 0) is success
    assert process["input_sha256_before"] == process["input_sha256_after"]
    if success:
        images = list(directory.glob("*.png"))
        assert len(images) == 1
        with Image.open(images[0]) as png:
            assert png.format == "PNG"
            assert min(png.size) > 1
            png.verify()
    return directory, process


@pytest.mark.parametrize(
    ("block", "expected_alt"),
    [
        (_sample_mermaid_block("graph TD\nA-->B"), "Sample Caption"),
        (
            _sample_mermaid_block("graph TD\nA-->B").replace(
                "*Sample Caption*", "<!-- alt: Explicit diagram description. -->\n*Sample Caption*"
            ),
            "Explicit diagram description.",
        ),
    ],
)
@pytest.mark.timeout(120)
def test_replace_inline_mermaid_preserves_repo_puppeteer_config_and_authored_alt(
    tmp_path: Path,
    mermaid_runtime: Path,
    block: str,
    expected_alt: str,
) -> None:
    manuscript_dir = _fake_manuscript_dir(tmp_path)
    repo_config = manuscript_dir.parent / ".puppeteer.json"
    original = (json.dumps({"executablePath": str(mermaid_runtime), "args": ["--no-sandbox"]}) + "\n").encode()
    repo_config.write_bytes(original)

    result = replace_inline_mermaid(block, manuscript_dir)

    assert result.diagrams_rendered == 1
    assert "\\includegraphics" in result.content
    assert f"alt={{{expected_alt}}}" in result.content
    assert "Sample Caption" in result.content
    directory, process = _render_evidence(manuscript_dir, success=True)
    assert not list(directory.glob("*.puppeteer.json"))
    assert repo_config.read_bytes() == original
    assert process["input_sha256_before"][str(repo_config)] == hashlib.sha256(original).hexdigest()


def test_replace_inline_mermaid_falls_back_when_no_chrome_resolves(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    manuscript_dir = _fake_manuscript_dir(tmp_path)
    mmdc = _write_shell_executable(tmp_path / "bin" / "mmdc", "echo 'should not run' >&2\nexit 99\n")

    monkeypatch.setenv("PATH", str(mmdc.parent))
    monkeypatch.setenv("PUPPETEER_EXECUTABLE_PATH", str(tmp_path / "missing" / "chrome"))
    monkeypatch.delenv("CHROME_EXECUTABLE_PATH", raising=False)
    monkeypatch.setenv("PUPPETEER_CACHE_DIR", str(tmp_path / "missing-cache"))
    caplog.set_level("WARNING")

    result = replace_inline_mermaid(
        _sample_mermaid_block("graph TD\nA-->B"), manuscript_dir, home=tmp_path / "missing-home"
    )

    assert result.diagrams_rendered == 0
    assert "\\begin{figure}[htbp]" in result.content
    assert "\\begin{verbatim}" in result.content
    assert "graph TD" in result.content
    assert any("no Chrome resolved" in record.message for record in caplog.records)


def test_replace_inline_mermaid_falls_back_on_empty_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    manuscript_dir = _fake_manuscript_dir(tmp_path)
    mmdc = _write_shell_executable(tmp_path / "bin" / "mmdc", "echo 'unexpected mmdc call' >&2\nexit 98\n")
    chrome = _write_shell_executable(tmp_path / "bin" / "google-chrome", "exit 0\n")

    monkeypatch.setenv("PATH", os.pathsep.join((str(mmdc.parent), str(chrome.parent))))
    monkeypatch.delenv("PUPPETEER_EXECUTABLE_PATH", raising=False)
    monkeypatch.delenv("CHROME_EXECUTABLE_PATH", raising=False)
    monkeypatch.setenv("PUPPETEER_CACHE_DIR", str(tmp_path / "missing-cache"))
    caplog.set_level("WARNING")

    result = replace_inline_mermaid(_sample_mermaid_block(""), manuscript_dir, home=tmp_path / "missing-home")

    assert result.diagrams_rendered == 0
    assert "\\begin{verbatim}" in result.content
    assert any("is empty" in record.message for record in caplog.records)


@pytest.mark.parametrize("success", [True, False], ids=["real-render", "invalid-source"])
@pytest.mark.timeout(120)
def test_replace_inline_mermaid_runtime_config_is_real_then_portable(
    tmp_path: Path,
    mermaid_runtime: Path,
    caplog: pytest.LogCaptureFixture,
    success: bool,
) -> None:
    manuscript_dir = _fake_manuscript_dir(tmp_path)
    source = "graph TD\nA-->B" if success else "this is not a Mermaid diagram"
    caplog.set_level("WARNING")

    result = replace_inline_mermaid(_sample_mermaid_block(source), manuscript_dir, home=mermaid_runtime.parent)

    assert result.diagrams_rendered == int(success)
    directory, process = _render_evidence(manuscript_dir, success=success)
    config_path = directory / "inline_mermaid.puppeteer.json"
    runtime_bytes = (json.dumps({"executablePath": str(mermaid_runtime), "args": ["--no-sandbox"]}) + "\n").encode()
    assert process["input_sha256_before"][str(config_path)] == hashlib.sha256(runtime_bytes).hexdigest()
    persisted = json.loads(config_path.read_bytes())
    assert persisted == {"executablePath": f"<home>/{mermaid_runtime.resolve().name}", "args": ["--no-sandbox"]}
    if not success:
        assert "\\begin{verbatim}" in result.content
        assert any("mmdc failed" in record.message for record in caplog.records)


def test_unprofiled_mermaid_executable_is_refused_before_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    manuscript_dir = _fake_manuscript_dir(tmp_path)
    marker = tmp_path / "executed"
    mmdc = _write_shell_executable(tmp_path / "bin" / "mmdc", f"touch '{marker}'\nexit 0\n")
    # A declared config lets this exercise producer admission without needing
    # a browser. The unprofiled command must never reach either executable.
    (manuscript_dir.parent / ".puppeteer.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("PATH", str(mmdc.parent))
    caplog.set_level("WARNING")

    result = replace_inline_mermaid(_sample_mermaid_block("graph TD\nA-->B"), manuscript_dir)

    assert result.diagrams_rendered == 0
    assert "\\begin{verbatim}" in result.content
    assert not marker.exists()
    directory = manuscript_dir.parent / "output" / "figures" / "mermaid_inline"
    assert not list(directory.glob("*.png"))
    assert not list(directory.glob("*.mermaid-process.json"))
    assert any("no admitted runtime profile" in record.message for record in caplog.records)
