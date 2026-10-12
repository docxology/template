"""Independent portable browser source, DOM, pixel and supervised control replay."""

from __future__ import annotations

import hashlib
import math
import re
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from infrastructure.reporting.native_format_html_admitted_source import AdmittedHTMLSource
from collections.abc import Callable

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_format_content_contracts import NativeContentContract
from infrastructure.reporting.native_format_portable_custody import producer_path, validate_executable_observation
from infrastructure.reporting.native_format_html_child_custody import validate_retained_html_child
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader


def _validate_browser_candidate_semantic_witness(viewport: dict[str, Any], observation: dict[str, Any]) -> None:
    """Compare candidate DATA in original order; no native admission is granted."""
    for key in ("findings", "blockers", "status", "source_text_indices", "structure", "metadata"):
        if viewport.get(key) != observation[key]:
            raise ValueError("browser independently recomputed semantic/layout observations differ")


def replay_browser_observation(
    root: Path,
    directory: Path,
    snapshot: ArtifactSnapshot,
    contract: NativeContentContract,
    raw: dict[str, Any],
    reader: SnapshotReader,
    *,
    run_id: str,
    custody: dict[str, str],
    runtime: dict[str, Any],
    control: str | None = None,
    metadata_source: dict[str, Any] | None = None,
    admitted_source: AdmittedHTMLSource | None = None,
    deadline: float | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Reconstruct all source/DOM/glyph-region/pixel/asset and command bindings."""
    from infrastructure.reporting.native_format_acceptance_validation import _file, _tool
    from infrastructure.reporting.native_format_browser_assets import compile_browser_assets
    from infrastructure.reporting.native_format_browser_oracles import (
        BROWSER_SCHEMA,
        BROWSER_POLICY,
        OBSERVER_SCRIPT,
        inspect_browser_dom,
        inspect_browser_pixels,
    )
    from infrastructure.reporting.native_format_acceptance_checks import parse_native_bytes

    if (
        raw.get("schema_version") != BROWSER_SCHEMA
        or raw.get("contract_digest") != contract.digest
        or raw.get("policy_digest") != canonical_digest(BROWSER_POLICY)
        or raw.get("metadata_source_digest") != (metadata_source["digest"] if metadata_source is not None else None)
    ):
        raise ValueError("native browser source/policy identity changed")
    original_deadline = raw.get("deadline_monotonic")
    if (
        not isinstance(original_deadline, (int, float))
        or isinstance(original_deadline, bool)
        or not math.isfinite(original_deadline)
    ):
        raise ValueError("browser omitted original finite deadline")
    if raw.get("fidelity_source_digest") != (
        admitted_source.fidelity["digest"] if admitted_source is not None else None
    ):
        raise ValueError("browser original admitted Source fidelity witness changed")
    if raw.get("source_fidelity") != (None if admitted_source is None else admitted_source.fidelity):
        raise ValueError("browser retained Source fidelity differs from actual independent Source admission")
    if admitted_source is not None and (deadline is None or env is None or metadata_source != admitted_source.metadata):
        raise ValueError("source-bound HTML replay requires caller clock/environment and separate exact config witness")
    if deadline is not None:
        from infrastructure.reporting.native_format_html_source_metadata import remaining_seconds

        remaining_seconds(deadline)
    mirror = directory / "mirror"
    source = mirror / (snapshot.relative if control is None else "admitted.html")
    consumed = _file(raw.get("input"), reader)
    if consumed.path != source or consumed.content != snapshot.content:
        raise ValueError("browser consumed different exact original HTML")
    sdk_reader = SnapshotReader(Path(__file__).absolute().parents[2])
    driver_source = sdk_reader.read("infrastructure/reporting/native_format_browser_driver.py")
    driver = reader.read((directory / "browser-driver.py").relative_to(root).as_posix())
    if driver.content != driver_source.content or raw.get("driver_source_sha256") != driver_source.sha256:
        raise ValueError("browser driver source bytes changed")
    runtime_source = sdk_reader.read("infrastructure/reporting/native_format_browser_runtime.py")
    runtime_copy = reader.read((directory / "native_format_browser_runtime.py").relative_to(root).as_posix())
    if runtime_source.content != runtime_copy.content or raw.get("runtime_source_sha256") != runtime_source.sha256:
        raise ValueError("browser complete runtime observer source changed")
    observer = reader.read((directory / "observer.js").relative_to(root).as_posix())
    observer_script = OBSERVER_SCRIPT
    if admitted_source is not None:
        from infrastructure.reporting.native_format_html_browser_extensions import extend_browser_observer_script

        observer_script = extend_browser_observer_script(observer_script)
    script = observer_script.removeprefix("\n<script>\n").removesuffix("\n</script>\n").encode()
    if (
        observer.content != script
        or raw.get("observer_script_sha256") != hashlib.sha256(observer_script.encode()).hexdigest()
    ):
        raise ValueError("browser observation script changed")
    assets = (
        compile_browser_assets(root, snapshot, reader)
        if control is None
        else {"schema_version": "template-native-browser-assets-v1", "assets": [], "blockers": []}
    )
    if raw.get("asset_contract") != assets:
        raise ValueError("browser source-owned asset closure changed")
    bindings = raw.get("consumed_assets")
    if not isinstance(bindings, list) or len(bindings) != len(assets["assets"]):
        raise ValueError("browser consumed closure is incomplete")
    for item, expected in zip(bindings, assets["assets"], strict=True):
        if item.get("source") != expected:
            raise ValueError("browser consumed asset source identity differs")
        original = _file(expected, reader)
        copy = _file(item.get("consumed"), reader)
        if copy.path != mirror / original.relative or copy.content != original.content:
            raise ValueError("browser asset mirror is not byte-identical")
    cdn = assets.get("cdn_assets", [])
    if cdn:
        import json
        from infrastructure.reporting.native_format_browser_cdn import cdn_member_bytes

        consumed_cdn = raw.get("consumed_cdn")
        if not isinstance(consumed_cdn, list) or len(consumed_cdn) != len(cdn):
            raise ValueError("browser omitted its complete authenticated CDN response closure")
        mapping = {}
        for index, (row, binding) in enumerate(zip(cdn, consumed_cdn, strict=True)):
            member = _file(binding["consumed"], reader)
            if (
                binding["url"] != row["url"]
                or member.path != mirror / f"native-cdn/{index:04d}"
                or member.content != cdn_member_bytes(row, reader)
            ):
                raise ValueError("browser CDN response differs from lock-authenticated archive member")
            mapping[row["url"]] = {"path": member.path.relative_to(mirror).as_posix(), "sha256": member.sha256}
        cdn_map = reader.read((directory / "cdn-map.json").relative_to(root).as_posix())
        if cdn_map.content != json.dumps(mapping, sort_keys=True).encode():
            raise ValueError("browser exact CDN URL mapping differs")
    viewports = raw.get("viewports")
    tools = raw.get("tools")
    if not isinstance(viewports, list) or not isinstance(tools, list) or len(viewports) != 2 or len(tools) != 2:
        raise ValueError("browser omitted complete declared reflow views")
    fresh_viewports: list[dict[str, Any]] = []
    for width, viewport, tool in zip(BROWSER_POLICY["widths_px"], viewports, tools, strict=True):
        result_path = directory / f"browser-result-{width}.json"
        driver_result = _file(viewport.get("driver"), reader)
        if driver_result.path != result_path:
            raise ValueError("browser result belongs to another evidence attempt")
        result = driver_result.json_object()
        args = [
            str(producer_path(custody, root, driver.path)),
            "--chrome",
            result["browser_command"][0],
            "--source",
            str(producer_path(custody, root, source)),
            "--profile",
            str(producer_path(custody, root, directory / f"profile-{width}")),
            "--width",
            str(width),
            "--output",
            str(producer_path(custody, root, result_path)),
            "--deadline",
            str(original_deadline),
            "--observer-script",
            str(producer_path(custody, root, observer.path)),
            "--asset-root",
            str(producer_path(custody, root, mirror)),
        ]
        if admitted_source is not None:
            if deadline is None:
                raise ValueError("source font observer requires caller clock")
            from infrastructure.reporting.native_format_html_font_driver_adapter import replay_html_font_driver

            replay_html_font_driver(root, directory, reader, raw["font_observer"], result, deadline=deadline)
            args.extend(
                [
                    "--platform-font-observer",
                    str(producer_path(custody, root, directory / "native_format_html_platform_font_dom.py")),
                ]
            )
        elif raw.get("font_observer") is not None:
            raise ValueError("unadmitted browser acquired an unexplained font witness")
        if cdn:
            args.extend(["--cdn-map", str(producer_path(custody, root, directory / "cdn-map.json"))])
            expected_responses = {row["url"]: row["sha256"] for row in cdn}
            fulfilled = result.get("fulfilled_cdn")
            if (
                not isinstance(fulfilled, list)
                or not fulfilled
                or any(item.get("sha256") != expected_responses.get(item.get("url")) for item in fulfilled)
            ):
                raise ValueError("actual browser CDN fulfilment differs from authenticated mapped bytes")
        _tool(tool.get("artifact"), reader, run_id, runtime["executable"], f"browser-cdp-{width}", args)
        child_programs = {
            "native_format_browser_driver.py": driver_source.sha256,
            "native_format_browser_runtime.py": runtime_source.sha256,
        }
        if admitted_source is not None:
            child_programs["native_format_html_platform_font_dom.py"] = raw["font_observer"]["source"]["sha256"]
        if deadline is None:
            raise ValueError("HTML copied-driver Source replay needs the original finite reader clock")
        validate_retained_html_child(
            tool.get("artifact"), result, child_programs, reader, custody=custody, deadline=deadline
        )
        if (
            tool.get("exit_code") != 0
            or tool.get("original_exit_code") != 0
            or result.get("browser_original_exit") != 0
        ):
            raise ValueError("browser did not preserve successful original native exits")
        executable = result["browser_command"][0]
        expected_command = [
            executable,
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            "--disable-background-networking",
            "--disable-extensions",
            "--disable-sync",
            "--remote-debugging-port=0",
            "--proxy-server=http://127.0.0.1:9",
            "--proxy-bypass-list=127.0.0.1",
            f"--user-data-dir={producer_path(custody, root, directory / f'profile-{width}')}",
            "about:blank",
        ]
        if result["browser_command"] != expected_command or not isinstance(result.get("browser_version"), dict):
            raise ValueError("browser isolated profile/native version observation changed")
        for key in ("executable_observation_before", "executable_observation_after"):
            validate_executable_observation(result.get(key), executable, result.get("browser_sha256"))
        from infrastructure.reporting.native_format_browser_runtime import validate_runtime

        if result.get("runtime_observer_sha256") != runtime_source.sha256:
            raise ValueError("browser executed different runtime observer source bytes")
        before = result.get("runtime_observation_before")
        after = result.get("runtime_observation_after")
        if before != after or not isinstance(before, dict):
            raise ValueError("browser complete original application runtime changed")
        validate_runtime(before, executable, result["browser_sha256"])
        origin = result.get("asset_origin")
        if not isinstance(origin, str) or not re.fullmatch(r"http://127\.0\.0\.1:[1-9][0-9]{0,4}", origin):
            raise ValueError("browser server is not its own ephemeral loopback origin")
        if viewport.get("dom") != result.get("dom") or result["dom"].get("width") != width:
            raise ValueError("browser actual DOM viewport changed")
        pixels = _file({key: viewport["screenshot"][key] for key in ("path", "sha256")}, reader)
        if pixels.path != result_path.with_suffix(".png") or pixels.sha256 != result.get("screenshot_sha256"):
            raise ValueError("browser complete actual screenshot changed")
        dimensions = parse_native_bytes("png", pixels.content)
        if viewport["screenshot"] != {"path": pixels.relative, "sha256": pixels.sha256, **dimensions}:
            raise ValueError("browser screenshot metadata differs from original native bytes")
        if dimensions["width_px"] != width or dimensions["height_px"] < result["dom"]["height"]:
            raise ValueError("browser screenshot omits native page geometry")
        observation = inspect_browser_dom(result["dom"], contract, metadata_source)
        localized = inspect_browser_pixels(result["dom"], pixels.content, observation["source_text_indices"])
        from infrastructure.reporting.native_format_browser_figures import inspect_browser_figures

        figures = inspect_browser_figures(
            result["dom"], pixels.content, contract, snapshot if control is None else None, reader
        )
        if viewport.get("figures") != figures:
            raise ValueError("independent source/native/rendered figure pixels differ")
        observation["findings"].extend(figures["findings"])
        observation["blockers"].extend(figures["blockers"])
        observation["findings"].extend(localized["findings"])
        observation["blockers"].extend(localized["blockers"])
        fidelity = None
        if admitted_source is not None:
            if deadline is None or env is None:
                raise ValueError("HTML fidelity reader requires original caller clock/environment")
            from infrastructure.reporting.native_format_html_fidelity_observer import replay_html_fidelity
            from infrastructure.reporting.native_format_observer_dispatch import _chrome

            fidelity = replay_html_fidelity(
                root,
                directory / f"fidelity-{width}",
                admitted_source,
                result["dom"],
                pixels.content,
                snapshot,
                viewport["fidelity"],
                reader,
                run_id=run_id,
                custody=custody,
                runtime=runtime,
                env=env,
                deadline=deadline,
                original_deadline=original_deadline,
                chrome=_chrome(env),
            )
            observation["findings"].extend(fidelity["findings"])
            observation["blockers"].extend(fidelity["blockers"])
        elif "fidelity" in viewport:
            raise ValueError("browser fidelity observation has no admitted original source context")
        observation["status"] = (
            "fail" if observation["findings"] else "blocked" if observation["blockers"] else observation["status"]
        )
        _validate_browser_candidate_semantic_witness(viewport, observation)
        if viewport.get("pixels") != localized:
            raise ValueError("browser independently recomputed localized pixels differ")
        fresh_viewports.append(
            {
                **observation,
                "width": width,
                "pixels": localized,
                "figures": figures,
                "fidelity": fidelity,
            }
        )
    if raw.get("blockers") != sorted(
        set([*contract.blockers, *assets["blockers"], *(b for v in viewports for b in v["blockers"])])
    ):
        raise ValueError("browser unsupported source/asset obligations changed")
    expected_status = "fail" if any(v["findings"] for v in viewports) else "blocked" if raw["blockers"] else "pass"
    if raw.get("status") != expected_status:
        raise ValueError("browser aggregate source/native gate outcome differs")
    if not sdk_reader.unchanged():
        raise ValueError("current reader SDK source changed during replay")
    if admitted_source is not None:
        if deadline is None:
            raise ValueError("HTML source closing requires original caller clock")
        admitted_source.close(root, reader, deadline=deadline)
    if deadline is not None:
        remaining_seconds(deadline)
    return {
        "status": expected_status,
        "findings": [f for v in fresh_viewports for f in v["findings"]],
        "blockers": sorted(
            set([*contract.blockers, *assets["blockers"], *(b for v in fresh_viewports for b in v["blockers"])])
        ),
        "viewports": fresh_viewports,
        "asset_contract": assets,
        "source_fidelity": None if admitted_source is None else admitted_source.fidelity,
        "source_metadata": metadata_source,
    }


def replay_browser_controls(
    root: Path,
    directory: Path,
    records: list[dict[str, Any]],
    reader: SnapshotReader,
    *,
    run_id: str,
    custody: dict[str, str],
    runtime: dict[str, Any],
    semantic: bool = False,
    deadline: float | None = None,
    env: dict[str, str] | None = None,
    scope: str | None = None,
) -> dict[str, Any]:
    """Require real supervised control outcomes and independently replay their pixels."""
    from infrastructure.reporting.native_format_html_source_metadata import remaining_seconds

    if deadline is None:
        raise ValueError("browser control replay requires the original caller's finite clock")
    remaining_seconds(deadline)
    from infrastructure.reporting.native_format_acceptance_validation import _file
    from infrastructure.reporting.native_format_browser_oracles import (
        BROWSER_CONTROL_CODES,
        browser_control_bytes,
        browser_control_contract,
        require_browser_control_result,
    )
    from infrastructure.reporting.native_format_joint_source import require_native_operation
    from infrastructure.reporting.native_print_child_custody import (
        BasicBrowserControlReaderOperation,
        SemanticBrowserControlReaderOperation,
    )

    if scope is None:
        raise ValueError("browser controls require the genuine enclosing public scope")
    operation = require_native_operation(reader)
    role = SemanticBrowserControlReaderOperation if semantic else BasicBrowserControlReaderOperation
    context = role(operation.source, reader, records, scope=scope, run_id=run_id, deadline=deadline)
    parent_reader = reader
    reader = SnapshotReader(root, native_operation=operation, native_control_operation=context)

    require_result: Callable[[str, dict[str, Any]], int]
    if semantic:
        from infrastructure.reporting.native_format_browser_semantic_controls import (
            SEMANTIC_CONTROL_CODES,
            require_semantic_control_result,
        )

        names, require_result, prefix = SEMANTIC_CONTROL_CODES, require_semantic_control_result, "browser-semantic"
    else:
        names, require_result, prefix = BROWSER_CONTROL_CODES, require_browser_control_result, "browser-control"
    if [item.get("name") for item in records] != list(names):
        raise ValueError("browser negative-control suite is incomplete or reordered")
    outcomes: list[dict[str, Any]] = []
    for item in records:
        remaining_seconds(deadline)
        name = item["name"]
        leaf = directory / f"{prefix}-{name}"
        context.child(item, reader)
        result = _file(item.get("artifact"), reader)
        if result.path != leaf / "control-observation.json":
            raise ValueError("browser control belongs to another supervision attempt")
        raw = result.json_object()
        if (
            raw.get("schema_version")
            != (
                "template-native-browser-semantic-control-v1"
                if semantic
                else "template-native-browser-valid-control-v1"
            )
            or raw.get("name") != name
            or raw.get("run_id") != run_id
        ):
            raise ValueError("browser control source/run identity changed")
        if semantic:
            from infrastructure.reporting.native_format_browser_semantic_replay import replay_semantic_control

            if deadline is None or env is None:
                raise ValueError("semantic controls require bounded actual reader parser")
            replay_semantic_control(
                root, leaf, raw, reader, run_id=run_id, custody=custody, runtime=runtime, deadline=deadline, env=env
            )
        else:
            source = _file(raw["observation"].get("input"), reader)
            if source.content != browser_control_bytes(name):
                raise ValueError("browser mutant differs from independently reconstructed source")
            replay_browser_observation(
                root,
                leaf,
                source,
                browser_control_contract(),
                raw["observation"],
                reader,
                run_id=run_id,
                custody=custody,
                runtime=runtime,
                control=name,
                deadline=deadline,
                env=env,
            )
        code = require_result(name, raw["observation"])
        if raw.get("oracle_exit_code") != code or item.get("original_exit_code") != code:
            raise ValueError("browser control did not preserve its actual original oracle exit")
        outcomes.append(
            {
                "name": name,
                "original_exit_code": item["original_exit_code"],
                "reconstructed_exit_code": code,
                "intended_diagnostic": names[name],
                "targets": [{"fixture": prefix, "name": name}],
                "artifact": item["artifact"],
            }
        )
        remaining_seconds(deadline)
    if not reader.unchanged() or not parent_reader.unchanged():
        raise ValueError("browser original child Source/native evidence changed during independent replay")
    operation.verify(parent_reader)
    remaining_seconds(deadline)
    return {
        "suite_id": "html_semantic" if semantic else "html",
        "scope": scope,
        "original_run_id": run_id,
        "outcomes": outcomes,
    }
