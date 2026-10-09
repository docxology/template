"""Prepare exact Source-listed wheel DATA for the cold native provider factory."""

from __future__ import annotations

import hashlib
import io
import tomllib
import zipfile
from pathlib import Path

from packaging.tags import sys_tags
from packaging.utils import parse_wheel_filename

from infrastructure.core.implementation_custody import source_file_bytes
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_installed_preparation import NativePreparedRuntime
from infrastructure.reporting.native_installed_invocation import NativeInstalledInvocationFailure
from infrastructure.reporting.native_tool_process import run_native_tool_process

_DOWNLOAD = """import sys,urllib.request,urllib.parse
from pathlib import Path
url=sys.argv[1]; destination=Path(sys.argv[2]); limit=64*1024*1024
parsed=urllib.parse.urlsplit(url)
if parsed.scheme!='https' or parsed.hostname!='files.pythonhosted.org' or parsed.username or parsed.password:
 raise ValueError('only exact Source-listed public wheel transport is allowed')
with urllib.request.urlopen(url,timeout=60) as response,destination.open('xb') as output:
 resolved=urllib.parse.urlsplit(response.geturl())
 if resolved.scheme!='https' or resolved.hostname!='files.pythonhosted.org':raise ValueError('foreign wheel redirect')
 count=0
 while True:
  body=response.read(65536)
  if not body:break
  count+=len(body)
  if count>limit:raise ValueError('Source wheel exceeds unchanged64MiB file ceiling')
  output.write(body)
"""


def prepare_pdfium_nomination(
    prepared: NativePreparedRuntime,
    *,
    environment: dict[str, str],
    nominated: Path | None = None,
) -> tuple[Path, tuple[Path, ...], dict[str, str]]:
    """Return DATA paths/Code hashes, never a PDFium provider or runtime grant.

    Cold installed Source factories still admit the actual wheel, whole RECORD,
    selected package origins, preimport absence and loaded images independently.
    Downloading never changes the fresh environment or installs a new provider.
    """
    prepared.verify()
    packages = [
        row
        for row in tomllib.loads(prepared.initial_source_reader.read("uv.lock").content.decode())["package"]
        if row["name"] == "pypdfium2"
    ]
    if len(packages) != 1:
        raise ValueError("native preparation Source lock lacks one exact PDFium declaration")
    declarations = packages[0]["wheels"]
    if nominated is None:
        preference = {tag: ordinal for ordinal, tag in enumerate(sys_tags())}
        compatible = []
        for row in declarations:
            filename = row["url"].rsplit("/", 1)[-1]
            _, _, _, tags = parse_wheel_filename(filename)
            ranks = [preference[tag] for tag in tags if tag in preference]
            if ranks:
                compatible.append((min(ranks), filename, row))
        if not compatible:
            raise ValueError("no Source-listed PDFium wheel supports the actual preparing platform")
        _, filename, row = min(compatible, key=lambda value: (value[0], value[1]))
        nominated = prepared.scratch / filename
        result = run_native_tool_process(
            prepared.evidence,
            str(prepared.python),
            ["-I", "-c", _DOWNLOAD, row["url"], str(nominated)],
            cwd=prepared.scratch,
            env=environment,
            deadline=prepared.deadline,
            purpose="actual-source-pdfium-download",
            preserve_nominated_launcher=True,
        )
        if result["accepted"] is not True or result["original_exit_code"] != 0:
            raise NativeInstalledInvocationFailure(result)
    body = source_file_bytes(nominated)
    exact = [
        row
        for row in declarations
        if row["url"].rsplit("/", 1)[-1] == nominated.name
        and row["hash"] == "sha256:" + hashlib.sha256(body).hexdigest()
        and row["size"] == len(body)
    ]
    if len(exact) != 1 or len(body) > 64 * 1024 * 1024:
        raise ValueError("actual nominated PDFium bytes differ from exact Source filename/hash/size")
    sources = {}
    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        for item in archive.infolist():
            remaining(prepared.deadline)
            if item.filename.endswith(".py") and item.filename.startswith(("pypdfium2/", "pypdfium2_raw/")):
                sources[str(prepared.site / item.filename)] = hashlib.sha256(archive.read(item)).hexdigest()
    if not sources:
        raise ValueError("actual Source-listed PDFium wheel contains no declared Python provider bodies")
    prepared.verify()
    return nominated, (prepared.site / "pypdfium2", prepared.site / "pypdfium2_raw"), sources
