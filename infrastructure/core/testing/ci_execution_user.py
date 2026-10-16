"""A fresh unprivileged execution UID for disposable GitHub-hosted Linux jobs.

Preparation precedes Source custody. The observer, workload clocks and PID
namespace are unchanged. Export is independent, byte-preserving transport.
"""

from __future__ import annotations

import argparse
import grp
import hashlib
import json
import os
import pwd
import re
import shutil
import signal
import stat
import subprocess  # nosec B404 - fixed setup commands and explicit payload argv
import sys
import time
from pathlib import Path

# Direct script entry during sudo setup loads only this stdlib leaf, not the
# package's Source-custody bootstrap as root. Normal imports retain module identity.
if __package__:
    from infrastructure.core.testing import _ci_execution_files as _files
else:
    from importlib.util import module_from_spec, spec_from_file_location

    _spec = spec_from_file_location("_template_ci_execution_files", Path(__file__).with_name("_ci_execution_files.py"))
    if _spec is None or _spec.loader is None:
        raise ImportError("CI execution file helpers unavailable")
    _files = module_from_spec(_spec)
    _spec.loader.exec_module(_files)

_acl = _files._acl
_ancestor_search = _files._ancestor_search
_command = _files._command
_copy_cache = _files._copy_cache
_entries = _files._entries
_export = _files._export
_handoff = _files._handoff
_physical = _files._physical
_remaining = _files._remaining
_require = _files._require
_stable_copy = _files._stable_copy

ACCOUNT = "template-ci"
ENV_KEYS = frozenset(
    "CI GITHUB_ACTIONS GITHUB_SHA GITHUB_REF GITHUB_REF_NAME GITHUB_EVENT_NAME GITHUB_REPOSITORY "
    "GITHUB_RUN_ID GITHUB_RUN_ATTEMPT GITHUB_JOB RUNNER_OS RUNNER_ARCH RUNNER_ENVIRONMENT "
    "SOURCE_DATE_EPOCH TZ LANG LC_ALL UV_FROZEN UV_OFFLINE UV_LINK_MODE MPLBACKEND SHARD HOST MINOR "
    "CHROME_EXECUTABLE_PATH TTFONTS JAVA_HOME TEMPLATE_NATIVE_JAVA TEMPLATE_NATIVE_EPUBCHECK "
    "TEMPLATE_ACCEPTANCE_OLLAMA TEMPLATE_ACCEPTANCE_MODEL_DIRECTORY TEMPLATE_ACCEPTANCE_SIA_IMAGE_ID "
    "TEMPLATE_SIA_TEST_IMAGE TEMPLATE_FORMAL_TLC_JAR OLLAMA_MODELS OLLAMA_HOST OLLAMA_NO_CLOUD OLLAMA_NOPRUNE "
    "OLLAMA_NUM_PARALLEL OLLAMA_MAX_LOADED_MODELS OLLAMA_CONTEXT_LENGTH OLLAMA_KEEP_ALIVE "
    "OLLAMA_MODEL OLLAMA_TEST_PULL_MODEL OLLAMA_SKIP_TEST_MODEL_PULL".split()
)


def _environment(values: dict[str, str]) -> dict[str, str]:
    selected = {key: value for key, value in values.items() if key in ENV_KEYS}
    _require(all(len(v) <= 8192 and not any(ord(c) < 32 for c in v) for v in selected.values()), "invalid runtime DATA")
    return selected


def _hosted(values: dict[str, str]) -> None:
    _require(sys.platform == "linux", "execution-user profile requires Linux")
    _require(
        all(
            values.get(k) == v
            for k, v in (("GITHUB_ACTIONS", "true"), ("RUNNER_OS", "Linux"), ("RUNNER_ENVIRONMENT", "github-hosted"))
        ),
        "execution-user profile requires an actual GitHub-hosted Linux job",
    )


