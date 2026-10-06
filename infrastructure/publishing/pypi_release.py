"""Bounded TestPyPI transfer, exact retrieval, and isolated installed smoke.

This explicitly invoked sandbox operation establishes its own transfer receipt;
it cannot authorize production or replace complete platform acceptance. Tools
and source-owned locked runtime dependencies must already be prepared locally.
"""

from __future__ import annotations

import base64
import hashlib
import json
import math
import os
import re
import shutil
import signal
import sys
import tarfile
import tempfile
import time
import tomllib
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from email.parser import BytesParser
from io import BytesIO
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote, quote_plus, unquote, urlsplit

from packaging.utils import canonicalize_name, parse_wheel_filename
from packaging.version import Version

from infrastructure.core.execution_boundary import BoundedSubprocessResult, build_bounded_env, run_bounded_subprocess
from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined
from infrastructure.core.implementation_custody import bytecode_audit_bootstrap, source_file_bytes
from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.project.installed_acceptance_artifacts import AdmittedWheel, INSTALLED_PROBE, freeze_wheel_bytes
from infrastructure.project.installed_acceptance_runtime import freeze_locked_metadata, install_runtime
from infrastructure.reporting.readiness_receipts import public_source_paths
from infrastructure.reporting.release_readiness_profile import Requirement
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

TESTPYPI_UPLOAD_URL = "https://test.pypi.org/legacy/"
MAX_ARTIFACT_BYTES = 64 * 1024 * 1024
MAX_SOURCE_BYTES = 512 * 1024 * 1024
MAX_FILES = 20000


class TestPyPIError(RuntimeError):
    """A truthful typed failure, preserving timeout/block/failure exit policy."""

    def __init__(self, message: str, *, state: str = "fail", exit_code: int = 1) -> None:
        super().__init__(message)
        self.state, self.exit_code = state, exit_code


@dataclass(frozen=True)
class Deadline:
    """All tools and local work consume one finite operation budget."""

    end: float

    @classmethod
    def start(cls, seconds: float) -> Deadline:
        if (
            isinstance(seconds, bool)
            or not isinstance(seconds, (int, float))
            or not math.isfinite(seconds)
            or seconds <= 0
        ):
            raise ValueError("TestPyPI deadline must be positive and finite")
        return cls(time.monotonic() + seconds)

    def remaining(self) -> float:
        remaining = self.end - time.monotonic()
        if remaining <= 0:
            raise TestPyPIError("TestPyPI operation deadline exhausted", state="timed_out", exit_code=124)
        return remaining


def _redact(text: str, sensitive_values: Sequence[str] = ()) -> str:
    for value in sensitive_values:
        if value:
            variants = {
                value,
                quote(value, safe=""),
                quote_plus(value),
                json.dumps(value)[1:-1],
                base64.b64encode(("__token__:" + value).encode()).decode(),
            }
            for variant in sorted(variants, key=len, reverse=True):
                text = text.replace(variant, "<redacted>")
    return text


def _display_command(cmd: Sequence[str], sensitive_values: Sequence[str] = ()) -> str:
    return _redact(" ".join(cmd), sensitive_values)


def _clean_env() -> dict[str, str]:
    env = build_bounded_env()
    for key in tuple(env):
        if key.startswith(("UV_", "PIP_", "TWINE_")) or key in {"PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"}:
            env.pop(key)
    env.update(UV_PYTHON_DOWNLOADS="never", UV_OFFLINE="1", MPLBACKEND="Agg")
    return env


def _twine_token_env(token: str) -> dict[str, str]:
    env = _clean_env()
    env.update(TWINE_USERNAME="__token__", TWINE_PASSWORD=token)
    return env


def _binary_digest(binary: Path) -> str:
    real = binary.resolve(strict=True)
    return hashlib.sha256(read_bytes_confined(real.parent, real, max_bytes=MAX_ARTIFACT_BYTES)).hexdigest()


