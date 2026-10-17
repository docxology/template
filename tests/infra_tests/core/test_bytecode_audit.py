"""Actual standalone imports and complete trusted-code-field comparison controls."""

from __future__ import annotations

import ast
import hashlib
import os
import stat
import subprocess
import sys
import types
from pathlib import Path

import pytest

from infrastructure.core.bytecode_audit import canonical_code, _read_cache
from infrastructure.core.implementation_custody import bytecode_audit_bootstrap


def test_default_hook_origin_from_actual_aliased_import_executes_audited_source(tmp_path: Path):
    repository = Path(__file__).resolve().parents[3]
    # Hook changes must fail their focused owner before a costly browser run.
    # Check all three independent consumer pins against the actual hook bytes.
    expected_hook = hashlib.sha256((repository / "infrastructure/core/bytecode_audit.py").read_bytes()).hexdigest()
    custody = ast.parse((repository / "infrastructure/reporting/native_format_html_child_custody.py").read_bytes())
    parent_pins = [
        node.value.value
        for node in ast.walk(custody)
        if isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Constant)
        and any(isinstance(target, ast.Name) and target.id == "HOOK_SHA256" for target in node.targets)
    ]
    driver = ast.parse((repository / "infrastructure/reporting/native_format_browser_driver.py").read_bytes())
    startup_pins = [
        comparator.value
        for node in ast.walk(driver)
        if isinstance(node, ast.Compare)
        and isinstance(node.left, ast.Subscript)
        and isinstance(node.left.value, ast.Name)
        and node.left.value.id == "_hook_before"
        and isinstance(node.left.slice, ast.Constant)
        and node.left.slice.value == "sha256"
        for comparator in node.comparators
        if isinstance(comparator, ast.Constant)
    ]
    closing_pins = [
        value.value
        for node in ast.walk(driver)
        if isinstance(node, ast.Dict)
        for key, value in zip(node.keys, node.values, strict=True)
        if isinstance(key, ast.Constant) and key.value == "audit_hook_sha256" and isinstance(value, ast.Constant)
    ]
    assert parent_pins == startup_pins == closing_pins == [expected_hook]
    root = tmp_path.resolve() / "source"
    root.mkdir()
    (root / "domain.py").write_text("VALUE = 42\n")
    prefix = tmp_path.resolve() / "cache"
    prefix.mkdir()
    launch = (
        "import sys\nfrom pathlib import Path\n"
        f"sys.path.insert(0,{str(repository / 'scripts/..')!r})\n"
        "import infrastructure.core.implementation_custody as custody\n"
        "assert '..' in Path(custody.__file__).parts\n"
        "root=Path(sys.argv[1]);prefix=Path(sys.argv[2])\n"
        "bootstrap=custody.bytecode_audit_bootstrap((root,),prefix)\n"
        "exec(bootstrap,globals())\n"
        "sys.path.insert(0,str(root));import domain;assert domain.VALUE==42\n"
        "_audit_scope['verify_executed_source_code'](root,prefix)\n"
        "print('executed-bound-source')\n"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-X", f"pycache_prefix={prefix}", "-c", launch, str(root), str(prefix)],
        cwd=tmp_path.resolve(),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "executed-bound-source"


def test_explicit_hook_path_still_refuses_parent_traversal(tmp_path: Path):
    hook = Path(__file__).resolve().parents[3] / "infrastructure/core/bytecode_audit.py"
    supplied = hook.parent / "../core" / hook.name
    with pytest.raises(ValueError, match="parent traversal"):
        bytecode_audit_bootstrap((tmp_path.resolve(),), None, audit_path=supplied)


@pytest.mark.parametrize(
    "delivery",
    ["timestamp-cache", "unchecked-cache", "forged-timestamp-cache", "forged-unchecked-cache", "direct-exec"],
)
@pytest.mark.parametrize("stale", [False, True], ids=["current-source", "stale-payload"])
def test_actual_public_exec_is_source_checked_before_any_payload(tmp_path: Path, delivery: str, stale: bool) -> None:
    """Genuine imports/direct exec cannot run stale bytes before eventual refusal."""
    root = tmp_path.resolve() / "source"
    root.mkdir()
    source = root / "domain.py"
    current_marker = tmp_path.resolve() / "current-source-executed"
    stale_marker = tmp_path.resolve() / "stale-payload-executed"
    source.write_text(
        "from pathlib import Path\nVALUE = 1\n"
        f"Path({str(current_marker)!r} if VALUE == 1 else {str(stale_marker)!r}).write_text('executed')\n"
    )
    prefix = tmp_path.resolve() / "cache"
    prefix.mkdir()
    bootstrap = bytecode_audit_bootstrap((root,), prefix)
    launch = (
        bootstrap
        + """
import os,py_compile,sys
from pathlib import Path
source=Path(sys.argv[1]); delivery=sys.argv[2]; stale=sys.argv[3]=='stale'
original=source.read_bytes(); metadata=source.stat()
payload=original.replace(b'VALUE = 1',b'VALUE = 9') if stale else original
code=compile(payload,str(source),'exec',dont_inherit=True)
if delivery!='direct-exec':
    source.write_bytes(payload)
    os.utime(source,ns=(metadata.st_atime_ns,metadata.st_mtime_ns))
    mode=(py_compile.PycInvalidationMode.UNCHECKED_HASH if delivery.endswith('unchecked-cache')
          else py_compile.PycInvalidationMode.TIMESTAMP)
    # A genuine native source loader must normalize the untrusted dfile before
    # auditing actual exec; both valid and stale cache payloads exercise this.
    filename='/invented/outside-reviewed-roots.py' if delivery.startswith('forged-') else None
    py_compile.compile(str(source),dfile=filename,doraise=True,invalidation_mode=mode)
    source.write_bytes(original)
    os.utime(source,ns=(metadata.st_atime_ns,metadata.st_mtime_ns))
    sys.path.insert(0,str(source.parent))
    import domain
else:
    exec(code,{'__file__':str(source),'__name__':'__main__'})
_audit_scope['verify_executed_source_code'](source.parent,Path(sys.pycache_prefix))
print('source-bound-before-payload')
"""
    )
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-X",
            f"pycache_prefix={prefix}",
            "-c",
            launch,
            str(source),
            delivery,
            "stale" if stale else "current",
        ],
        cwd=tmp_path.resolve(),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert source.read_text().splitlines()[1] == "VALUE = 1"
    assert not stale_marker.exists(), "stale payload ran before the custody refusal"
    if stale:
        assert result.returncode != 0 and "executed public module differs from current source bytes" in result.stderr
        assert not current_marker.exists()
    else:
        assert result.returncode == 0, result.stderr
        assert current_marker.read_text() == "executed"
        assert result.stdout.strip() == "source-bound-before-payload"


