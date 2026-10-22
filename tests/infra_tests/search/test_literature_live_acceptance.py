"""Real HTTP/process controls for bounded unpaid literature evidence."""

from __future__ import annotations

import io
import json
from datetime import date
from pathlib import Path

import pytest
from reportlab.pdfgen import canvas

from infrastructure.search.literature.crossref_backend import crossref_item_to_paper
from infrastructure.search.literature.live_artifacts import annotation_schema, export_citations, validate_annotation
from infrastructure.search.literature.live_contract import (
    LiteratureBlocked,
    LiteratureFailed,
    LiveSession,
    LiveSettings,
    exact_json,
    environment_identity,
    platform_manifest,
    verify_platform,
)
from infrastructure.search.literature.live_providers import (
    LICENSE_URL,
    _pdf_text,
    licensed_fulltext,
    licensed_pdf_candidates,
    parse_licensed_jats,
    retrieve_crossref,
)
from infrastructure.search.literature.live_transport import (
    LocalGenerator,
    extract_pdf_text,
    fetch_bytes,
    validate_public_url,
)
from infrastructure.search.literature.models import Paper

SOURCE = "We measured the telescope spectrum and reported uncertainty for every calibrated observation. " * 4
DOI = "10.1000/example"

# Each actual worker has a <=60s process deadline. Cases with two workers and
# source/runtime custody checks need their own finite outer budget under load.
pytestmark = pytest.mark.timeout(120)


def project(tmp_path: Path) -> Path:
    root = tmp_path / "public-project"
    (root / "src").mkdir(parents=True)
    (root / "manuscript").mkdir()
    (root / "src/domain.py").write_text("VALUE = 1\n")
    (root / "pyproject.toml").write_text('[project]\nname="example"\nversion="0.1.0"\n')
    (root / "manuscript/config.yaml").write_text("project_config: {}\n")
    return root


def session(tmp_path: Path, **kwargs) -> LiveSession:
    root = project(tmp_path)
    return LiveSession(
        root, Path("output/.pipeline/literature_acceptance/test"), LiveSettings("unit-model", **kwargs), ["retrieval"]
    )


def item() -> dict:
    return {
        "DOI": DOI,
        "title": ["Real retrieved article"],
        "author": [{"given": "Ada", "family": "Researcher"}],
        "issued": {"date-parts": [[2024, 1, 1]]},
        "abstract": SOURCE,
        "license": [{"URL": LICENSE_URL, "content-version": "unspecified", "start": {"date-parts": [[2024, 1, 1]]}}],
        "link": [],
    }


def jats(*, doi: str = DOI, license_url: str = LICENSE_URL) -> bytes:
    return (
        f'<article><front><article-meta><article-id pub-id-type="doi">{doi}</article-id>'
        f'<permissions><license href="{license_url}"/></permissions></article-meta></front>'
        f"<body><p>{SOURCE}</p></body></article>"
    ).encode()


@pytest.mark.parametrize(
    "field,value",
    [
        ("max_results", True),
        ("max_results", 2.5),
        ("timeout_seconds", False),
        ("run_timeout_seconds", 601),
        ("num_predict", 0),
    ],
)
def test_exact_budget_validation(field, value):
    with pytest.raises(LiteratureFailed):
        LiveSettings("model", **{field: value})


@pytest.mark.parametrize("raw", ['{"a":1,"a":2}', '{"x":NaN}', 'prefix {"x":1}', "{"])
def test_strict_json_rejects_ambiguous_provider_outputs(raw):
    with pytest.raises(LiteratureFailed):
        exact_json(raw)


def test_directory_and_final_custody_are_fail_closed(tmp_path):
    run = session(tmp_path)
    output = run.directory / "consumed.json"
    output.write_text('{"x":1}')
    run.consume(output)
    output.write_text('{"x":2}')
    run.receipt["producer_results"]["retrieval"] = {"status": "passed"}
    receipt = json.loads(run.finalize("passed").read_text())
    assert receipt["status"] == "failed" and receipt["consumed_unchanged"] is False
    with pytest.raises(LiteratureFailed, match="already exists"):
        LiveSession(run.root, run.directory, run.settings, [])


def test_source_change_and_missing_producer_cannot_pass(tmp_path):
    run = session(tmp_path)
    (run.root / "src/domain.py").write_text("VALUE = 2\n")
    receipt = json.loads(run.finalize("passed").read_text())
    assert receipt["status"] == "failed" and receipt["source_unchanged"] is False
    other = LiveSession(run.root, Path("output/.pipeline/literature_acceptance/other"), run.settings, ["required"])
    assert json.loads(other.finalize("passed").read_text())["status"] == "failed"