def _git(root: Path, deadline: float) -> dict[str, str]:
    _require((root / ".git").is_dir() and not (root / ".git").is_symlink(), "shared Git worktree refused")
    _require(
        not (root / ".git/commondir").exists() and not (root / ".git/objects/info/alternates").exists(),
        "shared Git admin refused",
    )
    env = {
        "PATH": "/usr/bin:/bin",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_GRAFT_FILE": "/dev/null",
    }
    prefix = [
        "/usr/bin/git",
        "-c",
        "core.fsmonitor=false",
        "-c",
        "advice.graftFileDeprecated=false",
        "--no-optional-locks",
        "-C",
        str(root),
    ]

    def read(*args: str) -> bytes:
        result: subprocess.CompletedProcess[bytes] = _command([*prefix, *args], deadline, env=env, capture_output=True)
        return result.stdout

    config = read("config", "--local", "--list", "--null").lower()
    _require(
        not any(x in config for x in (b"extraheader", b"credential", b"safe.directory")),
        "checkout credentials/config bypass refused",
    )
    _require(re.search(rb"https?://[^/\x00\n]*@", config) is None, "credential-bearing checkout URL refused")
    _require(not read("status", "--porcelain", "--untracked-files=no"), "tracked checkout changes refused")
    modules = read("submodule", "status", "--recursive")
    _require(
        all(re.match(rb"^[ -][0-9a-f]{40} ", row) for row in modules.splitlines()),
        "submodule commit/availability refused",
    )
    return {
        "head": read("rev-parse", "HEAD").decode().strip(),
        "tree": read("rev-parse", "HEAD^{tree}").decode().strip(),
        "index": hashlib.sha256(read("ls-files", "--stage", "-z")).hexdigest(),
        "submodules": hashlib.sha256(modules).hexdigest(),
    }


def _load(path: Path) -> dict:
    _physical(path)
    info = path.stat()
    _require(
        stat.S_ISREG(info.st_mode) and info.st_uid == 0 and info.st_nlink == 1 and not info.st_mode & 0o022,
        "root-owned immutable profile state required",
    )
    _require(info.st_size <= 65536, "profile state bound exceeded")
    data: dict = json.loads(path.read_text())
    _require(
        data.get("schema") == 1 and path == Path(data["temp"]) / "template-ci-execution/state.json",
        "profile state scope refused",
    )
    _require(Path(data["home"]) == path.parent / "home" and data["account"] == ACCOUNT, "profile account/home refused")
    return data


def _prepare(path: Path, docker: bool) -> None:
    _files._phase("request")
    _hosted(dict(os.environ))
    _require(os.getuid() == os.geteuid() != 0, "prepare requires the original unprivileged runner")
    root, temporary = _physical(Path(os.environ["GITHUB_WORKSPACE"])), _physical(Path(os.environ["RUNNER_TEMP"]))
    _require(
        Path.cwd() == root and path == temporary / "template-ci-execution/state.json",
        "job workspace/state scope refused",
    )
    _require(
        not root.is_relative_to(temporary) and not temporary.is_relative_to(root),
        "workspace and runner temp must be disjoint",
    )
    _require(not path.parent.exists(), "execution profile is one-shot")
    deadline = time.monotonic() + 240
    _require(shutil.disk_usage(temporary).free >= _files.RESERVE, "execution profile disk reserve refused")
    identity = _git(root, deadline)
    _require(identity["head"] == os.environ["GITHUB_SHA"], "checkout differs from GitHub Source identity")
    caller = pwd.getpwuid(os.getuid())
    request = {
        "schema": 1,
        "account": ACCOUNT,
        "caller": caller.pw_uid,
        "caller_gid": caller.pw_gid,
        "old_home": caller.pw_dir,
        "root": str(root),
        "temp": str(temporary),
        "home": str(path.parent / "home"),
        "git": identity,
        "env": _environment(dict(os.environ)),
        "path": os.environ["PATH"],
        "uv": str(Path(shutil.which("uv") or "").resolve(strict=True)),
        "uv_cache": os.environ.get("UV_CACHE_DIR", str(Path(caller.pw_dir) / ".cache/uv")),
        "docker": docker,
        "deadline": deadline,
        "pidns": list((Path("/proc/self/ns/pid").stat().st_dev, Path("/proc/self/ns/pid").stat().st_ino)),
    }
    if docker:
        _require(grp.getgrnam("docker").gr_gid in os.getgroups(), "caller lacks declared Docker capability")
    path.parent.mkdir(mode=0o700)
    request_path = path.with_name("request.json")
    with request_path.open("x") as output:
        json.dump(request, output)
    os.chmod(request_path, 0o600)
    _command(
        [
            "/usr/bin/sudo",
            "-n",
            "--",
            sys.executable,
            "-I",
            "-B",
            str(Path(__file__).resolve()),
            "_prepare",
            "--state",
            str(path),
        ],
        deadline,
        env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin"},
    )


