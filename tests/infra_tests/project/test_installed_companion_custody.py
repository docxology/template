"""Real wheel/package custody keeps same-basename companions distinct."""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

from infrastructure.core.implementation_custody import bytecode_audit_bootstrap
from infrastructure.project.installed_acceptance_validation import _custody_matches_wheel
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

ROOT = Path(__file__).resolve().parents[3]
SCOPE = "templates/template_autopoiesis"


def _installed_companion(tmp_path: Path) -> tuple[Path, Path, dict[str, str], dict]:
    root = tmp_path / "repository"
    source = root / "projects" / SCOPE / "src"
    members = {
        "__init__.py": b'"""Authored top-level companion."""\n',
        "template_autopoiesis/__init__.py": b"VALUE = 17\n",
        "template_autopoiesis/engine.py": b"def measured():\n    return 19\n",
    }
    for name, raw in members.items():
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    metadata = "template_autopoiesis-2.0.0.dist-info"
    members[f"{metadata}/METADATA"] = b"Metadata-Version: 2.3\nName: template-autopoiesis\nVersion: 2.0.0\n"
    members[f"{metadata}/WHEEL"] = b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n"
    record = io.StringIO()
    writer = csv.writer(record)
    for name, raw in members.items():
        encoded = base64.urlsafe_b64encode(hashlib.sha256(raw).digest()).decode().rstrip("=")
        writer.writerow([name, "sha256=" + encoded, str(len(raw))])
    writer.writerow([f"{metadata}/RECORD", "", ""])
    members[f"{metadata}/RECORD"] = record.getvalue().encode()
    wheel = root / "output/readiness/companion.whl"
    wheel.parent.mkdir(parents=True)
    with zipfile.ZipFile(wheel, "w") as archive:
        for name, raw in members.items():
            archive.writestr(name, raw)
    # Materialize the exact admitted wheel members in an owned target install.
    site = tmp_path / "installed"
    with zipfile.ZipFile(wheel) as archive:
        for name in members:
            path = site / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(archive.read(name))
    prefix = tmp_path / "fresh-bytecode"
    prefix.mkdir()
    bootstrap = bytecode_audit_bootstrap((ROOT / "infrastructure", site / "template_autopoiesis"), prefix)
    code = bootstrap + (
        f"import sys;sys.path[:0]=[{str(site)!r},{str(ROOT)!r}];"
        "import json,template_autopoiesis;from pathlib import Path;"
        "assert template_autopoiesis.VALUE==17;"
        "from infrastructure.core.implementation_custody import capture_dependency_custody;"
        "print(json.dumps(capture_dependency_custody('template-autopoiesis',"
        "Path(template_autopoiesis.__file__).parent,"
        f"fresh_pycache_prefix=Path({str(prefix)!r}),public_modules=frozenset({{'__init__'}}))))"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-X", f"pycache_prefix={prefix}", "-c", code],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    binding = {"path": wheel.relative_to(root).as_posix(), "sha256": hashlib.sha256(wheel.read_bytes()).hexdigest()}
    return root, site, binding, json.loads(result.stdout)


@pytest.mark.parametrize(
    "fault",
    [None, "absent", "invented", "hash", "renamed", "undeclared", "file-hash", "record-size", "package-omitted"],
)
def test_real_installed_companion_union_requires_every_wheel_and_record_byte(tmp_path: Path, fault: str | None) -> None:
    root, _site, binding, custody = _installed_companion(tmp_path)
    distribution = custody["distribution"]
    package = distribution["public_python"]
    companions = distribution["companion_python"]
    assert custody["files"] == package
    assert set(package) == {"__init__.py", "engine.py"}
    assert set(companions) == {"__init__.py"}
    assert companions["__init__.py"] != package["__init__.py"]
    if fault == "absent":
        distribution.pop("companion_python")
    elif fault == "invented":
        companions["invented.py"] = "0" * 64
    elif fault == "hash":
        companions["__init__.py"] = package["__init__.py"]
    elif fault == "renamed":
        companions["template_autopoiesis/__init__.py"] = companions.pop("__init__.py")
    elif fault == "undeclared":
        distribution["declared_files"].pop("__init__.py")
    elif fault == "file-hash":
        distribution["file_sha256"]["__init__.py"] = "0" * 64
    elif fault == "record-size":
        distribution["declared_files"]["__init__.py"][1] = "999"
    elif fault == "package-omitted":
        package.pop("engine.py")
    if fault is None:
        _custody_matches_wheel(custody, binding, SCOPE, SnapshotReader(root))
    else:
        with pytest.raises(ValueError, match="companion|omits its actual wheel source"):
            _custody_matches_wheel(custody, binding, SCOPE, SnapshotReader(root))


def test_actual_installed_companion_mutation_is_rejected_before_inventory(tmp_path: Path) -> None:
    _root, site, _binding, _custody = _installed_companion(tmp_path)
    (site / "__init__.py").write_text("CHANGED = True\n")
    code = (
        f"import sys;sys.path[:0]=[{str(site)!r},{str(ROOT)!r}];"
        "import template_autopoiesis;from pathlib import Path;"
        "from infrastructure.core.implementation_custody import capture_dependency_custody;"
        "capture_dependency_custody('template-autopoiesis',Path(template_autopoiesis.__file__).parent,"
        "public_modules=frozenset({'__init__'}))"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", code], cwd=tmp_path, capture_output=True, text=True, timeout=30, check=False
    )
    assert result.returncode != 0
    assert "differs from its declared RECORD" in result.stderr