def test_project_parser_inputs_are_frozen_from_admitted_bytes(tmp_path):
    run = session(tmp_path)
    original = (run.root / "manuscript/config.yaml").read_bytes()
    snapshot = run.freeze_project_input("manuscript/config.yaml")
    assert snapshot.read_bytes() == original
    assert (
        run.receipt["frozen_project_inputs"]["manuscript/config.yaml"] == run.sources["project/manuscript/config.yaml"]
    )
    assert "inputs/manuscript/config.yaml" in run.consumed
    snapshot.write_bytes(b"project_config: {search: changed}\n")
    run.receipt["producer_results"]["retrieval"] = {"status": "passed"}
    assert json.loads(run.finalize("passed").read_text())["status"] == "failed"


def test_changed_or_unadmitted_project_input_cannot_be_frozen(tmp_path):
    run = session(tmp_path)
    (run.root / "manuscript/config.yaml").write_text("project_config: {changed: true}\n")
    with pytest.raises(LiteratureFailed, match="changed before consumption"):
        run.freeze_project_input("manuscript/config.yaml")
    with pytest.raises(LiteratureFailed, match="absent"):
        run.freeze_project_input("unadmitted.json")
    with pytest.raises(LiteratureFailed, match="inside"):
        run.freeze_project_input("../outside.json")


@pytest.mark.parametrize("restore", [False, True], ids=["lasting", "aba"])
def test_exact_admitted_parser_bytes_survive_real_snapshot_replacement(tmp_path, restore):
    import yaml

    from infrastructure.search.literature.configuration_sources import ConfigTextStream

    run = session(tmp_path)
    raw = run.freeze_project_input_bytes("manuscript/config.yaml")
    snapshot = run.directory / "inputs/manuscript/config.yaml"
    snapshot.write_bytes(b"project_config: {injected: true}\n")
    # Parse while the actual pathname contains B; restoration is intentionally
    # later. No parser reopens that pathname or consumes the replaced bytes.
    with ConfigTextStream(snapshot, raw) as source:
        assert yaml.safe_load(source) == {"project_config": {}}
    if restore:
        snapshot.write_bytes(raw)
    run.receipt["producer_results"]["retrieval"] = {"status": "passed"}
    receipt = json.loads(run.finalize("passed").read_text())
    assert receipt["status"] == ("passed" if restore else "failed")
    assert receipt["consumed_unchanged"] is restore
    assert run.consumed["inputs/manuscript/config.yaml"] == run.sources["project/manuscript/config.yaml"]


def test_shared_worker_requires_exact_transitive_sources_and_environment():
    sources, environment = platform_manifest(), environment_identity()
    assert "platform/infrastructure/core/subprocess_policy.py" in sources
    assert "platform/infrastructure/core/execution_boundary.py" in sources
    assert "platform/uv.lock" in sources
    with pytest.raises(ValueError, match="changed"):
        verify_platform(dict(sources, **{"platform/uv.lock": "0" * 64}), environment)
    with pytest.raises(ValueError, match="changed"):
        verify_platform(sources, dict(environment, implementation="different"))


def test_unconsumed_artifact_symlink_cannot_be_promoted(tmp_path):
    run = session(tmp_path)
    outside = tmp_path / "outside"
    outside.write_text("external bytes")
    (run.directory / "unsafe").symlink_to(outside)
    run.receipt["producer_results"]["retrieval"] = {"status": "passed"}
    result = json.loads(run.finalize("passed").read_text())
    assert result["status"] == "failed"
    assert "unsafe" not in result["artifacts"]


@pytest.mark.parametrize(
    "url",
    ["http://192.168.1.1/data", "https://127.0.0.1/data", "https://user:secret@example.org/data", "file:///tmp/data"],
)
def test_private_or_credential_urls_rejected(url):
    with pytest.raises((LiteratureFailed, LiteratureBlocked)):
        validate_public_url(url)