def _root_prepare(path: Path) -> None:
    _files._phase("account")
    _require(os.getuid() == os.geteuid() == 0, "privileged setup entry requires existing sudo authority")
    request_path = _physical(path.with_name("request.json"))
    caller = int(os.environ["SUDO_UID"])
    _require(
        request_path.stat().st_uid == caller and request_path.stat().st_size < 65536,
        "setup request ownership/bound refused",
    )
    data = json.loads(request_path.read_text())
    _require(data["caller"] == caller and data["old_home"] == pwd.getpwuid(caller).pw_dir, "setup caller disagrees")
    _hosted(data["env"])
    root, temporary = _physical(Path(data["root"])), _physical(Path(data["temp"]))
    _require(path == temporary / "template-ci-execution/state.json", "setup scope refused")
    deadline = data["deadline"]
    _remaining(deadline)
    _require(not any(row.pw_name == ACCOUNT for row in pwd.getpwall()), "execution account already exists")
    _command(
        [
            "/usr/sbin/useradd",
            "--user-group",
            "--no-create-home",
            "--no-log-init",
            "--home-dir",
            data["home"],
            "--shell",
            "/bin/bash",
            ACCOUNT,
        ],
        deadline,
        capture_output=True,
    )
    account = pwd.getpwnam(ACCOUNT)
    observed = _command(["/bin/ps", "-e", "-o", "uid="], deadline, capture_output=True, text=True).stdout.split()
    _require(
        bool(observed)
        and all(value.isdigit() for value in observed)
        and str(caller) in observed
        and str(account.pw_uid) not in observed,
        "execution UID is not fresh",
    )
    data.update(uid=account.pw_uid, gid=account.pw_gid, groups=[account.pw_gid])
    if data["docker"]:
        docker = grp.getgrnam("docker")
        _require(
            caller in (entry.pw_uid for entry in pwd.getpwall() if entry.pw_name in docker.gr_mem)
            or pwd.getpwuid(caller).pw_gid == docker.gr_gid,
            "declared original Docker membership changed",
        )
        _command(["/usr/sbin/usermod", "--append", "--groups", "docker", ACCOUNT], deadline, capture_output=True)
        data["groups"].append(docker.gr_gid)
    home = Path(data["home"])
    home.mkdir(mode=0o700)
    for name in ("bin", "tmp", "cache", "mpl"):
        (home / name).mkdir(mode=0o700)
    old_home = Path(data.pop("old_home"))
    _files._phase("public-caches")
    mappings = []
    candidates = [
        (Path(data.pop("uv_cache")), home / "cache/uv"),
        (old_home / ".cache/puppeteer", home / "cache/puppeteer"),
        (old_home / ".elan/bin", home / "elan/bin"),
        (old_home / ".elan/toolchains", home / "elan/toolchains"),
        (old_home / ".local/share/fonts/template-acceptance-juliamono", home / "fonts"),
    ]
    for source, destination in candidates:
        if source.exists():
            if destination == home / "cache/uv":
                _require(
                    source == old_home / ".cache/uv"
                    or source.parent == temporary
                    and re.fullmatch(
                        r"(?:setup-uv-cache|uv-cache|(?:acceptance|native)-installed-cache\.[A-Za-z0-9]+)", source.name
                    )
                    is not None,
                    "public UV cache scope refused",
                )
            destination.parent.mkdir(parents=True, exist_ok=True)
            _copy_cache(source, destination, deadline)
            mappings.append((str(source), str(destination)))
    _stable_copy(_physical(Path(data.pop("uv"))), home / "bin/uv", deadline, mode=0o755)

    def mapped(value: str) -> str:
        for before, after in mappings:
            if value == before or value.startswith(before + "/"):
                return after + value[len(before) :]
        return value

    environment = {key: mapped(value) for key, value in data["env"].items()}
    path_parts = [str(home / "bin")]
    for item in data.pop("path").split(os.pathsep):
        selected = Path(mapped(item))
        if selected.is_absolute() and any(
            selected.is_relative_to(base)
            for base in (
                root,
                home,
                Path("/usr"),
                Path("/bin"),
                Path("/sbin"),
                Path("/opt/hostedtoolcache"),
                Path("/snap/bin"),
                temporary,
            )
        ):
            path_parts.append(str(selected))
    environment.update(
        HOME=str(home),
        USER=ACCOUNT,
        LOGNAME=ACCOUNT,
        PATH=os.pathsep.join(path_parts),
        GITHUB_WORKSPACE=str(root),
        RUNNER_TEMP=str(home / "tmp"),
        TMPDIR=str(home / "tmp"),
        XDG_CACHE_HOME=str(home / "cache"),
        UV_CACHE_DIR=str(home / "cache/uv"),
        ELAN_HOME=str(home / "elan"),
        MPLCONFIGDIR=str(home / "mpl"),
    )
    data["env"] = environment
    # Only action-created public asset roots receive read/search ACLs.
    _files._phase("assets")
    assets = set()
    for value in (*environment.values(), *path_parts):
        for component in value.split(os.pathsep):
            candidate = Path(component.rstrip("/"))
            if (
                candidate.is_absolute()
                and candidate.is_relative_to(temporary)
                and not candidate.is_relative_to(path.parent)
            ):
                relative = candidate.relative_to(temporary)
                _require(
                    bool(relative.parts) and relative.parts[0].startswith("template-"),
                    "unrecognized job tool root refused",
                )
                assets.add(temporary / relative.parts[0])
    _acl([temporary], account.pw_uid, "--x", deadline)
    _ancestor_search([root, temporary], account.pw_uid, deadline)
    asset_entries = []
    for asset in assets:
        _physical(asset)
        for entry in _entries(asset, deadline):
            if entry.is_symlink():
                _require(entry.resolve(strict=True).is_relative_to(asset), "escaping job tool link refused")
                continue
            _require(entry.is_dir() or entry.is_file() and entry.stat().st_nlink == 1, "unsafe job tool entry refused")
            asset_entries.append(entry)
    _acl(asset_entries, account.pw_uid, "r-X", deadline)
    _files._phase("handoff")
    _handoff(root, account.pw_uid, account.pw_gid, caller, deadline)
    for entry in _entries(home, deadline):
        _remaining(deadline)
        os.chown(entry, account.pw_uid, account.pw_gid, follow_symlinks=False)
    artifacts = path.parent / "artifacts"
    artifacts.mkdir(mode=0o755)
    os.chown(artifacts, account.pw_uid, account.pw_gid)
    os.chown(request_path, 0, 0)
    os.chown(path.parent, 0, 0)
    os.chmod(path.parent, 0o700)
    _acl([path.parent], caller, "--x", deadline)
    _acl([path.parent], account.pw_uid, "--x", deadline)
    _files._phase("state")
    with path.open("x") as output:
        json.dump(data, output, sort_keys=True)
    os.chmod(path, 0o644)
    _require(shutil.disk_usage(temporary).free >= _files.RESERVE, "execution profile disk reserve refused")
    print(json.dumps({"execution_uid": account.pw_uid, "execution_gid": account.pw_gid, "prepared": True}))


