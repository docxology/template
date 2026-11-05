"""Conjunctions of actual completed specialized native predicates.

Only the live phase collectors call this DATA interpreter, after the existing
Source, Original/tool, full Current join and closing checks. Empty aggregates,
producer status and requirement declarations supply no coverage. Each axis
needs the concrete component returned by its real adapter; its own unsupported
nodes remain ordered residuals. No operation or admission is constructed here.
"""

from __future__ import annotations

from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest

from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
from infrastructure.reporting.native_mermaid_source_census import SourceMermaidCensus
from infrastructure.reporting.native_oracle_obligation_compiler import AXES, COMMON, PITCH_AXES, SLIDE_AXES
from infrastructure.reporting.native_oracle_obligation_spec import NativeOracleSpecification


def _object(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _digest(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _component(value: object, label: str, fields: tuple[str, ...]) -> tuple[str, ...]:
    """Retain a real component's failures and missing positive witness fields."""
    result = _object(value)
    findings = result.get("findings")
    if isinstance(findings, list) and findings:
        raise ValueError("checked native component still has findings: " + label)
    if not isinstance(findings, list) or any(name not in result or result[name] is None for name in fields):
        return (label + ": complete actual component witness is unavailable",)
    blockers = result.get("blockers", [])
    if not isinstance(blockers, list) or any(not isinstance(row, str) or not row for row in blockers):
        raise ValueError("checked component omitted its explicit residuals: " + label)
    return tuple(blockers)


def native_observer_components(observer: dict[str, Any]) -> list[dict[str, Any]]:
    """Keep the actual return fields already examined by native_observer_outcome."""
    from infrastructure.reporting.native_format_observer_outcome import native_observer_outcome

    native_observer_outcome(observer)
    value = observer["observation"]
    if isinstance(value, dict) and "observation" in value:
        value = value["observation"]
    rows = [value]
    if observer["format"] == "epub":
        rows.insert(0, observer["spine"])
    if str(observer["id"]).startswith("pitch:") and "projection_contract" in observer:
        rows.append(observer["source_package" if observer["format"] == "pptx" else "source_native_reference"])
    return rows


def _source_observer(report: dict[str, Any]) -> dict[str, Any]:
    value = _object(report.get("source_observer"))
    if not isinstance(report.get("observations"), list) or not report["observations"]:
        raise ValueError("native axis facts need actual specialized component returns")
    return value


def ordered_source_inputs(value: object) -> tuple[tuple[str, str], ...] | None:
    """Interpret exact ordered path/body pairs; missing/duplicate rows refuse."""
    if not isinstance(value, (tuple, list)) or not value:
        return None
    rows: list[tuple[str, str]] = []
    for item in value:
        if isinstance(item, dict):
            path, digest = item.get("path"), item.get("sha256")
        elif isinstance(item, (tuple, list)) and len(item) == 2:
            path, digest = item
        else:
            return None
        if not isinstance(path, str) or not path or path.startswith("/") or ".." in path.split("/"):
            return None
        if not isinstance(digest, str) or not _digest(digest):
            return None
        rows.append((path, digest))
    return tuple(rows) if len({path for path, _ in rows}) == len(rows) else None


def _ledger(artifact: NativeArtifact, observer: dict[str, Any], pdf: dict[str, Any]) -> object:
    if "office_complete_source" in observer:
        return observer["office_complete_source"]["reference"]["source"]["sources"]
    if "manuscript_projection" in observer:
        return observer["manuscript_projection"]["source"]["contract"]["sources"]
    if "semantic_source" in observer:
        return _object(_object(observer["semantic_source"].get("body")).get("contract")).get("sources")
    if "scientific_pdf_source" in observer:
        return observer["scientific_pdf_source"]["semantic_plan"]["sources"]
    predicates = _object(pdf.get("source_predicates"))
    return _object(predicates.get("source_plan")).get("sources")


def _census(
    artifact: NativeArtifact,
    spec: NativeOracleSpecification,
    census: SourceMermaidCensus,
    observer: dict[str, Any],
    pdf: dict[str, Any],
) -> tuple[str, ...]:
    if not isinstance(census, SourceMermaidCensus):
        raise ValueError("native axes require the actual complete Source census object")
    documents = [items for scope, items in census.document_inputs if scope == spec.scope]
    if len(documents) != 1 or not documents[0]:
        raise ValueError("actual complete Source census omitted/repeated phase scope")
    expected = documents[0]
    if artifact.id.startswith("section:"):
        suffix = artifact.id.removeprefix("section:").rsplit(":", 1)[0]
        expected = tuple(row for row in expected if row[0].endswith("/" + suffix))
        if len(expected) != 1:
            return (artifact.id + ": complete selected section input census is unavailable",)
    actual = ordered_source_inputs(_ledger(artifact, observer, pdf))
    if actual is None:
        return (artifact.id + ": actual semantic input/occurrence ledger is unavailable",)
    selected = tuple(row for row in actual if row[0] in {path for path, _ in expected})
    if selected != expected:
        raise ValueError("actual semantic ledger changed/omitted/reordered held Source manuscript bytes")
    # The remaining entries must already be the adapter's separately admitted
    # bibliography/config closure, never foreign manuscript inputs.
    if any(path.endswith((".md", ".tex")) and path not in {p for p, _ in expected} for path, _ in actual):
        return (artifact.id + ": semantic ledger includes an unaccounted manuscript input",)
    if "office_complete_source" in observer:
        source = observer["office_complete_source"]["reference"]["source"]
        survival = observer["observation"]["source_survival"]
        return _office_occurrences(source, survival)
    if "manuscript_projection" in observer:
        source = observer["manuscript_projection"]["source"]
        contract = source["contract"]
        if not all(name in contract for name in ("occurrences", "node_inventory", "ast_sha256", "digest")):
            return (artifact.id + ": complete Source/resolved marker census is unavailable",)
        return tuple(contract["blockers"])
    if pdf.get("source_predicates") is not None:
        plan = pdf["source_predicates"]["source_plan"]
        if not all(name in plan for name in ("text", "notes", "occurrences", "tables", "source_ast_sha256")):
            return (artifact.id + ": complete PDF semantic node census is unavailable",)
        return tuple(plan["blockers"])
    if "scientific_pdf_source" in observer:
        plan = observer["scientific_pdf_source"]["semantic_plan"]
        if all(name in plan for name in ("text", "notes", "occurrences", "tables", "source_ast_sha256")):
            return tuple(plan["blockers"])
    if "semantic_source" in observer:
        fidelity = _object(observer["observation"].get("source_fidelity"))
        if (
            all(
                name in fidelity
                for name in (
                    "original_ast_sha256",
                    "projected_ast_sha256",
                    "source_bytes",
                    "image_alt",
                    "column_allocation",
                    "characters",
                )
            )
            and ordered_source_inputs(fidelity["source_bytes"]) == actual
        ):
            return tuple(fidelity["blockers"])
    return (artifact.id + ": complete original/projected semantic node census remains unjoined",)


def _office_occurrences(source: dict[str, Any], survival: dict[str, Any]) -> tuple[str, ...]:
    coverage = _object(source.get("source_coverage"))
    rows = coverage.get("occurrences")
    if not isinstance(rows, list) or any(
        not isinstance(row, dict)
        or row.get("ordinal") != index
        or not isinstance(row.get("location"), list)
        or not _digest(row.get("content_sha256"))
        or not isinstance(row.get("content_json"), str)
        for index, row in enumerate(rows)
    ):
        return ("Office complete ordered Source location/payload census is unavailable",)
    expected = [{key: row[key] for key in ("ordinal", "kind", "content_sha256")} for row in rows]
    if survival.get("occurrences") != expected or survival.get("source_ast_sha256") != coverage.get(
        "source_ast_sha256"
    ):
        raise ValueError("actual Office native witness differs from the complete Source occurrence ledger")
    return _component(
        survival,
        "Office complete Source survival",
        (
            "source_ast_sha256",
            "filtered_ast_sha256",
            "native_ast_sha256",
            "prose_text_sha256",
            "witnesses",
            "raw_roles",
            "source_math_count",
            "native_math_count",
        ),
    )


def _pages(value: object, label: str) -> tuple[str, ...]:
    result = _object(value)
    reasons = _component(result, label, ("reference_pages", "candidate_pages"))
    left, right = result.get("reference_pages"), result.get("candidate_pages")
    if not isinstance(left, list) or not left or not isinstance(right, list) or len(left) != len(right):
        return (*reasons, label + ": every actual native page is required")
    if [row.get("page") for row in left] != list(range(1, len(left) + 1)) or any(
        row.get("page") != peer.get("page") or not _digest(row.get("sha256")) or row != peer
        for row, peer in zip(left, right, strict=True)
    ):
        raise ValueError("actual all-page native projection changed/omitted/reordered pages")
    return reasons


def _office(observer: dict[str, Any], observations: list[dict[str, Any]]) -> tuple[tuple[str, ...], ...]:
    complete = _object(observer.get("office_complete_source"))
    source = _object(_object(complete.get("reference")).get("source"))
    observed = observations[-1]
    survival = _object(observed.get("source_survival"))
    census = _office_occurrences(source, survival)
    semantics = (
        *census,
        *_component(
            observed.get("reference_source_survival"),
            "Office Source reference survival",
            (
                "source_ast_sha256",
                "native_ast_sha256",
                "prose_text_sha256",
                "witnesses",
                "occurrences",
            ),
        ),
        *_component(
            observed.get("package_parity"),
            "Office citeproc/package parity",
            (
                "reference_ast_sha256",
                "candidate_ast_sha256",
                "source_ast_sha256",
            ),
        ),
    )
    visual = (
        *semantics,
        *_pages(observed.get("native_page_parity"), "Office native full-page glyph/vector/pixel parity"),
    )
    images = observed.get("native_source_images")
    if not isinstance(images, dict) or set(images) != {"reference", "candidate"}:
        visual += ("Office full Source image/alpha and cover ink predicates are unavailable",)
    else:
        for name in ("reference", "candidate"):
            visual += _component(images[name], "Office " + name + " Source images", ("source_counts", "native_images"))
    covers = observed.get("covers")
    if covers is not None:
        for name in ("reference", "candidate"):
            visual += _component(
                _object(covers).get(name), "Office " + name + " Source cover", ("member", "image", "alternative")
            )
    return census, semantics, visual


def _html(observed: dict[str, Any]) -> tuple[tuple[str, ...], ...]:
    viewports = observed.get("viewports")
    if not isinstance(viewports, list) or [
        row.get("width", _object(row.get("dom")).get("width")) for row in viewports
    ] != [390, 1280]:
        missing = ("HTML requires actual complete 390/1280 Source DOM/pixel/fidelity returns",)
        return missing, missing, missing, missing
    dom: tuple[str, ...] = ()
    pixels: tuple[str, ...] = ()
    fidelity: tuple[str, ...] = ()
    for row in viewports:
        dom += _component(row, "HTML actual viewport DOM/metadata", ("structure", "metadata", "source_text_indices"))
        pixels += _component(row.get("pixels"), "HTML actual localized viewport pixels", ("regions",))
        pixels += _component(row.get("figures"), "HTML actual source figures/alpha", ("figures",))
        fidelity += _component(
            row.get("fidelity"),
            "HTML actual Source CSS/font/math/citation/table/footnote fidelity",
            ("components", "resampling", "digest"),
        )
    source = _object(observed.get("source_fidelity"))
    assets = _object(observed.get("asset_contract"))
    source_reasons = tuple(
        source.get("blockers", ["HTML complete independently admitted original/projected Source AST unavailable"])
    )
    assets_reasons = tuple(assets.get("blockers", ["HTML complete Source asset closure unavailable"]))
    if not _digest(source.get("digest")) or "source_admission" not in source:
        source_reasons += ("HTML Source AST/config/font commitment is unavailable",)
    semantic = (*dom, *fidelity, *source_reasons)
    return semantic, (*fidelity, *source_reasons, *assets_reasons), (*dom, *pixels), (*semantic, *pixels)


def _slides(observer: dict[str, Any], observed: dict[str, Any]) -> tuple[tuple[str, ...], ...]:
    source = _object(_object(observer.get("manuscript_projection")).get("source"))
    plan, contract = _object(source.get("plan")), _object(source.get("contract"))
    selected = (
        ()
        if all(name in plan for name in ("source", "config", "bibliographies", "profile"))
        else ("slide actual enabled Source profile/config/resource/bibliography plan is unavailable",)
    )
    paint = _object(observed.get("source_paint"))
    census = _component(paint, "slide actual complete Source occurrence paint", ("contract", "pages", "occurrences"))
    if paint.get("contract") != contract or not contract.get("node_inventory"):
        census += ("slide actual Source/resolved occurrence contract is unavailable",)
    parity = _pages(observed.get("native_parity"), "slide Source/candidate every-page parity")
    noninterference = _component(
        observed.get("instrumentation_noninterference"), "slide marked/source paint noninterference", ("pages",)
    )
    if not _object(observed.get("instrumentation_noninterference")).get("pages"):
        noninterference += ("slide marked/source complete page roster is unavailable",)
    return selected, census, (*census, *parity), (*census, *noninterference)


def _print(observed: dict[str, Any]) -> tuple[str, ...]:
    reasons = _component(observed, "print actual configured Source pixels/font/model comparison", ("projection",))
    projection = _object(observed.get("projection"))
    if (
        projection.get("schema_version")
        not in {"template-storybook-native-v1", "template-newspaper-print-projection-v1"}
        or not _digest(projection.get("source_sha256"))
        or not _digest(projection.get("artifact_sha256"))
        or type(projection.get("pages")) is not int
        or projection["pages"] < 1
    ):
        reasons += ("print actual complete Source/reference page/pixel projection is unavailable",)
    return reasons


def _pitch_native(
    artifact: NativeArtifact, actual: dict[str, Any], components: list[dict[str, Any]]
) -> tuple[str, ...]:
    if len(components) != 2:
        return ("Pitch actual Source-native companion is unavailable",)
    if artifact.format == "pdf":
        companion = _object(actual.get("source_native_reference"))
        reasons = _component(
            companion,
            "Pitch actual Source-only PDF reference",
            (
                "input_sha256",
                "projection_contract",
                "source_pdf",
                "native_projection",
            ),
        )
        reasons += _pages(
            components[-1].get("native_projection"), "Pitch independently checked Source PDF native pages"
        )
    else:
        companion = components[-1]
        reasons = _component(
            companion,
            "Pitch actual complete Source package/layout/theme/notes/QR",
            (
                "pages",
                "input_sha256",
                "contract",
                "source_notes_checked",
            ),
        )
        if companion.get("source_notes_checked") is not True or not companion.get("pages"):
            reasons += ("Pitch actual complete Source-model notes/package pages are unavailable",)
        layout = _object(_object(actual.get("source_package")).get("source_layout"))
        if (
            not layout
            or layout.get("source_layout_digest") != layout.get("candidate_layout_digest")
            or layout.get("findings")
        ):
            reasons += ("Pitch actual Source layout/theme package witness is unavailable",)
    reasons += _component(components[0], "Pitch actual complete native glyph/figure/QR projection", ("pages",))
    if not components[0].get("pages"):
        reasons += ("Pitch actual complete native page roster is unavailable",)
    return reasons


def _pdf_row(cohort: dict[str, Any] | None, artifact: NativeArtifact) -> dict[str, Any]:
    if cohort is None:
        return {}
    rows = cohort.get("artifacts")
    if not isinstance(rows, list):
        raise ValueError("actual whole-PDF return omitted its complete artifact roster")
    selected = [row for row in rows if row.get("id") == artifact.id]
    if len(selected) != 1:
        raise ValueError("actual whole-PDF return omitted/repeated a Source PDF artifact")
    row = selected[0]
    if not isinstance(row, dict):
        raise ValueError("actual selected whole-PDF return must be a JSON object")
    if row.get("findings"):
        raise ValueError("whole-PDF checked source/native findings remain failure")
    # Both retained parity fields use the Original candidate. A reproduced
    # reference never becomes evidence about the separate Current Core output.
    return row


def _pdf_witness(witness_value: object, plan_value: object, label: str) -> tuple[str, ...]:
    """Interpret optional witnesses only from the complete already checked plan."""
    witness, plan = _object(witness_value), _object(plan_value)
    reasons = _component(witness, label, ("source_plan_digest", "literal", "tables", "figures", "pagebreaks"))
    if (
        set(plan)
        != {
            "schema_version",
            "artifact_id",
            "source_ast_sha256",
            "sources",
            "text",
            "notes",
            "occurrences",
            "tables",
            "blockers",
            "literal_members",
        }
        or plan.get("schema_version") != "template-native-pdf-semantic-source-plan-v1"
        or not isinstance(plan.get("artifact_id"), str)
        or not plan["artifact_id"]
        or not _digest(plan.get("source_ast_sha256"))
        or ordered_source_inputs(plan.get("sources")) is None
        or any(
            not isinstance(plan.get(name), (list, tuple)) or any(not isinstance(row, dict) for row in plan[name])
            for name in ("text", "notes", "occurrences", "tables", "literal_members")
        )
        or any(not isinstance(row.get("kind"), str) or not row["kind"] for row in plan["occurrences"])
        or not isinstance(plan.get("blockers"), (list, tuple))
        or any(not isinstance(reason, str) or not reason for reason in plan["blockers"])
    ):
        return (*reasons, label + ": complete exact Source semantic plan is unavailable")
    if not _digest(witness.get("source_plan_digest")):
        return (*reasons, label + ": actual witness has no complete Source plan binding")
    if witness["source_plan_digest"] != canonical_digest(plan):
        raise ValueError("actual PDF witness changed its complete Source semantic plan")
    reasons += tuple(plan["blockers"])
    occurrences = plan["occurrences"]
    selected = {
        "notes": bool(plan["notes"]),
        "citations": any(
            row["kind"] == "Cite" or "citation_reference_id" in row or bool(row.get("raw_citation_reference_ids"))
            for row in occurrences
        ),
        "equations": any(row["kind"] == "Math" for row in occurrences),
    }
    fields = {
        "notes": ("contract_digest", "matches"),
        "citations": ("matches", "observed_glyphs"),
        "equations": ("observations",),
    }
    for name, applicable in selected.items():
        if name not in witness or applicable and witness[name] is None:
            reasons += (label + ": selected/required " + name + " witness is unavailable",)
        elif witness[name] is not None:
            reasons += _component(witness[name], label + " " + name, fields[name])
    # Unknown raw syntax and unbound scientific nodes remain in the actual
    # plan/witness blockers even when no supported reference was selected.
    return reasons


def _pdf(row: dict[str, Any]) -> tuple[tuple[str, ...], ...]:
    predicates = _object(row.get("source_predicates"))
    semantics = _component(predicates, "PDF complete Source semantic predicates", ("source_plan", "witness", "assets"))
    semantics += _pdf_witness(
        predicates.get("witness"),
        predicates.get("source_plan"),
        "PDF actual Source semantic/metadata/annotation witness",
    )
    parity = _component(row.get("every_page_parity"), "PDF actual every-page glyph/font/crop/pixel parity", ("pages",))
    if not _object(row.get("every_page_parity")).get("pages"):
        parity += ("PDF complete native page/ink roster is unavailable",)
    reference: tuple[str, ...] = (
        ()
        if row.get("whole_reference") is not None
        else ("PDF actual independent Source-only full reference is unavailable",)
    )
    if "current_reproduction" in row:
        current = _object(row["current_reproduction"])
        reference += _component(
            current.get("every_page_reproduction"), "PDF independent current reference reproduction", ("pages",)
        )
    return semantics, (*semantics, *parity), (*semantics, *parity, *reference)


def _pdf_current(observer: dict[str, Any]) -> tuple[tuple[str, ...], ...]:
    """Use only fresh Current candidate fields, never Original/reference parity."""
    source = _object(observer.get("scientific_pdf_source"))
    whole = _object(observer.get("current_whole_pdf"))
    predicates = _object(whole.get("source_predicates"))
    aggregate: tuple[str, ...] = ()
    if predicates:
        source = {"semantic_plan": predicates.get("source_plan"), "witness": predicates.get("witness")}
        aggregate = _component(
            predicates, "PDF fresh Current complete Source semantic predicates", ("source_plan", "witness", "assets")
        )
    residuals = whole.get("blockers", [])
    if not isinstance(residuals, list) or any(not isinstance(row, str) or not row for row in residuals):
        raise ValueError("fresh Current Source reference omitted its explicit residuals")
    witness = _object(source.get("witness"))
    semantics = (
        *_pdf_witness(witness, source.get("semantic_plan"), "PDF fresh Current Core Source semantic witness"),
        *aggregate,
    )
    parity = _component(
        witness.get("whole_page_parity"), "PDF fresh Current Core output every-page Source parity", ("pages",)
    )
    if not _object(witness.get("whole_page_parity")).get("pages"):
        parity += ("PDF fresh Current Core output full-page glyph/vector/ink parity is unavailable",)
    reference = (
        *_component(
            witness.get("source_reference_literal"),
            "PDF fresh Current Core independent Source reference literal",
            ("pdf_sha256", "raster_sha256", "contract_digest", "pages", "matches"),
        ),
        *_component(
            witness.get("source_reference_figures"),
            "PDF fresh Current Core independent Source reference figures",
            ("figures",),
        ),
    )
    return (*semantics, *residuals), (*semantics, *parity, *residuals), (*semantics, *parity, *reference, *residuals)


def _office_mermaid_reference(observer: dict[str, Any]) -> tuple[str, ...]:
    """Keep the selected Source-only reference's consuming-role and ink gaps."""
    source = _object(_object(_object(observer.get("office_complete_source")).get("reference")).get("source"))
    reference = _object(_object(source.get("mermaid")).get("reference"))
    remaining = reference.get("remaining_admission")
    if remaining is None:
        return ("Office selected Source-only Mermaid reference obligations are unavailable",)
    if not isinstance(remaining, list) or any(not isinstance(row, str) or not row for row in remaining):
        raise ValueError("checked Office Mermaid reference changed its explicit residual roster")
    return tuple(remaining)


def _epub_engine(observer: dict[str, Any]) -> tuple[str, ...]:
    native = _object(_object(observer.get("office_complete_source")).get("native"))
    for name in ("reference", "candidate"):
        conversion = _object(_object(native.get(name)).get("conversion"))
        engine = _object(conversion.get("engine"))
        jars, tools = conversion.get("consumed_jars"), conversion.get("tool_artifacts")
        if (
            engine.get("schema_version") != "template-native-epubcheck-engine-v1"
            or not engine.get("files")
            or not isinstance(jars, list)
            or not jars
            or not isinstance(tools, list)
            or len(tools) != 5
            or any(not _digest(_object(row).get("sha256")) for row in (*jars, *tools))
            or any(
                conversion.get(key) is None
                for key in (
                    "consumed_jar",
                    "reader_environment_artifact",
                    "reader_runtime_before",
                    "reader_runtime_after",
                    "pdf",
                )
            )
        ):
            return ("EPUB complete actual Java/JAR/frozen-engine/five-tool reader closure is unavailable",)
    return ()


def _suite(spec: NativeOracleSpecification, controls: dict[str, Any], id_: str, reader_phase: bool) -> tuple[str, ...]:
    from infrastructure.reporting.native_source_control_targets import normalize_checked_source_control_suite

    suite = next((row for row in spec.suites if row.id == id_), None)
    result = _object(_object(controls.get("suites")).get(id_))
    if suite is None or not result:
        return (id_ + ": complete actual Source-selected controls are unavailable",)
    if reader_phase and result.get("suite_id") is None:
        result = normalize_checked_source_control_suite(
            spec, suite, result, original_run_id=controls["original_run_id"]
        )
    outcomes = result.get("outcomes")
    if not isinstance(outcomes, list) or [row.get("name") for row in outcomes] != [row.name for row in suite.controls]:
        return (id_ + ": complete actual baseline/refusal roster is unavailable",)
    for actual, required in zip(outcomes, suite.controls, strict=True):
        if (
            actual.get("original_exit_code") != required.original_exit_code
            or actual.get("intended_diagnostic") != required.intended_diagnostic
        ):
            raise ValueError("actual configured control code/diagnostic differs from Source")
        targets = actual.get("target_outcomes")
        if not isinstance(targets, list) or [row.get("target") for row in targets] != [
            row.target for row in required.target_requirements
        ]:
            return (id_ + ": complete actual Source occurrence/placement targets are unavailable",)
        for row, target in zip(targets, required.target_requirements, strict=True):
            if (
                row.get("original_exit_code") != target.original_exit_code
                or reader_phase
                and (
                    row.get("current_exit_code") != target.original_exit_code
                    or row.get("reconstructed_exit_code") != target.original_exit_code
                )
            ):
                raise ValueError("actual configured target signed outcomes differ from Source")
    return ()


def collect_artifact_axis_facts(
    artifact: NativeArtifact,
    spec: NativeOracleSpecification,
    report: dict[str, Any],
    census: SourceMermaidCensus,
    whole_pdf: tuple[dict[str, Any], dict[str, Any]] | None,
    pitch_pairs: dict[str, Any] | None,
    controls: dict[str, Any],
    renderer: dict[str, Any],
    *,
    current_observer: dict[str, Any] | None,
) -> dict[str, tuple[str, ...]]:
    """Conjoin actual independent readback and real Current fields, per Source axis."""
    observer = _source_observer(report)
    observations = report["observations"]
    pdf = _pdf_row(None if whole_pdf is None else whole_pdf[0], artifact) if artifact.format == "pdf" else {}
    result: dict[str, tuple[str, ...]] = {COMMON[3]: _census(artifact, spec, census, observer, pdf)}
    checked = [(observer, observations)]
    if current_observer is not None:
        checked.append((current_observer, native_observer_components(current_observer)))
    values: list[tuple[tuple[str, ...], ...]] = []
    for phase_index, (actual, components) in enumerate(checked):
        if artifact.format in {"docx", "epub"}:
            office = _office(actual, components)
            if artifact.format == "docx":
                diagram = (
                    ()
                    if spec.diagram_applicability is not None and not spec.diagram_applicability.occurrence_identities
                    else _suite(spec, controls, "docx_diagrams", current_observer is not None)
                )
                source_mermaid = (
                    ()
                    if not spec.diagram_applicability or not spec.diagram_applicability.occurrence_identities
                    else _office_mermaid_reference(actual)
                )
                values.append((*office, (*office[2], *diagram, *source_mermaid)))
            else:
                spine = _component(
                    components[0],
                    "EPUB actual complete ordered Source spine",
                    ("chapter_contracts", "reference", "candidate"),
                )
                epub = _epub_engine(actual)
                diagram = (
                    ()
                    if spec.diagram_applicability is not None and not spec.diagram_applicability.occurrence_identities
                    else _suite(spec, controls, "epub_diagrams", current_observer is not None)
                )
                source_mermaid = (
                    ()
                    if not spec.diagram_applicability or not spec.diagram_applicability.occurrence_identities
                    else _office_mermaid_reference(actual)
                )
                values.append(
                    (office[0], office[1], (*spine, *epub, *office[2]), (*office[2], *diagram, *source_mermaid))
                )
        elif artifact.format == "html":
            values.append(_html(components[0]))
        elif artifact.format == "pdf":
            if "manuscript_projection" in actual:
                slides = _slides(actual, components[0])
                values.append((slides[1], (*slides[1], *slides[2]), slides[2]))
            elif "print_reference" in actual:
                print_reasons = _print(components[0])
                values.append((print_reasons, print_reasons, print_reasons))
            elif artifact.id.startswith("pitch:"):
                pitch_reasons = _pitch_native(artifact, actual, components)
                values.append((pitch_reasons, pitch_reasons, pitch_reasons))
            else:
                pdf_axes = _pdf(pdf) if phase_index == 0 else _pdf_current(actual)
                scientific = _object(actual.get("scientific_pdf_source"))
                fresh_pdf = _object(_object(actual.get("current_whole_pdf")).get("source_predicates"))
                if phase_index == 1 and fresh_pdf:
                    scientific = {"semantic_plan": fresh_pdf.get("source_plan"), "witness": fresh_pdf.get("witness")}
                if scientific:
                    witness = (
                        report.get("scientific_source_witness")
                        if phase_index == 0 and current_observer is not None
                        else scientific.get("witness")
                    )
                    if witness is None:
                        witness = scientific.get("witness")
                    source_reasons = _pdf_witness(
                        witness,
                        scientific.get("semantic_plan"),
                        "PDF actual independent Source semantic witness",
                    )
                    pdf_axes = tuple((*reasons, *source_reasons) for reasons in pdf_axes)
                values.append(pdf_axes)
        elif artifact.format == "pptx":
            pitch_reasons = _pitch_native(artifact, actual, components)
            values.append((pitch_reasons, pitch_reasons))
        else:
            print_reasons = _print(components[0])
            values.append((print_reasons, print_reasons))
    for index, axis in enumerate(AXES[artifact.format]):
        result[axis] = tuple(dict.fromkeys(reason for rows in values for reason in rows[index]))
    if artifact.id.endswith((":slides", ":reveal")):
        for index, axis in enumerate(SLIDE_AXES):
            result[axis] = tuple(
                dict.fromkeys(
                    reason for actual, components in checked for reason in _slides(actual, components[0])[index]
                )
            )
    if artifact.id.startswith("pitch:"):
        expected = [row.id for row in spec.artifacts if row.id.startswith("pitch:")]
        pairs = _object(pitch_pairs)
        pair_reasons = _component(pairs, "Pitch actual complete three native pairs", ("pairs",))
        if [row.id for row in spec.artifacts if row.id.startswith("pitch:")] != expected or [
            row.get("ids") for row in pairs.get("pairs", [])
        ] != [expected[i : i + 2] for i in range(0, len(expected), 2)]:
            pair_reasons += ("Pitch exact six Source companions/three actual pairs are unavailable",)
        result[PITCH_AXES[0]] = pair_reasons
        result[PITCH_AXES[1]] = (
            *pair_reasons,
            *result[AXES[artifact.format][0]],
            *_suite(spec, controls, "configured_pitch", current_observer is not None),
        )
    # These are actual returned consuming-role edges, never module-presence or
    # producer status. Preserve them even where page/content predicates close.
    renderers = renderer.get("renderers", [*renderer.get("original", []), *renderer.get("current", [])])
    relevant = tuple(
        dict.fromkeys(
            edge
            for row in renderers
            if row.get("writer") == {"pdf": "latex", "html": "html"}.get(artifact.format)
            for edge in row["unresolved_edges"]
        )
    )
    for axis in AXES[artifact.format]:
        result[axis] += relevant
    return result
