"""The hosted model cache is input bytes, never admission or daemon custody."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml


def test_cached_model_bytes_are_reauthenticated_before_daemon_use(tmp_path: Path) -> None:
    """Actual action Bash refuses corrupt regular files and symlinked cache paths."""
    root = Path(__file__).resolve().parents[3]
    action = yaml.safe_load((root / ".github/actions/setup-acceptance-model/action.yml").read_text())
    steps = action["runs"]["steps"]
    cache = next(step for step in steps if step.get("name") == "Restore source-pinned model bytes")
    assert cache["uses"] == "actions/cache@55cc8345863c7cc4c66a329aec7e433d2d1c52a9"
    assert "restore-keys" not in cache["with"]
    authenticate = next(
        step for step in steps if step.get("name") == "Authenticate exact manifest and every fixed model blob"
    )
    assert (
        steps.index(cache)
        < steps.index(authenticate)
        < next(
            index
            for index, step in enumerate(steps)
            if step.get("name") == "Start owned daemon and verify actual inference before observation"
        )
    )

    # Genuine registry manifest, retaining its exact source-pinned bytes. No
    # provider is substituted: every negative control fails before acquisition.
    manifest = {
        "schemaVersion": 2,
        "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
        "config": {
            "mediaType": "application/vnd.docker.container.image.v1+json",
            "digest": "sha256:b0f58c4c1a3ca56f34a7673b353d7d09b773a1abce00451a58d5ebd2541331cf",
            "size": 561,
        },
        "layers": [
            {
                "mediaType": "application/vnd.ollama.image.model",
                "digest": "sha256:f535f83ec568d040f88ddc04a199fa6da90923bbb41d4dcaed02caa924d6ef57",
                "size": 270885952,
                "from": "/Users/administrator/.ollama/models/blobs/sha256-f535f83ec568d040f88ddc04a199fa6da90923bbb41d4dcaed02caa924d6ef57",
            },
            {
                "mediaType": "application/vnd.ollama.image.system",
                "digest": "sha256:fbacade46b4da804e0398c339c64b944d4b954452adf77cf050b49420116129e",
                "size": 68,
            },
            {
                "mediaType": "application/vnd.ollama.image.template",
                "digest": "sha256:d502d55c1d609104ae6127aee92eb940e51e15c56dfb26dbd067e2771ee746f1",
                "size": 675,
            },
            {
                "mediaType": "application/vnd.ollama.image.license",
                "digest": "sha256:58d1e17ffe5109a7ae296caafcadfdbe6a7d176f0bc4ab01e12a689b0499d8bd",
                "size": 11357,
            },
            {
                "mediaType": "application/vnd.ollama.image.params",
                "digest": "sha256:f02dd72bb2423204352eabc5637b44d79d17f109fdb510a7c51455892aa2d216",
                "size": 59,
            },
        ],
    }
    manifest_bytes = json.dumps(manifest, separators=(",", ":")).encode()
    cache_root = "${{ runner.temp }}/template-acceptance-model-cache"
    expected_paths = {f"{cache_root}/manifests/registry.ollama.ai/library/smollm2/135m"}
    expected_paths.update(
        f"{cache_root}/blobs/{record['digest'].replace(':', '-')}"
        for record in [manifest["config"], *manifest["layers"]]
    )
    assert set(cache["with"]["path"].splitlines()) == expected_paths
    assert len(manifest_bytes) == 1124
    assert (
        hashlib.sha256(manifest_bytes).hexdigest() == "9077fe9d2ae1a4a41a868836b56b8163731a8fe16621397028c2c76f838c6907"
    )
    programs = tmp_path / "programs-without-downloaders"
    programs.mkdir()
    for name in ("mkdir", "wc", "tr", "shasum"):
        program = shutil.which(name)
        assert program, f"Required real action tool {name} is absent"
        (programs / name).symlink_to(program)
    (programs / "python").symlink_to(sys.executable)
    bash = shutil.which("bash")
    assert bash, "Required real action Bash is absent"

    for target, fault in (
        ("manifest", "length"),
        ("manifest", "sha256"),
        ("manifest", "symlink"),
        ("blob", "length"),
        ("blob", "sha256"),
        ("blob", "symlink"),
        ("root", "symlink"),
    ):
        case = tmp_path / f"{target}-{fault}"
        case.mkdir()
        fresh = case / "fresh-daemon-storage"
        fresh.mkdir()
        model_cache = case / "template-acceptance-model-cache"
        manifest_file = model_cache / "manifests/registry.ollama.ai/library/smollm2/135m"
        manifest_file.parent.mkdir(parents=True)
        manifest_file.write_bytes(manifest_bytes)
        (model_cache / "blobs").mkdir()
        blob = model_cache / "blobs/sha256-b0f58c4c1a3ca56f34a7673b353d7d09b773a1abce00451a58d5ebd2541331cf"
        affected = manifest_file if target == "manifest" else blob
        if fault == "length":
            affected.write_bytes(b"short corrupt input")
        elif fault == "sha256":
            affected.write_bytes(b"x" * (1124 if target == "manifest" else 561))
        elif target == "root":
            moved = case / "outside-cache"
            model_cache.rename(moved)
            model_cache.symlink_to(moved, target_is_directory=True)
        else:
            outside = case / "outside-file"
            outside.write_bytes(manifest_bytes if target == "manifest" else b"x" * 561)
            affected.unlink(missing_ok=True)
            affected.symlink_to(outside)
        environment = case / "github-env"
        result = subprocess.run(
            [bash, "-c", authenticate["run"]],
            env=dict(
                os.environ,
                PATH=str(programs),
                RUNNER_TEMP=str(case),
                TEMPLATE_ACCEPTANCE_MODEL_DIRECTORY=str(fresh),
                GITHUB_ENV=str(environment),
            ),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        assert result.returncode != 0, (target, fault)
        assert "command not found" not in result.stderr, result.stderr
        assert not environment.exists(), "Corrupt model bytes became the active model environment"
        assert not (fresh / "daemon-owner.json").exists()
