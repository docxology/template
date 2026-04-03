"""Tests for infrastructure.validation.repo._repo_ast — coverage."""


from infrastructure.validation.repo._repo_ast import (
    _candidate_module_paths,
    _defined_symbols,
    extract_imports,
    verify_import,
)


class TestCandidateModulePaths:
    def test_single_module(self, tmp_path):
        paths = _candidate_module_paths(tmp_path, "mymodule")
        assert tmp_path / "mymodule.py" in paths
        assert tmp_path / "mymodule" / "__init__.py" in paths
        # Single-part module also checks src/ and infrastructure/
        assert tmp_path / "src" / "mymodule.py" in paths
        assert tmp_path / "infrastructure" / "mymodule.py" in paths

    def test_dotted_module(self, tmp_path):
        paths = _candidate_module_paths(tmp_path, "infrastructure.core.exceptions")
        assert tmp_path / "infrastructure" / "core" / "exceptions.py" in paths
        assert tmp_path / "infrastructure" / "core" / "exceptions" / "__init__.py" in paths

    def test_single_module_with_projects(self, tmp_path):
        # Create a projects/foo/src directory
        (tmp_path / "projects" / "foo" / "src").mkdir(parents=True)
        paths = _candidate_module_paths(tmp_path, "mymod")
        src_path = tmp_path / "projects" / "foo" / "src" / "mymod.py"
        assert src_path in paths

    def test_no_duplicates(self, tmp_path):
        paths = _candidate_module_paths(tmp_path, "mod")
        assert len(paths) == len(set(paths))


class TestDefinedSymbols:
    def test_functions_and_classes(self, tmp_path):
        src = tmp_path / "module.py"
        src.write_text("def foo(): pass\ndef bar(): pass\nclass MyClass: pass\n")
        symbols = _defined_symbols(src)
        assert "foo" in symbols
        assert "bar" in symbols
        assert "MyClass" in symbols

    def test_empty_file(self, tmp_path):
        src = tmp_path / "empty.py"
        src.write_text("")
        symbols = _defined_symbols(src)
        assert symbols == set()

    def test_nested_functions(self, tmp_path):
        src = tmp_path / "nested.py"
        src.write_text("def outer():\n    def inner(): pass\n")
        symbols = _defined_symbols(src)
        assert "outer" in symbols
        assert "inner" in symbols


class TestExtractImports:
    def test_basic_imports(self, tmp_path):
        src = tmp_path / "test_file.py"
        src.write_text("import os\nimport sys\nfrom pathlib import Path\n")
        imports = extract_imports(src)
        assert "os" in imports
        assert "sys" in imports
        assert "pathlib" in imports
        assert "Path" in imports["pathlib"]

    def test_from_import_multiple(self, tmp_path):
        src = tmp_path / "test_file.py"
        src.write_text("from os.path import join, exists\n")
        imports = extract_imports(src)
        assert "os.path" in imports
        assert "join" in imports["os.path"]
        assert "exists" in imports["os.path"]

    def test_syntax_error(self, tmp_path):
        src = tmp_path / "bad.py"
        src.write_text("def broken(:\n")
        imports = extract_imports(src)
        assert imports == {}

    def test_file_not_found(self, tmp_path):
        imports = extract_imports(tmp_path / "nonexistent.py")
        assert imports == {}


class TestVerifyImport:
    def test_symbol_found(self, tmp_path):
        mod = tmp_path / "mymod.py"
        mod.write_text("def foo(): pass\ndef bar(): pass\n")
        assert verify_import(tmp_path, "mymod", ["foo", "bar"]) is True

    def test_symbol_not_found(self, tmp_path):
        mod = tmp_path / "mymod.py"
        mod.write_text("def foo(): pass\n")
        assert verify_import(tmp_path, "mymod", ["foo", "missing"]) is False

    def test_module_not_found(self, tmp_path):
        assert verify_import(tmp_path, "nonexistent", ["foo"]) is False

    def test_empty_items(self, tmp_path):
        mod = tmp_path / "mymod.py"
        mod.write_text("x = 1\n")
        assert verify_import(tmp_path, "mymod", []) is True

    def test_syntax_error_in_module(self, tmp_path):
        mod = tmp_path / "badmod.py"
        mod.write_text("def broken(:\n")
        assert verify_import(tmp_path, "badmod", ["broken"]) is False