def _identity(data: dict) -> None:
    account = pwd.getpwnam(ACCOUNT)
    _require(os.getuid() == os.geteuid() == data["uid"] == account.pw_uid != 0, "payload UID refused")
    _require(os.getgid() == os.getegid() == data["gid"] == account.pw_gid, "payload GID refused")
    _require(set(os.getgroups()) == set(data["groups"]), "undeclared supplementary group refused")
    _require(
        account.pw_dir == data["home"] and os.environ.get("HOME") == account.pw_dir, "genuine passwd home required"
    )
    status = dict(line.split(":", 1) for line in Path("/proc/self/status").read_text().splitlines())
    _require(
        status["Uid"].split() == [str(data["uid"])] * 4 and status["Gid"].split() == [str(data["gid"])] * 4,
        "mixed saved/filesystem credentials refused",
    )
    _require(
        all(int(status[key].strip(), 16) == 0 for key in ("CapPrm", "CapEff", "CapAmb")), "privileged payload refused"
    )
    pidns = Path("/proc/self/ns/pid").stat()
    _require([pidns.st_dev, pidns.st_ino] == data["pidns"], "PID namespace changed")


def _payload(argv: list[str], environment: dict[str, str], root: Path) -> int:
    _require(bool(argv) and all("\0" not in value for value in argv), "exact payload argv required")
    return subprocess.call(argv, cwd=root, env=environment)  # nosec B603 - deliberately authorized exact argv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("prepare", "run", "export", "_prepare", "_run", "_export"))
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--docker", action="store_true")
    parser.add_argument("--step-data", default="{}", help=argparse.SUPPRESS)
    supplied = list(sys.argv[1:] if argv is None else argv)
    divider = supplied.index("--") if "--" in supplied else len(supplied)
    args = parser.parse_args(supplied[:divider])
    payload = supplied[divider + 1 :]
    if args.operation == "prepare":
        _prepare(args.state, args.docker)
    elif args.operation == "_prepare":
        _root_prepare(args.state)
    else:
        data = _load(args.state)
        if args.operation in {"run", "export"}:
            _require(os.getuid() == os.geteuid() == data["caller"], "original runner required")
            operation = "_run" if args.operation == "run" else "_export"
            command = [
                "/usr/bin/sudo",
                "-n",
                "-H",
                "-u",
                ACCOUNT,
                "--",
                sys.executable,
                "-I",
                "-B",
                str(Path(__file__).resolve()),
                operation,
                "--state",
                str(args.state),
            ]
            step = {
                key: value for key, value in _environment(dict(os.environ)).items() if key in {"SHARD", "HOST", "MINOR"}
            }
            return _payload(
                [*command, "--step-data", json.dumps(step), "--", *payload],
                {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin"},
                Path(data["root"]),
            )
        step = json.loads(args.step_data)
        _require(set(step) <= {"SHARD", "HOST", "MINOR"} and _environment(step) == step, "step DATA refused")
        data["env"].update(step)
        os.environ.clear()
        os.environ.update(data["env"])
        _identity(data)
        root = _physical(Path(data["root"]))
        if args.operation == "_export":
            _files._phase("export")
            readiness = root / "output/readiness"
            _require(not readiness.is_symlink(), "symlinked readiness transport root refused")
            excluded: list[str] = []
            total = (
                _export(readiness, args.state.parent / "artifacts", time.monotonic() + 120, exclusions=excluded)
                if readiness.exists()
                else 0
            )
            print(
                json.dumps(
                    {
                        "transport_bytes": total,
                        "excluded_pytest_scratch": len(excluded),
                        "exclusions_sha256": hashlib.sha256(json.dumps(excluded).encode()).hexdigest(),
                        "runtime_acceptance": False,
                    }
                )
            )
        else:
            _files._phase("run-preflight")
            deadline = time.monotonic() + 60
            denied = subprocess.run(
                ["/usr/bin/sudo", "-n", "-l"], capture_output=True, timeout=_remaining(deadline), check=False
            )  # nosec B603 - fixed privilege refusal probe
            _require(denied.returncode != 0, "payload has undeclared sudo authority")
            _require(_git(root, deadline) == data["git"], "Source Git identity changed before payload")
            probe = (
                "import secrets,sys; from infrastructure.core._bounded_kill import observe_bounded_run_processes; "
                "observe_bounded_run_processes(secrets.token_hex(16),deadline=float(sys.argv[1]))"
            )
            _command([sys.executable, "-B", "-c", probe, str(deadline)], deadline, cwd=root, env=data["env"])
            _files._phase("payload")
            return _payload(payload, data["env"], root)
    return 0


if __name__ == "__main__":
    try:
        result = main()
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        _files._diagnostic(error)
        result = 1
    if result < 0:
        signal.signal(-result, signal.SIG_DFL)
        os.kill(os.getpid(), -result)
    raise SystemExit(result)
