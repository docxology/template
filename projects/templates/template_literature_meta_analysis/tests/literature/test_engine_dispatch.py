import argparse

from literature.engine_dispatch import ENGINE_SPECS, EngineSpec, dispatch_ordered, engine_enabled


def _args(**skip_flags: bool) -> argparse.Namespace:
    return argparse.Namespace(**skip_flags)


def test_engine_specs_covers_all_nine_engines_in_expected_order() -> None:
    names = tuple(spec.name for spec in ENGINE_SPECS)
    assert names == (
        "arxiv",
        "semantic_scholar",
        "openalex",
        "crossref",
        "pubmed",
        "sovietrxiv",
        "chinarxiv",
        "europepmc",
        "biorxiv",
    )


def test_engine_specs_skip_flags_and_config_keys_are_unique() -> None:
    skip_flags = [spec.skip_flag for spec in ENGINE_SPECS]
    config_keys = [spec.config_key for spec in ENGINE_SPECS]
    assert len(skip_flags) == len(set(skip_flags))
    assert len(config_keys) == len(set(config_keys))


def test_engine_spec_enabled_respects_skip_flag() -> None:
    spec = EngineSpec("crossref", "skip_crossref", "crossref")
    args = _args(skip_crossref=True)
    assert spec.enabled(args, {}, fast_api=False, injected=True) is False


def test_engine_spec_enabled_respects_config_toggle() -> None:
    spec = EngineSpec("crossref", "skip_crossref", "crossref")
    args = _args(skip_crossref=False)
    assert spec.enabled(args, {"crossref": False}, fast_api=False, injected=True) is False


def test_engine_spec_enabled_skips_when_fast_api_and_not_injected() -> None:
    spec = EngineSpec("crossref", "skip_crossref", "crossref")
    args = _args(skip_crossref=False)
    assert spec.enabled(args, {"crossref": True}, fast_api=True, injected=False) is False


def test_engine_spec_enabled_true_in_normal_case() -> None:
    spec = EngineSpec("crossref", "skip_crossref", "crossref")
    args = _args(skip_crossref=False)
    assert spec.enabled(args, {"crossref": True}, fast_api=False, injected=False) is True
    assert spec.enabled(args, {"crossref": True}, fast_api=True, injected=True) is True


def test_engine_enabled_non_special_engine_delegates_to_spec_enabled() -> None:
    spec = next(s for s in ENGINE_SPECS if s.name == "europepmc")
    args = _args(skip_europepmc=False)
    assert engine_enabled(spec, args, {"europepmc": True}, fast_api=False, url_injected=False) is True
    assert engine_enabled(spec, args, {"europepmc": True}, fast_api=True, url_injected=False) is False
    assert engine_enabled(spec, args, {"europepmc": True}, fast_api=True, url_injected=True) is True


def test_engine_enabled_biorxiv_respects_skip_flag_and_config() -> None:
    spec = next(s for s in ENGINE_SPECS if s.name == "biorxiv")
    args_skipped = _args(skip_biorxiv=True)
    assert engine_enabled(spec, args_skipped, {"biorxiv": True}, fast_api=False, url_injected=True) is False

    args_not_skipped = _args(skip_biorxiv=False)
    assert engine_enabled(spec, args_not_skipped, {"biorxiv": False}, fast_api=False, url_injected=True) is False


def test_engine_enabled_special_engines_ignore_fast_api_injection_gate() -> None:
    for name, skip_flag in (
        ("arxiv", "skip_arxiv"),
        ("semantic_scholar", "skip_s2"),
        ("openalex", "skip_openalex"),
    ):
        spec = next(s for s in ENGINE_SPECS if s.name == name)
        args = _args(**{skip_flag: False})
        assert engine_enabled(spec, args, {name: True}, fast_api=True, url_injected=False) is True


def test_engine_enabled_special_engines_still_honor_skip_flag() -> None:
    for name, skip_flag in (
        ("arxiv", "skip_arxiv"),
        ("semantic_scholar", "skip_s2"),
        ("openalex", "skip_openalex"),
    ):
        spec = next(s for s in ENGINE_SPECS if s.name == name)
        args = _args(**{skip_flag: True})
        assert engine_enabled(spec, args, {name: True}, fast_api=False, url_injected=True) is False


def test_engine_enabled_special_engines_honor_config_toggle_regression() -> None:
    """Regression: engine_enabled() previously ignored the `engines` config map
    for arxiv/semantic_scholar/openalex, contradicting search_runner.py's real
    per-engine gating which honors the config toggle for all nine engines."""
    for name, skip_flag in (
        ("arxiv", "skip_arxiv"),
        ("semantic_scholar", "skip_s2"),
        ("openalex", "skip_openalex"),
    ):
        spec = next(s for s in ENGINE_SPECS if s.name == name)
        args = _args(**{skip_flag: False})
        assert engine_enabled(spec, args, {name: False}, fast_api=False, url_injected=True) is False


def test_dispatch_ordered_invokes_runners_in_route_order() -> None:
    calls: list[str] = []
    runners = {
        "arxiv": lambda: calls.append("arxiv"),
        "crossref": lambda: calls.append("crossref"),
        "biorxiv": lambda: calls.append("biorxiv"),
    }
    dispatch_ordered(["biorxiv", "arxiv", "crossref"], runners)
    assert calls == ["biorxiv", "arxiv", "crossref"]


def test_dispatch_ordered_skips_keys_with_no_registered_runner() -> None:
    calls: list[str] = []
    runners = {"arxiv": lambda: calls.append("arxiv")}
    dispatch_ordered(["arxiv", "semantic_scholar", "openalex"], runners)
    assert calls == ["arxiv"]