def test_real_http_retrieval_dedup_and_complete_bibtex(tmp_path, httpserver):
    httpserver.expect_request("/works").respond_with_json({"message": {"items": [item(), item()]}})
    run = session(tmp_path)
    papers = retrieve_crossref(run, "configured topic", endpoint=httpserver.url_for("/works"))
    assert len(papers) == 1 and papers[0].doi == DOI
    keys = export_citations(run, papers)
    assert list(keys) == ["doi:" + DOI]
    raw = (run.directory / "retrieval/body.bin").read_bytes()
    assert json.loads(raw)["message"]["items"] == [item(), item()]
    report = json.loads((run.directory / "retrieval_report.json").read_text())
    assert report["deduplicated_count"] == 1 and report["execution_mode"] == "controlled-http"
    assert report["raw_count"] == report["eligible_count"] == 2
    assert report["unique_count"] == 1 and report["excluded_count"] == 0
    assert report["excluded_records"] == []
    for missing in ("authors", "year", "both"):
        incomplete = item()
        incomplete["DOI"] = "10.1000/incomplete"
        reasons = []
        if missing in {"authors", "both"}:
            incomplete.pop("author")
            reasons.append("missing_authors")
        if missing in {"year", "both"}:
            incomplete.pop("issued")
            reasons.append("missing_year")
        records = [item(), item(), incomplete]
        endpoint = "/works_" + missing
        httpserver.expect_request(endpoint).respond_with_json({"message": {"items": records}})
        eligible_run = session(tmp_path / missing)
        eligible = retrieve_crossref(eligible_run, "configured topic", endpoint=httpserver.url_for(endpoint))
        assert len(eligible) == 1 and eligible[0].doi == DOI
        assert list(export_citations(eligible_run, eligible)) == ["doi:" + DOI]
        raw = (eligible_run.directory / "retrieval/body.bin").read_bytes()
        assert json.loads(raw)["message"]["items"] == records
        filtered = json.loads((eligible_run.directory / "retrieval_report.json").read_text())
        assert filtered["status"] == "passed" and filtered["raw_count"] == 3
        assert filtered["eligible_count"] == 2 and filtered["unique_count"] == filtered["deduplicated_count"] == 1
        assert filtered["excluded_count"] == 1
        assert filtered["excluded_records"] == [
            {
                "raw_index": 2,
                "paper_id": "doi:10.1000/incomplete",
                "doi": "10.1000/incomplete",
                "reasons": reasons,
            }
        ]
        # Eligibility cannot weaken the strict downstream citation writer.
        with pytest.raises(LiteratureFailed, match="lacks title, DOI, authors, or year"):
            export_citations(eligible_run, [crossref_item_to_paper(incomplete)])


@pytest.mark.parametrize("body", [{"message": {"items": []}}, {"message": {"items": [{}]}}])
def test_real_http_empty_or_invalid_retrieval_is_not_success(tmp_path, httpserver, body):
    httpserver.expect_request("/works").respond_with_json(body)
    run = session(tmp_path)
    with pytest.raises((LiteratureFailed, LiteratureBlocked)):
        retrieve_crossref(run, "topic", endpoint=httpserver.url_for("/works"))
    assert json.loads((run.directory / "retrieval/body.bin").read_bytes()) == body
    if not body["message"]["items"]:
        for missing in ("authors", "year", "both", "title"):
            incomplete = item()
            reasons = []
            if missing in {"authors", "both", "title"}:
                incomplete.pop("author")
                reasons.append("missing_authors")
            if missing in {"year", "both"}:
                incomplete.pop("issued")
                reasons.append("missing_year")
            if missing == "title":
                incomplete["title"] = [""]
            endpoint = "/no_eligible_" + missing
            httpserver.expect_request(endpoint).respond_with_json({"message": {"items": [incomplete]}})
            excluded_run = session(tmp_path / missing)
            error = LiteratureFailed if missing == "title" else LiteratureBlocked
            with pytest.raises(error):
                retrieve_crossref(excluded_run, "topic", endpoint=httpserver.url_for(endpoint))
            raw = (excluded_run.directory / "retrieval/body.bin").read_bytes()
            assert json.loads(raw)["message"]["items"] == [incomplete]
            if error is LiteratureBlocked:
                filtered = json.loads((excluded_run.directory / "retrieval_report.json").read_text())
                assert filtered["status"] == "blocked" and filtered["raw_count"] == filtered["excluded_count"] == 1
                assert filtered["eligible_count"] == filtered["unique_count"] == filtered["deduplicated_count"] == 0
                assert filtered["excluded_records"] == [
                    {
                        "raw_index": 0,
                        "paper_id": "doi:" + DOI,
                        "doi": DOI,
                        "reasons": reasons,
                    }
                ]


