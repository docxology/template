"""Retain the one selected EPUBCheck bundle in the separate Current root.

Existing Source functions bind the actual nominated Java/JAR closure and freeze
its exact bytes. This is bounded input preparation, never native execution or
Original/Current owner construction. Original evidence stays read-only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_epub_observer import bind_epubcheck_engine, freeze_epubcheck_bundle
from infrastructure.reporting.native_format_acceptance_contracts import validate_native_specification
from infrastructure.reporting.native_epub_replay import replay_epub_conversion
from infrastructure.reporting.native_format_joint_source import (
    bound_input,
    require_native_operation,
    validate_original_joint_launch,
)
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.native_tool_replay import validate_original_native_tool
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def _validate_current_engine_equivalence(original: dict[str, Any], current: dict[str, Any]) -> None:
    """Compare the complete bound closure, allowing physical parent relocation.

    Inputs must come from the existing authenticated Original conversion and
    actual Current binder/replay. This predicate does not construct a native
    owner or grant execution, consuming-role, control or scientific acceptance.
    The exact ordered category/relative-path/body/size roster and selected main
    JAR name stay unchanged. Original absolute paths remain command labels.
    """
    fields = {"schema_version", "java", "jar", "files"}
    if (
        set(original) != fields
        or set(current) != fields
        or original["schema_version"] != "template-native-epubcheck-engine-v1"
        or current["schema_version"] != original["schema_version"]
        or not original["files"]
        or current["files"] != original["files"]
        or Path(current["jar"]).name != Path(original["jar"]).name
    ):
        raise ValueError("Current EPUB engine differs from the complete authenticated Original Java/JAR closure")
    for engine in (original, current):
        for name in ("java", "jar"):
            label = engine[name]
            if not isinstance(label, str):
                raise ValueError("EPUB engine physical nominations must be canonical absolute labels")
            path = Path(label)
            if not path.is_absolute() or ".." in path.parts or str(path) != label:
                raise ValueError("EPUB engine physical nominations must be canonical absolute labels")
        if Path(engine["java"]).name != "java" or Path(engine["java"]).parent.name != "bin":
            raise ValueError("Current EPUB relocation must retain the actual runtime bin/java selection")


def _validate_current_calibre_equivalence(original: dict[str, Any], current: dict[str, Any]) -> None:
    """Compare complete independently authenticated reader closures as DATA.

    Linux package paths remain exact across hosts; only physical metadata may
    differ. Darwin keeps its complete app-relative member/body/alias semantics.
    This check supplies no native loader/descendant or fidelity acceptance.
    """
    if original["schema_version"] != current["schema_version"]:
        raise ValueError("Current Calibre runtime platform/profile differs from authenticated Original")
    if original["schema_version"] == "template-native-linux-calibre-package-runtime-v1":
        from infrastructure.project.native_linux_calibre_custody import linux_calibre_body_projection

        if linux_calibre_body_projection(original) != linux_calibre_body_projection(current):
            raise ValueError("Current Calibre complete selected package bodies/roles differ from Original")
        return
    if original["schema_version"] != "template-native-reader-runtime-v1":
        raise ValueError("Current Calibre runtime profile is unknown")

    def projection(raw: dict[str, Any]) -> dict[str, Any]:
        rows = []
        for row in raw["files"]:
            selected = {k: v for k, v in row.items() if k != "metadata"}
            if row["kind"] == "file":
                selected["bytes"] = row["metadata"]["size"]
            elif row["kind"] == "alias" and Path(row["label"]).is_absolute():
                selected["label"] = "app-relative:" + Path(row["label"]).relative_to(raw["root"]).as_posix()
            rows.append(selected)
        return {
            "schema_version": raw["schema_version"],
            "consumed_members": raw["consumed_members"],
            "executable": Path(raw["executable"]).relative_to(raw["root"]).as_posix(),
            "files": rows,
        }

    if projection(original) != projection(current):
        raise ValueError("Current Calibre complete app-relative member bodies differ from Original")


def _replay_original_epub_conversion(
    scope: str, conversion: dict[str, Any], original_reader: SnapshotReader
) -> dict[str, Any]:
    """Use the existing genuine Original reader and exact command authenticator."""
    operation = require_native_operation(original_reader)
    original = operation.originals.get(scope)
    if original is None:
        raise ValueError("Current EPUB equivalence lacks its externally held Original scope")
    specification_file = original_reader.read(original.specification_relative)
    specification = specification_file.json_object()
    validate_native_specification(specification)
    _, descriptor = validate_original_joint_launch(
        specification,
        specification_file,
        original_reader.read(original.process_relative),
        original_reader.read(original.closure_relative),
        original_reader,
        operation,
    )
    producer_root = Path(descriptor["current_mirror"]["root"])
    result = replay_epub_conversion(
        conversion,
        bound_input(original_reader, conversion["input"]).content,
        read_artifact=lambda binding: bound_input(original_reader, binding).content,
        authenticate_tool=lambda binding, tool: validate_original_native_tool(
            binding, tool, original_reader, run_id=original.run_id
        ),
        producer_path=lambda relative: str(producer_root / relative),
        run_id=original.run_id,
    )
    operation.verify(original_reader)
    if not original_reader.unchanged():
        raise ValueError("authenticated Original EPUB closure changed during Current equivalence")
    remaining(operation.deadline)
    return result


def validate_current_epub_conversion_equivalence(
    scope: str,
    original_conversion: dict[str, Any],
    current_conversion: dict[str, Any],
    original_reader: SnapshotReader,
    current_reader: SnapshotReader,
) -> None:
    """Check fresh actual Current commands and the complete Original body closure.

    Both conversion replays authenticate all five existing Java/EPUBCheck/native
    reader commands and signed OS outcomes. Current tools must already belong
    to the actual live Current owner. No process, suite, clock or owner is added.
    """
    operation = require_native_operation(original_reader)
    owner = current_native_producer_operation()
    if (
        owner is None
        or current_reader.native_producer_operation is not owner
        or owner.source.bindings.current_root != current_reader.root
        or current_reader.root == original_reader.root
        or owner.deadline != operation.deadline
    ):
        raise ValueError("Current EPUB replay requires the genuine separate live Current Source/clock owner")
    owner.verify(current_reader, run_id=owner.run_id, deadline=operation.deadline)
    original = _replay_original_epub_conversion(scope, original_conversion, original_reader)
    current = replay_epub_conversion(
        current_conversion,
        bound_input(current_reader, current_conversion["input"]).content,
        read_artifact=lambda binding: bound_input(current_reader, binding).content,
        authenticate_tool=lambda binding, tool: owner.validate_tool(binding, tool, current_reader, run_id=owner.run_id),
        producer_path=lambda relative: str(current_reader.root / relative),
        run_id=owner.run_id,
    )
    _validate_current_engine_equivalence(original["engine"], current["engine"])
    _validate_current_calibre_equivalence(original["reader_runtime"], current["reader_runtime"])
    owner.verify(current_reader, run_id=owner.run_id, deadline=operation.deadline)
    operation.verify(original_reader)
    if not original_reader.unchanged() or not current_reader.unchanged():
        raise ValueError("Original/Current EPUB conversion changed during exact native equivalence")
    remaining(operation.deadline)


def prepare_current_epub_observer_tools(
    scope: str,
    original_reader: SnapshotReader,
    current_source: NativeSourceContext,
    *,
    epubcheck_jar: Path | None,
    java_executable: Path | None,
) -> dict[str, Path | None]:
    """Prepare once before Current Core; real observers later execute the engine.

    Nominees come from the existing caller, never from opening a producer path
    named in JSON. The externally bound specification checks paired selection/absence;
    a fresh complete physical engine binding checks every retained JAR and Java
    runtime member again. No success/control/axis claim is returned.
    """
    operation = require_native_operation(original_reader)
    original = operation.originals.get(scope)
    if (
        original is None
        or current_native_producer_operation() is not None
        or not isinstance(current_source, NativeSourceContext)
        or current_source.bindings.current_root == original_reader.root
        or current_source.bindings.current_root.is_relative_to(original_reader.root)
        or original_reader.root.is_relative_to(current_source.bindings.current_root)
        or current_source.bindings.current_root_identity == operation.source.bindings.current_root_identity
        or current_source.reference.commit != operation.source.reference.commit
        or current_source.reference.source_identity != operation.source.reference.source_identity
        or current_source.bindings.expected_implementation_bytes
        != operation.source.bindings.expected_implementation_bytes
    ):
        raise ValueError("Current EPUB inputs require the actual separately admitted Source and held Original")
    deadline, root = operation.deadline, current_source.bindings.current_root
    remaining(deadline)
    current_reader = SnapshotReader(root)
    current_source.verify_correspondence(current_source.reference, root, current_reader, deadline)
    spec_file = original_reader.read(original.specification_relative)
    if spec_file.sha256 != original.specification_sha256:
        raise ValueError("Current EPUB preparation changed its externally held Original spec")
    spec = spec_file.json_object()
    validate_native_specification(spec)
    if spec["scope"] != scope or spec["run_id"] != original.run_id:
        raise ValueError("Current EPUB input selection belongs to a different Original")
    if "epub" not in spec["formats"]:
        raise ValueError("Current EPUB preparation requires an explicitly selected completed EPUB Original scope")
    selected = spec.get("observer_tools", {"epubcheck_jar": None, "java_executable": None, "frozen_epub_engine": None})
    for name, nominee in (("epubcheck_jar", epubcheck_jar), ("java_executable", java_executable)):
        if (
            nominee is not None
            and (not isinstance(nominee, Path) or not nominee.is_absolute() or ".." in nominee.parts)
        ) or (nominee is None) != (selected[name] is None):
            raise ValueError("Current EPUB nominees must preserve the pinned pair/absence and actual caller Paths")
    frozen_label = selected["frozen_epub_engine"]
    result = {
        "epubcheck_jar": epubcheck_jar,
        "java_executable": java_executable,
        "frozen_epub_engine": None if frozen_label is None else root / frozen_label,
    }
    if frozen_label is None:
        # Preserve genuine absent/unshared selection. The real observer's
        # existing missing-engine refusal or per-observation freeze still runs.
        current_source.verify_correspondence(current_source.reference, root, current_reader, deadline)
        operation.verify(original_reader)
        if not original_reader.unchanged() or not current_reader.unchanged():
            raise ValueError("Original/Current EPUB input selection changed during unshared preparation")
        remaining(deadline)
        return result
    if epubcheck_jar is None or java_executable is None or Path(frozen_label).name != "epubcheck-engine":
        raise ValueError("selected shared EPUB engine lacks the complete Source caller nominees")
    execution = original_reader.read(original.native_execution_relative)
    if execution.sha256 != original.native_execution_sha256:
        raise ValueError("Original EPUB engine DATA changed before Current preparation")
    raw = execution.json_object()
    if raw["scope"] != scope or raw["run_id"] != original.run_id:
        raise ValueError("Original EPUB engine DATA belongs to a different original launch")
    rows = [row for row in raw["artifacts"] if row["id"] == "manuscript:epub" and row["format"] == "epub"]
    if len(rows) != 1:
        raise ValueError("shared Current EPUB engine requires its complete actual Original EPUB observation")
    native = rows[0]["native_observer"]["office_complete_source"]["native"]
    conversions = [
        _replay_original_epub_conversion(scope, native[name]["conversion"], original_reader)
        for name in ("reference", "candidate")
    ]
    engine = bind_epubcheck_engine(epubcheck_jar, java_executable, deadline=deadline)
    bundle_rows = [row for row in engine["files"] if row["category"] == "epubcheck-bundle"]
    bindings = [{"path": (Path(frozen_label) / row["path"]).as_posix(), "sha256": row["sha256"]} for row in bundle_rows]
    if not bindings:
        raise ValueError("Current EPUB engine has no complete actual JAR closure")
    for conversion in conversions:
        _validate_current_engine_equivalence(conversion["engine"], engine)
        if conversion["consumed_jars"] != bindings:
            raise ValueError("fresh complete Current JAR inventory differs from the Original consumed engine")
    for binding, row in zip(bindings, bundle_rows, strict=True):
        held = original_reader.read(binding["path"])
        if held.sha256 != binding["sha256"] or len(held.content) != row["bytes"]:
            raise ValueError("Original frozen EPUBCheck JAR changed before Current input preparation")
    destination = root / frozen_label
    if destination.exists() or destination.is_symlink():
        raise ValueError("Current shared EPUB input preparation requires its one fresh target")
    current_jar = freeze_epubcheck_bundle(root, destination.parent, engine, deadline=deadline)
    if current_jar.parent != destination or current_jar.name != Path(engine["jar"]).name:
        raise ValueError("Current EPUB Source freezer changed its exact selected target")
    for binding, row in zip(bindings, bundle_rows, strict=True):
        copied = current_reader.read(binding["path"])
        held = original_reader.read(binding["path"])
        if copied.content != held.content or copied.sha256 != row["sha256"] or len(copied.content) != row["bytes"]:
            raise ValueError("Current shared EPUBCheck DATA differs from its admitted exact original bytes")
    if engine != bind_epubcheck_engine(epubcheck_jar, java_executable, deadline=deadline):
        raise ValueError("actual selected Java/JAR closure changed during Current input retention")
    if not original_reader.unchanged() or not current_reader.unchanged():
        raise ValueError("Original/Current EPUB engine DATA changed during its single preparation")
    current_source.verify_correspondence(current_source.reference, root, current_reader, deadline)
    operation.verify(original_reader)
    remaining(deadline)
    return result