def prepared_tool_versions(scratch: Path, deadline: Deadline, *, require_twine: bool = True) -> dict[str, str]:
    """Observe prepared packages in the selected isolated interpreter; never install."""
    names = ("hatchling", "twine") if require_twine else ("hatchling",)
    code = (
        "import importlib.metadata,importlib.util,json,sys; "
        f"names={names!r}; "
        "missing=[name for name in names if importlib.util.find_spec(name) is None]; "
        "print(json.dumps({'missing':missing,'versions':{name:importlib.metadata.version(name) "
        "for name in names if name not in missing}},sort_keys=True)); sys.exit(75 if missing else 0)"
    )
    result = run_command((sys.executable, "-I", "-c", code), scratch, deadline=deadline, check=False)
    if result.returncode == 75:
        raise TestPyPIError(
            "prepared publishing/backend tool is unavailable; no installation attempted", state="blocked", exit_code=75
        )
    if result.returncode:
        raise TestPyPIError("prepared-tool preflight failed")
    return dict(json.loads(result.stdout)["versions"])


def run_command(
    cmd: Sequence[str],
    cwd: Path | None = None,
    check: bool = True,
    *,
    deadline: Deadline | None = None,
    env: Mapping[str, str] | None = None,
    sensitive_values: Sequence[str] = (),
) -> BoundedSubprocessResult:
    """Supervise each child and redact both captured channels before exposure."""
    budget = deadline or Deadline.start(120)
    display = _display_command(cmd, sensitive_values)
    print(f"> {display}")
    result = run_bounded_subprocess(
        cmd,
        cwd=cwd or Path.cwd(),
        env=dict(env) if env is not None else _clean_env(),
        timeout=budget.remaining(),
        capture_output=True,
    )
    result.stdout = _redact(result.stdout, sensitive_values)
    result.stderr = _redact(result.stderr, sensitive_values)
    result.command_error = _redact(result.command_error, sensitive_values)
    if result.stdout:
        print(result.stdout[-8192:], end="" if result.stdout.endswith("\n") else "\n")
    if result.stderr:
        print(result.stderr[-8192:], file=sys.stderr, end="" if result.stderr.endswith("\n") else "\n")
    if result.original_returncode in (130, -signal.SIGINT):
        raise TestPyPIError(f"command interrupted: {display}", state="interrupted", exit_code=130)
    if result.timed_out:
        raise TestPyPIError(f"command timed out: {display}", state="timed_out", exit_code=124)
    budget.remaining()
    if result.custody_refused:
        raise TestPyPIError("process guardian refused execution custody", state="blocked", exit_code=75)
    if check and (result.returncode or result.command_error):
        diagnostic = (result.stderr or result.stdout or result.command_error)[-8192:]
        raise TestPyPIError(f"command failed (exit {result.returncode}): {display}\n{diagnostic}")
    return result


@dataclass(frozen=True)
class PublicBuildSource:
    root: Path
    source: Path
    reader: SnapshotReader
    names: tuple[str, ...]
    requirement: Requirement

    def assert_current(self, deadline: Deadline) -> None:
        """Detect added/deleted inputs and original/private source mutations."""
        deadline.remaining()
        names = tuple(path.relative_to(self.root).as_posix() for path in public_source_paths(self.root))
        if names != self.names or not self.reader.unchanged():
            raise TestPyPIError("public source changed after build admission; refuse transfer/receipt")
        if tuple(path.relative_to(self.source).as_posix() for path in public_source_paths(self.source)) != self.names:
            raise TestPyPIError("private public build inventory changed after admission")
        for name in self.names:
            deadline.remaining()
            content = read_bytes_confined(self.source, self.source / name, max_bytes=MAX_ARTIFACT_BYTES)
            if hashlib.sha256(content).hexdigest() != self.reader.read(name).sha256:
                raise TestPyPIError("private build source changed after its admission")