def test_real_http_error_retains_diagnostics_and_is_blocked(tmp_path, httpserver):
    httpserver.expect_request("/down").respond_with_data("provider unavailable", status=503)
    run = session(tmp_path)
    with pytest.raises(LiteratureBlocked):
        fetch_bytes(run, httpserver.url_for("/down"), "down", allow_loopback=True)
    assert json.loads((run.directory / "down/http.json").read_text())["status_code"] == 503
    assert json.loads((run.directory / "down/execution.json").read_text())["returncode"] == 75

    challenge = b"<html><title>Radware Bot Manager Captcha</title><div class='h-captcha'></div></html>"
    httpserver.expect_request("/captcha").respond_with_data(
        challenge, content_type="text/html", headers={"X-Access-Challenge": "Radware"}
    )
    captcha_run = session(tmp_path / "captcha")
    with pytest.raises(LiteratureBlocked, match="unpaid worker unavailable"):
        fetch_bytes(captcha_run, httpserver.url_for("/captcha"), "captcha", allow_loopback=True)
    captcha_metadata = json.loads((captcha_run.directory / "captcha/http.json").read_text())
    assert captcha_metadata["status"] == "blocked" and captcha_metadata["status_code"] == 200
    assert captcha_metadata["requested_url"] == captcha_metadata["final_url"] == httpserver.url_for("/captcha")
    assert captcha_metadata["content_type"].startswith("text/html")
    assert dict(captcha_metadata["response_headers"])["X-Access-Challenge"] == "Radware"
    assert (captcha_run.directory / "captcha/body.bin").read_bytes() == challenge
    assert json.loads((captcha_run.directory / "captcha/execution.json").read_text())["returncode"] == 75

    # An arbitrary HTML body remains a responding malformed PDF producer,
    # rather than being reclassified as unavailable by its media type alone.
    generic_html = b"<html><title>Article landing page</title><p>Not a PDF.</p></html>"
    httpserver.expect_request("/not_pdf").respond_with_data(generic_html, content_type="text/html")
    invalid_run = session(tmp_path / "not-pdf")
    raw, metadata = fetch_bytes(invalid_run, httpserver.url_for("/not_pdf"), "not_pdf", allow_loopback=True)
    assert raw == generic_html and metadata["status"] == "passed" and metadata["status_code"] == 200
    with pytest.raises(LiteratureFailed, match="unpaid worker failed"):
        extract_pdf_text(invalid_run, invalid_run.directory / "not_pdf/body.bin", DOI, "invalid_pdf")
    invalid_execution = json.loads((invalid_run.directory / "invalid_pdf/execution.json").read_text())
    assert invalid_execution["returncode"] == 1 and "not a PDF" in invalid_execution["stdout"]


def test_http_byte_ceiling_is_a_failed_responding_producer(tmp_path, httpserver):
    httpserver.expect_request("/large").respond_with_data("abcdef")
    run = session(tmp_path)
    with pytest.raises(LiteratureFailed):
        fetch_bytes(run, httpserver.url_for("/large"), "large", max_bytes=2, allow_loopback=True)


def test_explicit_active_version_license_is_required():
    record = item()
    record["license"][0]["content-version"] = "vor"
    record["link"] = [
        {"URL": "https://publisher.example/paper.pdf", "content-version": "vor", "content-type": "application/pdf"}
    ]
    assert len(licensed_pdf_candidates(record, today=date(2024, 1, 1))) == 1
    assert licensed_pdf_candidates(record, today=date(2023, 1, 1)) == []
    record["license"][0]["content-version"] = "unspecified"
    assert licensed_pdf_candidates(record) == []


@pytest.mark.parametrize(
    "raw,error",
    [
        (jats(doi="10.1000/wrong"), LiteratureFailed),
        (jats(license_url="https://example.org/unknown"), LiteratureBlocked),
        (b'<!DOCTYPE article [<!ENTITY x SYSTEM "file:///etc/passwd">]><article>&x;</article>', LiteratureFailed),
    ],
)
def test_licensed_xml_identity_rights_and_entities_are_checked(raw, error):
    with pytest.raises(error):
        parse_licensed_jats(raw, DOI)


