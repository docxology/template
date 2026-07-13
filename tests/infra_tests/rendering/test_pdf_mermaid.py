from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

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
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))

    assert _resolve_chrome_executable() == env_chrome


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
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))

    resolved = _resolve_chrome_executable()

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
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))

    assert _resolve_chrome_executable() == headless


def test_resolve_chrome_uses_system_candidates_then_none(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    system_chrome = _write_shell_executable(tmp_path / "bin" / "chromium-browser", "exit 0\n")

    monkeypatch.delenv("PUPPETEER_EXECUTABLE_PATH", raising=False)
    monkeypatch.delenv("CHROME_EXECUTABLE_PATH", raising=False)
    monkeypatch.delenv("PUPPETEER_CACHE_DIR", raising=False)
    monkeypatch.setenv("PATH", str(system_chrome.parent))
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path / "missing-home"))

    assert _resolve_chrome_executable() == system_chrome

    monkeypatch.setenv("PATH", "")
    assert _resolve_chrome_executable() is None


def test_replace_inline_mermaid_preserves_repo_puppeteer_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manuscript_dir = _fake_manuscript_dir(tmp_path)
    repo_config = manuscript_dir.parent / ".puppeteer.json"
    repo_config.write_text('{"args":["--existing-config"]}\n', encoding="utf-8")
    mmdc = _write_shell_executable(
        tmp_path / "bin" / "mmdc",
        """
input=""
output=""
config=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --input) input="$2"; shift 2 ;;
    --output) output="$2"; shift 2 ;;
    --puppeteerConfigFile) config="$2"; shift 2 ;;
    *) shift ;;
  esac
done
[ "$config" = "$EXPECT_CONFIG" ] || { echo "wrong config: $config" >&2; exit 7; }
printf 'png' > "$output"
""",
    )

    monkeypatch.setenv("PATH", str(mmdc.parent))
    monkeypatch.setenv("EXPECT_CONFIG", str(repo_config))

    result = replace_inline_mermaid(_sample_mermaid_block("graph TD\nA-->B"), manuscript_dir)

    assert result.diagrams_rendered == 1
    assert "\\includegraphics" in result.content
    assert "Sample Caption" in result.content
    runtime_configs = list((manuscript_dir.parent / "output" / "figures" / "mermaid_inline").glob("*.puppeteer.json"))
    assert runtime_configs == []


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
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path / "missing-home"))
    caplog.set_level("WARNING")

    result = replace_inline_mermaid(_sample_mermaid_block("graph TD\nA-->B"), manuscript_dir)

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
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path / "missing-home"))
    caplog.set_level("WARNING")

    result = replace_inline_mermaid(_sample_mermaid_block(""), manuscript_dir)

    assert result.diagrams_rendered == 0
    assert "\\begin{verbatim}" in result.content
    assert any("is empty" in record.message for record in caplog.records)


def test_replace_inline_mermaid_falls_back_after_mmdc_failure_and_writes_runtime_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    manuscript_dir = _fake_manuscript_dir(tmp_path)
    chrome = _write_shell_executable(tmp_path / "bin" / "google-chrome", "exit 0\n")
    config_snapshot = tmp_path / "captured-config.json"
    mmdc = _write_shell_executable(
        tmp_path / "bin" / "mmdc",
        f"""
output=""
config=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --output) output="$2"; shift 2 ;;
    --puppeteerConfigFile) config="$2"; shift 2 ;;
    *) shift ;;
  esac
done
[ -n "$config" ] || {{ echo "missing config" >&2; exit 8; }}
cp "$config" "{config_snapshot}"
echo "simulated mmdc failure" >&2
exit 9
""",
    )

    monkeypatch.delenv("PUPPETEER_EXECUTABLE_PATH", raising=False)
    monkeypatch.delenv("CHROME_EXECUTABLE_PATH", raising=False)
    monkeypatch.setenv("PUPPETEER_CACHE_DIR", str(tmp_path / "missing-cache"))
    monkeypatch.setenv("PATH", str(mmdc.parent))
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    _write_shell_executable(tmp_path / "google-chrome", "exit 0\n")
    caplog.set_level("WARNING")

    result = replace_inline_mermaid(_sample_mermaid_block("graph TD\nA-->B"), manuscript_dir)

    assert result.diagrams_rendered == 0
    assert "\\begin{verbatim}" in result.content
    assert config_snapshot.exists()
    runtime_config = config_snapshot.read_text(encoding="utf-8")
    assert str(chrome) in runtime_config
    assert "--no-sandbox" in runtime_config
    assert any("mmdc failed" in record.message for record in caplog.records)