def freeze_build_source(root: Path, scratch: Path, deadline: Deadline) -> PublicBuildSource:
    """Build from fresh public bytes while preserving existing dist directories."""
    root = root.resolve(strict=True)
    reader = SnapshotReader(root)
    paths = public_source_paths(root)
    if len(paths) > MAX_FILES:
        raise ValueError("public build inventory exceeds its file bound")
    names = tuple(path.relative_to(root).as_posix() for path in paths)
    source = scratch / "source"
    source.mkdir()
    total = 0
    hashes = {}
    for name in names:
        deadline.remaining()
        snapshot = reader.read(name)
        total += len(snapshot.content)
        if total > MAX_SOURCE_BYTES:
            raise ValueError("public build inventory exceeds its byte bound")
        atomic_write_bytes_confined(source, source / name, snapshot.content, mode=0o400)
        hashes[name] = snapshot.sha256
    metadata = tomllib.loads(reader.read("pyproject.toml").content.decode())
    package, version = metadata["project"]["name"], metadata["project"]["version"]
    if package != "research-project-template" or not isinstance(version, str) or str(Version(version)) != version:
        raise ValueError("canonical platform package/version metadata is invalid")
    requirement = Requirement(
        "root:testpypi:installed", "installed", "root", version, version, canonical_digest(hashes), package=package
    )
    frozen = PublicBuildSource(root, source, reader, names, requirement)
    frozen.assert_current(deadline)
    return frozen


@dataclass(frozen=True)
class Distribution:
    """Original admitted bytes; observations never replace their expected hash."""

    path: Path
    content: bytes
    sha256: str
    kind: str

    def assert_current(self, scratch: Path) -> None:
        content = read_bytes_confined(scratch, self.path, max_bytes=MAX_ARTIFACT_BYTES)
        if content != self.content or hashlib.sha256(content).hexdigest() != self.sha256:
            raise TestPyPIError("admitted distribution changed before/after transfer")


def _metadata_identity(content: bytes, requirement: Requirement) -> None:
    metadata = BytesParser().parsebytes(content)
    if metadata.get_all("Name") != [requirement.package] or metadata.get_all("Version") != [requirement.version]:
        raise ValueError("built distribution metadata differs from canonical platform identity")


def admit_sdist(content: bytes, filename: str, source: PublicBuildSource) -> None:
    """Check tar identity and every source member byte without extraction."""
    requirement = source.requirement
    prefix = f"{requirement.package.replace('-', '_')}-{requirement.version}"
    if filename != prefix + ".tar.gz":
        raise ValueError("sdist filename differs from canonical package/version")
    names: set[str] = set()
    observed = set()
    total = 0
    metadata = None
    with tarfile.open(fileobj=BytesIO(content), mode="r:gz") as archive:
        for member in archive:
            total += member.size
            name = PurePosixPath(member.name)
            if len(names) >= MAX_FILES or total > MAX_ARTIFACT_BYTES:
                raise ValueError("sdist exceeds bounded member/expanded-byte limits")
            if (
                "\\" in member.name
                or "\0" in member.name
                or name.is_absolute()
                or ".." in name.parts
                or not name.parts
                or name.parts[0] != prefix
                or member.name in names
                or not (member.isfile() or member.isdir())
            ):
                raise ValueError("sdist has unsafe, duplicate, linked, or unowned members")
            names.add(member.name)
            if member.isdir():
                continue
            opened = archive.extractfile(member)
            if opened is None:
                raise ValueError("sdist regular file has no bytes")
            data = opened.read(MAX_ARTIFACT_BYTES + 1)
            if len(data) != member.size:
                raise ValueError("sdist member length differs from its declaration")
            relative = PurePosixPath(*name.parts[1:]).as_posix()
            if relative == "PKG-INFO":
                metadata = data
            else:
                if relative not in source.names or data != source.reader.read(relative).content:
                    raise ValueError("sdist contains unowned or different source bytes")
                observed.add(relative)
    expected = {name for name in source.names if name.startswith("infrastructure/")}
    expected.update({"pyproject.toml", "README.md", "LICENSE"})
    if metadata is None or not expected.issubset(observed):
        raise ValueError("sdist lacks metadata or canonical runtime source")
    _metadata_identity(metadata, requirement)