@pytest.mark.parametrize(
    "field,value",
    [
        ("co_stacksize", 100),
        ("co_flags", 0),
        ("co_consts", (None, 99)),
        ("co_names", ("changed",)),
        ("co_varnames", ("changed",)),
        ("co_filename", "different.py"),
        ("co_name", "different"),
        ("co_qualname", "different"),
        ("co_firstlineno", 99),
        ("co_linetable", b""),
        ("co_exceptiontable", b""),
        ("co_code", b"\x97\x00\x64\x00\x53\x00"),
    ],
)
def test_canonical_comparison_preserves_actual_code_fields(field, value):
    source = "def function(value):\n    try:\n        return value + 1\n    except ValueError:\n        return -1\n"
    namespace: dict[str, object] = {}
    exec(compile(source, "actual-source.py", "exec", dont_inherit=True), namespace)
    function = namespace["function"]
    assert isinstance(function, types.FunctionType)
    original = function.__code__
    changed = original.replace(**{field: value})
    assert canonical_code(changed) != canonical_code(original)


def test_standalone_import_nested_code_frozenset_slice_and_removed_module_are_bound(tmp_path: Path):
    root = tmp_path.resolve() / "standalone"
    root.mkdir()
    source = root / "domain.py"
    source.write_text(
        "VALUE = 'abcdef'[1:5:2]\n"
        "def outer(value):\n    def inner():\n        return value in {'alpha','beta'}\n    return inner\n"
    )
    prefix = tmp_path.resolve() / "cache"
    prefix.mkdir()
    bootstrap = bytecode_audit_bootstrap((root,), prefix)
    code = (
        bootstrap + "import sys,runpy;from pathlib import Path;sys.path.insert(0,sys.argv[1]);"
        "import domain;assert domain.VALUE=='bd';assert domain.outer('alpha')();"
        "del sys.modules['domain'];runpy.run_module('domain',run_name='__main__');"
        "_audit_scope['verify_executed_source_code'](Path(sys.argv[1]),Path(sys.pycache_prefix));"
        "registry=sys._template_executed_bytecode_audit;"
        "assert len(registry['snapshot']()[str(Path(sys.argv[1])/'domain.py')])==2;print('passed')"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-X", f"pycache_prefix={prefix}", "-c", code, str(root)],
        cwd=tmp_path.resolve(),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "passed"


def test_canonical_constant_expansion_has_a_finite_work_ceiling():
    original = compile("VALUE = 1\n", "bounded.py", "exec", dont_inherit=True)
    shared = ("x" * 1024,)
    expanded = original.replace(co_consts=(tuple(shared for _ in range(70000)),))
    with pytest.raises(ValueError, match="ceiling"):
        canonical_code(expanded)


@pytest.mark.parametrize("ancestor", ["outer", "inner"])
def test_real_detached_ancestor_during_held_read_is_rejected(tmp_path: Path, ancestor: str):
    root = tmp_path.resolve() / "source"
    leaf = root / "outer/inner/controlled-read.py"
    leaf.parent.mkdir(parents=True)
    leaf.write_bytes(b"ORIGINAL")
    prefix = tmp_path.resolve() / "cache"
    prefix.mkdir()
    code = (
        bytecode_audit_bootstrap((root,), prefix)
        + """
import sys
from pathlib import Path
source = Path(sys.argv[1])
ancestor = source.parents[1] if sys.argv[2] == "outer" else source.parent
changed = False
def rename_real_ancestor(event, arguments):
    global changed
    if event == "open" and arguments[0] == "controlled-read.py" and not changed:
        changed = True
        ancestor.rename(ancestor.parent / "detached")
        source.parent.mkdir(parents=True)
        source.write_bytes(b"REPLACED")
sys.addaudithook(rename_real_ancestor)
try:
    _audit_scope["_read_cache"](source)
except ValueError as error:
    assert "ancestor changed" in str(error), str(error)
else:
    raise AssertionError("detached ancestry was admitted")
assert changed and source.read_bytes() == b"REPLACED"
print("rejected")
"""
    )
    result = subprocess.run(
        [sys.executable, "-I", "-X", f"pycache_prefix={prefix}", "-c", code, str(leaf), ancestor],
        cwd=tmp_path.resolve(),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "rejected"


@pytest.mark.parametrize(
    "change", [None, "before-install", "after-install"], ids=["current", "stale-main", "edited-main"]
)
def test_actual_main_frame_is_seeded_and_checked_before_imports_and_after_execution(tmp_path: Path, change):
    root = tmp_path.resolve() / "standalone"
    root.mkdir()
    main = root / "main.py"
    prefix = tmp_path.resolve() / "cache"
    prefix.mkdir()
    bootstrap = bytecode_audit_bootstrap((root,), prefix, seed_main=True)
    original = (
        bootstrap + "from pathlib import Path\nimport sys\nVALUE = 1\n"
        "if sys.argv[1] == 'after-install':\n"
        "    source = Path(__file__)\n"
        "    source.write_text(source.read_text().replace('VALUE = 1', 'VALUE = 9'))\n"
        "_audit_scope['verify_executed_source_code'](Path(__file__).parent,Path(sys.pycache_prefix))\n"
        "print('bound-main')\n"
    )
    main.write_text(original)
    if change == "before-install":
        # Compile actual main A, change the actual source to B, then execute
        # A as __main__. The seed must reject its consumed CodeType immediately.
        launch = (
            "from pathlib import Path;import sys;"
            "path=Path(sys.argv[1]);source=path.read_bytes();"
            "code=compile(source,str(path),'exec',dont_inherit=True);"
            "path.write_bytes(source.replace(b'VALUE = 1',b'VALUE = 9'));"
            "__file__=str(path);__cached__=None;sys.argv=['main.py','before-install'];exec(code,globals())"
        )
        command = [sys.executable, "-I", "-X", f"pycache_prefix={prefix}", "-c", launch, str(main)]
    else:
        command = [sys.executable, "-I", "-X", f"pycache_prefix={prefix}", str(main), change or "current"]
    result = subprocess.run(command, cwd=tmp_path.resolve(), capture_output=True, text=True, timeout=30)
    if change is None:
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "bound-main"
    else:
        assert result.returncode != 0
        assert ("startup code differs" if change == "before-install" else "module differs") in result.stderr


def test_startup_seed_cannot_admit_an_already_imported_sibling_module(tmp_path: Path):
    root = tmp_path.resolve() / "standalone"
    root.mkdir()
    main = root / "main.py"
    (root / "domain.py").write_text("VALUE = 1\n")
    prefix = tmp_path.resolve() / "cache"
    prefix.mkdir()
    main.write_text(
        "import sys\nsys.path.insert(0,__file__.rsplit('/',1)[0])\nimport domain\n"
        + bytecode_audit_bootstrap((root,), prefix, seed_main=True)
    )
    result = subprocess.run(
        [sys.executable, "-I", "-X", f"pycache_prefix={prefix}", str(main)],
        cwd=tmp_path.resolve(),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0 and "must precede public imports" in result.stderr


@pytest.mark.skipif(os.name != "posix" or os.geteuid() == 0, reason="requires real nonroot POSIX permission checks")
def test_cache_read_traverses_search_only_ancestors_without_listing(tmp_path: Path) -> None:
    ancestor = tmp_path.resolve() / "search-only"
    root = ancestor / "selected"
    root.mkdir(parents=True)
    root.chmod(0o755)
    target = root / "cache.pyc"
    content = b"actual held cache bytes\x00\xff"
    target.write_bytes(content)
    target.chmod(0o600)
    ancestor.chmod(0o111)
    try:
        with pytest.raises(PermissionError):
            list(ancestor.iterdir())
        if hasattr(os, "O_PATH"):
            assert _read_cache(target) == content
        else:
            with pytest.raises(PermissionError):
                _read_cache(target)
        assert stat.S_IMODE(ancestor.stat().st_mode) == 0o111
        assert stat.S_IMODE(root.stat().st_mode) == 0o755
        assert stat.S_IMODE(target.stat().st_mode) == 0o600
    finally:
        ancestor.chmod(0o700)
    assert target.read_bytes() == content
    assert set(ancestor.iterdir()) == {root}
    assert set(root.iterdir()) == {target}
