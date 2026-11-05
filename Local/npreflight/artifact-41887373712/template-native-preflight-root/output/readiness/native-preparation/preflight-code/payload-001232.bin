"""Classify actual selected lineage; universal coverage limits remain advisory.

These functions retain checked DATA from the existing Source graph/domain
callers. They create no owner, clock, native result or scientific predicate.
An unsupported consumed occurrence or generated role remains a precise residual.
"""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_analysis_boundary_replay import REMAINING as ANALYSIS_LIMITS
from infrastructure.reporting.native_hydration_reconstruction import REMAINING as HYDRATION_LIMITS
from infrastructure.reporting.native_project_domain import REMAINING as DOMAIN_LIMITS
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

__all__ = [
    "classify_selected_native_lineage",
    "observe_selected_native_lineage",
    "selected_lineage_residuals",
    "selected_asset_lineage_residuals",
    "collect_code_figure_domains",
    "selected_value_lineage_residuals",
]

SCHEMA = "template-native-selected-lineage-facts-v1"
CODE_SCOPE = "templates/template_code_project"


def _digest(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _binding(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {"path", "sha256", "bytes"}:
        raise ValueError("selected lineage requires the actual complete held body binding")
    path = value["path"]
    if (
        not isinstance(path, str)
        or not path
        or PurePosixPath(path).is_absolute()
        or ".." in PurePosixPath(path).parts
        or PurePosixPath(path).as_posix() != path
        or not _digest(value["sha256"])
        or type(value["bytes"]) is not int
        or value["bytes"] < 0
    ):
        raise ValueError("selected lineage body binding is malformed or escapes Source")
    return value


def _reasons(value: object) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(row, str) or not row for row in value):
        raise ValueError("selected lineage requires explicit actual residuals")
    return value


def _graph(value: dict[str, Any], schema: str) -> None:
    if (
        not isinstance(value, dict)
        or value.get("schema_version") != schema
        or not isinstance(value.get("scope"), str)
        or not value["scope"]
        or not isinstance(value.get("pipeline_run_id"), str)
        or not value["pipeline_run_id"]
        or not _digest(value.get("plan_digest"))
        or not isinstance(value.get("source_binding"), list)
        or len(value["source_binding"]) != 2
        or any(not isinstance(item, str) or not item for item in value["source_binding"])
        or value.get("content_digest")
        != canonical_digest({key: item for key, item in value.items() if key != "content_digest"})
    ):
        raise ValueError("selected lineage changed its checked Source/Core graph identity")
    _reasons(value.get("unresolved_edges"))


def _occurrences(hydration: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    rows = hydration.get("ordered_inputs")
    if not isinstance(rows, list) or not rows or len(rows) > 1000:
        raise ValueError("selected lineage omitted the complete actual consumed manuscript roster")
    selected: list[dict[str, Any]] = []
    residuals: list[str] = []
    for ordinal, row in enumerate(rows, 1):
        if not isinstance(row, dict) or row.get("ordinal") != ordinal:
            raise ValueError("selected lineage changed the actual consumed manuscript order")
        consumed = _binding(row.get("consumed"))
        transformation = row.get("transformation")
        if transformation == "exact-authored-source-body":
            source = _binding(row.get("source"))
            if (source["sha256"], source["bytes"]) != (consumed["sha256"], consumed["bytes"]):
                raise ValueError("exact authored Source row no longer contains its actual Source bytes")
            continue
        if transformation != "shared-uppercase-token-hydration":
            if transformation == "Source-generated-transmission-boundary":
                bookend = row.get("bookend")
                boundary = None
                project = PurePosixPath("projects") / hydration["scope"]
                for name, kind in (("00_00_transmission_begin.md", "begin"), ("99_zz_transmission_end.md", "end")):
                    if PurePosixPath(consumed["path"]) in {
                        project / parent / name for parent in ("manuscript", "output/manuscript", "docs/manuscript")
                    }:
                        boundary = kind
                if not isinstance(bookend, dict) or boundary is None:
                    raise ValueError("checked transmission text changed its exact Source-selected path")
                config = _binding(bookend.get("config"))
                ledger = bookend.get("ledger")
                if ledger is not None:
                    _binding(ledger)
                if (
                    bookend.get("algorithm") != "Source-transmission-config-ledger-context-and-boundary-v1"
                    or bookend.get("boundary") != boundary
                    or bookend.get("output_sha256") != consumed["sha256"]
                    or bookend.get("publication_history_is_data") is not True
                    or PurePosixPath(config["path"])
                    not in {
                        project / parent / "config.yaml"
                        for parent in ("manuscript", "output/manuscript", "docs/manuscript")
                    }
                    or ledger is not None
                    and ledger["path"] != (project / "output/data/publication_ledger.json").as_posix()
                ):
                    raise ValueError("checked transmission text lost its complete config/ledger/boundary binding")
                # The genuine enclosing reconstruction compared all produced
                # bytes and closing absence/history inputs. Only that text
                # edge is closed; pairing images/history residuals stay below.
                continue
            # A custom writer, transmission boundary or unclassified fragment
            # is an actual selected role. Its byte match is not domain proof.
            custom = row.get("project_hydration")
            authored_source = row.get("source")
            if (
                transformation == "Source-selected-project-authored-hydration"
                and hydration["scope"] == "templates/template_template"
                and isinstance(custom, dict)
                and custom.get("algorithm") == "Source-template-ancillary-verbatim-v1"
            ):
                authored = _binding(authored_source)
                if (authored["sha256"], authored["bytes"]) != (consumed["sha256"], consumed["bytes"]):
                    raise ValueError("Source ancillary verbatim row changed its actual authored bytes")
                continue
            residuals.append("selected-generated-fragment-lineage:" + consumed["path"])
            continue
        source = _binding(row.get("source"))
        mapping = row.get("hydration")
        tokens = mapping.get("occurrences") if isinstance(mapping, dict) else None
        if not isinstance(tokens, list) or len(tokens) > 10000:
            raise ValueError("selected lineage omitted the complete actual hydration occurrence roster")
        for position, token in enumerate(tokens, 1):
            if (
                not isinstance(token, dict)
                or token.get("ordinal") != position
                or not isinstance(token.get("key"), str)
                or not token["key"]
                or type(token.get("resolved")) is not bool
                or any(
                    type(token.get(name)) is not int
                    for name in ("source_start_byte", "source_end_byte", "output_start_byte", "output_end_byte")
                )
                or not 0 <= token["source_start_byte"] < token["source_end_byte"] <= source["bytes"]
                or not 0 <= token["output_start_byte"] <= token["output_end_byte"] <= consumed["bytes"]
                or not _digest(token.get("replacement_sha256"))
            ):
                raise ValueError("selected lineage changed an actual Source token identity/order")
            selected.append({"source": source, "consumed": consumed, **token})
    return selected, residuals


def _identity(row: dict[str, Any]) -> tuple[str, int, str]:
    if (
        not isinstance(row, dict)
        or not isinstance(row.get("source"), dict)
        or not isinstance(row["source"].get("path"), str)
        or type(row.get("ordinal")) is not int
        or row["ordinal"] < 1
        or not isinstance(row.get("key"), str)
        or not row["key"]
    ):
        raise ValueError("selected lineage occurrence omitted its actual Source identity")
    return row["source"]["path"], row["ordinal"], row["key"]


def _code_values(
    value: dict[str, Any] | None,
    analysis: dict[str, Any],
    hydration: dict[str, Any],
    occurrences: list[dict[str, Any]],
) -> list[str]:
    if value is None:
        return [
            "selected-generated-value-domain-origin-native-location:" + ":".join(map(str, _identity(row)))
            for row in occurrences
        ]
    if (
        not isinstance(value, dict)
        or analysis["scope"] != CODE_SCOPE
        or any(value.get(name) != analysis[name] for name in ("scope", "pipeline_run_id", "source_binding"))
        or value.get("analysis_digest") != analysis["content_digest"]
        or value.get("hydration_digest") != hydration["content_digest"]
        or value.get("content_digest")
        != canonical_digest({key: item for key, item in value.items() if key != "content_digest"})
        or not isinstance(value.get("values"), list)
        or "registered_origin" not in value
    ):
        raise ValueError("selected lineage requires the current direct Source Code domain/origin return")
    residuals = list(_reasons(value.get("residuals")))
    expected = {_identity(row): row for row in occurrences}
    if len(expected) != len(occurrences):
        raise ValueError("selected Source hydration repeated an occurrence identity")
    covered: set[tuple[str, int, str]] = set()
    keys: list[str] = []
    for checked in value["values"]:
        if not isinstance(checked, dict) or not isinstance(checked.get("key"), str):
            raise ValueError("actual Code domain return omitted its selected field")
        key = checked["key"]
        selected = checked.get("selected_occurrences")
        if not isinstance(selected, list) or not selected or not _digest(checked.get("payload_sha256")):
            raise ValueError("actual Code domain return omitted its complete bound occurrences")
        keys.append(key)
        for row in selected:
            if not isinstance(row, dict):
                raise ValueError("actual Code domain occurrence must be an object")
            identity = _identity(row)
            if (
                identity in covered
                or expected.get(identity) != row
                or row["key"] != key
                or checked["payload_sha256"] != row.get("replacement_sha256")
            ):
                raise ValueError("actual Code domain changed/omitted/repeated Source occurrence correspondence")
            covered.add(identity)
            # The selected finite Code adapter admits no native-location edge.
            # It must retain the exact occurrence refusal it actually returns;
            # a producer's empty aggregate cannot erase that selected obligation.
            reason = "consumed-value-native-location-link:" + ":".join(map(str, identity))
            if reason not in residuals:
                raise ValueError("actual finite Code join omitted its unresolved native occurrence")
        if value["registered_origin"] is None:
            residuals.append("selected-generated-value-completed-origin-unavailable:" + key)
    if keys != sorted(set(keys)):
        raise ValueError("actual Code domain values changed their complete unique key order")
    residuals.extend(
        "selected-generated-value-domain-origin-native-location:" + ":".join(map(str, _identity(row)))
        for row in occurrences
        if _identity(row) not in covered
    )
    return residuals


def classify_selected_native_lineage(
    analysis: dict[str, Any],
    hydration: dict[str, Any],
    *,
    code_values: dict[str, Any] | None = None,
    graph_artifacts: dict[str, Any] | None = None,
    figure_domains: dict[str, Any] | None = None,
    native_locations: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Interpret direct checked graph returns; never standalone receipt authority.

    All dynamic edges remain. The universal coverage descriptions stay advisory.
    Generated outputs are retained as DATA. A complete actual Source/native
    asset roster selects the per-artifact obligations in the companion function.
    """
    _graph(analysis, "template-native-analysis-boundary-graph-v3")
    _graph(hydration, "template-native-hydration-reconstruction-v3")
    if any(analysis[name] != hydration[name] for name in ("scope", "pipeline_run_id", "plan_digest", "source_binding")):
        raise ValueError("selected lineage changed the actual same-Source analysis/hydration identity")
    occurrences, residuals = _occurrences(hydration)
    residuals[:0] = [edge for edge in analysis["unresolved_edges"] if edge not in ANALYSIS_LIMITS]
    residuals.extend(edge for edge in hydration["unresolved_edges"] if edge not in HYDRATION_LIMITS)
    residuals.extend(_code_values(code_values, analysis, hydration, occurrences))
    if figure_domains is not None:
        if (
            analysis["scope"] != CODE_SCOPE
            or any(figure_domains.get(name) != analysis[name] for name in ("source_binding", "pipeline_run_id"))
            or figure_domains.get("analysis_digest") != analysis["content_digest"]
            or figure_domains.get("content_digest")
            != canonical_digest({key: item for key, item in figure_domains.items() if key != "content_digest"})
            or not isinstance(figure_domains.get("figures"), list)
        ):
            raise ValueError("selected figures lost their direct same-Source analysis/domain join")
        residuals.extend(_reasons(figure_domains.get("residuals")))
    if native_locations is not None:
        if (
            analysis["scope"] != CODE_SCOPE
            or any(
                native_locations.get(name) != analysis[name]
                for name in ("scope", "source_binding", "pipeline_run_id", "plan_digest")
            )
            or native_locations.get("analysis_digest") != analysis["content_digest"]
            or native_locations.get("hydration_digest") != hydration["content_digest"]
            or native_locations.get("content_digest")
            != canonical_digest({key: item for key, item in native_locations.items() if key != "content_digest"})
        ):
            raise ValueError("selected native locations changed its direct actual Source/graph/phase join")
    produced = analysis.get("produced_current_bodies")
    if not isinstance(produced, list):
        raise ValueError("selected lineage omitted the actual complete generated-body roster")
    project = PurePosixPath("projects") / analysis["scope"]
    figures = []
    for row in produced:
        if not isinstance(row, dict) or not isinstance(row.get("producer_stage"), str) or not row["producer_stage"]:
            raise ValueError("selected lineage generated body omitted its actual producer role")
        body = _binding(row.get("body"))
        if not PurePosixPath(body["path"]).is_relative_to(project):
            raise ValueError("selected lineage generated body escaped the actual Source scope")
        if PurePosixPath(body["path"]).is_relative_to(project / "output/figures"):
            figures.append({"producer_stage": row["producer_stage"], "body": body})
    if graph_artifacts is not None and (
        not isinstance(graph_artifacts, dict)
        or set(graph_artifacts) != {"analysis", "hydration"}
        or any(
            not isinstance(binding, dict)
            or set(binding) != {"path", "sha256"}
            or not isinstance(binding["path"], str)
            or not binding["path"]
            or PurePosixPath(binding["path"]).is_absolute()
            or ".." in PurePosixPath(binding["path"]).parts
            or not _digest(binding["sha256"])
            for binding in graph_artifacts.values()
        )
    ):
        raise ValueError("Current lineage graph artifacts differ from their actual held comparison bindings")
    body = {
        "schema_version": SCHEMA,
        "scope": analysis["scope"],
        "source_binding": analysis["source_binding"],
        "pipeline_run_id": analysis["pipeline_run_id"],
        "plan_digest": analysis["plan_digest"],
        "analysis_digest": analysis["content_digest"],
        "hydration_digest": hydration["content_digest"],
        "graph_artifacts": graph_artifacts,
        "selected_occurrences": occurrences,
        "generated_figure_roles": figures,
        "code_figure_domains": figure_domains,
        "code_native_locations": native_locations,
        "residuals": list(dict.fromkeys(residuals)),
        "advisory_limits": {
            "configured_suite": list(DOMAIN_LIMITS),
            "analysis_api": list(ANALYSIS_LIMITS),
            "hydration_api": list(HYDRATION_LIMITS),
        },
    }
    return {**body, "content_digest": canonical_digest(body)}


def observe_selected_native_lineage(
    source: NativeSourceContext,
    reader: SnapshotReader,
    analysis: dict[str, Any],
    hydration: dict[str, Any],
    *,
    deadline: float,
    figure_domains: dict[str, Any] | None = None,
    native_locations: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Collect under the existing live producer or genuine Original reader."""
    from infrastructure.reporting.native_format_joint_source import require_native_operation
    from infrastructure.reporting.native_tool_producer import current_native_producer_operation

    remaining(deadline)
    operation = require_native_operation(reader) if reader.native_operation is not None else None
    owner = current_native_producer_operation() if operation is None else None
    if operation is not None:
        if (
            operation.source is not source
            or deadline != operation.deadline
            or analysis["scope"] not in operation.originals
        ):
            raise ValueError("selected lineage lost its genuinely held Original Source/clock")
        operation.verify(reader)
    else:
        if (
            owner is None
            or owner.source is not source
            or reader.native_producer_operation is not owner
            or deadline != owner.deadline
        ):
            raise ValueError("selected lineage lost its real live Source producer/clock")
        owner.verify(reader, run_id=owner.run_id, deadline=deadline)
    source.verify_correspondence(source.reference, reader.root, reader, deadline)
    if reader.root != source.bindings.current_root or any(
        graph.get("source_binding") != [source.reference.commit, source.reference.source_identity]
        for graph in (analysis, hydration)
    ):
        raise ValueError("selected lineage lost its actual Source root or identity")
    code_values = None
    if analysis["scope"] == CODE_SCOPE:
        from infrastructure.reporting.native_code_consumed_value_join import join_code_consumed_value

        code_values = join_code_consumed_value(source, reader, analysis, hydration, deadline=deadline)
    result = classify_selected_native_lineage(
        analysis, hydration, code_values=code_values, figure_domains=figure_domains, native_locations=native_locations
    )
    if not reader.unchanged():
        raise ValueError("selected lineage actual Source/domain inputs changed")
    source.verify_correspondence(source.reference, reader.root, reader, deadline)
    if operation is not None:
        operation.verify(reader)
    elif owner is not None:
        owner.verify(reader, run_id=owner.run_id, deadline=deadline)
    remaining(deadline)
    return result


def selected_lineage_residuals(
    values: tuple[dict[str, Any], ...],
    analysis: dict[str, Any],
    hydration: dict[str, Any],
    *,
    reader_phase: bool,
    current_artifacts: dict[str, Any] | None = None,
) -> tuple[str, ...]:
    """Join actual Original facts and, only for reader, separate Current facts."""
    if not isinstance(values, tuple) or len(values) != (2 if reader_phase else 1):
        raise ValueError("selected lineage requires the independently checked actual phase facts")
    residuals: list[str] = []
    for index, value in enumerate(values):
        if (
            not isinstance(value, dict)
            or value.get("schema_version") != SCHEMA
            or value.get("scope") != analysis["scope"]
            or value.get("source_binding") != analysis["source_binding"]
            or index == 0
            and value.get("plan_digest") != analysis["plan_digest"]
            or value.get("content_digest")
            != canonical_digest({key: item for key, item in value.items() if key != "content_digest"})
            or value.get("advisory_limits")
            != {
                "configured_suite": list(DOMAIN_LIMITS),
                "analysis_api": list(ANALYSIS_LIMITS),
                "hydration_api": list(HYDRATION_LIMITS),
            }
        ):
            raise ValueError("selected lineage facts changed their checked Source/plan/advisory identity")
        if index == 0 and (
            value.get("pipeline_run_id") != analysis["pipeline_run_id"]
            or value.get("analysis_digest") != analysis["content_digest"]
            or value.get("hydration_digest") != hydration["content_digest"]
        ):
            raise ValueError("selected lineage omitted the independently reconstructed Original graph")
        if index == 1 and value.get("pipeline_run_id") == values[0]["pipeline_run_id"]:
            raise ValueError("reader selected lineage reused Original instead of actual fresh Current")
        if index == 1 and (
            current_artifacts is None
            or value.get("pipeline_run_id") != current_artifacts.get("current_pipeline_run_id")
            or value.get("plan_digest") != current_artifacts.get("current_plan_digest")
            or value.get("graph_artifacts") is None
        ):
            raise ValueError("reader selected lineage differs from the actual fresh Current Core artifact join")
        residuals.extend(_reasons(value.get("residuals")))
    return tuple(dict.fromkeys(residuals))


def _assets(observer: dict[str, Any], pdf: dict[str, Any] | None) -> list[tuple[str, dict[str, str]]] | None:
    """Read complete asset returns only after the caller's existing predicates."""
    if "office_complete_source" in observer:
        reference = observer["office_complete_source"]["reference"]
        rows = reference.get("figures")
        if not isinstance(rows, list) or "cover" not in reference:
            return None
        selected = [(str(index), row["source"]) for index, row in enumerate(rows)]
        cover = reference["cover"]
        if cover is not None:
            if not isinstance(cover, dict) or "source" not in cover:
                return None
            selected.append(("cover", cover["source"]))
        return selected
    scientific = observer.get("scientific_pdf_source")
    fresh = observer.get("current_whole_pdf")
    predicates = fresh.get("source_predicates") if isinstance(fresh, dict) else None
    if predicates is None and pdf is not None:
        predicates = pdf.get("source_predicates")
    if isinstance(predicates, dict):
        assets = predicates.get("assets")
        plan = predicates.get("source_plan")
        witness = predicates.get("witness")
    elif isinstance(scientific, dict):
        assets = scientific.get("assets")
        plan = scientific.get("semantic_plan")
        witness = scientific.get("witness")
    else:
        assets = plan = witness = None
    if isinstance(assets, dict):
        if (
            not isinstance(plan, dict)
            or plan.get("schema_version") != "template-native-pdf-semantic-source-plan-v1"
            or not isinstance(plan.get("occurrences"), (list, tuple))
            or not isinstance(witness, dict)
            or witness.get("source_plan_digest") != canonical_digest(plan)
        ):
            return None
        images = [row for row in plan["occurrences"] if row["kind"] == "Image"]
        if set(assets) != {row["identity"] for row in images}:
            return None
        if not assets:
            # The actual asset compiler also returns {} on refusal. A bound,
            # completed zero-occurrence figure witness establishes absence.
            figures = witness.get("figures")
            if not isinstance(figures, dict) or any(
                figures.get(name) != [] for name in ("figures", "findings", "blockers")
            ):
                return None
        return list(assets.items())
    observation = observer.get("observation")
    if isinstance(observation, dict) and "observation" in observation:
        observation = observation["observation"]
    closure = observation.get("asset_contract") if isinstance(observation, dict) else None
    if isinstance(closure, dict) and closure.get("schema_version") == "template-native-browser-assets-v1":
        rows = closure.get("assets")
        if isinstance(rows, list):
            return [(str(index), row) for index, row in enumerate(rows)]
    return None


def selected_asset_lineage_residuals(
    facts: dict[str, Any],
    artifact_id: str,
    observer: dict[str, Any],
    *,
    pdf: dict[str, Any] | None = None,
    native_qualified: bool = False,
) -> tuple[str, ...]:
    """Select actual consumed generated figures, preserving unfinished domains.

    Source/native fidelity predicates still reject missing/extra/altered assets.
    A complete returned roster can establish that a produced file is unused;
    output presence alone creates no scientific/native occurrence obligation.
    No existing finite figure domain adapter is claimed by this projection.
    """
    figures = facts["generated_figure_roles"]
    selected = _assets(observer, pdf)
    if selected is None:
        return tuple(
            "actual-generated-asset-consumer-roster-unavailable:" + artifact_id + ":" + row["body"]["path"]
            for row in figures
        )
    project_figures = PurePosixPath("projects") / facts["scope"] / "output/figures"
    produced = {row["body"]["path"]: row["body"] for row in figures}
    residuals: list[str] = []
    for identity, binding in selected:
        if (
            not isinstance(identity, str)
            or not identity
            or not isinstance(binding, dict)
            or set(binding) != {"path", "sha256"}
            or not isinstance(binding["path"], str)
            or not binding["path"]
            or PurePosixPath(binding["path"]).is_absolute()
            or ".." in PurePosixPath(binding["path"]).parts
            or not _digest(binding["sha256"])
        ):
            raise ValueError("actual complete Source asset roster has an invalid occurrence binding")
        path = binding["path"]
        if not PurePosixPath(path).is_relative_to(project_figures):
            parts = PurePosixPath(path).parts
            if parts[0] == "projects" and any(
                parts[index : index + 2] == ("output", "figures") for index in range(len(parts) - 1)
            ):
                residuals.append(
                    "selected-external-generated-asset-lineage-unjoined:" + artifact_id + ":" + identity + ":" + path
                )
            continue
        body = produced.get(path)
        if body is None:
            residuals.append(
                "consumed-figure-completed-origin-unavailable:" + artifact_id + ":" + identity + ":" + path
            )
        elif body["sha256"] != binding["sha256"]:
            raise ValueError("actual consumed Source figure differs from its observed producer body")
        domains = facts.get("code_figure_domains")
        qualified = []
        if native_qualified and isinstance(domains, dict):
            for figure in domains["figures"]:
                if figure.get("png") == body and any(
                    row == {"identity": artifact_id + ":" + identity, "asset": binding}
                    for row in figure.get("selected_occurrences", ())
                ):
                    qualified.append(figure)
        if len(qualified) > 1:
            raise ValueError("direct Code figure domain repeated a selected native occurrence")
        if not qualified:
            residuals.append("consumed-figure-domain-and-native-lineage:" + artifact_id + ":" + identity + ":" + path)
    return tuple(dict.fromkeys(residuals))


def collect_code_figure_domains(
    source: NativeSourceContext,
    reader: SnapshotReader,
    analysis: dict[str, Any],
    observers: tuple[tuple[str, dict[str, Any], dict[str, Any] | None], ...],
    *,
    deadline: float,
) -> dict[str, Any] | None:
    """Join one complete actual selected asset union under the enclosing role.

    Unavailable rosters remain unavailable in the existing per-artifact
    projection. A successful zero-image roster stays a genuine absence.
    This DATA function creates no owner or native qualification.
    """
    if analysis["scope"] != CODE_SCOPE:
        return None
    from infrastructure.reporting.native_code_figure_lineage import join_code_figure_domains

    selected: list[tuple[str, dict[str, str]]] = []
    ids = []
    for artifact, observer, pdf in observers:
        if not isinstance(artifact, str) or not artifact or artifact in ids:
            raise ValueError("Code figure domain union repeated or omitted an actual artifact identity")
        ids.append(artifact)
        assets = _assets(observer, pdf)
        if assets is not None:
            selected.extend((artifact + ":" + identity, binding) for identity, binding in assets)
    if len({identity for identity, _ in selected}) != len(selected):
        raise ValueError("Code figure domain union repeated an actual Source image occurrence")
    return join_code_figure_domains(source, reader, analysis, tuple(selected), deadline=deadline)


def selected_value_lineage_residuals(
    facts: tuple[dict[str, Any], ...],
    artifact_id: str,
    baseline: tuple[str, ...],
    *,
    native_qualified: bool,
) -> tuple[str, ...]:
    """Reconcile exact baseline location refusals after complete native closure.

    The finite Code domain's original residual remains in its checked return.
    Only this artifact's actual checked Original/Current roles or own complete
    Source-input absence can close that exact source/key/ordinal at projection.
    All origin/domain/style/scientific/control/pairing/history failures remain.
    """
    if not native_qualified:
        return baseline
    closed = []
    specific: list[str] = []
    for value in facts:
        locations = value.get("code_native_locations")
        if not isinstance(locations, dict):
            return baseline
        matches = [row for row in locations["artifacts"] if row["artifact_id"] == artifact_id]
        if len(matches) != 1:
            raise ValueError("selected native closure omitted/repeated the actual artifact")
        row = matches[0]
        selected_inputs = {binding["path"] for binding in row["source_inputs"]}
        phase_closed = set()
        for occurrence in value["selected_occurrences"]:
            identity = _identity(occurrence)
            reason = "consumed-value-native-location-link:" + ":".join(map(str, identity))
            if reason not in value["residuals"]:
                continue
            actual = [item for item in row["occurrences"] if _identity(item["hydration"]) == identity]
            if len(actual) > 1 or actual and actual[0]["hydration"] != occurrence:
                raise ValueError("selected native endpoint changed/repeated its exact Source/key/ordinal")
            if occurrence["consumed"]["path"] not in selected_inputs:
                if actual:
                    raise ValueError("selected native Source absence contains a foreign occurrence")
                phase_closed.add(reason)
            elif actual and actual[0]["roles"] and not actual[0]["residuals"]:
                phase_closed.add(reason)
            elif actual:
                specific.extend(artifact_id + ":" + reason for reason in actual[0]["residuals"])
        closed.append(phase_closed)
    common = set.intersection(*closed) if closed else set()
    return tuple(dict.fromkeys([reason for reason in baseline if reason not in common] + specific))