def build_package(
    source: PublicBuildSource,
    scratch: Path,
    uv: str,
    deadline: Deadline,
) -> tuple[AdmittedWheel, tuple[Distribution, ...]]:
    """Use explicitly prepared build tools without cleanup/network/tool installs."""
    prepared_tool_versions(scratch, deadline, require_twine=False)
    output = scratch / "built-distributions"
    output.mkdir()
    run_command(
        (
            uv,
            "build",
            "--offline",
            "--no-config",
            "--no-python-downloads",
            "--no-build-isolation",
            "--no-create-gitignore",
            "--python",
            sys.executable,
            "--out-dir",
            str(output),
            str(source.source),
        ),
        scratch,
        deadline=deadline,
    )
    paths = tuple(sorted(output.iterdir()))
    wheels = tuple(path for path in paths if path.suffix == ".whl")
    sdists = tuple(path for path in paths if path.name.endswith(".tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1 or len(paths) != 2:
        raise TestPyPIError(
            "fresh build must produce exactly one wheel and one sdist; "
            f"observed entries: {', '.join(path.name for path in paths)}"
        )
    wheel = wheels[0]
    content = read_bytes_confined(scratch, wheel, max_bytes=MAX_ARTIFACT_BYTES)
    package, version, _, _ = parse_wheel_filename(wheel.name)
    if package != canonicalize_name(source.requirement.package) or str(version) != source.requirement.version:
        raise ValueError("wheel filename differs from its canonical METADATA identity")
    admitted = freeze_wheel_bytes(source.root, source.requirement, content, scratch, wheel.name, reader=source.reader)
    sdist = sdists[0]
    data = read_bytes_confined(scratch, sdist, max_bytes=MAX_ARTIFACT_BYTES)
    admit_sdist(data, sdist.name, source)
    private_sdist = scratch / "admitted-sdist" / sdist.name
    atomic_write_bytes_confined(scratch, private_sdist, data, mode=0o400)
    source.assert_current(deadline)
    return admitted, (
        Distribution(admitted.path, admitted.content, admitted.sha256, "wheel"),
        Distribution(private_sdist, data, hashlib.sha256(data).hexdigest(), "sdist"),
    )


def upload_to_testpypi(
    distributions: tuple[Distribution, ...],
    token: str,
    scratch: Path,
    deadline: Deadline,
    *,
    source: PublicBuildSource,
) -> None:
    """Upload original admitted artifacts to the fixed sandbox destination."""
    for item in distributions:
        item.assert_current(scratch)
    config = scratch / "empty-pypirc"
    atomic_write_bytes_confined(scratch, config, b"[distutils]\nindex-servers =\n", mode=0o400)
    common = (sys.executable, "-I", "-m", "twine")
    files = tuple(str(item.path) for item in distributions)
    run_command((*common, "check", "--strict", *files), scratch, deadline=deadline)
    for item in distributions:
        item.assert_current(scratch)
    source.assert_current(deadline)
    run_command(
        (
            *common,
            "upload",
            "--non-interactive",
            "--disable-progress-bar",
            "--config-file",
            str(config),
            "--repository-url",
            TESTPYPI_UPLOAD_URL,
            *files,
        ),
        scratch,
        deadline=deadline,
        env=_twine_token_env(token),
        sensitive_values=(token,),
    )
    for item in distributions:
        item.assert_current(scratch)
    source.assert_current(deadline)


# This supervised child has no platform imports or credentials. Reads consume
# its original deadline; the parent guardian owns mandatory process cleanup.
RETRIEVAL_CHILD = r"""
import hashlib,json,pathlib,re,ssl,sys,time,urllib.parse,urllib.request
spec_path,output_path=sys.argv[1:]
spec=json.loads(pathlib.Path(spec_path).read_bytes())
deadline=time.monotonic()+spec['timeout']
maximum=spec['max_bytes']
def remaining():
    result=deadline-time.monotonic()
    if result<=0: raise TimeoutError('TestPyPI retrieval deadline exhausted')
    return result
def valid(url,host):
    parsed=urllib.parse.urlsplit(url)
    if (parsed.scheme!='https' or parsed.hostname!=host or parsed.port not in (None,443)
        or parsed.username is not None or parsed.password is not None or parsed.query or parsed.fragment):
        raise ValueError('retrieval destination is outside the admitted TestPyPI authority')
class Redirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,request,fp,code,msg,headers,newurl):
        valid(newurl,urllib.parse.urlsplit(request.full_url).hostname)
        return super().redirect_request(request,fp,code,msg,headers,newurl)
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),Redirects(),
    urllib.request.HTTPSHandler(context=ssl.create_default_context()))
def download(url,host,limit):
    valid(url,host)
    data=bytearray()
    with opener.open(url,timeout=min(15,remaining())) as response:
        valid(response.geturl(),host)
        if response.status!=200: raise ValueError('retrieval did not return HTTP 200')
        while True:
            remaining()
            chunk=response.read(min(65536,limit-len(data)+1))
            if not chunk: break
            data.extend(chunk)
            if len(data)>limit: raise ValueError('retrieval exceeds its admitted byte bound')
    return bytes(data)
package,version=spec['package'],spec['version']
api='https://test.pypi.org/pypi/'+urllib.parse.quote(package,safe='')+'/'+urllib.parse.quote(version,safe='')+'/json'
record=download(api,'test.pypi.org',1024*1024)
value=json.loads(record)
info=value['info']
canonical=lambda name: re.sub(r'[-_.]+','-',name).lower()
if canonical(info['name'])!=package or info['version']!=version:
    raise ValueError('remote package/version differs from originally uploaded identity')
expected=spec['artifacts']
urls=value['urls']
if not isinstance(urls,list) or len(urls)!=len(expected):
    raise ValueError('remote version has a different artifact set')
seen=set();observed=[]
destination=pathlib.Path(output_path).parent/'downloaded'
destination.mkdir()
for item in urls:
    name=item['filename']
    if name not in expected or name in seen or item['digests']['sha256']!=expected[name]['sha256']:
        raise ValueError('remote artifact hash/name differs from originally uploaded bytes')
    seen.add(name)
    url=item['url'];valid(url,'test-files.pythonhosted.org')
    if urllib.parse.unquote(urllib.parse.urlsplit(url).path.rsplit('/',1)[-1])!=name:
        raise ValueError('remote artifact URL filename differs from original upload')
    data=download(url,'test-files.pythonhosted.org',min(maximum,expected[name]['size']))
    digest=hashlib.sha256(data).hexdigest()
    if digest!=expected[name]['sha256'] or len(data)!=expected[name]['size']:
        raise ValueError('retrieved bytes differ from originally uploaded bytes')
    path=destination/name
    with path.open('xb') as stream: stream.write(data)
    path.chmod(0o400)
    observed.append({'filename':name,'url':url,'sha256':digest,'size':len(data)})
remaining()
pathlib.Path(output_path).write_text(json.dumps({'package':package,'version':version,'artifacts':observed,
    'metadata_sha256':hashlib.sha256(record).hexdigest(),'nonce':spec['nonce']},sort_keys=True))
"""


def admit_retrieved(
    scratch: Path,
    distributions: tuple[Distribution, ...],
    observation: dict[str, Any],
    *,
    package: str,
    version: str,
    nonce: str,
) -> tuple[Distribution, ...]:
    """Independently compare returned real bytes with original upload custody."""
    if (
        observation.get("package") != package
        or observation.get("version") != version
        or observation.get("nonce") != nonce
    ):
        raise ValueError("retrieval receipt has wrong package/version/run identity")
    entries = observation.get("artifacts")
    if not isinstance(entries, list) or len(entries) != len(distributions):
        raise ValueError("retrieval receipt has incomplete artifact coverage")
    expected = {item.path.name: item for item in distributions}
    seen = set()
    returned = []
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("filename") not in expected or entry["filename"] in seen:
            raise ValueError("retrieval receipt has unknown/duplicate artifacts")
        name = entry["filename"]
        seen.add(name)
        original = expected[name]
        url = entry.get("url")
        if not isinstance(url, str):
            raise ValueError("retrieval receipt lacks its admitted remote artifact URL")
        parsed = urlsplit(url)
        if (
            parsed.scheme != "https"
            or parsed.hostname != "test-files.pythonhosted.org"
            or parsed.port not in (None, 443)
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or unquote(parsed.path.rsplit("/", 1)[-1]) != name
        ):
            raise ValueError("retrieval receipt artifact URL differs from TestPyPI authority/name")
        path = scratch / "retrieval/downloaded" / name
        actual = read_bytes_confined(scratch, path, max_bytes=MAX_ARTIFACT_BYTES)
        if (
            entry.get("sha256") != original.sha256
            or entry.get("size") != len(original.content)
            or actual != original.content
            or hashlib.sha256(actual).hexdigest() != original.sha256
        ):
            raise ValueError("actual retrieved artifact differs from originally uploaded bytes")
        returned.append(Distribution(path, actual, original.sha256, original.kind))
    return tuple(returned)


def retrieve_distributions(
    source: PublicBuildSource,
    distributions: tuple[Distribution, ...],
    scratch: Path,
    deadline: Deadline,
) -> tuple[tuple[Distribution, ...], dict[str, Any]]:
    directory = scratch / "retrieval"
    directory.mkdir()
    package, version = canonicalize_name(source.requirement.package), source.requirement.version
    nonce = uuid.uuid4().hex
    spec = {
        "package": package,
        "version": version,
        "nonce": nonce,
        "timeout": deadline.remaining(),
        "max_bytes": MAX_ARTIFACT_BYTES,
        "artifacts": {item.path.name: {"sha256": item.sha256, "size": len(item.content)} for item in distributions},
    }
    spec_path, observation = directory / "spec.json", directory / "observation.json"
    atomic_write_bytes_confined(scratch, spec_path, json.dumps(spec, sort_keys=True).encode(), mode=0o400)
    run_command(
        (sys.executable, "-I", "-c", RETRIEVAL_CHILD, str(spec_path), str(observation)), scratch, deadline=deadline
    )
    payload = json.loads(read_bytes_confined(scratch, observation, max_bytes=1024 * 1024))
    returned = admit_retrieved(scratch, distributions, payload, package=package, version=version, nonce=nonce)
    for item in distributions:
        item.assert_current(scratch)
    source.assert_current(deadline)
    return returned, payload


def install_and_verify(
    source: PublicBuildSource,
    retrieved: tuple[Distribution, ...],
    scratch: Path,
    uv: str,
    deadline: Deadline,
) -> dict[str, Any]:
    """Install the exact retrieved wheel through hashes and offline runtime locks."""
    wheel = next(item for item in retrieved if item.kind == "wheel")
    selected_digest = _binary_digest(Path(sys.executable))
    admitted = freeze_wheel_bytes(
        source.root, source.requirement, wheel.content, scratch, wheel.path.name, reader=source.reader
    )
    metadata = freeze_locked_metadata(source.source, scratch)
    directory = scratch / "output/readiness/installed-smoke"
    directory.mkdir(parents=True)

    def run(command: tuple[str, ...], label: str) -> BoundedSubprocessResult:
        try:
            return run_command(command, scratch, deadline=deadline)
        except TestPyPIError as exc:
            if label in {"runtime-lock", "runtime-dependencies"} and any(
                phrase in str(exc) for phrase in ("network is disabled", "network connectivity is disabled")
            ):
                raise TestPyPIError(
                    "locked runtime dependencies are absent from the offline cache", state="blocked", exit_code=75
                ) from exc
            raise

    python, _ = install_runtime(
        scratch,
        source.requirement,
        scratch,
        directory,
        Path(sys.executable),
        admitted,
        uv,
        run,
        provider_wheels={},
        metadata=metadata,
    )
    outside, bytecode = scratch / "outside-source", scratch / "fresh-bytecode"
    outside.mkdir()
    bytecode.mkdir()
    runtime = f"{sys.version_info.major}.{sys.version_info.minor}"
    site = (
        python.parent.parent / "Lib/site-packages"
        if os.name == "nt"
        else python.parent.parent / "lib" / f"python{runtime}" / "site-packages"
    )
    audit_path = site / "infrastructure/core/bytecode_audit.py"
    roots = tuple(site / name for name in admitted.members if name.endswith(".py")) + tuple(
        site / target for target in admitted.targets
    )
    bootstrap = bytecode_audit_bootstrap(roots, bytecode, audit_path=audit_path)
    spec = {
        "scope": "root",
        "package": source.requirement.package,
        "version": source.requirement.version,
        "targets": admitted.targets,
        "wheel_members": admitted.members,
        "dependency_providers": [],
        "forbidden_roots": [str(source.root), str(source.source)],
        "python_version": runtime,
        "run_nonce": uuid.uuid4().hex,
        "audit": {
            "roots": [str(path.absolute()) for path in roots],
            "path": str(audit_path),
            "prefix": str(bytecode),
            "sha256": hashlib.sha256(source_file_bytes(audit_path)).hexdigest(),
        },
    }
    content = json.dumps(spec, sort_keys=True).encode()
    spec_path, observation = outside / "spec.json", outside / "observation.json"
    atomic_write_bytes_confined(scratch, spec_path, content, mode=0o400)
    run_command(
        (
            str(python),
            "-I",
            "-X",
            f"pycache_prefix={bytecode}",
            "-c",
            bootstrap + "\n" + INSTALLED_PROBE,
            str(spec_path),
            str(observation),
        ),
        outside,
        deadline=deadline,
    )
    result: dict[str, Any] = json.loads(read_bytes_confined(scratch, observation, max_bytes=MAX_ARTIFACT_BYTES))
    if not isinstance(result, dict):
        raise TestPyPIError("installed functional probe result is not an object")
    if (
        result.get("run_nonce") != spec["run_nonce"]
        or result.get("probe_spec_sha256") != hashlib.sha256(content).hexdigest()
        or result.get("package") != source.requirement.package
        or result.get("version") != source.requirement.version
        or result.get("imported_modules") != list(admitted.targets)
        or result.get("domain") != {"completion_policy": True}
        or result.get("isolated") is not True
        or result.get("execution_exit_code") != 0
        or result.get("interpreter") != str(python)
        or result.get("interpreter_sha256") != selected_digest
        or _binary_digest(Path(sys.executable)) != selected_digest
    ):
        raise TestPyPIError("installed functional probe has invalid identity or completion evidence")
    if not metadata.unchanged():
        raise TestPyPIError("locked metadata changed during installed smoke")
    source.assert_current(deadline)
    for item in retrieved:
        item.assert_current(scratch)
    return result


def run_test_pypi_release(
    token: str,
    *,
    repo_root: Path | None = None,
    timeout_seconds: float = 600,
) -> dict[str, Any]:
    """Explicit sandbox transfer, returning limited acceptance facts."""
    deadline = Deadline.start(timeout_seconds)
    if not isinstance(token, str) or not token.strip():
        raise TestPyPIError("TEST_PYPI_API_TOKEN is required", state="blocked", exit_code=75)
    if any(character.isspace() for character in token):
        raise ValueError("TestPyPI token must not contain whitespace")
    uv = shutil.which("uv")
    if uv is None:
        raise TestPyPIError("prepared uv is unavailable", state="blocked", exit_code=75)
    root = repo_root or Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="template-testpypi-") as temporary:
        scratch = Path(temporary).resolve()
        tool_versions = prepared_tool_versions(scratch, deadline)
        tool_hashes = {"uv": _binary_digest(Path(uv)), "python": _binary_digest(Path(sys.executable))}
        source = freeze_build_source(root, scratch, deadline)
        _, distributions = build_package(source, scratch, uv, deadline)
        source.assert_current(deadline)
        if tool_hashes != {"uv": _binary_digest(Path(uv)), "python": _binary_digest(Path(sys.executable))}:
            raise TestPyPIError("prepared tool identity changed before transfer")
        upload_to_testpypi(distributions, token, scratch, deadline, source=source)
        source.assert_current(deadline)
        retrieved, transfer = retrieve_distributions(source, distributions, scratch, deadline)
        installed = install_and_verify(source, retrieved, scratch, uv, deadline)
        source.assert_current(deadline)
        if tool_hashes != {"uv": _binary_digest(Path(uv)), "python": _binary_digest(Path(sys.executable))}:
            raise TestPyPIError("prepared tool identity changed during sandbox acceptance")
        receipt = {
            "schema_version": "template-testpypi-transfer-v1",
            "status": "pass",
            "package": source.requirement.package,
            "version": source.requirement.version,
            "platform_version": source.requirement.platform_version,
            "source_identity": source.requirement.source_identity,
            "destination": TESTPYPI_UPLOAD_URL,
            "transfer": transfer,
            "tool_versions": tool_versions,
            "tool_sha256": tool_hashes,
            "installed_smoke": {
                key: installed[key]
                for key in (
                    "package",
                    "version",
                    "python_version",
                    "interpreter_sha256",
                    "domain",
                    "probe_spec_sha256",
                    "isolated",
                    "source_path_contamination",
                    "bytecode_binding",
                )
            },
            "assurance": "sandbox transfer, exact retrieval and installed functional smoke only",
            "program_acceptance": "not established by this receipt",
        }
        deadline.remaining()
        print(json.dumps(receipt, sort_keys=True))
        return receipt


def verify_candidate_wheel(
    wheel: Path,
    original_sha256: str,
    *,
    repo_root: Path | None = None,
    timeout_seconds: float = 600,
) -> dict[str, Any]:
    """Verify explicitly supplied original bytes offline; no index/name fallback."""
    if re.fullmatch(r"[0-9a-f]{64}", original_sha256) is None:
        raise ValueError("installed verification requires the original wheel SHA-256")
    deadline = Deadline.start(timeout_seconds)
    uv = shutil.which("uv")
    if uv is None:
        raise TestPyPIError("prepared uv is unavailable", state="blocked", exit_code=75)
    wheel = wheel.absolute()
    content = read_bytes_confined(wheel.parent, wheel, max_bytes=MAX_ARTIFACT_BYTES)
    if hashlib.sha256(content).hexdigest() != original_sha256:
        raise ValueError("candidate bytes differ from the explicitly supplied original wheel hash")
    root = repo_root or Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="template-wheel-verification-") as temporary:
        scratch = Path(temporary).resolve()
        source = freeze_build_source(root, scratch, deadline)
        admitted = freeze_wheel_bytes(root, source.requirement, content, scratch, wheel.name, reader=source.reader)
        distribution = Distribution(admitted.path, admitted.content, original_sha256, "wheel")
        result = install_and_verify(source, (distribution,), scratch, uv, deadline)
        return {
            "schema_version": "template-installed-smoke-v1",
            "status": "pass",
            "package": source.requirement.package,
            "version": source.requirement.version,
            "platform_version": source.requirement.platform_version,
            "source_identity": source.requirement.source_identity,
            "wheel_sha256": original_sha256,
            "installed_smoke": {
                key: result[key]
                for key in (
                    "package",
                    "version",
                    "python_version",
                    "interpreter_sha256",
                    "domain",
                    "probe_spec_sha256",
                    "isolated",
                    "source_path_contamination",
                    "bytecode_binding",
                )
            },
            "assurance": "explicit-wheel offline installed functional smoke only",
            "publication": "not established by this receipt",
            "program_acceptance": "not established by this receipt",
        }