def test_actual_jats_fulltext_receipt_uses_exact_response_bytes(tmp_path, httpserver):
    httpserver.expect_request("/search").respond_with_json(
        {"resultList": {"result": [{"doi": DOI, "isOpenAccess": "Y", "pmcid": "PMC123"}]}}
    )
    httpserver.expect_request("/PMC123/fullTextXML").respond_with_data(jats(), content_type="application/xml")
    run = session(tmp_path)
    paper = Paper("doi:" + DOI, "Article", doi=DOI)
    selected, text, receipt = licensed_fulltext(run, [paper], europepmc_endpoint=httpserver.url_for(""))
    assert selected is paper and SOURCE.strip() in text
    assert receipt["license_url"] == LICENSE_URL and receipt["provider"] == "europepmc"
    assert (run.directory / "fulltext_0_xml/body.bin").read_bytes() == jats()
    assert run.consumed["fulltext.txt"] == receipt["text_sha256"]


def test_real_pdf_extraction_and_wrong_identity_control():
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(30, 800, DOI)
    for index in range(4):
        pdf.drawString(
            30, 760 - index * 25, "A measured source result with calibrated observations and clear uncertainty."
        )
    pdf.save()
    assert "measured source" in _pdf_text(buffer.getvalue(), DOI)
    with pytest.raises(LiteratureFailed):
        _pdf_text(buffer.getvalue(), "10.1000/wrong")


def test_quote_annotation_rejects_fabrication_coercion_and_extra_fields():
    assert validate_annotation({"summary": "A short annotation", "source_quote": SOURCE[:40]}, SOURCE)["summary"]
    for value in (
        {"summary": None, "source_quote": SOURCE[:40]},
        {"summary": "annotation", "source_quote": "This fabricated sentence is absent."},
        {"summary": "annotation", "source_quote": SOURCE[:40], "path": "/tmp/code"},
    ):
        with pytest.raises(LiteratureFailed):
            validate_annotation(value, SOURCE)

    assert annotation_schema()["properties"]["summary"] == {"type": "string"}
    assert annotation_schema(SOURCE)["properties"]["summary"] == {"type": "string", "minLength": 1, "maxLength": 512}
    assert annotation_schema(SOURCE, labels=["yes", "no"])["properties"]["label"] == {
        "type": "string",
        "enum": ["yes", "no"],
    }
    # The generation bound does not truncate or relax independent response parsing.
    assert validate_annotation({"summary": "x" * 2000, "source_quote": SOURCE[:40]}, SOURCE)["summary"] == "x" * 2000
    with pytest.raises(LiteratureFailed):
        validate_annotation({"summary": "x" * 2001, "source_quote": SOURCE[:40]}, SOURCE)
    with pytest.raises(LiteratureFailed):
        exact_json('{"source_quote":"' + SOURCE[:40] + '","summary":"unterminated')


def test_real_local_model_worker_binds_provider_request_response_and_digest(tmp_path, httpserver):
    identity = "a" * 64
    httpserver.expect_request("/api/tags").respond_with_json({"models": [{"name": "unit-model", "digest": identity}]})
    httpserver.expect_request("/api/generate", method="POST").respond_with_json(
        {
            "model": "unit-model",
            "done": True,
            "eval_count": 5,
            "response": json.dumps({"summary": "source note", "source_quote": SOURCE[:40]}),
        }
    )
    run = session(tmp_path, endpoint=httpserver.url_for("").replace("localhost", "127.0.0.1"))
    generator = LocalGenerator(run, max_calls=1)
    schema = {"type": "object"}
    value = generator.generate("actual bounded prompt", schema)
    assert value["summary"] == "source note" and generator.model_sha256 == identity
    request = json.loads((run.directory / "model_1/request.json").read_text())
    assert request["prompt"] == "actual bounded prompt" and request["format"] == schema
    assert generator.calls[0]["eval_count"] == 5 and len(run.consumed) == 4
    with pytest.raises(LiteratureFailed, match="ceiling"):
        generator.generate("again", schema)


@pytest.mark.parametrize("model,tokens", [("wrong-model", 5), ("unit-model", 0), ("unit-model", 4096)])
def test_real_local_model_identity_and_token_controls(tmp_path, httpserver, model, tokens):
    httpserver.expect_request("/api/tags").respond_with_json({"models": [{"name": "unit-model", "digest": "a" * 64}]})
    httpserver.expect_request("/api/generate", method="POST").respond_with_json(
        {"model": model, "done": True, "eval_count": tokens, "response": '{"result":"responding"}'}
    )
    run = session(tmp_path, endpoint=httpserver.url_for("").replace("localhost", "127.0.0.1"))
    with pytest.raises(LiteratureFailed):
        LocalGenerator(run).generate("bounded prompt", {"type": "object"})
